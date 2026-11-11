#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""CLI emitter for §7.13 archetype-baseline-telemetry.

Wires loader → aggregator → §7.13 output. Passes engagement_id / measurement_window
/ telemetry_source THROUGH from the loaded object (no re-read of raw input);
stamps produced_at fresh at emit time. Validates output before write.

Exit codes:
  0 — success
  1 — user error (file not found, schema-invalid input)
  2 — logic bug (output schema validation fails — input was already validated)
"""

from __future__ import annotations

import argparse
import datetime as dt
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
from archetype_baseline_aggregator import aggregate  # noqa: E402
from archetype_baseline_input_loader import load_and_validate  # noqa: E402

OUTPUT_SCHEMA_PATH = SCHEMAS_DIR / "archetype-baseline-telemetry.schema.json"
DEFAULT_OUTPUT = ".aiml/archetype-baseline-telemetry.json"


@functools.lru_cache(maxsize=1)
def _output_schema() -> dict:
    return json.loads(OUTPUT_SCHEMA_PATH.read_text())


def _now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Archetype baseline telemetry emitter (Charter sub-spec 4c)"
    )
    ap.add_argument(
        "--input", type=Path, required=True, help="Path to archetype-cost-samples v1.0.0 JSON"
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help="Output path (default .aiml/archetype-baseline-telemetry.json)",
    )
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    refusal = out_path_error("--out", args.out)
    if refusal:
        print(refusal, file=sys.stderr)
        return 1

    # PHASE 1 — load + aggregate. Any failure here is input-side → exit 1.
    try:
        samples = load_and_validate(args.input)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 1
    except OSError as e:
        # IsADirectoryError / PermissionError / other filesystem errors on the input path
        print(f"Cannot read input file: {args.input}: {e}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        print(f"Input schema validation failed: {e}", file=sys.stderr)
        return 1

    baselines = aggregate(samples)

    # PHASE 2 — assemble + validate output. A failure here is an emitter logic bug → exit 2.
    out = {
        "engagement_id": samples.engagement_id,
        "produced_at": _now_utc_iso(),
        "schema_version": "1.0.0",
        "audience": "internal",
        "measurement_window": samples.measurement_window,
        "telemetry_source": samples.telemetry_source,
        "baselines": {
            name: {
                "baseline_cost_per_interaction": r.baseline_cost_per_interaction,
                "sample_size_n": r.sample_size_n,
                "aggregation": r.aggregation,
            }
            for name, r in baselines.items()
        },
    }
    try:
        Draft7Validator(_output_schema(), format_checker=FORMAT_CHECKER).validate(out)
    except jsonschema.ValidationError as e:
        print(f"Output schema validation failed (logic bug): {e.message}", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    if args.verbose:
        print(f"Wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
