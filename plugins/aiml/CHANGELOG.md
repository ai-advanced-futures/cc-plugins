# Changelog

## 0.8.1

### Fixed

- Each `--input` reader of the scripts takes only a regular file of 8 MiB or less, and reads numbers that are finite. A folder, a device, a named pipe, a link to one of them, a larger file, text that is not UTF-8, a nesting that is too deep, `NaN`, `Infinity`, `1e999` and an integer that a float cannot hold give 1 line on standard error and exit 1, with no traceback and no wait. These `--input` readers are `balance`, `leakage`, `roc-auc`, `split`, `min-samples`, `confusion` and `hyperparameter_validator.py` (`--input`), `feasibility_check.py`, the 3 emitters, and the `--history` file of the P15 emitter.
- `balance` takes only whole counts of 0 or more, and not `true`. A class with 0 samples gives `"imbalance_ratio": null`, and not `Infinity`.
- Each number option refuses `nan`, `inf` and an integer that a float cannot hold, with 1 line and exit 1 (`--lr`, `--lora-alpha`, `--tp`, `--hours`, `--cap-pct` and the others). A result that is not finite gives 1 line and exit 1, and an emitter writes no file and exits 2. No script writes `NaN` or `Infinity`.

### Added

- The module `scripts/_safe_input.py` and the tests `test_safe_input.py` and `test_input_readers.py`. STORY-368, issue #1552.

## 0.8.0

### Changed

- No agent of the plugin has `Bash` (D-266). The 5 skills `evaluate`, `tune`, `archetype-baseline-telemetry`, `cost-amplifier-readout` and `p15-trigger-detection` run the scripts in the main conversation, one command in each Bash call, with no other command and no echo. Each of the 5 skills has an `allowed-tools` line that grants only its scripts and the folder `.aiml`; `evaluate` and `tune` also grant `docs/aiml`. The 5 agents keep only `Read` and `Write`.
- `/aiml:evaluate` has 3 steps. `evaluate-agent` with `phase: prepare` writes the input file of each check and ends with `READY: evaluate-agent <check> ...`; the skill runs the command of each named check; then `evaluate-agent` with `phase: report` reads the outputs, writes `docs/aiml/evaluation/iteration-N.md`, and ends with `DONE: evaluate-agent`. `evaluate-agent` has a new section `Input files`: the 6 input files and their JSON shapes.
- `/aiml:tune` has 3 steps. `tune-agent` with `phase: diagnose` writes `.aiml/tune/diagnosis.md` and `.aiml/tune/validator-input.json`; the skill runs `hyperparameter_validator.py`; then `tune-agent` with `phase: recommend` writes `docs/aiml/tune-recommendations.md`.
- The 3 emitter skills run the emitter first, before they start any agent. On a non-zero exit, the skill shows the lines on standard error, starts no agent and writes no file. The 3 emitter agents read the output file and write the handoff. This closes STORY-302 and STORY-303.
- Each of the 5 skills runs its agents in the foreground, and says why: an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of the skill.
- The scripts `data_validator.py` (`split`, `min-samples`), `metric_calculator.py` (`confusion`) and `hyperparameter_validator.py` read their values from a file with `--input`. All the checks of `data_validator.py` and `metric_calculator.py`, and `hyperparameter_validator.py`, write the JSON object to a file with `--out` and print nothing. The old options still work. `--out` must name a file inside the folder `.aiml` of the current directory. A `..`, an absolute path outside it and a link to an outside folder exit 1 and touch no file. After the arguments pass, the script deletes the old file, so a file that exists after exit 0 is from this run. The 3 emitters (`--out`, and `--output` of `p15_trigger_emitter.py`) keep their output file inside `.aiml` in the same way. The options of these scripts are not shortened (`--ou` is an error). `hyperparameter_validator.py` now exits 1, and not 2, for an argument error.
- `tune-agent` follows the same rules for `.aiml/tune/diagnosis.md` as for `.aiml/tune/validator-input.json`: it reads the file before it writes it, and when a `Write` call fails it ends with `NEEDS-INPUT: tune-agent`, so the phase `recommend` cannot read an old `diagnosis.md`.
- The docs say that the skills run the scripts: ADR-001, ADR-003, ADR-004, `docs/c4/container.md` and `README.md`.

### Added

- A live tier `nobash` in `tests/integration/test_live_port.py`: a session in the default permission mode, with no `--allowedTools`, runs `evaluate` (3 runs), `tune` and `cost-amplifier-readout`, and runs the 3 emitter skills with an input path that does not exist (9 runs). Each script call is a top-level `Bash` call (it exits 0, except in the 9 missing-input runs), no agent calls `Bash`, and no tool call is refused.
- Tests: a rule that each `uv run` line has the form `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py` and sits in a skill with the grant; a list of the files that have a `uv run` line; the rules of the section `Input files`; the order of the steps of the 3 emitter skills; the `--input` and `--out` cases of the 3 scripts.

