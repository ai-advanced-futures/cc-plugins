---
name: design
description: Use after /aiml:decide, when the approach (LLM, ML or hybrid) is known and you need the AIML spec. Asks two or three short questions, then writes docs/aiml/spec.md (architecture, data needs, success metrics, feasibility) and the ADR docs/adr/aiml-approach.md.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/feasibility_check.py *)
---

# /aiml:design

Writes the AIML spec and the approach ADR. Needs `docs/aiml/decision.md` from `/aiml:decide`.

## Steps

1. Check that `docs/aiml/decision.md` exists. If it does not, tell the person to run `/aiml:decide` first, and stop.
2. Read `.aiml/handoff.json` if it exists.
3. Choose two or three questions from the list below, the ones that matter most for the approach in `decision.md`. Skip a question that `decision.md`, `.aiml/handoff.json` or the text after the command already answers. Ask them with `AskUserQuestion`.
4. Make the analyses. Do the three parts in this order:
   1. Start `aiml:design-analyst` 2 times, one at a time, in the foreground (`subagent_type: aiml:design-analyst`, `run_in_background: false`). Wait for run 1 to end before you start run 2, because an agent that starts in a group runs in the background, and the grant of this skill is gone when the agent returns. Give each run the fields `labeled_data`, `latency_volume`, `infrastructure`, `constraints`, `team`, the path `docs/aiml/decision.md`, and the path `.aiml/handoff.json` when it exists. Run 1 has `focus: data-requirements` and `out_path: .aiml/design/data-requirements.md`. Run 2 has `focus: model-architecture` and `out_path: .aiml/design/model-architecture.md`. Run 2 also writes `.aiml/design/feasibility-input.json`.
   2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/feasibility_check.py --input .aiml/design/feasibility-input.json --out .aiml/design/feasibility.json`. Run this command on its own, with no other command and no echo. The Bash tool reports a non-zero exit code. If the exit code is not 0, go on: the agent in the next part writes that the numbers are not computed.
   3. Start `aiml:design-agent` (`subagent_type: aiml:design-agent`). Give it the answers as fields (`labeled_data`, `latency_volume`, `infrastructure`, `constraints`, `team`, and `handoff_context`), the 3 paths `.aiml/design/data-requirements.md`, `.aiml/design/model-architecture.md` and `.aiml/design/feasibility.json`, and `feasibility_exit_code` (0, or the non-zero exit code that the Bash tool reported).
5. Read the last line of the reply of `aiml:design-agent`.
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

## How it works

The skill starts `design-analyst` 2 times, one at a time (data requirements and model architecture), runs `feasibility_check.py` on the input file that the model run wrote, and starts `design-agent`. The two analysts and `design-agent` use **Opus**. No agent runs a command or starts an agent: the skill does both.
