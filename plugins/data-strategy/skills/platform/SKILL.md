---
name: platform
description: Audits the data platform of a software company against the 4 Data Mesh principles and the 5 stages of the data engineering lifecycle. Use when the person asks only for a data platform or Data Mesh review. Can scan the current project for pipeline files. Writes platform.md.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_mesh_evaluator.py *)
---

# Data strategy: data platform audit only

Ask the questions for the platform domain, run the Data Mesh scorer, then start the platform auditor.

Run each command on its own, in one Bash call. Write no heredoc, no `; echo`, and no loop, because the tool refuses a joined command. Write each file with the Write tool.

After each script, if the exit code is not 0, show the error line of the script, start no agent, and stop.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask parts 1, 4 and 5 of that file with `AskUserQuestion`, one part at a time. For part 5, if the person says yes, scan the current project with `find` through the Bash tool as that file says.
3. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py new .data-strategy-tmp platform`. The script prints the session id. The `output_dir` is `.data-strategy-tmp/<id>`.
4. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of parts 1, 4 and 5.
5. Use the Write tool to write `mesh_answers.json` in the `output_dir`. The file holds the `mesh_answers` object from `context.yaml`. Then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_mesh_evaluator.py '.data-strategy-tmp/<id>/mesh_answers.json' --out '.data-strategy-tmp/<id>/mesh_result.json'`.
6. Start the agent `data-strategy:platform-auditor` with the `Agent` tool. Give it the fields `session_id` and `output_dir` (`.data-strategy-tmp/<id>`).
7. Check the output file: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files '.data-strategy-tmp/<id>' platform.md`. If the exit code is 0, write the flag with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py done '.data-strategy-tmp/<id>' platform`, then show the path `.data-strategy-tmp/<id>/platform.md`. Else show the last lines of the agent and say that the run failed. The line `DONE: platform` is a second sign. Do not fail a run because the line is missing when the file exists.
