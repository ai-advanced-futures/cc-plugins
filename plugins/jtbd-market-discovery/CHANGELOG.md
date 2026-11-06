# Changelog

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
