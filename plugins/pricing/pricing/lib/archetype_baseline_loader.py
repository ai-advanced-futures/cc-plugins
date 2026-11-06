"""Consumer-side loader for the §7.13 archetype-baseline-telemetry artifact.

pricing reads the aiml-produced artifact via its OWN jsonschema reader (no aiml
import). Graceful fallback: None/absent → {}. The schema file is in the schema
folder of this plugin (schemas/agentic-pricing/).
"""
from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft7Validator


@dataclass(frozen=True)
class TelemetryBaseline:
    baseline_cost_per_interaction: float
    sample_size_n: int
    aggregation: str


def _schema_path() -> Path:
    """Location of the telemetry schema in the schema folder of this plugin."""
    return Path(__file__).resolve().parents[2] / "schemas" / "agentic-pricing" / "archetype-baseline-telemetry.schema.json"


@functools.lru_cache(maxsize=1)
def _schema() -> dict:
    return json.loads(_schema_path().read_text())


def load_archetype_baselines(path: str | Path | None) -> dict[str, TelemetryBaseline]:
    """Read + validate the §7.13 artifact; return {} when path is None or file is absent."""
    if path is None:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    obj = json.loads(p.read_text())
    Draft7Validator(_schema()).validate(obj)
    return {
        name: TelemetryBaseline(
            baseline_cost_per_interaction=b["baseline_cost_per_interaction"],
            sample_size_n=b["sample_size_n"],
            aggregation=b["aggregation"],
        )
        for name, b in obj["baselines"].items()
    }
