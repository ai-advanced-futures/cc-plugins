---
name: products
description: Assesses the data product portfolio of a software company, by how complete each data product is and how mature its data contracts are. Use when the person asks only for a data product or data contract review. Writes products.md.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/product_portfolio_scorer.py *)
---

# Data strategy: data product portfolio only

Ask the questions for the products domain, start the product analyst for the list of products, run the scorer, then start the product analyst for the report.

Run each command on its own, in one Bash call. Write no heredoc, no `; echo`, and no loop, because the tool refuses a joined command. Write each file with the Write tool.

After each script, if the exit code is not 0, show the error line of the script, start no agent, and stop.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask part 1 of that file with `AskUserQuestion`.
3. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py new .data-strategy-tmp products`. The script prints the session id. The `output_dir` is `.data-strategy-tmp/<id>`.
4. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of part 1.
5. Start the agent `data-strategy:product-analyst` with the `Agent` tool. Give it the fields `session_id`, `output_dir` (`.data-strategy-tmp/<id>`), and `step: inputs`.
6. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/product_portfolio_scorer.py '.data-strategy-tmp/<id>/products.json' --out '.data-strategy-tmp/<id>/products_result.json'`.
7. Start the agent `data-strategy:product-analyst` with the fields `session_id`, `output_dir`, and `step: report`.
8. Check the output file: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files '.data-strategy-tmp/<id>' products.md`. If the exit code is 0, write the flag with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py done '.data-strategy-tmp/<id>' products`, then show the path `.data-strategy-tmp/<id>/products.md`. Else show the last lines of the agent and say that the run failed. The line `DONE: products` is a second sign. Do not fail a run because the line is missing when the file exists.
