from __future__ import annotations

import json
from pathlib import Path

from scripts.gtm_constants import ALL_FLAGS, CONTENT_AGENTS, INTEGRITY_AGENTS

_MQL_THRESHOLDS_PATH = Path(__file__).parent.parent / "definitions" / "mql-thresholds.json"
MQL_THRESHOLDS: dict = json.loads(_MQL_THRESHOLDS_PATH.read_text())


def create_directories(base_dir: str = ".") -> None:
    base = Path(base_dir)
    for agent in CONTENT_AGENTS:
        (base / ".gtm" / "working" / agent).mkdir(parents=True, exist_ok=True)
    (base / ".gtm" / "audit").mkdir(parents=True, exist_ok=True)
    (base / "gtm-output").mkdir(parents=True, exist_ok=True)


def initialize_flags(context: dict) -> dict:
    existing_flags = context.get("completion_flags", {})
    merged_flags = {flag: False for flag in ALL_FLAGS}
    merged_flags.update(existing_flags)

    existing_log = context.get("completion_log", {})
    existing_scores = context.get("integrity_scores", {})
    existing_errors = context.get("error_log", {})

    scores = {agent: None for agent in INTEGRITY_AGENTS}
    scores.update({k: v for k, v in existing_scores.items() if k in INTEGRITY_AGENTS})

    errors = {f"{agent}_integrity": None for agent in INTEGRITY_AGENTS}
    errors.update({k: v for k, v in existing_errors.items() if k in errors})

    return {
        **context,
        "completion_flags": merged_flags,
        "completion_log": existing_log,
        "integrity_scores": scores,
        "error_log": errors,
        "_meta": {**context.get("_meta", {}), "dispatched_agents": context.get("_meta", {}).get("dispatched_agents", [])},
    }


def add_dispatched_agent(context: dict, agent_name: str) -> dict:
    """Record that an agent was dispatched in this session (for Wave 0 polling)."""
    meta = dict(context.get("_meta", {}))
    dispatched = list(meta.get("dispatched_agents", []))
    if agent_name not in dispatched:
        dispatched.append(agent_name)
    meta["dispatched_agents"] = dispatched
    return {**context, "_meta": meta}


# Default behavioral signals seeded into preliminary_mql.
# marketing-agent may ADD signals (never remove) — see agents/marketing-agent.md Rules.
# Threshold values live in definitions/mql-thresholds.json.
_DEFAULT_BEHAVIORAL_SIGNALS = ["page_visit_3+", "content_download", "demo_request"]
_DEFAULT_STAGE = "pmf"


def _normalize_stage(stage: str) -> str:
    normalized = stage.lower().strip()
    return normalized if normalized in MQL_THRESHOLDS else _DEFAULT_STAGE


def seed_mql(context: dict, business_stage: str) -> dict:
    stage = _normalize_stage(business_stage)
    thresholds = MQL_THRESHOLDS[stage]
    preliminary_mql = {
        "icp_fit_score_threshold": thresholds["icp_fit_score_threshold"],
        "required_behavioral_signals": list(_DEFAULT_BEHAVIORAL_SIGNALS),
        "engagement_score_minimum": thresholds["engagement_score_minimum"],
        "derived_from": "profiling_heuristic",
    }
    return {**context, "preliminary_mql": preliminary_mql}
