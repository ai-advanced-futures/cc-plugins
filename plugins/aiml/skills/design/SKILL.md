---
name: design
description: Use after /aiml:decide, when the approach (LLM, ML or hybrid) is known and you need the AIML spec. Asks two or three short questions, then writes docs/aiml/spec.md (architecture, data needs, success metrics, feasibility) and the ADR docs/adr/aiml-approach.md.
---

# /aiml:design

Writes the AIML spec and the approach ADR. Needs `docs/aiml/decision.md` from `/aiml:decide`.

## Steps

1. Check that `docs/aiml/decision.md` exists. If it does not, tell the person to run `/aiml:decide` first, and stop.
2. Read `.aiml/handoff.json` if it exists.
3. Choose two or three questions from the list below, the ones that matter most for the approach in `decision.md`. Skip a question that `decision.md`, `.aiml/handoff.json` or the text after the command already answers. Ask them with `AskUserQuestion`.
4. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:design-agent`. The prompt gives the answers as fields: `labeled_data`, `latency_volume`, `infrastructure`, `constraints`, `team`, and `handoff_context`.
5. Read the last line of the agent reply.
   - `DONE: design-agent`: show the paths of the two files and the next step (`/aiml:plan`).
   - `NEEDS-INPUT: design-agent`: ask each question in `.aiml/open-questions.md`, then do step 4 again with the new answers.

## Questions

- `labeled_data`: How much labeled data do you have now, and can you collect more?
- `latency_volume`: What is the target inference latency and the expected request volume?
- `infrastructure`: Do you have GPU infrastructure, or do you use cloud APIs?
- `constraints`: Do data residency, privacy or regulation limit the design?
- `team`: How much ML and Python experience does the team have?

## Result

- `docs/aiml/spec.md`: the full spec. The agent writes it again on each run.
- `docs/adr/aiml-approach.md`: the approach ADR, in the ADR folder of your project. An existing ADR numbering scheme there can conflict with it.

## How the agent works

It uses **Opus**. It runs three parallel sub-tasks with the `Agent` tool (`data-requirements`, `model-architecture`, `feasibility-check`), then merges them. The feasibility sub-task runs `cost_estimator.py` and `data_validator.py` from the plugin.
