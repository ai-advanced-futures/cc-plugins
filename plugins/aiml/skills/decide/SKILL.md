---
name: decide
description: Use when you consider adding AI or ML to a feature and do not know if an LLM, classical ML or a hybrid fits. Asks five short questions, then writes docs/aiml/decision.md with a recommendation, reasons and risks. First step of the aiml pipeline.
---

# /aiml:decide

Chooses between an LLM, classical ML and a hybrid. Writes `docs/aiml/decision.md`.

## Steps

1. Read `.aiml/handoff.json` if it exists. Read the text after the command as `problem`.
2. Ask the person the five questions below with `AskUserQuestion`, one question at a time. Skip a question that `problem` or `.aiml/handoff.json` already answers.
3. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:decision-agent`. The prompt gives the answers as fields: `problem`, `core_task`, `data_shape`, `latency_cost`, `labeled_data`, `success`, and `handoff_context` (the content of `.aiml/handoff.json`).
4. Read the last line of the agent reply.
   - `DONE: decision-agent`: show the recommendation from `docs/aiml/decision.md` and the next step (`/aiml:design`).
   - `NEEDS-INPUT: decision-agent`: ask each question in `.aiml/open-questions.md`, then do step 3 again with the new answers.

## Questions

1. **Core task.** Classify (give a label), generate (text, code, summaries), retrieve (find items in a corpus), predict (a number or an event), recommend (suggest items), or other?
2. **Data shape.** Structured (rows and columns), unstructured text, images or video, time series, or no data yet?
3. **Latency and cost.** Real-time (<100ms), near-real-time (<1s), batch (minutes to hours), or cost-sensitive at scale?
4. **Labeled data today.** None, fewer than 1,000 examples, 1,000 to 100,000, or more than 100,000?
5. **Success.** A numeric accuracy target, user satisfaction, a business metric, or "good enough"?

## Result

- `docs/aiml/decision.md`: the recommendation (**LLM**, **ML (classical)** or **Hybrid**), the reasons, the risks, and the next step.
- `.aiml/handoff.json`: the phase, `completed_skills`, and `project_type`.

## When to run

- First step of the pipeline: run it before `/aiml:design`.
- Run it again when a need changes, for example a new latency limit or a new rule.
