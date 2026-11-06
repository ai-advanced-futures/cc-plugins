---
name: products
description: Assesses the data product portfolio of a software company, by how complete each data product is and how mature its data contracts are. Use when the person asks only for a data product or data contract review. Writes products.md.
---

# Data strategy: data product portfolio only

Ask the questions for the products domain, then start the product analyst.

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/intake.md`.
2. Ask part 1 of that file with `AskUserQuestion`.
3. Make the session id with `uv run --no-project python3 -c "import uuid; print(uuid.uuid4().hex[:8])"`.
4. Make the session: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py create <id> .data-strategy-tmp/<id> products`
5. Write `.data-strategy-tmp/<id>/context.yaml` with the keys of part 1.
6. Start the agent `data-strategy:product-analyst` with the `Agent` tool. Give it the fields `session_id` and `output_dir` (`.data-strategy-tmp/<id>`).
7. Check the flag file and the output file: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py all-done .data-strategy-tmp/<id> products`, then `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py has-files .data-strategy-tmp/<id> products.md`. If both exit codes are 0, the run is done: show the path `.data-strategy-tmp/<id>/products.md`. Else show the last lines of the agent and say that the run failed. The line `DONE: products` is a second sign. Do not fail a run because the line is missing when the flag file exists.
