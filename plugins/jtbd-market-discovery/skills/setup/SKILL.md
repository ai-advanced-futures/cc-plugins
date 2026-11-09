---
description: Sets up the jtbd graph of this repository - the bundle at docs/jtbd/, the manifest, the registry entry, and the router block in CLAUDE.md. Use for "/jtbd-market-discovery:setup".
argument-hint: "[bundle folder]"
disable-model-invocation: true
allowed-tools: Bash, Read, Skill
---

# Set up the jtbd graph

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When that command fails, stop with: "This is not a git repository." Write that path itself in each command, and not a command or a variable, because Claude Code cannot check such a command before it runs, and it then asks the person or refuses the command. Write each path in single quotes, and write each `'` in a path as `'\''`, because inside single quotes the shell runs nothing and keeps a space in the path.

## Step 1: make or upgrade the bundle

- When `.claude/knowledge.json` names the graph `jtbd`, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' upgrade`.
- When not, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<git root>' init`. Add `--dir $ARGUMENTS` when the person gave a
  folder. A folder name is safe in a command only when it matches
  `[A-Za-z0-9._/-]{1,100}`, has no `..` part and does not start with `/`.
  When it does not match, it is not a folder name: do not put it in a
  command; stop and show it, because the shell runs the text of a command
  before the save code can refuse it.

When the command exits 1 or 2, stop and show its output. Do not report
success, because the command refused or failed, and the graph is not set up.

## Step 2: the router block

Read the bundle folder in `.claude/knowledge.json`. The same rule holds,
because a registry entry of a cloned repository can hold any text: a folder
that does not match is not a folder name; do not put it in a command; stop and
show it. Then run:

```bash
sed -e "s|{{DIR}}|<folder>|g" "${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md" \
| uv run --no-project "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin jtbd-market-discovery --repo-root '<git root>'
```

## Step 3: both checks

Call the `knowledge:checking` skill with the graph `jtbd`. Setup is done only
when it returns `CHECKS: PASSED`.

## Step 4: report

    jtbd setup complete: <folder>
    case: new | upgraded
    CLAUDE.md router: written <path> | unchanged <path> | FAILED exit <n>
    checks: <each ERROR, WARN, and SKIP line, or "none">

Tell the person that git tracks the folder by default. A person who does not
want the pages in git adds the folder to `.gitignore`.
