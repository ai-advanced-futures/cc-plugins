---
name: claim
description: Take one ready Beads Plan work item with an actor-owned lease through the Plan lifecycle guards.
argument-hint: "TYPE NUMBER --actor ACTOR [--lease 30m] [--workspace PROFILE]"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Claim Plan work

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Actors, ready work, and claim leases |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace, `ready`, `show`, and `claim` commands |

## Instructions

Return 1 verified claim from Plan's `claim` and `show` commands, using the 2 references, selected workspace, executing actor, and requested or default lease: item presented under the command reference's user-facing text rule, state, holder, lease expiry, and the returned claim token for later operations, or the CLI refusal.
