#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""CLI emitter for P15 trigger events. Wires loader → detector → JSON output.

Per Charter sub-spec 4b §6 + §10A CLI flag table. MUST-omit detection_notes
when empty per §3.15 T2A-7. Output validates against
p15-trigger-event.schema.json before write.

Exit codes:
  0 — success
  1 — user error (missing thresholds, schema-invalid input, file not found)
  2 — logic bug (output schema validation fails OR severity-miss_band mismatch)
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft7Validator

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from _jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from _out_path import out_path_error  # noqa: E402
from p15_trigger_detector import derive_severity, detect  # noqa: E402
from p15_trigger_input_loader import (  # noqa: E402
    NoThresholdsResolvedError,
    load_history,
    load_input,
    resolve_thresholds,
)

OUTPUT_SCHEMA_PATH = SCHEMAS_DIR / "p15-trigger-event.schema.json"


@functools.lru_cache(maxsize=1)
def _output_schema() -> dict:
    return json.loads(OUTPUT_SCHEMA_PATH.read_text())

DEFAULT_OUTPUT = Path(".aiml") / "p15-trigger-event.json"


def _parse_quality_floor_target(s: str) -> dict:
    """`--quality-floor-target metric_id=value` → {metric_id, target_value}."""
    if "=" not in s:
        raise argparse.ArgumentTypeError(f"expected metric_id=value, got {s!r}")
    mid, val = s.split("=", 1)
    return {"metric_id": mid.strip(), "target_value": float(val.strip())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="P15 trigger detection emitter (Charter sub-spec 4b)")
    ap.add_argument("--input", type=Path, required=True, help="Path to amplifier-telemetry-input v1.1.0 JSON file")
    ap.add_argument("--history", type=Path, default=None, help="Optional sidecar history file (array of v1.1.0 inputs)")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output path (default .aiml/p15-trigger-event.json)")
    ap.add_argument("--threshold-pct", type=float, default=None, help="P15 cost-rate threshold percent")
    ap.add_argument("--cap-pct", type=float, default=None, help="P15 cost-pass-through cap percent")
    ap.add_argument("--quality-floor-target", action="append", type=_parse_quality_floor_target,
                    default=None, help="Repeatable: metric_id=value")
    args = ap.parse_args(argv)

    refusal = out_path_error("--output", args.output)
    if refusal:
        print(refusal, file=sys.stderr)
        return 1

    # Step 1: load + validate input
    try:
        current = load_input(args.input)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        print(f"Input schema validation failed: {e}", file=sys.stderr)
        return 1

    # Step 2: optional history
    try:
        history = load_history(args.history)
    except FileNotFoundError:
        print(f"History file not found: {args.history}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError) as e:
        print(f"History load failed: {e}", file=sys.stderr)
        return 1

    # Step 3: resolve thresholds
    dispatch_context = {}
    if args.threshold_pct is not None:
        dispatch_context["threshold_pct"] = args.threshold_pct
    if args.cap_pct is not None:
        dispatch_context["cap_pct"] = args.cap_pct
    if args.quality_floor_target:
        dispatch_context["quality_floor_targets"] = args.quality_floor_target
    try:
        resolved = resolve_thresholds(
            dispatch_context=dispatch_context,
            input_file=current,
            has_history=(history is not None),
        )
    except NoThresholdsResolvedError as e:
        print(f"NoThresholdsResolvedError: {e}", file=sys.stderr)
        return 1

    # Step 4: detect
    events, detection_notes = detect(current, history, resolved)

    # Step 5: severity ↔ miss_band runtime check (row 48 + I4 closure)
    for ev in events:
        expected_sev = derive_severity(ev["miss_band_pct"])
        if ev["severity"] != expected_sev:
            print(f"Severity mismatch: ev.severity={ev['severity']} but derive_severity({ev['miss_band_pct']})={expected_sev}", file=sys.stderr)
            return 2

    # Step 6: assemble envelope (MUST-omit detection_notes when empty per T2A-7)
    envelope = {
        "engagement_id": current["engagement_id"],
        "produced_at": current["produced_at"],
        "schema_version": "1.0.0",
        "audience": "internal",
        "events": events,
    }
    if detection_notes:
        envelope["detection_notes"] = detection_notes

    # Step 7: validate output against schema (Draft7Validator + format_checker per 4a precedent
    # — enforces format:uuid on engagement_id and format:date-time on produced_at /
    # trigger_timestamp; bare jsonschema.validate would silently accept malformed values)
    try:
        Draft7Validator(_output_schema(), format_checker=FORMAT_CHECKER).validate(envelope)
    except jsonschema.ValidationError as e:
        print(f"Output schema validation failed: {e}", file=sys.stderr)
        return 2

    # Step 8: mkdir + write
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
