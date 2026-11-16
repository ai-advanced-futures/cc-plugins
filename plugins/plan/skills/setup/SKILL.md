---
description: Configure an explicit Plan workspace with a Beads directory and a read-only Product PRD source. Leaves Product and Sofa configuration unchanged.
argument-hint: "--workspace PROFILE --beads-dir DIR --source-root ROOT"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Set up a Plan workspace

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace profile, source root, Beads directory, and setup command |
| `${CLAUDE_PLUGIN_ROOT}/references/planning.md` | Read-only source and explicit activation boundaries |
| `${CLAUDE_PLUGIN_ROOT}/references/single-factory.md` | One machine, the backup remote and the automatic push, restore, and `unshare` for a profile from shared mode |

Setup selects a Plan store. It does not select a different factory backend, start a team, or replace a graph registration. Product and Sofa installation are not prerequisites.

## Instructions

1. Use the references to agree on one explicit profile, Beads directory, and source root. Ask only for absent or unclear values.
2. Return one verified setup from Plan's `setup`, `describe`, `prd`, and `list` commands: workspace identity, source, store, the `backup` block of `describe`, and read checks, or the exact CLI refusal. If the user names a backup remote, save it with `backup --remote NAME --auto on`. If the refusal names `unshare`, report it and run `unshare` only after the user approves. Keep migration, backup, and factory activation as separate approved operations.
