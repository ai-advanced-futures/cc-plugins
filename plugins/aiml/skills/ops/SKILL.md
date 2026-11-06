---
name: ops
description: Use after /aiml:evaluate returns SHIP, when the model is ready for production. Asks three short questions about deployment, traffic and SLA, then writes docs/aiml/ops/pipeline.md (registry, serving, monitoring, feedback loops, CI/CD, rollback) and the template .github/workflows/ml-pipeline.yml. Last skill of the pipeline.
---

# /aiml:ops

Designs the MLOps pipeline. Run it only after `/aiml:evaluate` returns **SHIP**.

## Steps

1. Check `.aiml/handoff.json` and `docs/aiml/evaluation/`. If the last verdict is not SHIP, tell the person to run `/aiml:evaluate` first, and stop.
2. Ask the three questions below with `AskUserQuestion`, in one call. Skip a question that `.aiml/handoff.json` or the text after the command already answers.
3. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:ops-agent`. The prompt gives the answers as fields: `deployment_target`, `traffic`, `sla`.
4. Read the last line of the agent reply.
   - `DONE: ops-agent`: show the paths of the two files. The agent sets `done: true` in `.aiml/handoff.json`.
   - `NEEDS-INPUT: ops-agent`: ask each question in `.aiml/open-questions.md`, then do step 3 again with the new answers.

## Questions

- `deployment_target`: Cloud (AWS, GCP or Azure), on-premises, or an edge device? (default: cloud)
- `traffic`: How many requests per second at peak? (default: low traffic)
- `sla`: What is the maximum p95 latency, and what uptime do you need? (default: 500ms p95)

## Result

- `docs/aiml/ops/pipeline.md`: the MLOps pipeline spec.
- `.github/workflows/ml-pipeline.yml`: a CI/CD template. All jobs are commented out. Remove the comments you need.

## Pipeline parts

- **Model registry:** versions, promotion, rollback.
- **Serving:** LLM (HuggingFace Endpoints or vLLM) or ML (sklearn with FastAPI).
- **Monitoring:** input drift, output drift, performance alerts.
- **Feedback loops:** RLHF, SFT or DPO for LLMs; active learning for classical ML.
- **CI/CD:** data validation, training, evaluation, shadow deploy, promotion.
