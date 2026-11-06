---
name: platform
description: Audits the data platform of a software company against the 4 Data Mesh principles and the 5 stages of the data engineering lifecycle. Use when the person asks only for a data platform or Data Mesh review. Can scan the current project for pipeline files. Writes platform.md.
---

# Data strategy: data platform audit only

Ask the questions for the platform domain, then start the platform auditor.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask parts 1, 4 and 5 of that file with `AskUserQuestion`, one part at a time. For part 5, if the person says yes, scan the current project with Glob as that file says.
3. Make the session id with `uv run --no-project python3 -c "import uuid; print(uuid.uuid4().hex[:8])"`.
4. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py create <id> .data-strategy-tmp/<id> platform`
5. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of parts 1, 4 and 5.
6. Start the agent `data-strategy:platform-auditor` with the `Agent` tool. Give it the fields `session_id` and `output_dir` (`.data-strategy-tmp/<id>`).
7. Check the flag file and the output file: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py all-done .data-strategy-tmp/<id> platform`, then `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files .data-strategy-tmp/<id> platform.md`. If both exit codes are 0, the run is done: show the path `.data-strategy-tmp/<id>/platform.md`. Else show the last lines of the agent and say that the run failed. The line `DONE: platform` is a second sign. Do not fail a run because the line is missing when the flag file exists.
