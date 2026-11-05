"""
handoff_schema.py — JSON schema validator for grounded-synthesis handoff.json.

Used by: grounded-synthesis-orchestrator (via gap_report.py --emit-handoff)
         tests/unit/test_handoff_schema.py
Replaces logic that would otherwise live in orchestrator agent prose.

Handoff schema (written to {session_dir}/handoff.json) per BUILD_PLAN §2.5.9:
  {
    "session_id": "<uuid4>",
    "plugin": "grounded-synthesis",
    "version": "0.1.0",
    "schema_version": "1",
    "invocation": {
      "draft_path": "<absolute path>",
      "source_paths": ["<absolute path>", "..."],
      "key_facts_per_source": 12,
      "output_path": "<absolute path of gap report>"
    },
    "outputs": {
      "gap_report_path": "<absolute path> | null",   // nullable when status=failed + report never produced
      "session_dir": "<absolute path>"               // required non-null always
    },
    "summary": {
      "facts_checked": 36,
      "facts_present": 28,
      "facts_missing": 8,
      "sources_analyzed": 3,
      "sources_skipped": 0
    },
    "status": "ok | partial | failed",
    "failure_reason": "<string>",  // required when status=failed, absent otherwise
    "warnings": ["..."],           // optional array of strings
    "next_action_hint": "<optional one-liner for downstream orchestrator>"
  }

schema_version "1" reserves the contract namespace for later extensions of the caller contract.
outputs.gap_report_path MAY be null when status=failed (Round 6 M1 clarification).
outputs.session_dir is always required as a non-null string.
summary fields are non-nullable but may be 0 when no analysis ran.
failure_reason is required when status="failed", must be absent otherwise.

Nullable conditional approach: pure Python post-jsonschema check.
The base schema permits gap_report_path as {"type": ["string", "null"]} for Draft7
simplicity, then a Python guard rejects null when status != "failed".
This is cleaner than Draft7 if/then/else with dependentRequired — jsonschema's
Draft7 if/then/else interaction with required fields has sharp edges.

ValidationResult reuse decision: HandoffValidationResult is kept as a separate
frozen dataclass (not aliased to FactValidationResult) to maintain independent
evolution paths. The two schemas may diverge; sharing a type would couple them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import jsonschema

from lib.jsonschema_utils import format_error, load_json_file

# ---------------------------------------------------------------------------
# JSON Schema definition (mirrors BUILD_PLAN §2.5.9)
# ---------------------------------------------------------------------------

_SUMMARY_SCHEMA: dict = {
    "type": "object",
    "required": ["facts_checked", "facts_present", "facts_missing", "sources_analyzed", "sources_skipped"],
    "additionalProperties": True,
    "properties": {
        "facts_checked":    {"type": "integer", "minimum": 0},
        "facts_present":    {"type": "integer", "minimum": 0},
        "facts_missing":    {"type": "integer", "minimum": 0},
        "sources_analyzed": {"type": "integer", "minimum": 0},
        "sources_skipped":  {"type": "integer", "minimum": 0},
    },
}

_INVOCATION_SCHEMA: dict = {
    "type": "object",
    "required": ["draft_path", "source_paths", "key_facts_per_source", "output_path"],
    "additionalProperties": True,
    "properties": {
        "draft_path":          {"type": "string", "minLength": 1},
        # minItems: 0 — empty array is valid for the catastrophic case where all sources
        # were rejected by source_loader.py before dispatch (zero usable sources).
        # The key must be present (required above), but an empty list is legitimate.
        "source_paths":        {"type": "array", "items": {"type": "string"}, "minItems": 0},
        "key_facts_per_source": {"type": "integer", "minimum": 1},
        "output_path":         {"type": "string", "minLength": 1},
    },
}

_OUTPUTS_SCHEMA: dict = {
    "type": "object",
    # gap_report_path is ["string", "null"] in base schema;
    # the null-with-non-failed check is enforced in Python after jsonschema runs.
    "required": ["gap_report_path", "session_dir"],
    "additionalProperties": True,
    "properties": {
        "gap_report_path": {"type": ["string", "null"]},
        "session_dir":     {"type": "string", "minLength": 1},
    },
}

_HANDOFF_SCHEMA: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "session_id",
        "plugin",
        "version",
        "schema_version",
        "invocation",
        "outputs",
        "summary",
        "status",
    ],
    "additionalProperties": True,
    "properties": {
        "session_id":    {"type": "string", "minLength": 1},
        "plugin":        {"type": "string", "const": "grounded-synthesis"},
        "version":       {"type": "string", "minLength": 1},
        "schema_version": {"type": "string", "const": "1"},
        "invocation":    _INVOCATION_SCHEMA,
        "outputs":       _OUTPUTS_SCHEMA,
        "summary":       _SUMMARY_SCHEMA,
        "status":        {"type": "string", "enum": ["ok", "partial", "failed"]},
        "failure_reason": {"type": "string", "minLength": 1},
        "warnings":      {"type": "array", "items": {"type": "string"}},
        "next_action_hint": {"type": "string"},
    },
}

# Pre-compile validator once for performance.
_VALIDATOR = jsonschema.Draft7Validator(_HANDOFF_SCHEMA)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HandoffValidationResult:
    """Result of validating a handoff.json against the schema."""

    valid: bool
    errors: list[str] = field(default_factory=list)


def validate_handoff(data: dict) -> HandoffValidationResult:
    """Validate a handoff dict against the handoff schema (BUILD_PLAN §2.5.9).

    Returns HandoffValidationResult(valid=True, errors=[]) on success.
    Returns HandoffValidationResult(valid=False, errors=[...]) on schema violation.

    Nullable conditional (Round 6 M1):
      outputs.gap_report_path MAY be null only when status is "failed".
      This invariant is enforced by a Python post-check after jsonschema validates
      the structural shape, because Draft7 if/then/else + dependentRequired has
      sharp edges when the conditional property is nested inside an object.

    failure_reason conditional:
      Required when status="failed". Must be absent when status in ["ok", "partial"].
      Enforced by Python post-check for the same reason.
    """
    schema_errors = sorted(_VALIDATOR.iter_errors(data), key=lambda e: e.path)
    messages = [format_error(e) for e in schema_errors]

    if not messages:
        # Apply Python post-checks for conditional constraints.
        status = data.get("status")
        outputs = data.get("outputs", {})
        gap_report_path = outputs.get("gap_report_path") if isinstance(outputs, dict) else None
        has_failure_reason = "failure_reason" in data

        # Rule: gap_report_path=null is only valid when status="failed"
        if gap_report_path is None and status != "failed":
            messages.append(
                "outputs.gap_report_path: null is only permitted when status is 'failed'"
            )

        # Rule: failure_reason required when status="failed"
        if status == "failed" and not has_failure_reason:
            messages.append(
                "failure_reason: required when status is 'failed'"
            )

        # Rule: failure_reason must be absent when status is not "failed"
        if status != "failed" and has_failure_reason:
            messages.append(
                f"failure_reason: must not be present when status is '{status}'"
            )

    if messages:
        return HandoffValidationResult(valid=False, errors=messages)
    return HandoffValidationResult(valid=True, errors=[])


def validate_handoff_file(path: str) -> HandoffValidationResult:
    """Validate the handoff file at *path* against the handoff schema.

    Returns HandoffValidationResult(valid=True, errors=[]) on success.
    Returns HandoffValidationResult(valid=False, errors=[<messages>]) on failure.
    Does NOT raise on JSON-parse errors or schema violations.
    """
    data, err = load_json_file(path)
    if err is not None:
        return HandoffValidationResult(valid=False, errors=[err])

    return validate_handoff(data)


