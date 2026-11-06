---
name: evaluate
description: Use before training, to check dataset quality (splits, class balance, minimum samples, leakage), or after training, to score the model against the targets of docs/aiml/spec.md and decide to ship, retrain or redesign. Writes docs/aiml/evaluation/iteration-N.md. Asks which mode when it cannot tell.
---

# /aiml:evaluate

Evaluates the dataset (before training) or the model (after training).

## Steps

1. Read `.aiml/handoff.json` if it exists. Read `training.status`: `pending` or absent means pre-training; `tuning` or `complete` means post-training.
2. If the argument text or `training.status` does not tell the mode, ask the person with `AskUserQuestion`: pre-training (dataset quality) or post-training (model scoring)?
3. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:evaluate-agent`. The prompt gives the answer as the field `mode` (`pre-training` or `post-training`), and the paths of the dataset or the metrics when you know them.
4. Read the last line of the agent reply.
   - `DONE: evaluate-agent`: show the verdict and the next steps from `docs/aiml/evaluation/iteration-N.md`.
   - Any other last line: show the reply to the person, and stop.

## Pre-training checks

- Split ratios (train, val and test sum to 1.0)
- Class balance (imbalance ratio, minority %)
- Minimum sample estimate
- Data leakage risk

Verdicts: **GO**, **FIX**, **REDESIGN**.

## Post-training scoring

- Precision, recall, F1 and accuracy (from the confusion matrix)
- ROC-AUC estimate
- Comparison with the targets of `docs/aiml/spec.md`
- Over-fitting and under-fitting diagnosis

## Verdict

- **SHIP:** the model meets the targets. Run `/aiml:ops`.
- **RETRAIN:** the model is close. Change the hyperparameters, and run `/aiml:tune`.
- **REDESIGN:** the model is far off. Go back to `/aiml:design`.

## Result

`docs/aiml/evaluation/iteration-N.md`: the metrics, the analysis and the verdict.
