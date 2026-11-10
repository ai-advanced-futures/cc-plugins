---
description: Runs both checks after a write to a graph - the brain check of each changed brain, then the full general check of the knowledge plugin - and returns each ERROR, WARN, and SKIP line. knowledge:learn, knowledge:forget, and the learn skill of each brain call it. Do not use it for any other task.
user-invocable: false
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py brain-check *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py check *), Bash(git rev-parse *)
---

# Run both checks

Inputs: the names of the graphs that changed.

`ROOT` is the output of `git rev-parse --show-toplevel`.

Run each command of this skill as it is written, one command for each Bash
call, because the skill grants only these commands.

## Step 1: the brain check

Run 1 command, with one `--graph` for each graph that changed:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py brain-check --root "$ROOT" --graph <graph>
```

The command finds the plugin of each graph and runs the `check` of its save
code. Graphs with the same `plugin` and `save_code` share one brain check. For
example, `prd` and `roadmap` both use `scripts/prd.py`, and one `check` checks
both graphs.

For a brain that is not installed, and for a pair of `plugin` and `save_code`
that is not a known brain, the command prints one line
`SKIP: brain-check (<the cause>)` and exits 1. The general check of Step 2 then
gives the `K-manifest` ERROR for a bad pair.

## Step 2: the general check

Run the full general check one time. It reads each graph in
`.claude/knowledge.json`, and it reports a graph with no manifest:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge.py check --root "$ROOT"
```

## Step 3: the result

- Copy each `ERROR:`, `WARN:`, and `SKIP:` line into the result. A SKIP line
  is a rule that did not run, and the caller reports it.
- The result is PASSED only when the command of Step 1 and the command of
  Step 2 both exit 0. Otherwise it is FAILED. Never report PASSED when a
  command exits 1 or 2, because the caller then reports success on a broken
  graph.

Return this text:

    CHECKS: PASSED | CHECKS: FAILED
    <each ERROR, WARN, and SKIP line>
