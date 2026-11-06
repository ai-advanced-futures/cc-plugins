#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Deterministic loop control for the humanize loop (ADR-001).

The orchestrator agent NEVER decides iterate/stop — it calls this module
after every stage and does what next_action says. Pure state transitions;
persistence is plain JSON at .prose-authenticity/run-<id>/loop-state.json.

Actions (seven): RUN_QUESTION_SCAN -> (ADJUDICATE_GATE | RUN_DETECTORS) ->
RUN_DETECTORS -> (ACCEPT | DISPATCH_REWRITE) -> RUN_FACT_CHECK ->
(retry DISPATCH_REWRITE once on fact miss | next iteration | GIVE_UP).
The re-scan after a fact-checked rewrite is why every iteration re-enters at
RUN_QUESTION_SCAN, not RUN_DETECTORS: a rewrite must not smuggle in a new
rhetorical question undetected.
Plateau rule: improvement < min_delta between consecutive SAME-TIER scores
=> GIVE_UP. Tier change => delta undefined: counts toward the cap, not the
plateau test; the new tier re-baselines comparisons (spec §4).
"""
import json
from pathlib import Path

from question_gate import EXEMPT_GENRES
from verdicts import GATE_STATUSES

_PASS, _EXEMPT, _FAIL, _UNADJUDICATED = GATE_STATUSES

DEFAULT_MAX_ITERATIONS = 4
DEGRADED_MAX_ITERATIONS = 2   # when the fact guard is degraded (spec §3.3)
DEFAULT_MIN_DELTA = 5.0
FACT_MISS_MAX_RETRIES = 1


def init_state(max_iterations=DEFAULT_MAX_ITERATIONS, min_delta=DEFAULT_MIN_DELTA,
               genre_override=None):
    return {
        "iteration": 1,
        "max_iterations": max_iterations,
        "min_delta": min_delta,
        # start -> scanned -> (adjudicated ->) scored -> rewritten -> fact_checked
        "phase": "start",
        "verdict": None,
        "scores": [],                # [{iteration, tier, composite}]
        "best_iteration": None,      # [inferred] iteration with the lowest same-tier composite
        "fact_retries_this_iter": 0,
        "missing_facts": [],
        "candidate_count": 0,        # written by record_scan
        "gate": None,                # written by record_scores, from GateResult
        "genre_override": genre_override,
        "give_up_reason": None,      # written by next_action; read by orchestrator
    }


def record_scan(state, candidate_count):
    state["candidate_count"] = candidate_count
    state["phase"] = "scanned"


def record_adjudication(state):
    """Records that the step RAN, not that it succeeded. The orchestrator calls
    this on dispatch failure too, or the loop wedges in `scanned` forever."""
    state["phase"] = "adjudicated"


def record_scores(state, verdict, tier, composite, gate=None):
    state["scores"].append(
        {"iteration": state["iteration"], "tier": tier, "composite": composite}
    )
    state["verdict"] = verdict
    state["gate"] = gate
    state["phase"] = "scored"
    # Track the iteration with the lowest composite among scores sharing the
    # CURRENT tier (lower = better); ties keep the earliest. Recomputed from
    # full history so a tier that disappears and reappears still resolves to
    # its own best iteration, not merely the most recent one.
    if composite is not None:
        same_tier = [s for s in state["scores"]
                     if s["tier"] == tier and s["composite"] is not None]
        best = min(same_tier, key=lambda s: (s["composite"], s["iteration"]))
        state["best_iteration"] = best["iteration"]


def record_rewrite(state):
    state["phase"] = "rewritten"


def record_factcheck(state, missing):
    state["missing_facts"] = list(missing)
    if missing:
        state["fact_retries_this_iter"] += 1
        state["phase"] = "fact_missed"
    else:
        state["phase"] = "fact_checked"


def _plateaued(state):
    """Improvement < min_delta between the two latest SAME-TIER scores."""
    if len(state["scores"]) < 2:
        return False
    cur, prev = state["scores"][-1], state["scores"][-2]
    if cur["tier"] != prev["tier"]:
        return False                 # delta undefined on tier change
    if cur["composite"] is None or prev["composite"] is None:
        return False                 # [inferred] None composite (trivial PASS): plateau undefined
    return (prev["composite"] - cur["composite"]) < state["min_delta"]


def _gate_action_pre_cap(state, gate):
    """Gate rules 3, 4, 5 -> (action, reason) | None."""
    if gate.get("genre") == "verbatim":
        return ("GIVE_UP", "verbatim artifact — rewriting a record of an "
                           "utterance would make it false")
    if gate.get("status") == _FAIL:
        if gate.get("rewritable_remaining") == 0:
            return ("GIVE_UP", "rhetorical questions in human-authored zones — "
                               "manual fix required")
        if state["scores"] and state["scores"][-1]["tier"] is None:
            return ("GIVE_UP", "rhetorical questions flagged, but no detector "
                               "signal — never rewrite blind")
    return None


def _gate_action_post_cap(state, gate):
    """Gate rule 7 -> (action, reason) | None. Plateau exemption."""
    if gate.get("status") == _FAIL and gate.get("rewritable_remaining", 0) > 0:
        return ("DISPATCH_REWRITE", None)
    return None


def next_action(state):
    phase = state["phase"]
    if phase == "start":
        return "RUN_QUESTION_SCAN"
    if phase == "scanned":
        if state["candidate_count"] > 0 and \
                state.get("genre_override") not in EXEMPT_GENRES:
            return "ADJUDICATE_GATE"
        return "RUN_DETECTORS"
    if phase == "adjudicated":
        return "RUN_DETECTORS"
    if phase == "scored":
        state["give_up_reason"] = None
        gate = state.get("gate") or {}
        if state["verdict"] == "UNAVAILABLE":
            return "GIVE_UP"          # [inferred] no detector signal — never dispatch a rewrite blind
        if state["verdict"] == "PASS":
            return "ACCEPT"
        hit = _gate_action_pre_cap(state, gate)
        if hit:
            state["give_up_reason"] = hit[1]
            return hit[0]
        if state["iteration"] >= state["max_iterations"]:
            return "GIVE_UP"
        hit = _gate_action_post_cap(state, gate)
        if hit:
            return hit[0]
        if _plateaued(state):
            return "GIVE_UP"
        return "DISPATCH_REWRITE"
    if phase == "rewritten":
        return "RUN_FACT_CHECK"
    if phase == "fact_missed":
        if state["fact_retries_this_iter"] > FACT_MISS_MAX_RETRIES:
            return "GIVE_UP"
        return "DISPATCH_REWRITE"    # retry once, missing facts named in state
    if phase == "fact_checked":
        state["iteration"] += 1
        state["fact_retries_this_iter"] = 0
        state["missing_facts"] = []
        state["phase"] = "start"
        return "RUN_QUESTION_SCAN"    # NOT RUN_DETECTORS — the re-scan matters
    raise ValueError(f"unknown phase: {phase}")


def save_state(state, path):
    Path(path).write_text(json.dumps(state, indent=2))


def load_state(path):
    return json.loads(Path(path).read_text())


if __name__ == "__main__":
    import argparse

    import question_gate

    ap = argparse.ArgumentParser(description="Humanize-loop state machine")
    ap.add_argument("--state", required=True, help="Path to loop-state.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init")
    p_init.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    p_init.add_argument("--min-delta", type=float, default=DEFAULT_MIN_DELTA)
    p_init.add_argument("--genre-override", choices=question_gate.GENRES, default=None)
    sub.add_parser("next")
    p_scan = sub.add_parser("record-scan")
    p_scan.add_argument("--candidate-count", type=int, required=True)
    sub.add_parser("record-adjudication")
    p_sc = sub.add_parser("record-scores")
    p_sc.add_argument("--verdict", required=True)
    # [inferred] --tier/--composite are optional: a trivial PASS (zero ai/mixed
    # zones) reports tier=None composite=None, so `record-scores --verdict PASS`
    # alone must succeed — the orchestrator is a dumb executor of this CLI.
    p_sc.add_argument("--tier", default=None)
    p_sc.add_argument("--composite", type=float, default=None)
    # The gate arrives as the TOP-LEVEL `gate` key of scores-iter-N.json; this
    # CLI reads it, record_scores() itself does no file I/O.
    p_sc.add_argument("--gate", default=None, help="Path to scores-iter-N.json")
    sub.add_parser("record-rewrite")
    p_fc = sub.add_parser("record-factcheck")
    p_fc.add_argument("--missing", default="", help="Comma-separated missing fact ids")
    args = ap.parse_args()

    if args.cmd == "init":
        state = init_state(args.max_iterations, args.min_delta,
                           genre_override=args.genre_override)
    else:
        state = load_state(args.state)

    if args.cmd == "next":
        print(next_action(state))
    elif args.cmd == "record-scan":
        record_scan(state, args.candidate_count)
    elif args.cmd == "record-adjudication":
        record_adjudication(state)
    elif args.cmd == "record-scores":
        gate = json.loads(Path(args.gate).read_text()).get("gate") if args.gate else None
        record_scores(state, args.verdict, args.tier, args.composite, gate=gate)
    elif args.cmd == "record-rewrite":
        record_rewrite(state)
    elif args.cmd == "record-factcheck":
        record_factcheck(state, [m for m in args.missing.split(",") if m])
    save_state(state, args.state)
