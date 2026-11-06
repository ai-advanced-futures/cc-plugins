# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""CLI emitter for the sales-comp-precondition-gate file.

Run it by its path. It puts its own plugin folder on sys.path, never the cwd:
    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/sales_comp_gate_emitter.py" \
        --input <gate-input.json> --output-dir "${CLAUDE_PROJECT_DIR:-.}"

Two-phase exit codes: 1 = input/validation error, 2 = write error.
Writes <out>/.gtm/sales-comp-precondition-gate.json + <out>/.gtm/sales-comp-gate-handoff.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from jsonschema import Draft7Validator  # noqa: E402
from jsonschema.exceptions import ValidationError  # noqa: E402

from scripts._jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from scripts.sales_comp_gate import classify_cliff  # noqa: E402
from scripts.sales_comp_gate_input_loader import load_and_validate  # noqa: E402

_SCHEMA_NAME = "sales-comp-precondition-gate.schema.json"
_COMPLETED_SKILLS = ["gtm:sales-comp-gate-review"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_output(loaded, produced_at: str) -> dict:
    return {
        "engagement_id": loaded.engagement_id,
        "produced_at": produced_at,
        "schema_version": loaded.schema_version,
        "preconditions_met": dict(loaded.preconditions_met),
        "top_quintile_at_risk_pct": loaded.top_quintile_at_risk_pct,
        "cliff_recommendation": classify_cliff(
            loaded.preconditions_met,
            loaded.top_quintile_at_risk_pct,
            loaded.prior_recommendation,
            loaded.re_pause_trigger_fired,
        ),
        "audience": "internal",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", default=".")
    args = ap.parse_args(argv)
    produced_at = _now_iso()

    # ----- PHASE 1: input + schema resolution (exit 1) -----
    try:
        schema_path = SCHEMAS_DIR / _SCHEMA_NAME
        schema = json.loads(schema_path.read_text())
        loaded = load_and_validate(args.input)
        out = build_output(loaded, produced_at)
        Draft7Validator(schema, format_checker=FORMAT_CHECKER).validate(out)
    except (OSError, ValueError, ValidationError) as e:
        print(f"sales-comp-gate error: {e}", file=sys.stderr)
        return 1

    # ----- PHASE 2: write (exit 2) -----
    try:
        out_dir = Path(args.output_dir) / ".gtm"
        out_dir.mkdir(parents=True, exist_ok=True)
        gate_path = out_dir / "sales-comp-precondition-gate.json"
        gate_path.write_text(json.dumps(out, indent=2) + "\n")
        handoff = {
            "status": "complete",
            "classification_path": ".gtm/sales-comp-precondition-gate.json",
            "cliff_recommendation": out["cliff_recommendation"],
            "produced_at": produced_at,
            "done": True,
            "completed_skills": _COMPLETED_SKILLS,
        }
        (out_dir / "sales-comp-gate-handoff.json").write_text(json.dumps(handoff, indent=2) + "\n")
    except OSError as e:
        print(f"sales-comp-gate write error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
