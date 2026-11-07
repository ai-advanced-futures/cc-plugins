---
name: simulate
description: Use after /aiml:plan and before /aiml:scaffold, to find the gaps of the implementation plan before any code exists. Writes docs/aiml/simulation-report.md with findings (Critical, Important, Minor) and a verdict. Needs docs/aiml/plan.md.
---

# /aiml:simulate

Stress-tests the AIML implementation plan for ML-specific gaps. This skill asks the person nothing.

## Steps

1. Check that `docs/aiml/plan.md` exists. If it does not, tell the person to run `/aiml:plan` first, and stop.
2. Start `aiml:simulation-checker` 3 times in one message (`subagent_type: aiml:simulation-checker`). Give each run the paths `docs/aiml/plan.md`, `docs/aiml/spec.md` and `.aiml/handoff.json` (the agent reads the last 2 when they exist). Run 1 has `focus: ml-gaps` and `out_path: .aiml/simulation/ml-gaps.md`. Run 2 has `focus: timeline` and `out_path: .aiml/simulation/timeline.md`. Run 3 has `focus: risks` and `out_path: .aiml/simulation/risks.md`.
3. Start `aiml:simulator-agent` (`subagent_type: aiml:simulator-agent`). Give it the 3 paths `.aiml/simulation/ml-gaps.md`, `.aiml/simulation/timeline.md` and `.aiml/simulation/risks.md`.
4. Read the last line of the reply of `aiml:simulator-agent`.
   - `DONE: simulator-agent`: show the verdict from `docs/aiml/simulation-report.md` and the next step.
   - Any other last line: show the reply to the person, and stop.

## What it checks

- **ML gaps:** a missing baseline, no data validation, no leakage detection, no checkpointing.
- **Timeline:** training time, data collection, hyperparameter search, deployment.
- **Risks:** distribution shift, cold start, label noise, class imbalance, catastrophic forgetting.

The skill starts `simulation-checker` 3 times in one message (`ml-gaps`, `timeline`, `risks`), then starts `simulator-agent`, which merges the results. All four runs use **Opus**.

## Result

`docs/aiml/simulation-report.md`: the findings, sorted as Critical, Important and Minor, and a verdict.

## Verdict

- **PROCEED:** the plan is solid. Run `/aiml:scaffold`.
- **FIX_THEN_PROCEED:** fix the critical and important findings, then run `/aiml:scaffold`.
- **REDESIGN:** the gaps are basic. Go back to `/aiml:design`.
