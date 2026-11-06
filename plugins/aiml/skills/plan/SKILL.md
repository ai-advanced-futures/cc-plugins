---
name: plan
description: Use after /aiml:design, when you have docs/aiml/spec.md and need an implementation plan. Asks three short questions, then writes docs/aiml/plan.md with four phases; each task has files, steps and verify commands.
---

# /aiml:plan

Turns the AIML spec into an implementation plan. Needs `docs/aiml/spec.md` from `/aiml:design`.

## Steps

1. Check that `docs/aiml/spec.md` exists. If it does not, tell the person to run `/aiml:design` first, and stop.
2. Read `.aiml/handoff.json` if it exists.
3. Ask the three questions below with `AskUserQuestion`, in one call. Skip a question that `.aiml/handoff.json` or the text after the command already answers.
4. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:plan-agent`. The prompt gives the answers as fields: `team_size`, `sprint_length`, `deployment_target`, and `handoff_context`.
5. Read the last line of the agent reply.
   - `DONE: plan-agent`: show the path of the plan and the next step (`/aiml:simulate`).
   - `NEEDS-INPUT: plan-agent`: ask each question in `.aiml/open-questions.md`, then do step 4 again with the new answers.

## Questions

- `team_size`: Solo, small team, or ML team?
- `sprint_length`: What is the sprint length or time-box? (default: 2 weeks)
- `deployment_target`: Cloud-managed (for example AWS SageMaker or GCP Vertex), self-hosted, or edge?

## Result

`docs/aiml/plan.md`, with four phases:

1. Environment and data pipeline
2. Model training
3. Evaluation harness
4. MLOps and deployment

Each task has the files to change, numbered steps, and verify commands.

To run the plan, use `superpowers:executing-plans` if it is installed (optional). Else do the tasks in order.
