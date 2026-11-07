#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""RUN_DETECTORS executor: runs the requested tiers over a document's zones,
computes human-zone baselines, calls verdicts.decide, writes
run-<id>/scores-iter-N.json. The orchestrator invokes this CLI via Bash —
it never reads artifact text (Layer 1c).

Consent pre-flight (spec §3.2/§7): the api tier requires api_consent: true
in <project_dir>/config.yaml — recorded once by /setup. Absent -> the tier
is UNAVAILABLE with reason "consent not recorded", identically on /check
and /humanize. Deterministic; no agent judgment.

Human-zone baselines are computed for the heuristics tier only in v0.1.0;
the hf/api tiers run without a baseline clause (spec §4). [inferred]"""
import json
import statistics
from pathlib import Path

import api_detectors
import heuristics
import hf_detectors
import question_gate
import verdicts
import yaml
import zone_parser

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MIN_WORDS = 50


class InputTooShortError(ValueError):
    pass


def _load_config():
    return yaml.safe_load((PLUGIN_ROOT / "config" / "detectors.yaml").read_text())


def _consent_recorded(project_dir):
    cfg = Path(project_dir) / "config.yaml"
    if not cfg.exists():
        return False
    return bool((yaml.safe_load(cfg.read_text()) or {}).get("api_consent"))


def _zones_for(doc, decisions_path=None):
    doc = Path(doc)
    if doc.suffix in (".md", ".txt", ""):
        return zone_parser.parse_zones(doc), "markdown"
    import extract_prose
    # [inferred] Thread the zone-mapping decisions through so include-resolved
    # ambiguous zones are SCORED, not just extracted at ingest — mirrors
    # extract_prose's own --decisions CLI contract.
    zones, _ = extract_prose.extract(doc, decisions_path=decisions_path)
    return zones, "code"


def _load_adjudication(gate_path):
    if not gate_path:
        return None
    p = Path(gate_path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _group_counts(cands):
    """Occurrences per (content_hash, zone_id) group. The hash is produced by
    question_gate.content_hash(normalized_text) — the same producer scan() uses
    for the id — never parsed back out of the `-N`-suffixed id string."""
    counts = {}
    for c in cands:
        key = (question_gate.content_hash(c["normalized_text"]), c["zone_id"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def _populate_original_lines(gate, original_path, doc_path):
    """Join candidate -> original_line on (id, zone_id). No-op when the gate
    carries no candidates (code surface, EXEMPT-by-override, zero candidates).

    The id's ordinal `-N` suffix is assigned per-scan by order of appearance, so
    the (id, zone_id) join is only sound when the original and the candidate
    agree on how many occurrences a (content_hash, zone_id) group has. If a
    rewrite added or removed an occurrence the surviving ordinals no longer
    correspond, and joining would silently resolve to a deleted occurrence's
    line. For such groups we do NOT guess: original_line falls back to the
    candidate's own line and original_line_ambiguous is set. Every candidate
    carries original_line_ambiguous (False on the sound path) so consumers never
    see a missing key."""
    if not gate.get("candidates"):
        return
    original_path = Path(original_path)
    if original_path == Path(doc_path):     # same bytes -> the join is the identity
        for c in gate["candidates"]:
            c["original_line"] = c["line"]
            c["original_line_ambiguous"] = False
        return
    orig_zones, _ = _zones_for(original_path)
    orig_cands = question_gate.scan(original_path, orig_zones)
    by_key = {(c["id"], c["zone_id"]): c["line"] for c in orig_cands}
    orig_counts = _group_counts(orig_cands)
    cand_counts = _group_counts(gate["candidates"])
    for c in gate["candidates"]:
        group = (question_gate.content_hash(c["normalized_text"]), c["zone_id"])
        if orig_counts.get(group, 0) == cand_counts.get(group, 0):
            c["original_line"] = by_key.get((c["id"], c["zone_id"]), c["line"])
            c["original_line_ambiguous"] = False
        else:
            c["original_line"] = c["line"]
            c["original_line_ambiguous"] = True


def _unavailable(reason):
    return {"status": "UNAVAILABLE", "reason": reason, "detectors": {}}


def _tier_heuristics(ai_zones):
    per_zone = {}
    for z in ai_zones:
        m = heuristics.analyze_with_hits(z["text"])
        # [inferred] Spec §7: per-zone shortness never refuses; under-50-word
        # zones are scored with a low-confidence flag instead.
        m["low_confidence"] = len(z["text"].split()) < MIN_WORDS
        per_zone[z["id"]] = m
    worst = max(per_zone.values(), key=lambda m: m["composite_ai_score"])
    return {
        "status": "OK",
        "detectors": {"heuristics": worst["composite_ai_score"]},
        "structural": {"burstiness": worst["burstiness"], "ttr": worst["ttr"]},
        "zones": per_zone,
    }


def _tier_hf(ai_zones, config):
    if not hf_detectors.available():
        return _unavailable("torch/transformers not installed")
    text = "\n\n".join(heuristics.strip_markdown(z["text"]) for z in ai_zones)
    # [inferred] score_text_all reads config["detectors"] + config["inference"];
    # remap the plugin YAML's hf_detectors key and pass the inference block so
    # chunk_token_max/stride/device in detectors.yaml are live, not dead config.
    results = hf_detectors.score_text_all(
        text, {"detectors": config["hf_detectors"],
               "inference": config.get("inference", {})})
    dets = {r["detector_id"]: round(r["score"] * 100, 1)
            for r in results if r.get("score") is not None}
    if not dets:
        return _unavailable("all hf detectors errored")
    return {"status": "OK", "detectors": dets, "structural": {}}


def _tier_api(ai_zones, project_dir, config):
    if not _consent_recorded(project_dir):
        return _unavailable("consent not recorded")
    text = "\n\n".join(z["text"] for z in ai_zones)
    # [inferred] detectors.yaml's api_detectors list is live config: only the
    # listed adapters run (defaults to all registered adapters when absent).
    results = [a.check(text) for name, a in api_detectors.ADAPTERS.items()
               if name in config.get("api_detectors", list(api_detectors.ADAPTERS))]
    dets = {r["id"]: r["composite"] for r in results if r["status"] == "OK"}
    if not dets:
        reasons = "; ".join(f"{r['id']}: {r['reason']}" for r in results)
        return _unavailable(reasons)
    return {"status": "OK", "detectors": dets, "structural": {}}


def _write_scores(run_dir, payload, iteration):
    run_dir.mkdir(parents=True, exist_ok=True)
    out = run_dir / f"scores-iter-{iteration}.json"
    out.write_text(json.dumps(payload, indent=2))
    return out


def run(doc, run_dir, iteration, tiers, project_dir, decisions_path=None,
        gate_path=None, genre=None, original_path=None, gate_error=None):
    doc, run_dir = Path(doc), Path(run_dir)
    src_words = len(doc.read_text().split())
    if src_words < MIN_WORDS:
        raise InputTooShortError(
            f"{doc}: {src_words} words < {MIN_WORDS} — heuristics statistically meaningless"
        )
    if "all" in tiers:
        tiers = ["heuristics", "hf", "api"]
    config = _load_config()
    zones, source_surface = _zones_for(doc, decisions_path=decisions_path)

    # --- gate: always scanned; never opt-in; before the early return ---
    candidates = question_gate.scan(doc, zones)
    adjudication = _load_adjudication(gate_path)   # None on absent/unreadable/malformed
    gate = question_gate.evaluate(candidates, adjudication, genre_override=genre,
                                  source_surface=source_surface,
                                  gate_error=gate_error)
    _populate_original_lines(gate, original_path or doc, doc)

    ai_zones = [z for z in zones if z["author"] != "human"]
    human_zones = [z for z in zones if z["author"] == "human"]

    if not ai_zones:
        # [inferred] All zones author="human": nothing rewritable -> trivial
        # PASS with a note (spec-consistent zero-ai-zones behavior; avoids a
        # max()-on-empty crash and scoring empty strings in hf/api tiers).
        v = {"verdict": "PASS", "strictest_tier": None, "tier_verdicts": {},
             "baseline": None, "note": "no ai/mixed zones — nothing to check"}
        v = verdicts.apply_gate_override(v, gate)   # lattice rules 1-2 only
        return _write_scores(run_dir, {
            "doc": str(doc), "iteration": iteration,
            "tiers": {}, "baselines": None,
            "verdict": v, "gate": gate,
            "loop_scalar": {"tier": None, "composite": None},
        }, iteration)

    scores, baselines = {}, {}
    for t in tiers:
        if t == "heuristics":
            scores[t] = _tier_heuristics(ai_zones)
            if human_zones:
                baselines[t] = {"heuristics": round(statistics.mean(
                    heuristics.analyze(z["text"])["composite_ai_score"]
                    for z in human_zones), 1)}
        elif t == "hf":
            scores[t] = _tier_hf(ai_zones, config)
        elif t == "api":
            scores[t] = _tier_api(ai_zones, project_dir, config)
        else:
            raise ValueError(f"unknown tier: {t}")

    baselines = baselines or None
    verdict = verdicts.decide(scores, baselines, config["thresholds"], gate=gate)
    strictest = verdict["strictest_tier"]
    composite = (max(scores[strictest]["detectors"].values())
                 if strictest and scores[strictest].get("detectors") else None)

    return _write_scores(run_dir, {
        "doc": str(doc), "iteration": iteration,
        "tiers": scores, "baselines": baselines,
        "verdict": verdict, "gate": gate,
        "loop_scalar": {"tier": strictest, "composite": composite},
    }, iteration)


if __name__ == "__main__":
    import argparse

    # allow_abbrev=False: `--gate-error` must be an error, not a short form of `--gate-error-file`.
    ap = argparse.ArgumentParser(description="Run detector tiers over a document", allow_abbrev=False)
    ap.add_argument("doc")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--iter", type=int, default=1)
    ap.add_argument("--tiers", default="heuristics", help="csv: heuristics,hf,api")
    ap.add_argument("--project-dir", default=".prose-authenticity")
    ap.add_argument("--decisions", help="zone-mapping-decisions.json for code "
                                        "surfaces (mirrors extract_prose)")  # [inferred]
    ap.add_argument("--gate", help="adjudication.json produced by question-adjudicator")
    ap.add_argument("--genre", choices=question_gate.GENRES,
                    help="override the adjudicator's genre classification")
    ap.add_argument("--original", help="the original document, for original_line")
    ap.add_argument("--gate-error-file",
                    help="file that holds the adjudicator dispatch error (UTF-8, white space at the ends removed)")
    args = ap.parse_args()
    gate_error = None
    if args.gate_error_file:
        try:
            gate_error = Path(args.gate_error_file).read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            gate_error = f"gate error file not readable: {args.gate_error_file}"
    out = run(args.doc, args.run_dir, args.iter,
              [t.strip() for t in args.tiers.split(",") if t.strip()], args.project_dir,
              decisions_path=args.decisions, gate_path=args.gate, genre=args.genre,
              original_path=args.original, gate_error=gate_error)
    data = json.loads(out.read_text())
    print(f"{out}\nverdict={data['verdict']['verdict']} tier={data['verdict']['strictest_tier']} "
          f"composite={data['loop_scalar']['composite']}")
