# Changelog

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
