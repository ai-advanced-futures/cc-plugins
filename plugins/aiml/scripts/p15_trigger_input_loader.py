"""Input + history loader and threshold resolver for P15 trigger detection.

Per Charter sub-spec 4b §6.4 + §3.3 D3 4-way precedence. No I/O in the
detector itself — all reads happen here. No imports from plugins/pricing/
per Charter §6.3 reimplementation mandate (enforced by
test_no_pricing_lib_imports.py).
"""
from __future__ import annotations

import functools
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import jsonschema
from jsonschema import Draft7Validator

# Ensure the scripts dir is on sys.path so the shared module is importable when
# this loader is invoked as a script directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from _safe_input import read_json  # noqa: E402

INPUT_SCHEMA_PATH = SCHEMAS_DIR / "amplifier-telemetry-input.schema.json"


class NoThresholdsResolvedError(RuntimeError):
    """Raised when detection sources are present but no thresholds resolved."""


@dataclass(frozen=True)
class ResolvedThresholds:
    threshold_pct: float | None
    cap_pct: float | None
    # list of {metric_id, target_value, target_unit?} per Charter sub-spec 4b §5.2
    quality_floor_targets: list[dict] | None


@functools.lru_cache(maxsize=1)
def _input_schema() -> dict:
    return json.loads(INPUT_SCHEMA_PATH.read_text())


def load_input(path: Path) -> dict:
    """Parse + schema-validate an amplifier-telemetry-input v1.1.0 file."""
    obj = read_json(path)
    Draft7Validator(_input_schema(), format_checker=FORMAT_CHECKER).validate(obj)
    return obj


def load_history(path: Path | None) -> list[dict] | None:
    """Parse + validate a JSON array of v1.1.0 input objects. None if path absent."""
    if path is None:
        return None
    arr = read_json(path)
    if not isinstance(arr, list):
        raise ValueError(f"history file must contain a JSON array, got {type(arr).__name__}")
    schema = _input_schema()
    validator = Draft7Validator(schema, format_checker=FORMAT_CHECKER)
    for i, el in enumerate(arr):
        try:
            validator.validate(el)
        except jsonschema.ValidationError as e:
            raise ValueError(f"history[{i}] schema validation failed: {e.message}") from e
    return arr


def resolve_thresholds(
    dispatch_context: dict,
    input_file: dict,
    has_history: bool,
) -> ResolvedThresholds:
    """Resolve thresholds per spec §6.4 (4-way precedence; short-circuit on no sources).

    Precedence:
      1. dispatch_context (CLI flags)
      2. input_file["contractual_thresholds"]
      3. input_file["quality_metrics"][*]["contracted_floor"]  (per-metric, handled in detector)
      4. None present → short-circuit (return all-None) OR raise if detection needed.

    Per spec §6.4 T1C-2: gate-with-ANY semantics — loader passes if AT LEAST ONE
    metric has a floor source. Per-metric skips happen in detect() (§6.2) and
    append a detection_note (row 7c). Mixed coverage is fine at loader level.
    """
    threshold_pct = dispatch_context.get("threshold_pct")
    cap_pct = dispatch_context.get("cap_pct")
    quality_floor_targets = dispatch_context.get("quality_floor_targets")

    ct = input_file.get("contractual_thresholds") or {}
    if threshold_pct is None:
        threshold_pct = ct.get("p15_threshold_pct")
    if cap_pct is None:
        cap_pct = ct.get("p15_cap_pct")
    if quality_floor_targets is None:
        quality_floor_targets = ct.get("quality_floor_targets")

    has_cost_input = bool(input_file.get("amplifiers"))  # falsy for missing OR empty dict
    has_quality_input = bool(input_file.get("quality_metrics"))

    # Short-circuit when no detection sources present
    if not has_cost_input and not has_quality_input:
        return ResolvedThresholds(threshold_pct, cap_pct, quality_floor_targets)

    needs_cost = has_cost_input and has_history
    if needs_cost and threshold_pct is None:
        raise NoThresholdsResolvedError(
            "threshold_pct missing from both dispatch context and input file's contractual_thresholds"
        )

    # Quality-floor coverage union check (gate-with-ANY per spec §6.4 T1C-2):
    if has_quality_input:
        qm = input_file["quality_metrics"]
        any_coverage = False
        floor_target_ids = {t["metric_id"] for t in (quality_floor_targets or [])}
        for entry in qm:
            mid = entry["metric_id"]
            if "contracted_floor" in entry or mid in floor_target_ids:
                any_coverage = True
                break
        if not any_coverage:
            raise NoThresholdsResolvedError(
                "quality_floor_targets missing from dispatch context + contractual_thresholds "
                "AND no quality_metrics[].contracted_floor for ANY metric"
            )

    return ResolvedThresholds(threshold_pct, cap_pct, quality_floor_targets)
