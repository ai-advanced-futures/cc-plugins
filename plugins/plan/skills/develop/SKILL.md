---
name: develop
description: Continue a Beads milestone, epic, or feature through Plan's themes, features, and stories helpers. Preserve scope, per-feature stop points, criteria, and requirement coverage.
argument-hint: "[milestone-or-epic-or-feature] [--workspace PROFILE]"
model: opus
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Grep, Glob, Bash, Skill
---

# Develop a Plan slice

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/planning.md` | Conversation, the 3 adapted Product helpers, selected-slice completion, and summary |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Item relationships, criterion identity, actor approval, and spec guards |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Plan-only write interface and result handling |

`plan:generate` supplies the scope and milestone set. A standalone run continues an existing Milestone, Epic, or Feature selected from Plan. Existing children and criteria are part of the input. The caller contract gives each helper the workspace, chosen parent, source context, and confirmation history, and leaves 1 final check with develop.

## Instructions

1. Read the 3 references and resolve the selected Plan item or caller slice in 1 workspace; when no item is given, ask which existing Milestone, Epic, or Feature to continue.
2. Use `plan:themes-identify` for the missing Epic groups of selected milestones and `plan:features-identify` for their Epics or direct milestone Features, preserving confirmed existing items instead of making duplicates.
3. Give the user 1 stop point before `plan:stories-identify` for each Feature; continue only the chosen Features and retain a partial plan when the user stops.
4. Check trace targets, code-written hashes, and scope coverage for the selected slice; get the user's classification of every uncovered scope entry as a gap or an intentional omission.
5. Request selected-slice promotion through Plan status with the executing actor and actual approval evidence; report the returned ready or blocked state and leave each refused Story promotion visible as a spec or approval gap.
6. Run 1 final Plan check and return the reference's summary fields, including all milestones supplied by generate, item and criterion counts, blockers, missing traces, warnings, and the next Plan step.
