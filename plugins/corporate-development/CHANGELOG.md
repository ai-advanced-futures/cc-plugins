# Changelog

## 0.20.2

- Fix: `python -m corporate_development <input_json>` works again. `corporate_development/__main__.py` imported `run_investigation` from `main.py`, but `main.py` defines only `run_pipeline`, so the command stopped with `ImportError`. The module now imports and calls `run_pipeline`. Add `tests/unit/test_main_module.py`.

## 0.20.1

- Fix: the command `pipeline` sets `run_in_background: false` in each `Agent` call. A background agent returned in a new turn, and a `claude -p` run could end while Phase 3 or Phase 4 still ran.
- Fix: the command `pipeline` reads a questions file only at the path that it builds itself, `.corporate-development/targets/<slug>/handoffs/phase_<N>_questions.md`. It reads no path that a phase agent returns. When an agent returns another path, the command stops and shows the 2 paths. Before, a path from web search text could make the command read any file (issue #657).
- Fix: the slug check of `docs/pipeline-inputs.md` also refuses `.` and `..`. `TargetManager` and `ArtifactBuilder` use the same regex (`SLUG_PATTERN`).
- Behavior change: `ArtifactBuilder` makes the folder name with `make_slug`. "Acme, Inc." now gives the folder `acme-inc` (before: `acme,-inc.`). A name with no letter and no digit raises `ValueError` before any folder is made, and `scripts/run_pipeline.py` exits 1. A person who ran the pipeline with such a name moves the old files to the new folder.

## 0.20.0

- The command `pipeline` starts the phase agents in the main conversation. The agent `pipeline-orchestrator` is removed, because a subagent cannot start an agent.
- Add the agent `readiness-assessor` for Phase 0. No agent starts a `general-purpose` agent now. The command gives it `assessment_date`, because the agent has no tool that gives the date.
- Move the handoff schema, the engine key maps and the integration terms to `docs/phase-handoff.md`. The phase agents read this file.
- Give each agent a narrow tool list: no agent has `Agent` or `Bash`. `operational-auditor` and `deal-advisor` keep `Skill`, with a rule in their text that names the skills they may start.
- Add `check_slug` and `make_slug` to `TargetManager`. A slug must match `[a-z0-9][a-z0-9-]{0,63}`. The slug rule in `docs/pipeline-inputs.md` removes each other character, cuts the slug to 64 characters, and stops on an empty slug.
- Add `tests/unit/test_agent_grants.py`.

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
