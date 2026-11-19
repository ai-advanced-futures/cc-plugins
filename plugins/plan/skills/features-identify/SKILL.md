---
name: features-identify
description: Divide one Beads Epic or Milestone into confirmed Features and separate Criterion items through Product-style questions.
argument-hint: "[epic-or-milestone] [--workspace PROFILE]"
model: opus
context: fork
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Grep, Glob, Bash
---

# Identify Plan features

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/planning.md` | Conversation contract and features: epics or milestones to features |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Parent, Milestone, trace, and Criterion model |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Plan PRD reads and item writes |

A Feature can belong directly to a Milestone with no Epic parent. Existing Features and Criteria are input for a continuation. Under the develop caller contract, source context and confirmations can be reused, and develop owns the final check.

## Instructions

Return a confirmed Feature set for 1 Epic or Milestone through Plan CLI writes under the 3 reference contracts: dependencies, priority, at least 1 PRD trace per Feature, and 1 distinct Criterion per agreed acceptance result. Existing Features and Criteria remain the starting point; ask for a missing parent. Execution checks remain separate work.

The develop handoff contains the saved Features, parents, Milestones, traces, Criteria, criterion counts, and uncovered capabilities with their source identities. Develop owns the final check; a standalone run includes 1 Plan check and presents its result under the command reference's user-facing text rule.
