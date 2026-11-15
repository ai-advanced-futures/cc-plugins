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

Setup selects a Plan store. It does not select a different factory backend, start a team, or replace a graph registration. Product and Sofa installation are not prerequisites.

## Instructions

1. Use the 2 references to agree 1 explicit profile, Beads directory, and source root; ask only for values that are absent or unclear.
2. Return 1 verified setup from Plan's `setup`, `prd`, and `list` commands: workspace, source, store, and read checks, or the exact CLI refusal, followed by the user's chosen generate or migration step.
