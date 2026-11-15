---
name: generate
description: Turn a Product PRD into a Beads plan. Choose MVP, one phase, or the full product, keep a milestone for every phase, and develop the selected slice.
argument-hint: "[scope] [--workspace PROFILE]"
model: opus
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Grep, Glob, Bash, Skill
---

# Generate a Plan roadmap

## References

| File | Content |
| --- | --- |
| `${CLAUDE_PLUGIN_ROOT}/references/planning.md` | Product planning behavior, scope choices, phase coverage, helper contracts, and summary fields |
| `${CLAUDE_PLUGIN_ROOT}/references/roadmap-model.md` | Types, relationships, traces, states, actors, and claims |
| `${CLAUDE_PLUGIN_ROOT}/references/cli.md` | Workspace selection, Plan commands, and result handling |

The reader model is `opus`, with prompt checks tuned against Claude Opus 5.5. A model change needs the behavior tests again.

## Instructions

1. Read the 3 references and the configured PRD through Plan; establish 1 workspace and report any missing source or incomplete capabilities and scope evidence before planning.
2. Agree 1 scope choice and the phase set described in the planning reference, using a supplied scope as the answer rather than asking the same question again.
3. Reuse or create 1 Project from the PRD summary and 1 Milestone for every agreed phase through the Plan CLI, including future phases with 0 children outside the selected slice.
4. Invoke `plan:develop` with the selected milestone IDs, scope decision, workspace, and caller contract; keep every out-of-slice milestone outside that call.
5. Return 1 combined summary using the reference's summary fields and the verified Plan check result, including any partial stop, warning, or refused promotion.
