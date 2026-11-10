# Changelog

## 1.11.7

- The skill `vendor-archetype-classify` starts its agent in the foreground with `run_in_background: false`, and says so in a line at the top. Before, the agent could start in the background and return in a new turn that did not have the `allowed-tools` of the skill, and the emitter was refused (STORY-312).

## 1.11.6

- Each skill that names a file of its own folder reads it in a headless run: `competitive-intelligence` reads `reference/run-rules.md`, and `vendor-archetype-classify` reads `reference/archetype-reference-card.md` when the person asks what a signal or an archetype means, or asks for the anchor vendors of an archetype. The skill text names the file as `${CLAUDE_SKILL_DIR}/reference/<file>`, and `allowed-tools` has a `Read` rule for that 1 file. Before, a run with `claude -p` in the default mode refused the `Read`, and the skill went on with no file (STORY-289).

## 1.11.5

- Each skill names each script that it runs in its Bash grant (`scripts/<file> *`). Before, the grant `scripts/*` also permitted `uv run` of a file outside the scripts folder through a path with `..`, also a file of the project (STORY-283).

## 1.11.4

- The ingest makes a Gap page for each item of `gaps.json` in the 1 list `gaps` and in a list for each level (`critical`, `important`, `nice_to_have`); an item of a level list with no `type` takes the level. A gap links the competitor that it names by `competitor_id`, or by `competitor` (an id or a name); a gap of more than 1 competitor links none and makes no Competitor page. Before, a run with level lists made no Gap page, and a gap with only a `competitor` name linked no competitor (STORY-220).
- `intelligence-gatherer` names the shape of `gaps.json`.

## 1.11.3

- `set` and `new --set` keep a date or a time as the text that you give, at each depth of a list or a map. Before, a value such as `2026-11-06T22:21:48Z` became a date object, and the save refused the page (STORY-275).

## 1.11.2

- Each optional web or MCP grant in `caller-grants.json` and in the README now has a warning: give the grant only in a session whose input you trust, because it lets the run send data of the case out of the session (STORY-277).

## 1.11.1

- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).

## 1.11.0

- The result file of `discover` and `analyze` is `result.json` in the session folder (`result-2.json` if that name is taken). The folder `.competitive-intelligence/results/` is gone. No file of a run stays beside the graph (STORY-113, D-056).
- A halt with no session folder writes its file in `.competitive-intelligence/`, named by `result_name.py`. A clean `ingest --result <file>` removes it and prints `removed <path>`. A failed ingest keeps it.
- `ingest` keeps no file for the readers: `READER_FILES` is empty. `analyze` reads an earlier run through `ci_graph.py view`.

## 1.10.9

- The file `caller-grants.json` and a block in the README name the grants that the session which starts a plugin run must give: the 2 scripts, the output folder, the plugin files, the answers file, and the web tools. `tests/unit/test_caller_grants.py` checks the list (STORY-168).
- Each skill that writes under `.competitive-intelligence/` has the grant `Edit(/.competitive-intelligence/**)` in its `allowed-tools`.
- When a `WebSearch` or `WebFetch` call is refused, the 3 agents with a web tool go on and say so, and `discover` and `analyze` write the gap `Web research` in the result file.

## 1.10.8

- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).

## 1.10.7

- The "Learn these results?" step of `discover`, `analyze`, `monitor`, `respond`, `validate`, `competitive-intelligence` and `vendor-archetype-classify` asks with `AskUserQuestion`, in the same turn, so `learn` runs with the grant of the skill. With no `AskUserQuestion` tool (`claude -p`), the skill asks nothing and writes the line `Next: /competitive-intelligence:learn <session>` (STORY-195).
- `learn`, `ask` and `setup` run `git rev-parse --show-toplevel` on its own and write the path in each command, because Claude Code refuses a command with a command substitution. `learn` and `ask` say to run one command per Bash call, with no pipe, `;` or `&&` (STORY-195).

## 1.10.6

- A page that a person makes with `new` and no run cites passes the check. The rule `CI-run` accepts a page with no `run` link when its `field_runs` names `(person)` for each field, so a fact that a person saves with `learn` no longer stops each later `ingest`. A page that a run wrote with no `run` link is still an ERROR. `new` refuses a page with no `run` link of each type other than Run, Market, Competitor, Offer and Source, because that page belongs to 1 run (STORY-222).

## 1.10.5

- Step 1 of `analyze` and `discover` reads an earlier run only with `ci_graph.py pages Run` and `ci_graph.py view`, and names the files to read. Before, it scanned the session folders with `grep` and `cat`, so a person's analyze did not read `intelligence-data.json`, which `ingest` moves into the graph (STORY-209).
- `analyze` and `discover` say to run each command on its own, with no pipe, `;` or `&&`, because each compound command asks the person in the default mode.

## 1.10.4

- `ingest` removes a file only when a page holds it. A file that gave no page stays where it is, the output names it in a `NO PAGE:` line, and the `ingested` line ends with `, no page N`. The files of metadata, context, notes, monitoring and plan have the Run page, so `ingest` removes them as before, and `pages.json` now names them. Before, a file that gave no page went from the session folder, and no line named it (STORY-217).

## 1.10.3

- The ingest order does not change the graph. A shared page (Market, Competitor, Offer, Source) keeps the value of the newest run for each field, and the new field `field_runs` names that run. A later description replaces the placeholder of a competitor. The description of a source follows its type. A run that finds a known competitor by its name gives its name by the same rule, and links the market of that competitor. A run gets a `field_runs` entry only for a field that it gives: a run that names no market changes no field of the market. A field that a person gives with `new` or sets with `set` (the title and the description too) is kept, and no run replaces it. `ingest` prints a `note:` line for a start time that it cannot read (STORY-185).

