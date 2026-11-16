---
name: sync
description: Verify and refresh an explicitly selected shared Plan workspace through its coordination gate. Report blocked or uncertain synchronization without falling back to local claims.
argument-hint: "--workspace PROFILE"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Synchronize shared Plan work

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Explicit workspace and command forms |
| `${CLAUDE_PLUGIN_ROOT}/references/sharing.md` | Shared publication, gate ownership, and recovery limits |

## Instructions

Use the selected profile and the references to run Plan's `sync`, then `check`. Return the workspace identity, actual synchronization result, and every warning or refusal. A busy or retained gate is a blocker, not permission to run raw Beads synchronization, transfer ownership, or use stale local claims. Setup or conversion belongs to `plan:setup`.
