# Changelog

## 1.9.1

The commands that read the graph stop on a page or a folder that they cannot read (STORY-214, FEATURE-26).

- `results`, `pages`, `resolve`, `verify-run`, `set`, `body`, `link`, `unlink` and `remove` exit 1 with 1 line on stderr that names the file, when a page of the graph does not parse, has no type or cannot be read, or when a folder of the graph cannot be listed. Before, they skipped such a page or folder and gave a wrong answer with exit 0, and a page file with no read access gave a traceback.
- `check` names a folder that it cannot list as `J-schema`, and it gives no traceback for a file that it cannot read.

## 1.9.0

No agent runs code that the model writes, and each agent has a narrow `tools:` line (STORY-121, FEATURE-26).

- No agent has the `Bash` tool. The skills `discover` and `wtp-check` run the scripts with `uv run` between the agent starts, and the agents read the result files.
- The agents `orchestrator` and `wtp-check-runner` are removed. The `discover` skill runs the 10 phases, and the `wtp-check` skill runs the price check and writes its result file.
- The grants are `Read, Write` for seven agents, and `Read, Write, Glob` for `output-assembler` and `wtp-validator`.
- The skill starts the 4 `need-generator` agents one at a time, in the foreground, because an agent that runs in the background returns in a new turn that has no tool grant from the skill. A run of Phase 3 is slower than before.
- New scripts: `run_phase_6.py` to `run_phase_9.py`, `jtbd_state.py merge-needs` and `jtbd_state.py place-result`. `composite_scorer.py` has `--out`.
- `evc-calculator` has two steps, `inputs` and `report`. It writes `evc-input.json`, the skill runs `run_phase_7.py`, and the agent reads `evc-results.json`. When the agent changes an input, it ends with `RERUN: evc-input.json` and the skill runs the script one more time.
- The agents no longer write the Excel and PNG secondary files. The skill writes the CSV reports with `report_exporter.py`.
- The skill writes the pages of the graph (`jtbd_graph.py write-run`) after `place-result` has written the result file.
- A value that the person gave (the survey path, a column name, `run_id`, `case`) goes into a command in single quotes, and each `'` in it is written as `'\''` (issue #742).
- Tests: `tests/unit/test_agent_grants.py` fails when an agent has `Bash`, `Agent`, `Skill`, an `mcp__` tool or `general-purpose`, and when a `uv run` line of a skill has an unquoted `<...>` placeholder.
- `composite_scorer.py` counts a segment with `"size_percent": null` as 0, and no longer stops with a `TypeError`.
- The skill `discover` says that a request to not ask the questions of step 2 again does not change `checkpoints`, and that a reply the person types in the chat is written to `answers.json` before the next phase.
- The live tier loads the `knowledge` plugin that `plugin.json` depends on (`--plugin-dir` and `--add-dir`). The Phase 8 live test agrees with the skill: with no survey file, no `run_phase_8.py` runs and the dispatch of `segmentation-analyst` holds the segment count of the person.

## 1.8.0

A run writes its output as the `jtbd` graph. This version has the hook, the three skills and the write flow of the agents.

- The agents `output-assembler` and `wtp-validator` call `jtbd_graph.py write-run` at the end of a run. When it fails, the agent writes the line `GRAPH: FAILED <exit code> <first error line>`.
- New skills: `setup` adds the router block to `CLAUDE.md`, `ask` answers a question from the graph, and `learn` confirms a run or saves other results.
- `jtbd_graph.py verify-run` sets `status: stable` and a `verified` entry on a run and its pages.
- The skills `discover`, `wtp-check` and `quick-validate` end with the question "Learn these results?".
- A hook runs `regen` and both checks after a write. `hooks/brain-hook.sh` is a copy of the file in `system-design`.
- Four files are not written at the root of `.jtbd-market-discovery/` any more: `job-statement.json`, `job-steps.json`, `customer-segments.json` and `final-output.json`. Four stay, because other plugins read them.
- `remove` stops when a page that stays links to a page that goes. It matches the run with `==` and not with `in`.
- The input session of a `wtp-check` run must be a folder beside the session folder. The registry path must stay in the project.
- The folder name of the graph may hold only letters, digits, and the characters `.`, `_`, `/` and `-` (at most 100). The skills `setup` and `learn` test each text before they put it in a command.
- ADR-004 records the decision.

## 1.7.0

The plugin has a brain of the knowledge standard: one graph in `docs/jtbd/`. This version has the schema, the save code and the brain check. The skills `setup`, `learn` and `ask`, the hook, and the write flow of the agents come in the next version.

- `schema/jtbd.yaml` has 7 page types: `Run`, `Job`, `JobStep`, `Outcome`, `Segment`, `WtpValidation` and `Result`. `scripts/gen-schema.sh` makes the JSON files from it.
- `scripts/jtbd_graph.py` is the save code. The operations of the standard are `init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check` and `log`.
- `write-run` writes all pages of one run from the session folder and the result file. It runs `init` when the project has no graph. A `wtp-check` run links to the `discover` run that it read. A halt before a session writes one `Run` page.
- `results` prints the `Result` pages of one run in the shape of a result file. `pages` prints the pages of one type.
- The brain check has the rules `J-schema`, `J-run`, `J-tree`, `J-score`, `J-rank`, `J-finished`, `J-result` and `J-once`.
- `plugin.json` names the plugin `knowledge` as a dependency. `scripts/probe-plugin.sh` is a copy of the file in `system-design`.

## 1.6.0

First version in this repository. Versions 1.0.0 to 1.5.1 came before it, from commit c2a329f of a private repository.

- Three skills replace the three commands: `discover`, `wtp-check` and `quick-validate`. The skills ask the questions. An agent of the plugin cannot ask the person anything, because Claude Code removes `AskUserQuestion` from each subagent.
- The orchestrator stops at each checkpoint when the dispatch has `checkpoints: true`. It writes `questions.json` and ends with a `QUESTIONS:` line. The `discover` skill asks the items, writes `answers.json`, and dispatches the orchestrator again. A dispatch with no `checkpoints` field never stops.
- Scripts run with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. Each script has a PEP 723 block with its packages. `uv` must be on the path of the person.
- Agents are dispatched as `jtbd-market-discovery:<agent>` with the `Agent` tool. Each agent has a `tools:` line that names only the tools it needs.
- The plugin result standard, its checker and its conformance test are now inside the plugin folder. The result file registry `result-file.json` lists seven defaults.
- The blocks for the team tool of the source repository, and the hand-off file for other plugins, are removed.
- The end of a run offers `/product:explore`, `/gtm` and `/pricing:price`, and `/jtbd-market-discovery:wtp-check`.
- The author, the homepage and the repository in `plugin.json` name this repository. The plugin has a `NOTICE` file with the MIT notice of the source plugin.
