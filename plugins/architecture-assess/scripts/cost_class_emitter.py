#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""CLI emitter for the §7.14 cost-class-classification artifact.

Reads a §7.3 cost-amplifier-readout, derives the deterministic cost-class band
(cost_class_band), the requires_guardrail flag, and the advisory remediation,
copies provenance, fresh-stamps produced_at, validates against §7.14, and writes
the output plus an internal cost-class-handoff.json. Two-phase exit codes:
  exit 1 = input/load/validation failure (PHASE-1)
  exit 2 = output write failure (PHASE-2), or a bad argument (argparse)
  exit 0 = success
Invoked by cost-class-gate-agent via:
  uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cost_class_emitter.py --readout <path> --ai-stack-layer <layer> \
    --ai-stack-layer-basis <basis> --feature-id <id>
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft7Validator, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from cost_class_band import classify_cost_class  # noqa: E402
from cost_class_input_loader import load_and_validate  # noqa: E402

OUTPUT_SCHEMA_PATH = SCHEMAS_DIR / "cost-class-classification.schema.json"
DEFAULT_OUTPUT = ".architecture/cost-class-classification.json"
SCHEMA_VERSION = "1.0.0"

_LAYERS = ["foundation_model", "infrastructure_orchestration", "application", "vertical_labor_anchor"]

_REMEDIATION_GUARDRAIL = (
    "Add a metered escape valve or repricing trigger before ship; surface the "
    "tail to customers before margin goes negative (framework: Developer Tool "
    "Loop Creep remedy, JustKeenAI v2.1 Ch. 3)."
)
_REMEDIATION_CLASS4_NONAPP = (
    "Tail-dominated cost class on a non-application layer; the framework's full "
    "amplifier prescription does not apply at strength, but confirm the layer "
    "classification and monitor the P95 tail."
)
_REMEDIATION_BOUNDED = (
    "Within bounded-surface regime (Perplexity/Notion-core class); standard "
    "design review sufficient — the full amplifier model does not apply at strength."
)
_REMEDIATION_ELSE = (
    "Moderate-to-elevated cost class; no application-layer guardrail mandated, "
    "but record the cost-class declaration and revisit at the next pricing review."
)


def derive_requires_guardrail(ai_stack_layer: str, cost_class: str) -> bool:
    return ai_stack_layer == "application" and cost_class in {"class_3_high", "class_4_critical"}


def derive_remediation(ai_stack_layer: str, cost_class: str, requires_guardrail: bool) -> str:
    if requires_guardrail:
        return _REMEDIATION_GUARDRAIL
    if cost_class == "class_4_critical":
        return _REMEDIATION_CLASS4_NONAPP
    if cost_class == "class_1_bounded":
        return _REMEDIATION_BOUNDED
    return _REMEDIATION_ELSE


@functools.lru_cache(maxsize=1)
def _output_schema() -> dict:
    return json.loads(OUTPUT_SCHEMA_PATH.read_text())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_handoff(out_dir: Path, classification_path: str, produced_at: str) -> None:
    handoff = {"status": "complete", "classification_path": classification_path, "produced_at": produced_at}
    (out_dir / "cost-class-handoff.json").write_text(json.dumps(handoff, indent=2))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Emit a cost-class-classification (§7.14).")
    ap.add_argument("--readout", required=True)
    ap.add_argument("--ai-stack-layer", required=True, choices=_LAYERS)
    ap.add_argument("--ai-stack-layer-basis", required=True)
    ap.add_argument("--feature-id", required=True)
    ap.add_argument("--output", default=DEFAULT_OUTPUT)
    ap.add_argument("--notes", default="")
    args = ap.parse_args(argv)

    # PHASE 1 — bundled-schema read, then readout load + validation.
    # Separated so that a mis-packaged deploy (schema missing) produces a
    # clear "bundled schema" message rather than a misleading "readout not found".
    try:
        schema = _output_schema()
    except (FileNotFoundError, OSError) as e:
        print(f"cost_class_emitter: bundled output schema not found: {e}", file=sys.stderr)
        return 1

    try:
        readout = load_and_validate(args.readout)
    except FileNotFoundError as e:
        print(f"cost_class_emitter: readout not found: {e}", file=sys.stderr)
        return 1
    except (OSError, ValidationError, ValueError, json.JSONDecodeError) as e:
        print(f"cost_class_emitter: invalid readout: {e}", file=sys.stderr)
        return 1

    now = _now_iso()
    cost_class = classify_cost_class(readout.composite_p75, readout.composite_p95)
    requires_guardrail = derive_requires_guardrail(args.ai_stack_layer, cost_class)
    remediation = derive_remediation(args.ai_stack_layer, cost_class, requires_guardrail)

    doc = {
        "engagement_id": readout.engagement_id,
        "produced_at": now,
        "schema_version": SCHEMA_VERSION,
        "audience": "internal",
        "feature_id": args.feature_id,
        "ai_stack_layer": args.ai_stack_layer,
        "ai_stack_layer_basis": args.ai_stack_layer_basis,
        "cost_class": cost_class,
        "cost_class_basis": {
            "composite_p75": readout.composite_p75,
            "composite_p95": readout.composite_p95,
        },
        "requires_guardrail": requires_guardrail,
        "recommended_remediation": remediation,
        "source_readout": {
            "engagement_id": readout.engagement_id,
            "produced_at": readout.produced_at,
            "mode": readout.mode,
        },
        "notes": args.notes,
    }

    try:
        Draft7Validator(schema, format_checker=FORMAT_CHECKER).validate(doc)
    except ValidationError as e:
        print(f"cost_class_emitter: assembled doc failed §7.14 validation: {e}", file=sys.stderr)
        return 1

    # PHASE 2 — output write
    out_path = Path(args.output)
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(doc, indent=2))
        _write_handoff(out_path.parent, str(out_path), now)
    except OSError as e:
        print(f"cost_class_emitter: output write failed: {e}", file=sys.stderr)
        return 2

    print(f"cost_class_emitter: wrote {out_path} (cost_class={cost_class}, requires_guardrail={requires_guardrail})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
