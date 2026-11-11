---
name: evaluate
description: Use before training, to check dataset quality (splits, class balance, minimum samples, leakage), or after training, to score the model against the targets of docs/aiml/spec.md and decide to ship, retrain or redesign. Writes docs/aiml/evaluation/iteration-N.md. Asks which mode when it cannot tell.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_validator.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/metric_calculator.py *), Edit(/.aiml/**), Edit(/docs/aiml/**)
---

# /aiml:evaluate

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

Evaluates the dataset (before training) or the model (after training). The agent writes the input file of each check, this skill runs the scripts, and the agent reads the outputs and writes the report. No agent runs a command. The agent writes the input files, so that a value from a dataset never goes into a shell command, because a name can hold shell text.

## Steps

1. Read `.aiml/handoff.json` if it exists. Read `training.status`: `pending` or absent means pre-training; `tuning` or `complete` means post-training.
2. If the argument text or `training.status` does not tell the mode, ask the person with `AskUserQuestion`: pre-training (dataset quality) or post-training (model scoring)?
3. Start the agent with the `Agent` tool in the foreground (`subagent_type: aiml:evaluate-agent`, `run_in_background: false`). Wait for it to end. The prompt gives the field `phase: prepare`, the answer as the field `mode` (`pre-training` or `post-training`), and the paths of the dataset or the metrics when you know them.
4. Read the last line of the reply.
   - `READY: evaluate-agent` and the names of the checks that the agent wrote an input file for (for example `READY: evaluate-agent split balance leakage`): go to step 5.
   - Any other last line: show the reply to the person, and stop.
5. For each check of the line, in the order of the line, run its command from the table below. Run each command on its own, with no other command and no echo. The Bash tool reports a non-zero exit code. Record the exit code of each check. A name that is not in the table has no command, because only the commands of the table are granted: record it with the exit code `not run`. Run only the checks of the line, because an input file that the agent did not write in this run can be from an earlier run.
6. Start the agent again, in the foreground (`subagent_type: aiml:evaluate-agent`, `run_in_background: false`). Wait for it to end. The prompt gives the field `phase: report`, the field `mode`, the same paths as in step 3, and the field `exit_codes` (each check of the line and its exit code).
7. Read the last line of the reply.
   - `DONE: evaluate-agent`: show the verdict and the next steps from `docs/aiml/evaluation/iteration-N.md`.
   - Any other last line: show the reply to the person, and stop.

| Check | Mode | Command |
|---|---|---|
| `split` | pre-training | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_validator.py split --input '.aiml/evaluation/split-input.json' --out '.aiml/evaluation/split-output.json'` |
| `balance` | pre-training | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_validator.py balance --input '.aiml/evaluation/balance-input.json' --out '.aiml/evaluation/balance-output.json'` |
| `min-samples` | pre-training | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_validator.py min-samples --input '.aiml/evaluation/min-samples-input.json' --out '.aiml/evaluation/min-samples-output.json'` |
| `leakage` | pre-training | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/data_validator.py leakage --input '.aiml/evaluation/leakage-input.json' --out '.aiml/evaluation/leakage-output.json'` |
| `confusion` | post-training | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/metric_calculator.py confusion --input '.aiml/evaluation/confusion-input.json' --out '.aiml/evaluation/confusion-output.json'` |
| `roc-auc` | post-training | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/metric_calculator.py roc-auc --input '.aiml/evaluation/roc-auc-input.json' --out '.aiml/evaluation/roc-auc-output.json'` |

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
