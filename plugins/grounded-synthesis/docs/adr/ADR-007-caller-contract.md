# ADR-007 — The caller contract

**Status:** Accepted
**Related:** ADR-005 (handoff.json), ADR-006 (session folder)

## Context

Other agents must be able to start the audit. The entry point is the agent `grounded-synthesis:grounded-synthesis-orchestrator`. The source plugin also had caller fields that belong to one other plugin (a mission folder, a work-item number, and an automated-mode flag). This repository does not have that plugin. This port removes those three fields.

## Decision

The caller starts the orchestrator with the `Agent` tool. It sends these dispatch fields:

| Field | Required | Meaning |
|---|---|---|
| `draft_path` | yes | Absolute path of the draft. |
| `source_paths` | yes | List of absolute paths of 1 or more source files. |
| `key_facts_per_source` | no | Facts for each source. Default 12. The orchestrator clamps it to [8, 20]. |
| `output_dir_override` | no | Absolute path. `gap-report.md` and `handoff.json` go to this folder. The session scratch files stay in the session folder (ADR-006). |
| `output_path` | no | Path of the gap report. Default: `<draft_path>.grounded-synthesis-report.md`. |

If `draft_path` or `source_paths` is missing, the orchestrator writes no file. It ends with `DONE: grounded-synthesis FAILED: draft_path and source_paths are required`.

When `output_dir_override` is set, `lib/gap_report.py` writes both files to that folder. This is also true on a failure. The caller reads only that folder.

The `handoff.json` schema, the fact file schema, the coverage file schema, and the `DONE: grounded-synthesis` lines are the same as before (ADR-005 gives the schema changes).

## Consequences

- A caller needs only the five fields. The set is in `EXPECTED_DISPATCH_FIELDS` of `lib/constants.py`, and a test checks that the orchestrator text names each field.
- A change to these fields breaks every caller. Change them with the same care as a public interface.
- The plugin writes to a path that the caller names. The orchestrator passes the path to `lib/gap_report.py` as it is, with no check. The caller owns the path.
