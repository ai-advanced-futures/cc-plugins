# aiml

Helps a software engineer build an AI or ML feature. It covers the choice of approach (LLM, classical ML or hybrid), the design, the plan, a check of the plan, the starter code, training guidance, evaluation, and MLOps. You need no data science background. The plugin asks short questions and writes specs, plans and code.

13 agents, 12 skills, 15 Python scripts.

## Install

```
claude plugin install aiml@cc-plugins
```

Install `uv` (https://docs.astral.sh/uv/). The scripts of the plugin run with `uv run`, and `uv` installs their packages.

## The pipeline

Run the skills in this order. Each skill works alone, so you can start at any step.

| Step | Skill | Agent (model) | Writes |
|---|---|---|---|
| 1 | `/aiml:decide` | `decision-agent` (opus) | `docs/aiml/decision.md` |
| 2 | `/aiml:design` | `design-analyst` (opus, 2 runs), `design-agent` (opus) | `docs/aiml/spec.md`, `docs/adr/aiml-approach.md` |
| 3 | `/aiml:plan` | `plan-agent` (sonnet) | `docs/aiml/plan.md` |
| 4 | `/aiml:simulate` | `simulation-checker` (opus, 3 runs), `simulator-agent` (opus) | `docs/aiml/simulation-report.md` |
| 5 | `/aiml:scaffold` | `scaffold-agent` (sonnet) | `src/`, `requirements.txt` |
| 6 | `/aiml:tune` | `tune-agent` (sonnet) | `docs/aiml/tune-recommendations.md` |
| 6 | `/aiml:evaluate` | `evaluate-agent` (sonnet) | `docs/aiml/evaluation/iteration-N.md` |
| 7 | `/aiml:ops` | `ops-agent` (sonnet) | `docs/aiml/ops/pipeline.md`, `.github/workflows/ml-pipeline.yml` |

`/aiml:tune` runs during training. `/aiml:evaluate` runs before training (it checks the dataset) or after training (it scores the model).

The skills start the agents in the main conversation. No agent starts another agent. The skill `design` runs `feasibility_check.py` between the `design-analyst` runs and `design-agent`. Only 5 agents have `Bash` (`evaluate-agent`, `tune-agent` and the three producer agents), and no agent has `Skill`.

`/aiml:orchestrate [phase]` reads `.aiml/handoff.json` and runs the next skill. With a phase name, it runs that skill.

## Quick start

```
/aiml:decide                          # Start here. Choose LLM, ML or hybrid.
/aiml:decide I need to classify...    # Start with text about your problem.
/aiml:design
/aiml:plan
/aiml:simulate                        # Find the gaps of the plan before you write code.
/aiml:scaffold                        # Write the starter code.
/aiml:tune                            # During training.
/aiml:evaluate                        # Before or after training.
/aiml:ops                             # After the verdict SHIP.
```

## Questions

Only a skill asks you questions. An agent never asks. When an agent needs more, it writes the questions to `.aiml/open-questions.md` and ends its reply with `NEEDS-INPUT: <agent>`. The skill then asks you and starts the agent again.

| Skill | Questions |
|---|---|
| `decide` | Five: the core task, the data shape, latency and cost, the labeled data you have, and what success means. |
| `design` | Two or three of: the labeled data, latency and volume, infrastructure, constraints, and team experience. |
| `plan` | Three: team size, sprint length, deployment target. |
| `simulate` | None. |
| `scaffold` | None. |
| `tune` | A log path, or the current epoch and the loss and metric values, when the plugin finds no log. |
| `evaluate` | Pre-training or post-training, when the plugin cannot tell. |
| `ops` | Three: deployment target, peak traffic, latency and uptime targets. |

A skill skips a question when your text, `.aiml/handoff.json` or an earlier file already answers it.

## Producer skills

Three skills turn a JSON file into a result file. They run a script and ask you nothing, except for a missing input path. They need `uv`.

| Skill | Input | Output |
|---|---|---|
| `/aiml:cost-amplifier-readout <input>` | `amplifier-telemetry-input.json` (measured P75 and P95 multipliers for each cost amplifier) | `.aiml/cost-amplifier-readout.json` |
| `/aiml:p15-trigger-detection --input <file> [--history <file>] [--output <file>] [--threshold-pct N] [--cap-pct M] [--quality-floor-target metric_id=value ...]` | `amplifier-telemetry-input.json` | `.aiml/p15-trigger-event.json` |
| `/aiml:archetype-baseline-telemetry --input <file> [--out <file>]` | `archetype-cost-samples.json` | `.aiml/archetype-baseline-telemetry.json` |

The schemas of these files are in the folder `schemas/` of the plugin. A small sample input is `tests/fixtures/agentic-pricing/sample-input.json`.

## Files that the plugin writes into your project

- `docs/aiml/decision.md`, `spec.md`, `plan.md`, `simulation-report.md`, `tune-recommendations.md`, `evaluation/iteration-N.md`, `ops/pipeline.md`
- `docs/adr/aiml-approach.md`. The skill `design` says this before it runs.
- `.github/workflows/ml-pipeline.yml` (a template with all jobs commented out)
- The starter code of `/aiml:scaffold`, in `src/`
- `.aiml/handoff.json`, `.aiml/open-questions.md`, and the three producer files

The plugin makes no network call and writes nothing outside your project.

## `.aiml/handoff.json`

The plugin creates this file on the first run. Each skill updates it when it ends. You do not write it by hand.

```json
{
  "phase": "decide|design|plan|simulate|scaffold|tune|evaluate|ops|complete",
  "approach": "llm|ml|hybrid|undecided",
  "artifacts": {
    "decision": "docs/aiml/decision.md",
    "spec": "docs/aiml/spec.md",
    "plan": "docs/aiml/plan.md",
    "simulation": "docs/aiml/simulation-report.md",
    "adr": "docs/adr/aiml-approach.md"
  },
  "training": {
    "iteration": 0,
    "metrics": {},
    "target_metrics": {},
    "status": "not_started|tuning|evaluating|ship|retrain"
  },
  "simulation_gaps": [],
  "completed_skills": [],
  "done": false
}
```

## Python scripts

The folder `scripts/` holds math and validation helpers and the helpers of the three producer skills. Each script that has a command line starts with a PEP 723 block, so `uv run` installs its packages.

| Script | Purpose |
|---|---|
| `metric_calculator.py` | Precision, recall, F1, accuracy, ROC-AUC |
| `data_validator.py` | Split ratios, class balance, minimum samples, leakage |
| `cost_estimator.py` | Training and inference cost |
| `feasibility_check.py` | The feasibility check of `/aiml:design`: training cost, inference cost and minimum samples from one input file |
| `hyperparameter_validator.py` | Learning rate, batch size, epochs, LoRA settings |
| `amplifier_telemetry_loader.py`, `amplifier_composer.py`, `cost_amplifier_readout_emitter.py` | The cost-amplifier readout |
| `p15_trigger_input_loader.py`, `p15_trigger_detector.py`, `p15_trigger_emitter.py` | The P15 trigger event |
| `archetype_baseline_input_loader.py`, `archetype_baseline_aggregator.py`, `archetype_baseline_emitter.py` | The archetype baseline |
| `_jsonschema_formats.py` | The shared format checker and the path of `schemas/` |

Example:

```
uv run scripts/metric_calculator.py confusion --tp 95 --tn 90 --fp 5 --fn 5
```

## Optional tools

The plugin works without these tools.

- **superpowers.** `/aiml:plan` writes a plan that `superpowers:executing-plans` can run. Without superpowers, do the tasks of the plan in order.
- **context7.** `/aiml:scaffold` reads the current API of each library from context7 before it writes code. To add context7:

  ```
  claude mcp add --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: <your-key>"
  ```

  Without context7, the agent writes the code from the spec and the plan.

## Run the tests

From the folder `plugins/aiml`:

```
uv run --with-requirements requirements-dev.txt python -m pytest tests -q -rs
```

## Knowledge sources

The agents use ideas from these works:

- Géron, *Hands-on Machine Learning with Scikit-Learn, Keras & TensorFlow* (chapters 1 to 3, 11, 14, 16, 18)
- Iusztin and Labonne, *LLM Engineer's Handbook*
- Vaswani and others, *Attention Is All You Need* (2017)
- Karpathy, Chip Huyen, Andrew Ng and Lilian Weng

The starter code uses HuggingFace Transformers, PEFT, TRL and datasets.

## More

- `CHANGELOG.md`
- `docs/INDEX.md`: the ADRs and the C4 diagrams
- `NOTICE`: the license of the source plugin
