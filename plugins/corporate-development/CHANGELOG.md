# Changelog

## 0.19.0

First version in this marketplace. It is a port of the plugin from commit `c2a329f` of a private repository. The versions 0.1.0 to 0.18.0 came before the port.

- Add the agent `pipeline-orchestrator` in file-based mode. The command `pipeline` asks the intake questions. A phase agent that needs an answer writes `handoffs/phase_<N>_questions.md`, and the command asks and dispatches again.
- Add `docs/pipeline-inputs.md` with the input fields of each phase and the rule for the slug.
- Move the 12 skills to `skills/<group>-<name>/SKILL.md`.
- Give the 7 agents a name, a description, the tools, and a model.
- Give the 8 commands a description and an argument hint.
- Add `uv` script headers to `scripts/run_pipeline.py` and `scripts/run_investigation.py`.
- Remove the parts for a mission runner of the source repository, the plugin adapter, the slide generation text, and the plugin names that this marketplace does not have, except the optional plugins `tech-contracts`, `tech-budget`, `team-assessment`, `product-finance` and `value-ip`, which the plugin keeps as optional plugins.
- Move the tests of `tests/integration` to `tests/unit/flows`. The tests run in a temporary folder.
