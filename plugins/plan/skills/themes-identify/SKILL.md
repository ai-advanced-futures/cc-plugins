---
name: themes-identify
description: Group one Beads milestone's capabilities into confirmed Epics with Product-style questions, milestone links, and PRD traces.
argument-hint: "[milestone] [--workspace PROFILE]"
model: opus
context: fork
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Grep, Glob, Bash
---

# Identify Plan themes

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/planning.md` | Conversation contract and themes: milestones to epics |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Epic, Milestone, and trace model |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Plan PRD reads and item writes |

A standalone run needs 1 existing Milestone. `plan:generate` supplies milestones through `plan:develop`. Under that caller contract, source context and confirmations can be reused, and develop owns the final check.

## Instructions

1. Read the 3 references and the selected Milestone, its existing Epics, and its relevant PRD capabilities and scope; ask for 1 Milestone when the caller and argument name none.
2. Agree 3 to 6 themes with the user using the reference's value, dependency, risk, and scope questions, or record the user's reason for a smaller set.
3. Store 1 Epic per confirmed missing theme through Plan, with its Milestone and at least 1 PRD trace; resolve untraced proposals with the user before storing them.
4. Return each Epic ID, Milestone, trace, and uncovered capability; run 1 Plan check for a standalone run or return these fields to develop for its final check.
