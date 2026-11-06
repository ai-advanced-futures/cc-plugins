# Changelog

## 1.8.0

This version adds the competitive-intelligence brain: the save code and the schema. It is the first of two parts. The hook, the skills, and the `ingest` steps come in the next version.

- New script `scripts/ci_graph.py`. It is the only code that writes the graph `docs/competitive-intelligence/`. Its commands are `init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, `log`, `ingest`, `view`, `results`, and `pages`.
- New schema in `schema/`. It has 19 page types: Run, Market, Competitor, Offer, Source, Finding, Gap, LensResult, Moat, SwotItem, Recommendation, Change, Threat, Response, Validation, Archetype, Summary, BattleCard, and Result. `scripts/gen-schema.sh` makes the generated files again.
- New check `ci_graph.py check`. Its rules are CI-schema, CI-id, CI-required, CI-run, CI-duplicate, CI-lens, CI-result, and CI-evidence. It also has CI-link (a link goes to a page that exists, of the right type) and CI-stale (a generated file is not up to date). These 2 rules are not in the design. They report a broken link and an old generated file in the brain check.
- The schema imports the base schema of the knowledge plugin by a sibling path, and `scripts/gen-schema.sh` gives that path to `scripts/gen_slots.py`. They run only in the marketplace checkout, with `plugins/knowledge` beside this plugin. No installed code reads that path.
- `ci_graph.py ingest <path> [--result FILE]` writes the pages of a run from its session folder and its result file. It uses a lock, works on a copy of the graph, and changes the graph only when the check passes. It removes each ingested file, except the files that a reader still reads (`READER_FILES`). It writes `pages.json` in the session folder. When the project has no graph, it makes one first and prints `INIT: docs/competitive-intelligence/`.
- `ci_graph.py view RUN FILE` builds a session file again from the pages. The result is the same as the file that `ingest` read.
- `ci_graph.py results` prints the `plugin-result/1` file of a run from the Result pages. `ci_graph.py pages TYPE` prints the pages of one type as JSON.
- A page of the types Market, Competitor, Offer, and Source is shared between runs. It keeps the item of each run under the name of the run, so `view` of an older run shows the data of that run. The fields of the page itself hold the data of the latest run. A file that gives a competitor with no website finds the one competitor of the graph with that name; when 2 or more have the name, `ingest` stops. A run with no market name uses the one market of the graph. An Offer page is for one competitor. The order of 2 ingests does not change the graph: a file with a website finds the page that an earlier file with the same name and no website made, and a run that names its market gives its name to the "Unnamed market" page that an earlier run with no subject made. `ingest` stops, and writes nothing, when no file of the path is one that a handler reads.
- The CI job `competitive-intelligence` installs the requirements of the knowledge plugin and runs the new tests.
- The version in `plugin.json`, in `scripts/__init__.py` and in the result-file examples is 1.8.0.

## 1.7.2

This version fixes the 10 findings and the 3 notes of the review of the port.

- The rule for a free-text question is the rule of `discover`: a skill asks each text question with `AskUserQuestion`, 1 question for each call. The skills `competitive-intelligence`, `analyze` and `discover` and the file `run-rules.md` said "in one chat message". This holds for the question "what to change" after a checkpoint too.
- `run-rules.md` asks "Retry or Cancel?" when a phase fails twice, as the skill does.
- The depth value is `quick_scan` in the context analyst, as in `questions/discover.json`. The agent said `quick`.
- The skill `vendor-archetype-classify` no longer tells the skill to expect `QUESTIONS:` from the classifier. The classifier reports a gap, and the skill shows the gap and stops.
- The skill `competitive-intelligence` asks "Retry or Cancel?" when a phase fails twice. Skip stays for a lens only.
- The lens executor says when a lens is done: when it writes the line `DONE: lens-<name>`. The old `Await:` lines named a sender that does not exist.
- `run-rules.md` says that the deliverable generator still writes `session-metadata.json`.
- The skill `discover` no longer lists `metadata.json`, which only the deliverable generator writes.
- The README and the context analyst name the optional output files of the `jtbd-market-discovery` plugin in the same way. The line for the `product-finance` plugin is gone.
- `docs/DESIGN.md` gives the real command names. The line for the `update` command is gone, because the plugin has no `update` skill.
- 3 tests can fail now: the agent dispatch names, the Skip rule for a lens, and the default deliverable. New tests pin the other rules.

## 1.7.1

- `result_name.py` refuses a `run_id` or a command part that is not a plain name. A plugin run with such a `run_id` runs with no `run_id` and records a gap.

## 1.7.0

This version ports the plugin to this marketplace.

- The plugin works when you install it. Each question to the person now comes from a skill, because a subagent cannot ask a question.
- New skill `competitive-intelligence`. It runs the full six-phase analysis in the main conversation, and it asks the person at each checkpoint.
- The five commands are gone. Each skill takes the text of the command with the same name.
- The six lens skills moved to `skills/lenses-<name>/SKILL.md`. A lens skill is not a command, and the person cannot start it.
- The lens executor reads each lens skill and follows it, because the `Agent` tool starts an agent and not a skill.
- Each skill and each agent name is now the name of its folder or file. The names have no `competitive-intelligence:` prefix and no `comp-intel` name.
- Each agent has only the tools it needs. No agent has `AskUserQuestion` or `Task`.
- The intelligence gatherer uses its own `WebSearch` and `WebFetch` tools. It can use an MCP research server that the person added. It does not need one.
- Script calls use `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. The scripts `result_name.py` and `vendor_archetype_emitter.py` list their packages in a PEP 723 block.
- The vendor-archetype schema is now in `schemas/`, and the result-file checker is in `tests/plugin_result/`. No file of the plugin reads a path outside the plugin folder.
- The plugin no longer has a link to a dispatcher plugin, a deck output, or the handoff file `plugin-handoff.json`. The vendor archetype handoff file `vendor-archetype-handoff.json` stays. The result file of `discover` and `analyze` stays.
- Tests run in CI with no skips.
- The version in `plugin.json`, in `scripts/__init__.py` and in the result-file examples is 1.7.0.

Versions 1.0.0 to 1.6.1 came before the port. They come from commit `c2a329f` of a private repository.
