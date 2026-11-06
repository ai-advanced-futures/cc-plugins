---
name: strategy
description: Assesses the data strategy of a software company against the 11 DAMA-DMBOK knowledge areas and the 5 Gartner D&A maturity levels. Use when the person asks only for a data strategy or data governance check. Writes strategy.md.
---

# Data strategy: strategy alignment only

Ask the questions for the strategy domain, then start the strategy assessor.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask parts 1 to 3 of that file with `AskUserQuestion`, one part at a time.
3. Make the session id with `uv run --no-project python3 -c "import uuid; print(uuid.uuid4().hex[:8])"`.
4. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py create <id> .data-strategy-tmp/<id> strategy`
5. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of parts 1 to 3.
6. Start the agent `data-strategy:strategy-assessor` with the `Agent` tool. Give it the fields `session_id` and `output_dir` (`.data-strategy-tmp/<id>`).
7. Check the flag file and the output file: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py all-done .data-strategy-tmp/<id> strategy`, then `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files .data-strategy-tmp/<id> strategy.md`. If both exit codes are 0, the run is done: show the path `.data-strategy-tmp/<id>/strategy.md`. Else show the last lines of the agent and say that the run failed. The line `DONE: strategy` is a second sign. Do not fail a run because the line is missing when the flag file exists.
