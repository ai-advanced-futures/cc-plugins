# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""The 5 assumptions of Phase 7: the default of each, and the check of a value that is marked as a default (STORY-287).

The default values come from `questions/discover.json`, and the markers from `result-file.json`. This file
keeps no second copy of them. It has no dependency, so `run_phase_7.py` and `write-run` can both read it.
"""
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
INPUTS = ("labor_rate", "average_error_cost", "average_revenue", "revenue_margin", "risk_tolerance")
# How evc-calculator can settle an assumption (agents/evc-calculator.md, step `inputs`).
SOURCES = ("person", "recommended", "asked", "default")
DEFAULT = "default"


def defaults() -> dict:
    """The default of each assumption, from the questions file of the discover command."""
    questions = json.loads((PLUGIN_ROOT / "questions" / "discover.json").read_text(encoding="utf-8"))["questions"]
    found = {q["input"]: q["default"] for q in questions if q.get("input") in INPUTS and "default" in q}
    missing = [name for name in INPUTS if name not in found]
    if missing:
        raise ValueError("questions/discover.json has no default for %s" % ", ".join(missing))
    return found


def markers() -> dict:
    """The default marker of each assumption, from the result file declaration of the plugin."""
    declared = json.loads((PLUGIN_ROOT / "result-file.json").read_text(encoding="utf-8"))["defaults"]
    return {d["input"]: d["marker"] for d in declared if d.get("input") in INPUTS}


def source_of(sources, name) -> str:
    """How the input was settled. An input with no recorded source counts as a default (agents/output-assembler.md)."""
    value = sources.get(name) if isinstance(sources, dict) else None
    return DEFAULT if value is None else value


def is_default(value, default) -> bool:
    """75 and 75.0 are the same number, and 0.2 and 0.20 too. A string must be the same string."""
    if isinstance(default, str):
        return value == default
    return not isinstance(value, bool) and isinstance(value, (int, float)) and float(value) == float(default)


def problems(assumptions, sources, strict=False) -> list:
    """One line for each assumption that is marked as a default and does not have the default value.

    With `strict`, also one line for each source that is not one of SOURCES.
    """
    lines = []
    for name, default in defaults().items():
        source = source_of(sources, name)
        if strict and source not in SOURCES:
            lines.append("assumption_sources: %s is %r, but it must be one of %s" % (name, source, ", ".join(SOURCES)))
        elif source == DEFAULT and name in assumptions and not is_default(assumptions[name], default):
            lines.append(
                "assumptions: %s is %r and its source is default, but the default is %r. Use %r, or use a value "
                "that a person gave and record its source" % (name, assumptions[name], default, default)
            )
    return lines
