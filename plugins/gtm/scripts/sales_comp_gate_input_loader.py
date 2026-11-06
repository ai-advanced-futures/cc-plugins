"""Load + validate the sales-comp gate INPUT file.

Validates the 5 precondition booleans, top_quintile_at_risk_pct, and the two
derivation inputs (prior_recommendation, re_pause_trigger_fired) that are NOT in
the output schema. Raises ValueError on any malformed input (caught by the
emitter PHASE-1). Package-form imports only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_PRECONDITION_KEYS = (
    "ae_comp_impact_modeled",
    "top_3_quota_retention_completed",
    "hire_back_runway_filled",
    "competitor_comp_benchmarked",
    "executive_sponsor_named",
)
_PRIOR_ENUM = ("proceed", "pause", "re_pause")


@dataclass(frozen=True)
class SalesCompGateInput:
    engagement_id: str
    schema_version: str
    preconditions_met: dict
    top_quintile_at_risk_pct: float
    prior_recommendation: str | None
    re_pause_trigger_fired: bool


def load_and_validate(path: Path | str) -> SalesCompGateInput:
    raw = json.loads(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ValueError("gate input must be a JSON object")

    pm = raw.get("preconditions_met")
    if not isinstance(pm, dict):
        raise ValueError("preconditions_met must be an object")
    for k in _PRECONDITION_KEYS:
        if k not in pm:
            raise ValueError(f"preconditions_met missing required key: {k}")
        if not isinstance(pm[k], bool):
            raise ValueError(f"precondition {k} must be a boolean")
    preconditions = {k: pm[k] for k in _PRECONDITION_KEYS}

    pct = raw.get("top_quintile_at_risk_pct")
    if not isinstance(pct, (int, float)) or isinstance(pct, bool) or pct < 0:
        raise ValueError("top_quintile_at_risk_pct must be a number >= 0")

    prior = raw.get("prior_recommendation", None)
    if prior is not None and prior not in _PRIOR_ENUM:
        raise ValueError(f"prior_recommendation must be one of {_PRIOR_ENUM} or null")

    trigger = raw.get("re_pause_trigger_fired", False)
    if trigger is None:
        trigger = False
    if not isinstance(trigger, bool):
        raise ValueError("re_pause_trigger_fired must be a boolean")

    eid = raw.get("engagement_id")
    if not isinstance(eid, str):
        raise ValueError("engagement_id must be a string")
    sv = raw.get("schema_version")
    if not isinstance(sv, str):
        raise ValueError("schema_version must be a string")

    return SalesCompGateInput(
        engagement_id=eid,
        schema_version=sv,
        preconditions_met=preconditions,
        top_quintile_at_risk_pct=float(pct),
        prior_recommendation=prior,
        re_pause_trigger_fired=trigger,
    )
