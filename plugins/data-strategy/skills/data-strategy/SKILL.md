---
name: data-strategy
description: Runs the full data strategy assessment of a software company (strategy alignment, data platform, and data product portfolio). Use when the person asks for a data strategy assessment, a data maturity review, or a data roadmap. Writes a strategy report, a data platform ADR, and a data roadmap.
---

# Data strategy: full assessment

Ask the person the intake questions, then start the orchestrator. The orchestrator runs the 3 domain agents, the synthesizer, and the deliverable generator.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask parts 1 to 5 of that file with `AskUserQuestion`, one part at a time. For part 5, if the person says yes, scan the current project with Glob as that file says.
3. Make the session id with `uv run --no-project python3 -c "import uuid; print(uuid.uuid4().hex[:8])"`.
4. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py create <id> .data-strategy-tmp/<id> strategy platform products`
5. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
6. Start the agent `data-strategy:orchestrator` with the `Agent` tool. Give it the fields `session_id` and `output_dir` (`.data-strategy-tmp/<id>`).
7. Check the 3 files: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files .data-strategy-tmp/<id> strategy-report.md data-platform-adr.md data-roadmap.md`. If the exit code is 0, the run is done: show the 3 paths in `.data-strategy-tmp/<id>/`. Else show the last lines of the orchestrator and say that the run failed. The line `DONE: data-strategy` is a second sign. Do not fail a run because the line is missing when the 3 files exist.
