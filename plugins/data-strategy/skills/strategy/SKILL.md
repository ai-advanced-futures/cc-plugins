---
name: strategy
description: Assesses the data strategy of a software company against the 11 DAMA-DMBOK knowledge areas and the 5 Gartner D&A maturity levels. Use when the person asks only for a data strategy or data governance check. Writes strategy.md.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/dama_scorer.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/maturity_calculator.py *)
---

# Data strategy: strategy alignment only

Ask the questions for the strategy domain, run the 2 scorers, then start the strategy assessor.

Run each command on its own, in one Bash call. Write no heredoc, no `; echo`, and no loop, because the tool refuses a joined command. Write each file with the Write tool.

After each script, if the exit code is not 0, show the error line of the script, start no agent, and stop.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask parts 1 to 3 of that file with `AskUserQuestion`, one part at a time.
3. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py new .data-strategy-tmp strategy`. The script prints the session id. The `output_dir` is `.data-strategy-tmp/<id>`.
4. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of parts 1 to 3.
5. Use the Write tool to write `dama_answers.json` and `gartner_answers.json` in the `output_dir`. Each file holds the object of the same name from `context.yaml`. Then run:
   - `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/dama_scorer.py '.data-strategy-tmp/<id>/dama_answers.json' --out '.data-strategy-tmp/<id>/dama_result.json'`
   - `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/maturity_calculator.py '.data-strategy-tmp/<id>/gartner_answers.json' --out '.data-strategy-tmp/<id>/gartner_result.json'`
6. Start the agent `data-strategy:strategy-assessor` with the `Agent` tool. Give it the fields `session_id` and `output_dir` (`.data-strategy-tmp/<id>`).
7. Check the output file: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files '.data-strategy-tmp/<id>' strategy.md`. If the exit code is 0, write the flag with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py done '.data-strategy-tmp/<id>' strategy`, then show the path `.data-strategy-tmp/<id>/strategy.md`. Else show the last lines of the agent and say that the run failed. The line `DONE: strategy` is a second sign. Do not fail a run because the line is missing when the file exists.
