from __future__ import annotations

import json
from pathlib import Path

from scripts.gtm_constants import ALL_FLAGS, INTEGRITY_AGENTS


def _validate_flag_name(agent_name: str) -> None:
    if agent_name not in ALL_FLAGS:
        raise ValueError(f"Unknown agent: '{agent_name}'. Must be one of: {ALL_FLAGS}")


def _validate_integrity_agent(agent_name: str) -> None:
    if agent_name not in INTEGRITY_AGENTS:
        raise ValueError(
            f"Unknown integrity agent: '{agent_name}'. Must be one of: {INTEGRITY_AGENTS}"
        )


def set_flag(context: dict, agent_name: str, value: bool = True) -> dict:
    _validate_flag_name(agent_name)
    flags = dict(context.get("completion_flags", {}))
    flags[agent_name] = value
    return {**context, "completion_flags": flags}


def get_flag(context: dict, agent_name: str) -> bool:
    return bool(context.get("completion_flags", {}).get(agent_name, False))


def set_integrity_score(context: dict, agent_name: str, score: float) -> dict:
    _validate_integrity_agent(agent_name)
    scores = dict(context.get("integrity_scores", {}))
    scores[agent_name] = score
    return {**context, "integrity_scores": scores}


def set_completion_log(context: dict, agent_name: str, summary: str) -> dict:
    log = dict(context.get("completion_log", {}))
    log[agent_name] = summary
    return {**context, "completion_log": log}


_WAVE_ROUTING_PATH = Path(__file__).parent.parent / "definitions" / "wave-routing.json"
_WAVES: dict[str, list[str]] = json.loads(_WAVE_ROUTING_PATH.read_text())


def set_floor_breach(context: dict, agent_name: str, score: float, issues: list) -> dict:
    _validate_integrity_agent(agent_name)
    error_log = dict(context.get("error_log", {}))
    error_log[f"{agent_name}_integrity"] = {
        "breach": True,
        "score": score,
        "top_issues": list(issues),
    }
    flags = dict(context.get("completion_flags", {}))
    flags[f"{agent_name}_integrity"] = False
    return {**context, "error_log": error_log, "completion_flags": flags}


def is_wave_complete(context: dict, wave: str) -> bool:
    if wave not in _WAVES:
        raise ValueError(f"Unknown wave: '{wave}'. Must be one of: {list(_WAVES.keys())}")
    flags = context.get("completion_flags", {})
    return all(flags.get(flag, False) for flag in _WAVES[wave])
