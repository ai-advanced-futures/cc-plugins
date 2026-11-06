# ADR-002: Fact-Guard Federation via grounded-synthesis

**Status:** Accepted

## Context

A rewrite of AI-flagged prose can silently drop or distort the facts of the original text. A rewrite can "read more human" and still be wrong. That result is worse than a draft that a detector flags as AI but keeps the facts. The humanize loop needs a fact-coverage guard. The guard goes between "rewrite produced" and "rewrite accepted".

We considered three designs:

1. **Re-implement fact extraction and coverage checking** inside the `lib/` folder of prose-authenticity.
2. **Drive the leaf agents of grounded-synthesis directly** (fact-extractor and coverage-checker) from the prose-authenticity orchestrator.
3. **Dispatch the orchestrator entry point of grounded-synthesis.** The entry point is `grounded-synthesis:grounded-synthesis-orchestrator`. The dispatch is one call with the Agent tool. We then use its output contract, which is already tested.

## Decision

We chose option 3. The orchestrator dispatches the entry point of grounded-synthesis. We use its tested contract: source validation, fact-schema validation, and recovery from a partial source failure. We do not re-implement it. We do not drive its leaf agents directly.

The dispatch contract has these parts:

- The orchestrator dispatches `grounded-synthesis:grounded-synthesis-orchestrator` with the Agent tool.
- The call gives it three fields: `draft_path`, `source_paths`, and `output_dir_override`.
- **A failed dispatch is the authoritative trigger to degrade.** The dispatch fails in any of these cases:
  - The Agent tool call gives an error.
  - The agent ends with the last line `DONE: grounded-synthesis FAILED`.
  - `lib/fact_gate.py` exits with a non-zero code. It exits 1 and prints `failure_reason` when `handoff.json` has `status: "failed"`.
- A failed dispatch is not the same as a coverage report that finds gaps. The dispatch itself fails.
- On a failed dispatch, the run degrades. The humanize output is an *advisory diff* only. The run attaches an `UNVERIFIED FACTS` banner. The run does at most 2 iterations, not the normal cap. This limit stops an unverifiable rewrite from iterating without end.
- **The run reads the coverage JSON files from the grounded-synthesis session folder.** The field `outputs.session_dir` in `handoff.json` gives the path. The path is never hardcoded.
- The override output folder receives only `gap-report.md` and `handoff.json`. This follows ADR-006 of grounded-synthesis. The full coverage JSON for each source is in the session folder that the handoff names.
- `lib/fact_gate.py` resolves this indirection with `--from-handoff`. It never assumes a hardcoded path such as `facts/source-N-coverage.json`.

We rejected option 1. It would copy a capability that the maintainers already test. It would also drift from the fact-schema changes of grounded-synthesis.

We rejected option 2. It would tie prose-authenticity to the internal agent layout of grounded-synthesis, which splits into fact-extractor and coverage-checker. That layout is an implementation detail. Grounded-synthesis can change it at any time. The orchestrator dispatch is the stable, documented integration surface.

## Consequences

- prose-authenticity has a hard read dependency on two parts of grounded-synthesis: the `handoff.json` schema (`outputs.session_dir`) and the gap-report format. This is a doc contract between two plugins. The test `test_fact_gate_reads_via_handoff_not_hardcoded_coverage_path` in `tests/unit/test_doc_contracts.py` covers it.
- A dispatch failure of grounded-synthesis degrades the run in a safe way. The output is an advisory diff with `UNVERIFIED FACTS` and a limit of 2 iterations. The humanize loop does not stop completely. It never silently accepts an unverified rewrite as PASS.
- Grounded-synthesis can change its internals, for example leaf agent names or the layout of coverage files. prose-authenticity needs no change while the orchestrator dispatch contract and the handoff schema stay stable.
