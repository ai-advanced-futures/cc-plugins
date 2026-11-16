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
| `${CLAUDE_PLUGIN_ROOT}/references/sharing.md` | Local or shared selection, paused conversion, and joining other machines |

Setup selects a Plan store. It does not select a different factory backend, start a team, or replace a graph registration. Product and Sofa installation are not prerequisites.

## Instructions

1. Use the references to agree on one explicit profile, Beads directory, source root, and local or shared mode. Ask only for absent or unclear values. Sharing an existing store requires the operator's verified pause and upgrade checks; joining requires the existing published control.
2. Return one verified setup from Plan's `setup`, `describe`, `prd`, and `list` commands: workspace identity, mode, source, store, and read checks, or the exact CLI refusal. Keep sharing, migration, and factory activation as separate approved operations.
