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

1. Read the 3 references and resolve 1 Epic or Milestone with its existing Features, Criteria, and relevant PRD capabilities; ask for a parent when neither the caller nor argument supplies one.
2. Agree the Feature set, dependencies, priority, and acceptance text through the reference's discovery, challenge, and set-confirmation questions, keeping each criterion to 1 observable completion sentence.
3. Store 1 Feature per confirmed missing outcome through Plan, with the chosen parent when present, Milestone, and at least 1 PRD trace.
4. Store 1 distinct Criterion item per agreed missing Feature criterion and link it to that Feature, leaving execution checks for separate work.
5. Return every Feature ID, parent, Milestone, trace, criterion ID and count, and uncovered capability; run 1 Plan check for a standalone run or return these fields to develop for its final check.
