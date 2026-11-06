# Changelog

## 0.19.1

- The command `pipeline` reads only the open questions files in a questions round: the file of `questions_path`, and the file of the other parallel phase when Phase 3 and Phase 4 both asked. An old questions file of another phase does not come back.
- Phase 4 reads the income statement keys of the engine (`cogs`, `interest_expense`, `tax_expense`). It also reads the other names of a key from `StatementParser.INCOME_STATEMENT_SYNONYMS`, so `cost_of_goods_sold` gives `cogs`. `docs/pipeline-inputs.md` and the `execution-pipeline` skill name the engine keys and ask for no net income.
- The README gives the 2 input shapes: the `phase_N` objects of `pipeline_inputs.json`, and the flat object of a script.

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
