---
description: Sets up the system-design graph of this repository - the bundle at docs/system-design/ with system.md and the eight areas, the manifest, the registry entry, and the router block in CLAUDE.md. Use for "/system-design:setup".
argument-hint: "[bundle folder]"
disable-model-invocation: true
allowed-tools: Bash, Read, Skill
---

# Set up the system-design graph

`ROOT` is `$(git rev-parse --show-toplevel)`. When that command fails, stop
with: "This is not a git repository."
`S` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/system_design.py --root "$ROOT"`.

## Step 1: make or upgrade the bundle

- When `.claude/knowledge.json` names the graph `system-design`, run `$S upgrade`.
- When not, run `$S init`. Add `--dir $ARGUMENTS` when the person gave a
  folder, and `--title "<repository name> system"`.

When the command exits 1 or 2, stop and show its output. Do not report
success, because the command refused or failed, and the graph is not set up.

## Step 2: the router block

Read the bundle folder in `.claude/knowledge.json`, then run:

```bash
sed -e "s|{{DIR}}|<folder>|g" "${CLAUDE_PLUGIN_ROOT}/templates/claude-md-block.md" \
| python3 "${CLAUDE_PLUGIN_ROOT}/scripts/claude_md_router.py" --plugin system-design --repo-root "$ROOT"
```

## Step 3: both checks

Call the `knowledge:checking` skill with the graph `system-design`. Setup is
done only when it returns `CHECKS: PASSED`.

## Step 4: report

    system-design setup complete: <folder>
    case: new | upgraded
    CLAUDE.md router: written <path> | unchanged <path> | FAILED exit <n>
    checks: <each ERROR, WARN, and SKIP line, or "none">

When `docs/product/system-design.md` exists, add: "An old design file exists.
Run `/system-design:learn`. It offers to migrate the file."
