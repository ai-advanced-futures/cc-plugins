---
name: data-strategy
description: Runs the full data strategy assessment of a software company (strategy alignment, data platform, and data product portfolio). Use when the person asks for a data strategy assessment, a data maturity review, or a data roadmap. Writes a strategy report, a data platform ADR, and a data roadmap.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/dama_scorer.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/maturity_calculator.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_mesh_evaluator.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/product_portfolio_scorer.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap_builder.py *), Read(/${CLAUDE_PLUGIN_ROOT}/docs/intake.md), Read(/${CLAUDE_PLUGIN_ROOT}/docs/frameworks.md), Edit(/.data-strategy-tmp/**)
---

# Data strategy: full assessment

Ask the person the intake questions. Then run the scripts and start the agents in the order below. No agent starts an agent and no agent runs a script.

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

Run each command on its own, in one Bash call. Write no heredoc, no `; echo`, and no loop, because the tool refuses a joined command. Write each file with the Write tool.

After each script, if the exit code is not 0, show the error line of the script, start no agent, and stop.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask parts 1 to 5 of that file with `AskUserQuestion`, one part at a time. For part 5, if the person says yes, scan the current project with `find` through the Bash tool as that file says.
3. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py new .data-strategy-tmp strategy platform products`. The script prints the session id. The `output_dir` is `.data-strategy-tmp/<id>`.
4. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
5. Use the Write tool to write `dama_answers.json`, `gartner_answers.json`, and `mesh_answers.json` in the `output_dir`. Each file holds the object of the same name from `context.yaml`. Then run the 3 scorers:
   - `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/dama_scorer.py '.data-strategy-tmp/<id>/dama_answers.json' --out '.data-strategy-tmp/<id>/dama_result.json'`
   - `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/maturity_calculator.py '.data-strategy-tmp/<id>/gartner_answers.json' --out '.data-strategy-tmp/<id>/gartner_result.json'`
   - `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_mesh_evaluator.py '.data-strategy-tmp/<id>/mesh_answers.json' --out '.data-strategy-tmp/<id>/mesh_result.json'`
6. Start `data-strategy:strategy-assessor`, `data-strategy:platform-auditor`, and `data-strategy:product-analyst` with the `Agent` tool, one at a time, in this order. Each call is in the foreground: set `run_in_background: false`. Wait for the reply of an agent before you start the next, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next script is then refused. Give each the fields `session_id`, `output_dir`, and `step: inputs`.
7. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/product_portfolio_scorer.py '.data-strategy-tmp/<id>/products.json' --out '.data-strategy-tmp/<id>/products_result.json'`.
8. Start `data-strategy:product-analyst` in the foreground (`run_in_background: false`) with the fields `session_id`, `output_dir`, and `step: report`.
9. For each of `strategy`, `platform`, and `products`, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files '.data-strategy-tmp/<id>' '<slug>.md'`, and then `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py done '.data-strategy-tmp/<id>' '<slug>'`. Then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py all-done '.data-strategy-tmp/<id>' strategy platform products`. If an exit code is not 0, show the output, start no agent, and stop.
10. Start `data-strategy:synthesizer` in the foreground (`run_in_background: false`) with the fields `session_id`, `output_dir`, and `step: inputs`. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/roadmap_builder.py '.data-strategy-tmp/<id>/roadmap_items.json' --out '.data-strategy-tmp/<id>/roadmap_result.json'`. Start `data-strategy:synthesizer` in the foreground (`run_in_background: false`) with the fields `session_id`, `output_dir`, and `step: report`. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files '.data-strategy-tmp/<id>' synthesis.md`.
11. Start `data-strategy:deliverable-generator` in the foreground (`run_in_background: false`) with the fields `session_id` and `output_dir`. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files '.data-strategy-tmp/<id>' strategy-report.md data-platform-adr.md data-roadmap.md`. If the exit code is 0, the run is done: show the 3 paths in `.data-strategy-tmp/<id>/`. Else show the last lines of the agent and say that the run failed.

The `DONE` line of an agent is a second sign. Do not fail a run because the line is missing when the files exist.
