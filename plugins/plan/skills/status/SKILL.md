---
name: status
description: Read or change a Beads Plan work state through actor, approval, spec, and blocker guards. Reports the actual stored state.
argument-hint: "TYPE NUMBER [STATE] [--actor ACTOR] [--approved-by REF] [--claim-token TOKEN] [--workspace PROFILE]"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Read or change Plan status

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Work states, the 5 unapproved agent transitions, spec evidence, and blocker rules |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace, `show`, and `status` commands |

A request without a target state is read-only. Ownership uses `plan:assign`; taking work uses `plan:claim`. The executing agent's actor remains `agent:ID`, including when the user supplies the approval.

## Instructions

Return 1 verified status from Plan's `show` and, when a change is requested, `status` commands, using the 2 references, selected workspace, executing actor, actual required approval, and exact current token for held work: item ID, requested and stored state, and blockers, or the exact CLI refusal for missing approval, spec, or other evidence.
