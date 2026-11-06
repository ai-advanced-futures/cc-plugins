# Changelog

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
