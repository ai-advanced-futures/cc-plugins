# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""Emitter: compose AmplifierTelemetryInput + AmplifierCompositeResult → cost-amplifier-readout dict.

Validates output against Charter §7.3 schema before returning.
Also the single CLI entry-point run by the skill cost-amplifier-readout with uv run.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import jsonschema

# Ensure the scripts dir is on sys.path so the shared module is importable when
# this emitter is invoked as a script directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from _out_path import out_path_error  # noqa: E402
from amplifier_composer import AmplifierCompositeResult, compose  # noqa: E402
from amplifier_telemetry_loader import (  # noqa: E402
    AmplifierTelemetryInput,
    load_and_validate,
)
from jsonschema import Draft7Validator  # noqa: E402

_OUTPUT_SCHEMA_PATH = SCHEMAS_DIR / "cost-amplifier-readout.schema.json"
_OUTPUT_SCHEMA = json.loads(_OUTPUT_SCHEMA_PATH.read_text())

# Charter §7.3 const-pinned values — bumping these requires schema update.
_MODE = "telemetry_enriched"      # Charter §7.3 mode enum
_AUDIENCE = "internal"             # Charter §7.3 audience const

_NOTES_MAX = 2000


def _now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_provenance_notes(inp: AmplifierTelemetryInput, comp: AmplifierCompositeResult) -> str:
    present = sorted(a for a in inp.amplifiers if inp.amplifiers[a].present)
    sample_total = sum(inp.amplifiers[a].sample_size_n for a in present)
    parts = [
        f"telemetry_enriched mode. Source={inp.telemetry_source}. ",
        f"Window {inp.measurement_window.start} → {inp.measurement_window.end} "
        f"({inp.measurement_window.duration_days}d). ",
        f"Present amps: {present} (n_total={sample_total}). ",
        f"Composite p75={comp.p75:.4f} p95={comp.p95:.4f}. ",
        "Framework attribution: JustKeenAI v2.1 (per ATTRIBUTION.md). ",
    ]
    for amp_id in present:
        sig = inp.amplifiers[amp_id].detection_signal
        parts.append(f"[amp{amp_id}:{sig}] ")
    return "".join(parts).strip()


def emit(inp: AmplifierTelemetryInput, comp: AmplifierCompositeResult) -> dict:
    """Produce a cost-amplifier-readout dict; validate against Charter §7.3 schema."""
    notes = build_provenance_notes(inp, comp)
    if len(notes) > _NOTES_MAX:
        raise ValueError(
            f"notes template produced {len(notes)} chars >2000; "
            f"emitter template needs redesign for maximal input shape"
        )

    out_amps = {}
    for amp_id, reading in inp.amplifiers.items():
        out_amps[str(amp_id)] = {
            "multiplier_p75": reading.multiplier_p75,
            "multiplier_p95": reading.multiplier_p95,
            "detection_signal": reading.detection_signal,
            "present": reading.present,
        }

    out = {
        "engagement_id": inp.engagement_id,
        "produced_at": _now_utc_iso(),
        "schema_version": "1.0.0",
        "mode": _MODE,
        "audience": _AUDIENCE,
        "amplifiers": out_amps,
        "composite_p75": comp.p75,
        "composite_p95": comp.p95,
        "notes": notes,
    }

    Draft7Validator(_OUTPUT_SCHEMA, format_checker=FORMAT_CHECKER).validate(out)

    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Emit cost-amplifier-readout from telemetry input.")
    p.add_argument("--input", required=True, help="Path to amplifier-telemetry-input.json")
    p.add_argument("--out", default=".aiml/cost-amplifier-readout.json", help="Output path")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args(argv)

    refusal = out_path_error("--out", args.out)
    if refusal:
        print(refusal, file=sys.stderr)
        return 1

    # PHASE 1 — input load + compose. ANY validation failure here is an
    # input-side error → exit 1 per spec §6.2. We DO NOT branch on `e.schema.$id`
    # because jsonschema's ValidationError.schema field points to the sub-schema
    # that failed (e.g. a property-level uuid format), which has no $id — that
    # made the previous $id-substring branch unreliable for most input failures
    # (bad UUID, bad audience const, bad schema_version pattern, per-amp field
    # missing). Splitting the two phases into distinct try blocks makes the
    # exit-code contract structural, not introspective.
    try:
        inp = load_and_validate(Path(args.input))
        comp = compose(inp.amplifiers)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    except jsonschema.ValidationError as e:
        print(f"Input schema validation failed: {e.json_path}: {e.message}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # PHASE 2 — emit + output-schema validate. A ValidationError here is a
    # LOGIC BUG in the emitter (the input was already validated). exit 2 per
    # spec §6.2.
    try:
        out_dict = emit(inp, comp)  # emit() internally validates output
    except jsonschema.ValidationError as e:
        print(f"Output schema validation failed (logic bug): {e.message}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Emit error: {e}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_dict, indent=2))
    if args.verbose:
        print(f"Wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
