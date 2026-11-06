#!/usr/bin/env python3
"""PASS/WARN/FAIL decision table. All thresholds in canonical composite
points [0,100] (model tiers report p(AI)*100 — the p(AI)<=0.5 <-> composite<=50
mapping lives HERE and nowhere else; adapters convert at the boundary).

Rules (spec §4):
- PASS: all detectors in the tier composite <= 50 AND composite <= baseline+10
  (one-sided — below-baseline always passes the clause, L-031).
- FAIL: >=2-detector tiers: >=2 detectors > 50. Single-detector tiers
  (heuristics): composite > 70; WARN in (50, 70].
- WARN: otherwise, incl. structural warns (burstiness < 0.40, TTR < 0.35 —
  a distinct non-composite threshold class).
- Final verdict = strictest AVAILABLE tier by fixed precedence api > hf >
  heuristics (never "worst verdict"; never counts detectors across tiers).

Gate override (ADR-005): `decide()` accepts an optional `gate` — the
rhetorical-question gate result — as a fourth verdict input that is NOT a tier
(no composite, no slot in TIER_PRECEDENCE). Its status is one of the four
`GATE_STATUSES`: a gate `PASS` or `EXEMPT` is a verdict no-op; a gate `FAIL`
overrides even a passing composite; a gate `UNADJUDICATED` forces the verdict to
UNAVAILABLE (question gate not adjudicated — fail-closed).
"""

TIER_PRECEDENCE = ["api", "hf", "heuristics"]

DEFAULT_THRESHOLDS = {
    "pass_max_composite": 50.0,
    "baseline_margin": 10.0,
    "multi_fail_count": 2,
    "single_fail_above": 70.0,
    "structural_warn": {"burstiness_below": 0.40, "ttr_below": 0.35},
}

_SEVERITY = {"PASS": 0, "WARN": 1, "FAIL": 2}

GATE_STATUSES = ("PASS", "EXEMPT", "FAIL", "UNADJUDICATED")

# Gate status -> the verdict it forces. Hoisted to module level so the AST
# doc-contract's ban on bare gate-status Compare operands is satisfiable inside
# apply_gate_override(), which must still WRITE tier-verdict strings.
_GATE_TO_VERDICT = {GATE_STATUSES[2]: "FAIL", GATE_STATUSES[3]: "UNAVAILABLE"}
_GATE_REASON = {GATE_STATUSES[3]: "question gate not adjudicated"}


def apply_gate_override(verdict, gate):
    """Lattice rules 1-2. The gate is a fourth verdict input, not a tier: it has
    no composite and no slot in TIER_PRECEDENCE, and it can override a PASS.

    gate PASS/EXEMPT are verdict no-ops and leave `verdict` byte-identical.
    """
    if not gate:
        return verdict
    forced = _GATE_TO_VERDICT.get(gate.get("status"))
    if forced is None:
        return verdict
    verdict["verdict"] = forced
    reason = _GATE_REASON.get(gate.get("status"))
    if reason:
        verdict["reason"] = reason
    return verdict


def decide_tier(tier_scores, tier_baselines, thresholds):
    """Verdict for ONE tier. tier_scores: {"status", "detectors": {id: composite},
    "structural": {burstiness, ttr}?}. tier_baselines: {id: composite} | None."""
    if tier_scores.get("status") != "OK" or not tier_scores.get("detectors"):
        return {"verdict": "UNAVAILABLE", "reasons": [tier_scores.get("reason", "no detectors")]}
    dets = tier_scores["detectors"]
    t = thresholds
    reasons = []

    above = [d for d, c in dets.items() if c > t["pass_max_composite"]]
    if len(dets) >= 2:
        if len(above) >= t["multi_fail_count"]:
            return {"verdict": "FAIL",
                    "reasons": [f"{len(above)} detectors composite > {t['pass_max_composite']}"]}
    else:
        only = next(iter(dets.values()))
        if only > t["single_fail_above"]:
            return {"verdict": "FAIL",
                    "reasons": [f"composite {only} > {t['single_fail_above']} (single-detector tier)"]}

    if above:
        reasons.append(f"detector(s) {above} composite > {t['pass_max_composite']}")
    if tier_baselines:
        for d, c in dets.items():
            b = tier_baselines.get(d)
            if b is not None and c > b + t["baseline_margin"]:
                reasons.append(f"{d}: composite {c} > baseline {b} + {t['baseline_margin']}")
    s = tier_scores.get("structural") or {}
    sw = t["structural_warn"]
    if s.get("burstiness") is not None and s["burstiness"] < sw["burstiness_below"]:
        reasons.append(f"burstiness {s['burstiness']} < {sw['burstiness_below']} (uniform rhythm)")
    if s.get("ttr") is not None and s["ttr"] < sw["ttr_below"]:
        reasons.append(f"TTR {s['ttr']} < {sw['ttr_below']} (low vocab diversity)")

    return {"verdict": "WARN" if reasons else "PASS", "reasons": reasons}


def decide(scores, baselines, thresholds, gate=None):
    """scores: {tier_name: tier_scores}. baselines: {tier_name: {id: composite}} | None
    (nullable — zero-human-zone runs drop the baseline clause and record null).
    Returns {verdict, strictest_tier, tier_verdicts, baseline}."""
    tier_verdicts = {
        name: decide_tier(ts, (baselines or {}).get(name), thresholds)
        for name, ts in scores.items()
    }
    strictest = next(
        (t for t in TIER_PRECEDENCE
         if t in tier_verdicts and tier_verdicts[t]["verdict"] != "UNAVAILABLE"),
        None,
    )
    out = {
        "verdict": tier_verdicts[strictest]["verdict"] if strictest else "UNAVAILABLE",
        "strictest_tier": strictest,
        "tier_verdicts": tier_verdicts,
        "baseline": baselines,
    }
    if gate is not None:
        out["gate"] = gate
        out = apply_gate_override(out, gate)
    return out