## 0.7.0

### Changed

- `data_validator.py balance` and `leakage`, and `metric_calculator.py roc-auc`, read their values from a JSON file with the option `--input`: `{"class_counts": {...}}`, `{"features": [...], "target": "..."}` and `{"pairs": [[tpr, fpr], ...]}`. The options `--class-counts`, `--features`, `--target` and `--pairs` are removed and exit 1 with one line. A file that is missing, is not JSON, is not an object, has no key or has a value of the wrong type gives one line `error: <path>: ...` and exit 1. A class name or a column name that holds a `'`, a `;` or a `$(...)` can no longer reach the shell.
- `evaluate-agent` writes `.aiml/evaluation/balance-input.json`, `leakage-input.json` and `roc-auc-input.json` with the `Write` tool and runs the 3 checks with `--input`. It does not run a check when the `Write` call fails. Each other placeholder in the commands of `evaluate-agent` and `tune-agent` is in single quotes.

### Added

- Tests: the `--input` files, the error lines, the old options, a leakage run with names that hold `'`, `;`, `$(...)` and a new line, and 3 text rules for the agents and skills (no value option in a command, each placeholder of a value script in single quotes, the sentences of `evaluate-agent`).

## 0.6.1

### Fixed

- The agents `cost-amplifier-readout-agent`, `p15-trigger-detector-agent` and `archetype-baseline-telemetry-agent` run the emitter as their first command. The step "Validate input file exists" is removed: the model ran `test -f` for it, and a session that allows `uv run` only refused that command, so the agent could stop with no file. The emitter checks the input, and exits 1 with `Input file not found: <path>` when it is missing.

### Added

- `tests/unit/test_emitter_first_step.py`: step 1 of each emitter agent is the `uv run` command of its emitter, no step checks the input file with a shell command, and each emitter exits 1 with the message `Input file not found: <path>` and writes no file when the input is missing.

## 0.6.0

### Changed

- The skill `design` starts the new agent `design-analyst` 2 times (data requirements and model architecture), runs the new script `scripts/feasibility_check.py`, and then starts `design-agent`. The skill `simulate` starts the new agent `simulation-checker` 3 times (ML gaps, timeline and risks), and then starts `simulator-agent`. The two parent agents no longer start `general-purpose` sub-tasks, and they merge the result files.
- `design-agent` and `simulator-agent` have `Read` and `Write`. `scaffold-agent` has no `Bash`, because no step runs a command. The new agents have `Read` and `Write`.
- The feasibility check runs in the skill: the model run writes `.aiml/design/feasibility-input.json`, and the script writes `.aiml/design/feasibility.json`. The script refuses a word that `cost_estimator.py` does not know. When the check fails, the spec says that the cost and minimum-samples numbers are not computed.

- The skill `design` starts the 2 `design-analyst` runs one at a time, in the foreground (D-377), and runs the check command on its own, with no `echo`. The script refuses a number that is NaN or Infinity, and writes `ok: false` when a cost is too large.

### Added

- `tests/unit/test_agent_grants.py` fails on an `Agent` grant, a `Skill` grant, a `Bash` grant outside the 5 agents that run scripts, and a `general-purpose` agent in a prompt file.
- The live tiers `design` and `simulate` (`make itest TIER=design`).

## 0.5.0

First version in this repository. The plugin is a port of `aiml` 0.4.2. Versions 0.1.0 to 0.4.2 came before the port, from commit `c2a329f` of a private repository.

### Changed

- Only a skill asks the person a question. An agent never asks. When an agent needs more information, it writes `.aiml/open-questions.md` and ends its reply with `NEEDS-INPUT: <agent>`. The skill then asks the person and dispatches the agent again.
- Each skill dispatches its agent with the `Agent` tool (`aiml:<agent>`). The skill `orchestrate` runs in the main conversation and runs the next skill with the `Skill` tool.
- Each script runs with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. A script that has a command line has a PEP 723 block, so `uv` installs its packages.
- The schemas are in the folder `schemas/` of the plugin.
- Each skill has `name: <folder>` and a `description`. Each agent has `name: <file name>` and a model alias (`opus`, `sonnet` or `haiku`).
- The `README.md`, the ADRs and the C4 pages are new, and agree with the plugin.

### Removed

- The agent `orchestrator`. The skill `orchestrate` takes its place.
- The `automated` key of `.aiml/handoff.json`, and each Mode Detection block.
- Each mention of other plugins and of PowerPoint, and the tests that read files outside the plugin.
- The `superpowers:executing-plans` skill is now optional. The plugin works without it.

### Added

- A command line for `data_validator.py`, `metric_calculator.py`, `cost_estimator.py` and `hyperparameter_validator.py`.
- `NOTICE`, with the MIT license of the source plugin.
- Tests for the command lines, the PEP 723 blocks, the prompt rules and the version.
