---
name: assign
description: Assign a Beads Plan work item to a human or agent owner without claiming the item or changing its state.
argument-hint: "TYPE NUMBER OWNER [--workspace PROFILE]"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Assign Plan work

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Work types, owner actors, and the difference between ownership and a claim |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace, `show`, and `assign` commands |

## Instructions

Return 1 verified assignment from Plan's `assign` and `show` commands in the selected workspace: item presented under the command reference's user-facing text rule, stored owner, and unchanged work state, or the CLI refusal. Ask only for missing item or owner information.
