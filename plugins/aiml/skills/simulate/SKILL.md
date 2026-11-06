---
name: simulate
description: Use after /aiml:plan and before /aiml:scaffold, to find the gaps of the implementation plan before any code exists. Writes docs/aiml/simulation-report.md with findings (Critical, Important, Minor) and a verdict. Needs docs/aiml/plan.md.
---

# /aiml:simulate

Stress-tests the AIML implementation plan for ML-specific gaps. This skill asks the person nothing.

## Steps

1. Check that `docs/aiml/plan.md` exists. If it does not, tell the person to run `/aiml:plan` first, and stop.
2. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:simulator-agent`.
3. Read the last line of the agent reply.
   - `DONE: simulator-agent`: show the verdict from `docs/aiml/simulation-report.md` and the next step.
   - Any other last line: show the reply to the person, and stop.

## What it checks

- **ML gaps:** a missing baseline, no data validation, no leakage detection, no checkpointing.
- **Timeline:** training time, data collection, hyperparameter search, deployment.
- **Risks:** distribution shift, cold start, label noise, class imbalance, catastrophic forgetting.

The agent uses **Opus** and runs three parallel sub-tasks with the `Agent` tool.

## Result

`docs/aiml/simulation-report.md`: the findings, sorted as Critical, Important and Minor, and a verdict.

## Verdict

- **PROCEED:** the plan is solid. Run `/aiml:scaffold`.
- **FIX_THEN_PROCEED:** fix the critical and important findings, then run `/aiml:scaffold`.
- **REDESIGN:** the gaps are basic. Go back to `/aiml:design`.
