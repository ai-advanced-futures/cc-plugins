# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""CLI emitter for vendor-archetype-classification.

Run by path with uv. The script finds its own `scripts` package:
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vendor_archetype_emitter.py \
        --input <input.json> --output-dir ${CLAUDE_PROJECT_DIR:-.}

Exit codes: 1 = input/validation/unclassified error (before any classification-artifact
write); 2 = write error. Handoff states: success | blocked (unclassified) | error
(input-validation or write failure). On unclassified, NO classification artifact is
written — only a blocked handoff naming the reason. NO cross-plugin import.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from jsonschema import Draft7Validator  # noqa: E402
from jsonschema.exceptions import ValidationError  # noqa: E402

from scripts._jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from scripts.vendor_archetype_classifier import classify  # noqa: E402
from scripts.vendor_archetype_input_loader import load_and_validate  # noqa: E402

_SCHEMA_NAME = "vendor-archetype-classification.schema.json"
_OUT_SUBDIR = ".competitive-intelligence"
_ARTIFACT = "vendor-archetype-classification.json"
_HANDOFF = "vendor-archetype-handoff.json"
_COMPLETED_SKILLS = ["competitive-intelligence:vendor-archetype-classify"]
# The emitter OWNS the output schema version (matches the schema's `const`); it is NOT
# propagated from the input, so a stale/wrong caller schema_version cannot reach the
# artifact (code-review finding). The input's schema_version is the caller's self-decl.
_SCHEMA_VERSION = "1.0.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_output(loaded, result, produced_at: str) -> dict:
    out = {
        "schema_version": _SCHEMA_VERSION,
        "audience": "mixed",
        "vendor_name": loaded.vendor_name,
        "classified_at": produced_at,
        "archetype": result.archetype,
        "seat_anchor": result.seat_anchor,
        "best_in_class_pattern": result.best_in_class_pattern,
        "signals": dataclasses.asdict(loaded.signals),
        "confidence": loaded.confidence,
        "rationale": loaded.rationale,
        "multi_sku": loaded.multi_sku,
    }
    if loaded.pricing_page_url is not None:
        out["pricing_page_url"] = loaded.pricing_page_url
    return out


def _write_handoff(out_dir: Path, payload: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / _HANDOFF).write_text(json.dumps(payload, indent=2) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", default=".")
    args = ap.parse_args(argv)
    produced_at = _now_iso()
    out_dir = Path(args.output_dir) / _OUT_SUBDIR

    # ----- PHASE 1: input + classify + schema validation (exit 1) -----
    try:
        schema = json.loads((SCHEMAS_DIR / _SCHEMA_NAME).read_text())
        loaded = load_and_validate(args.input)
        result = classify(loaded.signals)
        if not result.is_classified:
            _write_handoff(out_dir, {
                "state": "blocked",
                "reason": result.reason,
                "vendor_name": loaded.vendor_name,
                "classification_path": f"{_OUT_SUBDIR}/{_ARTIFACT}",
                "produced_at": produced_at,
                "done": True,
            })
            print(f"vendor-archetype blocked (unclassified): {result.reason}", file=sys.stderr)
            return 1
        out = build_output(loaded, result, produced_at)
        Draft7Validator(schema, format_checker=FORMAT_CHECKER).validate(out)
    except (OSError, ValueError, ValidationError) as e:
        try:
            _write_handoff(out_dir, {
                "state": "error",
                "reason": str(e),
                "classification_path": f"{_OUT_SUBDIR}/{_ARTIFACT}",
                "produced_at": produced_at,
                "done": True,
            })
        except OSError as write_err:
            # Handoff write itself failed — report both errors so the caller
            # knows the handoff file may be absent (not silently swallowed).
            print(f"vendor-archetype error: {e}; handoff write also failed: {write_err}", file=sys.stderr)
            return 1
        print(f"vendor-archetype error: {e}", file=sys.stderr)
        return 1

    # ----- PHASE 2: write artifact + success handoff (exit 2) -----
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / _ARTIFACT).write_text(json.dumps(out, indent=2) + "\n")
        _write_handoff(out_dir, {
            "state": "success",
            "classification_path": f"{_OUT_SUBDIR}/{_ARTIFACT}",
            "archetype": out["archetype"],
            "seat_anchor": out["seat_anchor"],
            "produced_at": produced_at,
            "done": True,
            "completed_skills": _COMPLETED_SKILLS,
        })
    except OSError as e:
        print(f"vendor-archetype write error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
