---
description: Sets up the generic knowledge graph of this repository - a new bundle on the brain standard, or the migration of an old wiki (.claude/wiki.json) - and writes the knowledge router block in CLAUDE.md. Use for "/knowledge:setup", "set up a wiki", and "migrate the wiki to the knowledge plugin".
argument-hint: "[container path]"
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Edit, Skill, AskUserQuestion
---

# Set up the knowledge graph

`ROOT` is `$(git rev-parse --show-toplevel)`. When that command fails, stop
with: "This is not a git repository."
`G` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/knowledge_graph.py --root "$ROOT"`.

## Step 1: find the case

| Case | Test | Go to |
|---|---|---|
| old default folder | the path of `knowledge` in `.claude/knowledge.json` is `docs/wiki/bundle` | Step 2a |
| set up | `.claude/knowledge.json` has the graph `knowledge` | Step 3 |
| old wiki | `.claude/wiki.json` exists | Step 2 |
| new | neither | Step 4 |

## Step 2a: move the old default folder

1. Show the items that move (`docs/wiki/AGENTS.md`, `docs/wiki/bundle/`,
   `docs/wiki/raw/`) and the new place `docs/knowledge/`. Ask one question:
   "Move the graph to docs/knowledge/?"
2. After a yes, run `$G move --to docs/knowledge/`. When it exits 1 or 2, show
   the output and stop, because Step 3 and Step 5 need a finished move. Else, search the
   repository for `docs/wiki/` and show each file that still names it. Then do
   Step 3. Step 3 ends with Step 5, which writes the router block with the new
   path.
3. After a no, do Step 3. The graph stays in `docs/wiki/`, and each command
   finds it through the registry. A later setup run asks again.

## Step 2: migrate an old wiki

1. Read `container` in `.claude/wiki.json`. The bundle is `<container>bundle/`.
2. Run `$G upgrade`. It back-fills `generated`, adds `log.md`, runs `regen`,
   writes `manifest.md` and the registry entry `knowledge`, and writes one
   Upgrade entry in `log.md`. When it exits 1 or 2, stop and show the output.
3. Show this list and ask one question: "Delete these old files?"
   - `.claude/wiki.json`
   - `<container>scripts/check_okf.py`, `<container>scripts/check_links.py`,
     `<container>scripts/regen_indexes.py`
   - `<container>tests/` and `<container>requirements.txt`
   Delete them only after a yes. When the project CI runs the old scripts,
   tell the person to change the CI to
   `uv run <knowledge plugin>/scripts/knowledge.py check --strict`, or to
   answer no and keep the copies.
4. Write `AGENTS.md` again from `${CLAUDE_PLUGIN_ROOT}/templates/rendered/AGENTS.md`
   (the same yes), with the tokens of Step 4.
5. Move the router block: remove the old block between
   `<!-- wiki:router start -->` and `<!-- wiki:router end -->` from `CLAUDE.md`
   with Edit. When there are no markers, remove the old `## Knowledge wiki`
   block. Then do Step 5.

## Step 3: already set up

Run `$G upgrade`. It prints "the bundle is on the standard: nothing to
change" when no change is necessary. Then do Step 5.

## Step 4: a new graph

1. Find the values, each with its fallback: the container (`$ARGUMENTS`, else
   `docs/knowledge/`), the subject (the README title), the repository name, the
   human actor (`human:` plus the git user name), the agent actor (for example
   `claude-code/opus-5.5`), and today's date.
2. Show the values and the file list of
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py --dry-run ...`. Ask one
   question to confirm them.
3. Run:

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py --target "$ROOT" --container <container> \
     --subject "<subject>" --repo <repo> --human-actor <human> --agent-actor <agent> --today <date>
   ```

   The script writes the router block. Skip Step 5.

## Step 5: the router block

Unless the person declined it, run:

```bash
sed -e "s|{{CONTAINER}}|<container>|g" "${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md" \
| python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin knowledge --repo-root "$ROOT"
```

## Step 6: both checks and the receipt

Call the `knowledge:checking` skill with the graph `knowledge`. Setup is done
only when it returns `CHECKS: PASSED`. Then report:

    knowledge setup complete: <bundle>
    case: new | migrated | upgraded
    CLAUDE.md router: written <path> | unchanged <path> | skipped (declined) | FAILED exit <n>
    checks: <each ERROR, WARN, and SKIP line, or "none">
