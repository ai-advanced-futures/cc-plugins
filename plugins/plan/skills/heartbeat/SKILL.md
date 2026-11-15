---
name: heartbeat
description: Renew the executing actor's claim lease on one Beads Plan work item.
argument-hint: "TYPE NUMBER --actor ACTOR --claim-token TOKEN [--lease 30m] [--workspace PROFILE]"
model: opus
allowed-tools: Read, Bash
---

# Renew a Plan claim

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Claim holder and lease meaning |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace, `heartbeat`, and `show` commands |

## Instructions

Return 1 verified renewal from Plan's `heartbeat` and `show` commands, using the 2 references, selected workspace, executing actor, exact current claim token, and requested or default lease: item ID, holder, heartbeat time, and lease expiry, or the exact CLI refusal.
