---
name: tune
description: Use during training, when you have loss curves or training logs and want to know what to adjust. Diagnoses overfitting, underfitting, learning rate and gradient problems, and LLM fine-tuning issues. Writes docs/aiml/tune-recommendations.md. Asks for logs or key metrics when it has none.
---

# /aiml:tune

Diagnoses your training run and recommends hyperparameter changes. Run it during training, not before or after.

## Steps

1. Read `.aiml/handoff.json` if it exists. Look for `training.log_paths`. Also look for `logs/training.log`, the file that the script of `/aiml:scaffold` writes.
2. If you find no log, ask the person with `AskUserQuestion` for a log path, or for the current epoch, training loss, validation loss and primary metric value (for example F1, accuracy or perplexity).
3. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:tune-agent`. The prompt gives the answers as fields: `log_paths` and `metrics`.
4. Read the last line of the agent reply.
   - `DONE: tune-agent`: show the diagnosis and the changes from `docs/aiml/tune-recommendations.md`.
   - `NEEDS-INPUT: tune-agent`: ask each question in `.aiml/open-questions.md`, then do step 3 again with the new answers.

## What it diagnoses

- Loss curve patterns: overfitting, underfitting, a learning rate that is too high or too low.
- Gradient problems: explosion and vanishing.
- LLM fine-tuning issues: catastrophic forgetting and LoRA config problems.

Each proposed change passes `hyperparameter_validator.py` first.

## Result

`docs/aiml/tune-recommendations.md`: the diagnosis, the recommended changes with their reasons, and what to watch at the next checkpoint.

## Timing

- Before training, for the first hyperparameter setup: use `/aiml:design`.
- After training, to assess the model: use `/aiml:evaluate`.
- After you apply the changes: continue training, or run `/aiml:evaluate` when the model has converged.
