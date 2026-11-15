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

1. Read the 3 references and resolve 1 Feature with its existing Stories, Criteria, PRD traces, and Personas; ask which Feature to divide when the caller and argument name none.
2. Agree an ordered Story set through the reference's action, failure, success, 6 story tests, split choices, and full-feature coverage questions; use the persona/action/benefit form in each description and body.
3. Store 1 Story per confirmed missing outcome through Plan with the Feature parent, inherited or agreed Milestone, and a direct trace only when it narrows the Feature's requirement coverage.
4. Store 1 distinct Criterion item per agreed missing Story criterion, linked to that Story and separate from the Feature's criteria.
5. Return every Story ID, parent, Milestone, criterion ID and count, and reason for each narrower trace; run 1 Plan check for a standalone run or return these fields to develop for its final check.
