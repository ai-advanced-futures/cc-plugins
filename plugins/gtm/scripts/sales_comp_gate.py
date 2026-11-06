"""Deterministic Phase-3 sales-comp cliff-recommendation rule.

Pure function: no I/O, no agent judgment. The agent decides WHETHER each
precondition is met (the 5 booleans) and supplies the prior state; this module
maps inputs -> {proceed, pause, re_pause}. See ADR-003.
"""
from __future__ import annotations

# Framework precondition #1: a top-quintile rep losing >15% cash comp blocks Phase 3.
_AT_RISK_THRESHOLD = 15.0


def classify_cliff(
    preconditions_met: dict[str, bool],
    top_quintile_at_risk_pct: float,
    prior_recommendation: str | None,
    re_pause_trigger_fired: bool,
) -> str:
    # re_pause is the regression escape hatch — reachable ONLY from a prior
    # `proceed` with an active risk-register trigger. Checked first so a
    # regression in a previously-cleared program is never masked by the
    # ordinary pause rule.
    if prior_recommendation == "proceed" and re_pause_trigger_fired:
        return "re_pause"
    if (not all(preconditions_met.values())) or top_quintile_at_risk_pct > _AT_RISK_THRESHOLD:
        return "pause"
    return "proceed"