## 1.10.2

- The ingest of an analyze run finds the competitor of `swot-<competitor>.json` from `competitor_id`, then `competitor` (as for `analysis-<competitor>.json`), then `competitor_swot.name`, then the name of the file. Before, each analyze run with no `competitor_id` and no `competitor_swot.name` stopped at step 9 with "unknown competitor id None" (STORY-208).
- A SWOT item that is 1 sentence (the SWOT Format Standard of `agents/synthesizer.md`) becomes a SwotItem page, as an item object does. Before, the ingest kept the sentence and made no page, so the SWOT of an analyze run gave no page.
- Step 7 of `analyze` writes `competitor`, and `competitor_id` when the ecosystem mapping has one, in `analysis-<competitor>.json` and `swot-<competitor>.json`.
- The ingest step of `analyze` and of `discover` gives `--result` as a path relative to the git root, because `ingest` refuses an absolute path.

## 1.10.1

- The contract test fails a skill route that can ask. A route under `skills/` cannot ask only when the first `##` heading of its `SKILL.md` is `## Plugin-run block` and that section holds the sentence `Ask the person nothing.`. Before, the test applied no ask check to a skill route. The `## Plugin-run block` of the skills `discover` and `analyze` now holds that sentence (STORY-173).

## 1.10.0

This version makes the plugin a brain: each run writes its results into a graph (STORY-88, part B). Part A gave the graph and its save code in 1.8.0.

- The plugin needs the plugin `knowledge` (`"dependencies": ["knowledge"]`) and Claude Code 2.1.110 or later.
- 3 new skills: `competitive-intelligence:setup` (writes the bundle `docs/competitive-intelligence/`, the registry entry, and the router block in `CLAUDE.md`), `competitive-intelligence:learn` (confirms the pages of a run, or saves a fact that the person gives), and `competitive-intelligence:ask` (answers a question from the graph).
- The skills `competitive-intelligence`, `discover`, `analyze`, `monitor`, `respond`, `validate` and `vendor-archetype-classify` end with an `ingest` step. The step moves the files of the run into pages with `status: draft`. A person's run then asks "Learn these results?". A plugin run asks nothing, and its halt also runs the `ingest` step, with `ingest --result <file>` and no session folder.
- `ci_graph.py verify-run RUN --by human:<login>` confirms a run and each page of it in one process, and `verify` confirms one page. A second confirmation adds a `verified` entry. `resolve` takes a session id. The skills that call `learn` have `Skill` in `allowed-tools`.
- `init`, `upgrade` and the bundle folder of `.claude/knowledge.json` must match `[A-Za-z0-9._/-]{1,100}` (#692). `ingest` refuses a path outside the project (#602).
- A finding with no source that has a `url` (`"url": null`, `"sources": []`, or no `sources` key) becomes a Gap page of type `no_source`, so the run still ingests. A Finding page must link a Source page, and a Source page needs a `url`.
- A skill that reads a file of an earlier run reads it with `ci_graph.py view`, because `ingest` moves the files of a run into the graph.
- A PostToolUse hook (`hooks/brain-hook.sh`) runs `regen` and both checks after a write to the bundle and after a call of `ci_graph.py`.
- `scripts/claude_md_router.py` and `templates/claude-md-block.md` write the router block.

## 1.9.1

- `result_name.py run-id` refuses the names that the plugin uses at the top of `.competitive-intelligence/` (`results`, `monitoring-history`, a `.json` file, and the name of a person's session, with case ignored), and exits 3 when the session folder of the `run_id` exists. A plugin run with such a `run_id` that the check refuses (exit 2) goes on with no `run_id`. A plugin run whose session folder exists (exit 3) halts with a gap and writes nothing in that folder (#549, STORY-144).

## 1.9.0

This version gives each agent a short list of tools, and it moves a plugin run from 2 runner agents into the skills (STORY-118, issue 470).

- The intelligence gatherer had no `tools:` list, so it had each tool of the session, with each MCP tool. Now it has `Read, Write, Grep, Glob, WebSearch, WebFetch`. It has no MCP tool.
- The MCP research server is now called by the skill `discover` or `competitive-intelligence`, which has the tools of the session. The skill writes the results to `research-notes.json` in the session folder and gives the gatherer the dispatch field `research_notes`. With no server, the gatherer uses `WebSearch` and `WebFetch`, as before.
- The classifier agent has `Read, Write, WebFetch`. It had `Bash(uv run *)`, which does not limit the program. It writes `vendor-archetype-input.json` and ends with the line `INPUT: <path>`. The skill `vendor-archetype-classify` now runs the emitter (its `allowed-tools` line is `Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)`), reads the handoff file, and shows the state.
- The agents `discover-runner` and `analyze-runner` are removed. A coach now calls the skill `competitive-intelligence:discover` or `competitive-intelligence:analyze` with the `Skill` tool. The arguments are the `plugin-run` block, or 1 line that is the path of a file that holds the block. The section `## Plugin-run block` of each skill holds the rules of a plugin run: no question, no checkpoint, each answer from the answers file, the `run_id` check, the session folder and `session.json`, and the halt. The skill starts the phase agents itself, so no agent of this plugin has `Agent` or `Bash`.
- A plugin run now happens in the conversation of the coach, so it has each tool of that session, as a person's run does (ADR-004, D-212).
- A new test fails on each agent with no `tools:` list, on each `Bash` entry (`Bash(uv run *)` too), and on each `Agent` entry.
- The README, ADR-001, and the C4 diagrams name the skills as the route of a plugin run.

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
