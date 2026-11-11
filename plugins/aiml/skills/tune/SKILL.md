---
name: tune
description: Use during training, when you have loss curves or training logs and want to know what to adjust. Diagnoses overfitting, underfitting, learning rate and gradient problems, and LLM fine-tuning issues. Writes docs/aiml/tune-recommendations.md. Asks for logs or key metrics when it has none.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/hyperparameter_validator.py *), Edit(/.aiml/**), Edit(/docs/aiml/**)
---

# /aiml:tune

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

Diagnoses your training run and recommends hyperparameter changes. Run it during training, not before or after. The agent writes the input file of the validator, this skill runs the script, and the agent reads the output and writes the recommendations. No agent runs a command.

## Steps

1. Read `.aiml/handoff.json` if it exists. Look for `training.log_paths`. Also look for `logs/training.log`, the file that the script of `/aiml:scaffold` writes.
2. If you find no log, ask the person with `AskUserQuestion` for a log path, or for the current epoch, training loss, validation loss and primary metric value (for example F1, accuracy or perplexity).
3. Start the agent with the `Agent` tool in the foreground (`subagent_type: aiml:tune-agent`, `run_in_background: false`). Wait for it to end. The prompt gives the field `phase: diagnose` and the answers as fields: `log_paths` and `metrics`.
4. Read the last line of the reply.
   - `READY: tune-agent validate`: go to step 5.
   - `READY: tune-agent no-change`: the agent proposes no change. Go to step 6, with `validator_exit_code` set to `none`.
   - `NEEDS-INPUT: tune-agent`: ask each question in `.aiml/open-questions.md`, then do step 3 again with the new answers.
   - Any other last line: show the reply to the person, and stop.
5. Run this command on its own, with no other command and no echo. The Bash tool reports a non-zero exit code. Record the exit code as `validator_exit_code`.

   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/hyperparameter_validator.py --input '.aiml/tune/validator-input.json' --out '.aiml/tune/validator-output.json'`

6. Start the agent again, in the foreground (`subagent_type: aiml:tune-agent`, `run_in_background: false`). Wait for it to end. The prompt gives the field `phase: recommend`, the field `validator_exit_code`, and the same fields `log_paths` and `metrics` as in step 3.
7. Read the last line of the reply.
   - `DONE: tune-agent`: show the diagnosis and the changes from `docs/aiml/tune-recommendations.md`.
   - Any other last line: show the reply to the person, and stop.

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
