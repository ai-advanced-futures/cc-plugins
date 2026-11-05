---
description: Runs both checks after a write to a graph - the brain check of each changed brain, then the full general check of the knowledge plugin - and returns each ERROR, WARN, and SKIP line. knowledge:learn, knowledge:forget, and the learn skill of each brain call it. Do not use it for any other task.
user-invocable: false
allowed-tools: Bash, Read
---

# Run both checks

Inputs: the names of the graphs that changed.

`ROOT` is the output of `git rev-parse --show-toplevel`.

## Step 1: the brain check

1. For each graph that changed, read `plugin` and `save_code` in the
   `manifest.md` of the graph. Graphs with the same `plugin` and `save_code`
   share one brain check. For example, `prd` and `roadmap` both use
   `scripts/prd.py`, and one `check` checks both graphs. Do steps 2 to 4 one
   time for each pair of `plugin` and `save_code`.
2. Find the plugin:

   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh <plugin> <save_code>
   ```

3. When the probe exits 1, record this line and go to the next pair:
   `SKIP: brain-check (the plugin <plugin> of <graphs> is not installed)`.
   `<graphs>` names each changed graph of the pair.
4. Run the brain check:

   ```bash
   uv run <plugin root>/<save_code> --root "$ROOT" check
   ```

## Step 2: the general check

Run the full general check one time. It reads each graph in
`.claude/knowledge.json`, and it reports a graph with no manifest:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py --root "$ROOT" check
```

## Step 3: the result

- Copy each `ERROR:`, `WARN:`, and `SKIP:` line into the result. A SKIP line
  is a rule that did not run, and the caller reports it.
- The result is PASSED only when each command of Step 1 and Step 2 exits 0.
  Otherwise it is FAILED. Never report PASSED when a command exits 1 or 2,
  because the caller then reports success on a broken graph.

Return this text:

    CHECKS: PASSED | CHECKS: FAILED
    <each ERROR, WARN, and SKIP line>
