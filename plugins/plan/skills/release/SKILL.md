---
name: release
description: Return a claimed Beads Plan work item to ready or blocked. This ends a claim, rather than marking product work released.
argument-hint: "TYPE NUMBER --actor ACTOR --claim-token TOKEN [--workspace PROFILE]"
model: opus
allowed-tools: Read, Bash
---

# Release a Plan claim

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Claim release and computed ready or blocked state |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace, `release`, and `show` commands |

The `released` work state is a separate `plan:status` request. This skill gives held work back without declaring a product release.

## Instructions

Return 1 verified claim release from Plan's `release` and `show` commands, using the 2 references, selected workspace, executing actor, and exact current claim token: item ID, cleared claim, stored state, and blockers, or the exact CLI refusal.
