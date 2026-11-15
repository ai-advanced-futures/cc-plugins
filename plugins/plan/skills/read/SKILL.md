---
name: read
description: Read a Beads Plan item, ready work, history, checks, or Product PRD evidence from one explicit workspace. Answers planning questions without a Product or Sofa installation.
argument-hint: "[question-or-item] [--workspace PROFILE]"
model: opus
allowed-tools: AskUserQuestion, Read, Bash
---

# Read Plan evidence

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Item identity, criteria, states, traces, and local claim limits |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace and read commands: `describe`, `prd`, `list`, `show`, `history`, `ready`, and `check` |

This skill answers from the selected store and its PRD source. A request to change the plan belongs to the corresponding planning or lifecycle skill.

## Instructions

Return 1 evidence-based answer to the requested question through the read commands in the 2 references, with the selected workspace, relevant Plan or PRD IDs, stored or effective state when relevant, and any warning or exact CLI refusal; ask for a missing target only when the question cannot identify one.
