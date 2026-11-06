"""Loader + validator for the consumed §7.3 cost-amplifier-readout.

Draft7-validates against the EXISTING cost-amplifier-readout.schema.json, then
applies the §2.1 positivity guard. Returns a frozen CostAmplifierReadout. No
imports from the pricing plugin (Charter §6.3 mandate).
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

INPUT_SCHEMA_PATH = SCHEMAS_DIR / "cost-amplifier-readout.schema.json"


@dataclass(frozen=True)
class CostAmplifierReadout:
    engagement_id: str
    produced_at: str
    mode: str
    composite_p75: float
    composite_p95: float


@functools.lru_cache(maxsize=1)
def _input_schema() -> dict:
    return json.loads(INPUT_SCHEMA_PATH.read_text())


def load_and_validate(path) -> CostAmplifierReadout:
    """Parse + schema-validate a cost-amplifier-readout, then guard positivity."""
    obj = json.loads(Path(path).read_text())
    Draft7Validator(_input_schema(), format_checker=FORMAT_CHECKER).validate(obj)
    p75 = obj["composite_p75"]
    p95 = obj["composite_p95"]
    if p75 <= 0 or p95 <= 0:
        raise ValueError(
            f"cost-amplifier-readout composite must be > 0 "
            f"(got composite_p75={p75}, composite_p95={p95})"
        )
    return CostAmplifierReadout(
        engagement_id=obj["engagement_id"],
        produced_at=obj["produced_at"],
        mode=obj["mode"],
        composite_p75=p75,
        composite_p95=p95,
    )
