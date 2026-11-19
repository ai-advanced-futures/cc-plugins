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

Return 3 to 6 confirmed themes for 1 Milestone through Plan CLI writes under the 3 reference contracts, or record the user's reason for a smaller set. Each missing theme becomes 1 Epic with its Milestone and at least 1 PRD trace. Existing Epics and PRD evidence remain the starting point; ask for a missing Milestone or source evidence before storing work.

The develop handoff contains the saved Epics, Milestone, traces, and uncovered capabilities with their source identities. Develop owns the final check; a standalone run includes 1 Plan check and presents its result under the command reference's user-facing text rule.
