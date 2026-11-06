---
description: Sets up the competitive-intelligence graph of this repository - the bundle at docs/competitive-intelligence/, the manifest, the registry entry, and the router block in CLAUDE.md - and offers to ingest the earlier runs. Use for "/competitive-intelligence:setup".
argument-hint: "[bundle folder]"
disable-model-invocation: true
allowed-tools: Bash, Read, Skill
---

# Set up the competitive-intelligence graph

`ROOT` is `$(git rev-parse --show-toplevel)`. When that command fails, stop
with: "This is not a git repository."
`S` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ci_graph.py --root "$ROOT"`.

## Step 1: make or upgrade the bundle

- When `.claude/knowledge.json` names the graph `competitive-intelligence`, run `$S upgrade`.
- When not, run `$S init`. Add `--dir '<folder>'` when the person gave a folder, in single quotes. The command refuses a folder with a character outside `A-Z a-z 0-9 . _ / -`.

When the command exits 1 or 2, stop and show its output. Do not report
success, because the command refused or failed, and the graph is not set up.

## Step 2: the router block

Read the bundle folder in `.claude/knowledge.json`. When it holds a character outside `A-Z a-z 0-9 . _ / -`, stop and show the folder, because a repository that you clone can set any text there, and the text goes into a shell command. Else run:

```bash
sed -e 's|{{DIR}}|<folder>|g' "${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md" \
| python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin competitive-intelligence --repo-root "$ROOT"
```

## Step 3: the earlier runs

List each session folder in `$ROOT/.competitive-intelligence/` and `$ROOT/.competitive-intel/` that has no `pages.json`, newest file first. When there is one or more, show the list. Ask one question: "Ingest these earlier runs?" On yes, run `$S ingest <session folder>` for each one, oldest first, and show each `ingest` error.

## Step 4: both checks

Call the `knowledge:checking` skill with the graph `competitive-intelligence`. Setup is
done only when it returns `CHECKS: PASSED`.

## Step 5: report

    competitive-intelligence setup complete: <folder>
    case: new | upgraded
    CLAUDE.md router: written <path> | unchanged <path> | FAILED exit <n>
    earlier runs ingested: <number>
    checks: <each ERROR, WARN, and SKIP line, or "none">
