# ADR-005 — Write a generic handoff.json

**Status:** Accepted

## Context

The orchestrator must tell its caller what happened. The caller can be any agent. The caller needs one file with a fixed shape.

## Decision

The plugin writes a generic `handoff.json` with `schema_version: "1"`. By default it goes to `{session_dir}/handoff.json`. When the caller sets `output_dir_override`, it goes to that folder (see ADR-007). `outputs.gap_report_path` and `outputs.session_dir` are null when `status` is `failed`. `lib/handoff_schema.py` checks the schema.

## Consequences

A caller has one stable file to read. The string `schema_version: "1"` reserves the contract name for later changes. The null fields let a failed run write a valid handoff when no gap report exists.

## Schema changes in 0.3.0

Two changes to the schema came from a review of the source plugin:

1. **`source_paths` `minItems` is 0, not 1.** When all sources fail the check before any agent starts, `source_paths` is an empty array. This is a valid failure case. With `minItems: 1`, `validate_handoff()` failed on this case. A test protects it: `TestHandoffSchema.test_handoff_schema_accepts_empty_source_paths` in `tests/unit/test_handoff_schema.py`.

2. **The `warnings` array has entries.** `_build_handoff` now writes `warnings: list[str]` from the `sources_skipped` entries of the session. The list is empty by default. A caller can read `dict["warnings"]` with no `KeyError`.
