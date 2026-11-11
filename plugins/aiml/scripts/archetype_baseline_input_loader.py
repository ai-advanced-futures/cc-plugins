"""Loader + validator for §7.12 archetype-cost-samples.

Reads the federation input, Draft7-validates against the shared FormatChecker,
and returns a frozen ArchetypeCostSamples carrying BOTH the per-archetype sample
map AND the envelope fields (engagement_id, measurement_window, telemetry_source)
the §7.13 output requires — so the emitter passes them through WITHOUT re-reading
the raw input. No imports from plugins/pricing/ (Charter §6.3 mandate).
"""

from __future__ import annotations

import functools
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft7Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from _safe_input import read_json  # noqa: E402

INPUT_SCHEMA_PATH = SCHEMAS_DIR / "archetype-cost-samples.schema.json"


@dataclass(frozen=True)
class ArchetypeSampleEntry:
    cost_samples: tuple[float, ...]
    sample_size_n: int
    present: bool


@dataclass(frozen=True)
class ArchetypeCostSamples:
    engagement_id: str
    measurement_window: dict
    telemetry_source: str
    archetypes: dict[str, ArchetypeSampleEntry]


@functools.lru_cache(maxsize=1)
def _input_schema() -> dict:
    return json.loads(INPUT_SCHEMA_PATH.read_text())


def load_and_validate(path: Path) -> ArchetypeCostSamples:
    """Parse + schema-validate an archetype-cost-samples v1.0.0 file."""
    obj = read_json(path)
    Draft7Validator(_input_schema(), format_checker=FORMAT_CHECKER).validate(obj)
    archetypes = {
        name: ArchetypeSampleEntry(
            cost_samples=tuple(entry["cost_samples"]),
            sample_size_n=entry["sample_size_n"],
            present=entry["present"],
        )
        for name, entry in obj["archetypes"].items()
    }
    return ArchetypeCostSamples(
        engagement_id=obj["engagement_id"],
        measurement_window=obj["measurement_window"],
        telemetry_source=obj["telemetry_source"],
        archetypes=archetypes,
    )
