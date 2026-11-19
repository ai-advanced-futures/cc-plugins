---
name: stories-identify
description: Divide one Beads Feature into user Stories and separate Criterion items through Product-style questions, with inherited milestones and narrower requirement traces.
argument-hint: "[feature] [--workspace PROFILE]"
model: opus
context: fork
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Grep, Glob, Bash
---

# Identify Plan stories

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/planning.md` | Conversation contract and stories: features to stories |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Story parent, milestone inheritance, narrower traces, and Criterion identity |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Plan PRD reads, story bodies, and item writes |

The selected Feature's criteria and PRD traces define this run's scope. Under the develop caller contract, source context and confirmations can be reused, the per-feature stop point has been answered, and develop owns the final check. Story discovery leaves work in backlog; a ready promotion is separate and subject to spec and actor guards.

## Instructions

Return a confirmed, ordered Story set for 1 Feature through Plan CLI writes under the 3 reference contracts: persona/action/benefit text, full-feature coverage, inherited or agreed Milestones, narrower traces when needed, and separate Story Criteria. Existing Stories, Criteria, PRD traces, and Personas remain the starting point; ask for a missing Feature.

The develop handoff contains the saved Stories, parents, Milestones, Criteria, criterion counts, and reasons for narrower traces with their source identities. Develop owns the final check; a standalone run includes 1 Plan check and presents its result under the command reference's user-facing text rule.
