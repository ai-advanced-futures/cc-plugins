# Changelog

## 0.11.1

- **fix:** A skill route of a build now keeps its grant in a later turn. The runner guard (ADR-016) has a 5th mode, `pre-skill`: in a marked session, in the conversation of the coach, it allows the `Skill` call of 1 of the 7 skill routes of `build.md` only for a planned run. The `args` must be the `plugin-run` block that `team-answers` printed, and `team/runs.json` of a case of the session must hold an open run of that route with the SHA-256 of that block. Before, a route that started after the notice of a background dispatch was refused, because a grant of `allowed-tools` ends with the turn. `bc.py team-answers` now records `block_sha256` in each run, and the mark of a session lists the case folder of each `bc.py session` call. `business-case:learn` gets no allow: Claude Code asks the person once in a later turn, and its `allowed-tools` hold `Skill(knowledge:checking)` in place of a bare `Skill`. A `--case` with a control character no longer adds a line to the mark, and the mark is read at the new line only. A session call adds a case line only for exactly 1 `--case` word, the mark is written in 1 step, and the guard refuses a `runs.json` that is a link (STORY-251, D-1049, D-1065; closes #1596, #1597 and the security issue #1621).

## 0.11.0

- **feat:** Each team card now says why the case asks it, in plain words. Each card of an analyst's plan has a new required field `because`: one sentence that says what the answer changes in the case. `team-answers` puts it in front of the question, so the person reads it as the first sentence of the card. `team-reply --check` refuses a card with no `because`, a card with a blank `because`, and a card that names an item id of the plugin map (its header, `because`, question, labels or descriptions). It also takes an empty `sets` on a `blocks: later` card as no `sets`. A plan that passed the check before this version keeps its question. The baseline analyst offers "None: this is the only offering" on the card about the best other use of the money, and the competition analyst says in its `because` that the case needs the customer's way today.
- **feat:** The 4 cards that code makes have new texts: "Run again?", "Which case?" (it names the plugin and the date of the result), "Missing" (it names the item by its title) and "Conflict" (it names the cards and the answer on each). The option labels do not change.
- **feat:** `team-answers` prints a `say` line, with the sentence about a note on an option, until code records the first answer or skip of a case. The coach tells the person that sentence in its exact words.
- **feat:** The coach's answers file (`--answers-file`) has a new key, `asked`: the key of each card that the coach asked in the call. The question tool of Claude Code leaves out a card that the person skipped, so code records `[No preference]` for each card in `asked` with no answer, and a skipped card is no longer printed as `open` again. `team-answers` refuses answers with no `asked`, an answer to a card that is not in `asked`, an `asked` that is not a list of keys, and an unknown key in `asked`, and writes nothing. A call with no answer needs no `asked` (STORY-340).

## 0.10.0

- **feat:** A typed answer on a team card no longer leaves the card open for the same question again. An option label that the person types at the start of the text, followed by a comma or another mark, records that option, `settled_by: person`, and the whole text goes to the next brief as the note. For other typed text, the coach gives its reading, and code makes a card headed "Your words": only its option "yes, record it" records the reading. Each card that `team-answers` asks again comes with a line that says why (`again <key>: <reason>`), and a card the person skipped waits for the after-cap rule. ADR-013 "The round cap" is amended (STORY-339).

## 0.9.8

- **fix:** The runner guard (ADR-016) allows `result_name.py version` in the pricing route. The `price-runner` agent of pricing 1.13.8 runs this call at its step 0 to get the plugin version, and before, the guard gave no decision for it. In a business-case build the call could be refused, and the runner then stopped with `BLOCKED: result_name.py version` and wrote no price (STORY-321).

## 0.9.7

- A new test, `tests/unit/test_plugin_map_routes.py`, checks that each route of the plugin map names a real agent or skill of the target plugin in this repository (`agents/<name>.md` with that name, or `skills/<name>/SKILL.md`), and that the plugin is at the floor of the map or later. Before, no test read the target plugin, so a route to a deleted agent failed only in a live build. The plugin `value-ip` is not in this repository, so the test skips its routes by name (STORY-200).

## 0.9.6

- `set` and `new --set` keep a date or a time as the text that you give, at each depth of a list or a map. Before, a value such as `2026-11-06T22:21:48Z` became a date object, and the save refused the page (STORY-275).

## 0.9.5

- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).

## 0.9.4

- `setup`, `learn` and `ask` grant only the commands of their steps: the graph script and the router script by their paths, `git rev-parse`, and the `gh` commands of `learn`. `setup` had the whole shell, and `learn` and `ask` had each program that `uv run` can start. `ask` runs no `knowledge.py` command and has no `Agent` grant, because `knowledge:ask` runs them under its own grant (STORY-263, #1044).
- The router command of `setup` runs with `uv run --no-project`, as in the other brains.

## 0.9.3

- `brain_read.snapshot` refuses a snapshot name that is not 1 file name. The run ends as a gap with "is not 1 file name", because `command` and `run_id` go into the name unchanged and a `/` or `..` in them named a file outside `team/upstream/` (STORY-264).
- `learn`, Step 6, shows the full issue body in a fenced block after the first yes. It then asks a second question that says the repository `ai-advanced-futures/cc-plugins` is public. It opens the issue only after a yes to the second question (STORY-264).

## 0.9.1

- The 5 runner plugins each name the grants that their caller must give, in a file `caller-grants.json` (STORY-168). The README says that this file is the source of each runner list. `test_runner_grants.py` compares the scripts of each file with `RUNNER_CALLS`, and the `Edit` grant of each file with `allowed-tools` of `build.md`. The same test holds that the hook, `hooks.json` and `build.md` name no web tool and no MCP tool, so a web call stays the approval of the person. ADR-016 says this.

## 0.9.0

The case graph, part B (STORY-89): a run writes the pages, 3 skills use them, and the evidence team reads the graphs of 2 other plugins.

- A run of `/business-case:build` writes the pages of its case. After each of its 3 `handoff` calls, the coach runs `bc_graph.py publish --case` for the case. When `publish` fails, the coach shows `GRAPH: FAILED <exit code> <first error line>` and ends as usual, because the case folder is complete. At the end of an interactive run, the coach asks "Learn these results?" and, on yes, loads `business-case:learn`. An automated run and a stop on the budget ask nothing, and their pages stay `draft`.
- 3 new skills. `/business-case:setup` makes the graph, writes the router block in `CLAUDE.md`, and writes the pages of each case folder of the repository. `/business-case:learn` confirms the pages of a case, or adds a note of the person to the page of a case. `/business-case:ask` answers a question from the pages and writes nothing.
- Each open item, each item verdict and each finding of a case is a page of its own: the new types `OpenItem`, `ItemVerdict` and `Finding` (14 page types). The `Case` page holds `open_item_count`, and the `Review` page holds `verdict_count` and `finding_count`, in place of the lists. `publish` removes the page of an item that the case closed, and keeps a protected page. `publish` also brings the manifest of a bundle of an earlier version to the 14 folders.
- `verify-case` has the option `--run RUN`: it confirms the `Case` page, that `Run` page, and each `draft` page of that run only. `publish` keeps the note of a person on a `Case` page.
- The brain hook, `hooks/brain-hook.sh`, runs `regen` and the 2 checks after a write to the bundle or a command that runs `bc_graph.py`. It blocks no write, and it runs with no `uv` on the PATH. It is a copy of the hook of the other brains.
- Reader change: `team-run --done` and `team-run --status` read a run of `jtbd-market-discovery` or `competitive-intelligence` from the graph of that plugin, through its save script (`lib/brain_read.py`). They do not look for a result file of these 2 plugins. When the graph gives no run, `--done` records a gap that names the graph and the error, and `--status` leaves the run open.
- The case keeps a snapshot of each such run in `team/upstream/`. The run entry of `team/runs.json` has the snapshot path as `result_file`, and the new fields `graph_run` and `graph_results`. A snapshot is written 1 time, because an evidence page and a decision pin its bytes. The cite check lists the snapshots of the case.
- An `Evidence` page links to the `Result` page of the jtbd graph or of the competitive-intelligence graph (`source_results`), for each run that the case ended through the graph.
- The plugin map has a `graph` key for the 2 plugins. Their `min_version` is `1.9.2` (`jtbd-market-discovery`) and `1.10.8` (`competitive-intelligence`), the versions that write the graph from a run of the coach.
- The command has 2 grants for `bc_graph.py` and the grant `Skill(business-case:learn)`. The examples of the 8 analysts name a snapshot path, and their cite rule names the `team/upstream/` folder.
- `scripts/claude_md_router.py` is a copy of the file of the other brains. `templates/claude-md-block.md` is the router block.
- A new coach session does not move a page. `publish` keeps the `run` link of a page whose value is the same, so a confirmed page stays `stable` and keeps its Run page. A page whose value changed links to the newest session.
- New decision record: ADR-015, the case graph.
- Tests: `test_hook.py`, `test_brain_read.py`, `test_skills.py` and `test_no_old_output.py`; `test_graph.py` ends a run of each of the 2 plugins through its real graph.
- Fixes of the review of PR 1034: the runner guard approves `bc_graph.py publish` (and the option `--root` before it), so a judge in the background no longer leaves a build with no page; `remove`, `set` and each other first word get no decision. It also approves a read of a file in `templates/`, `rubric/` or `agents/` of this plugin. The check `BC-fresh` does not warn about the page of a closed item that is protected, because `publish` keeps that page. `test_runner_guard.py` tests each of these, and it holds the 2 refusals of `words_of` (a newline after a word, and `$` in double quotes); `scripts/ci-changes.py` has the `READS` edge `gtm` for `business-case`. See ADR-016.
- Fixes of the review of PR 1047 (STORY-188): `test_runner_guard.py` reads the files of the routes with the plugin name written out, so the drift test of `scripts/ci-changes.py` sees each read; `scripts/ci-changes.py` has the `READS` edges `pricing` and `product-finance` for `business-case`, next to the 2 that it had; the hook counts in the README, the container diagram and ADR-006 are right; `build.md` no longer says that `team-run --done` asks the person in a new turn; ADR-016 has a line for a plugin from a directory-source marketplace.

## 0.8.0

- A hook, `hooks-handlers/runner_guard.py`, approves the exact script calls of a build session: a call of `bc.py` and a call of a listed script of the 5 runner plugins, in a session that ran `bc.py session`. The `Bash` grants for the runner scripts are removed, because a `*` in a `Bash` pattern matched any text (issue #703) and a grant ends with the turn (STORY-188). See ADR-016.
- Each case has its own temporary folder: `bc.py temp-dir` now takes `--case` and prints `<tmp>/bc-<slug>-<8 hex>/`. Each `bc.py` call deletes each file of that folder that it names, whatever the exit code. The command text has no `rm -f` (STORY-189).
- The folder grant of each runner plugin is `Edit(/.<plugin>/**)`, so a runner can write its run folder and its session folder (STORY-190).
- `bc.py temp-dir` without `--case` is refused.

## 0.7.1

- The command starts the 3 routes of `gtm` (`gtm:marketing-launch-runner`, `gtm:marketing-brand-runner` and `gtm:marketing-funnel-runner`) with the `Skill` tool, and has one `Skill(<route>)` grant for each one (STORY-146). Version 1.11.0 of `gtm` makes these 3 runner agents skills with the same names, so a dispatch with the `Agent` tool gets "agent type not found" and writes no result file. The command now has 7 routes that are skills.
- After a route that is a skill, the command goes on in the same turn: it runs `team-run --done` and then starts the next run or asks the next card. A skill runs in the conversation of the coach, and the text of a skill can say to stop at its result file. Before, the turn ended after the first gtm route in 3 of 3 runs, the runs stayed `open`, and a new turn did not have the grants of the command.
- The floor of `gtm` in the plugin map is `1.11.0`. The route names do not change. A lower `gtm` has the state `too_old`, so the coach plans no gtm command, and `bc.py evidence --from-result` refuses a gtm result file from below `1.11.0`. Run the route again for such a file.
- Update `gtm` and `business-case` together. With `gtm` 1.11.0 and a `business-case` below 0.7.1, each gtm route fails with "agent type not found".

## 0.7.0

The case graph, part A (STORY-89): the schema, the save code and the check. No command, skill or agent calls the save code yet.

- `.claude-plugin/plugin.json` has `"dependencies": ["knowledge"]`.
- New schema `schema/business-case.yaml` with 11 page types (`Case`, `Run`, `Part`, `Evidence`, `Decision`, `StrategyEntry`, `Condition`, `Note`, `Figure`, `Finance`, `Review`), and the generated `schema/business-case.schema.json` and `schema/business-case.slots.json`. `scripts/gen-schema.sh` and `scripts/gen_slots.py` write them.
- New save code `scripts/bc_graph.py` and `scripts/bclib/` with the operations `init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `verify`, `verify-case`, `regen`, `check`, `log` and `publish`. `publish --case DIR` writes one case folder into the pages of the graph `business-case` in `docs/business-case/`, and leaves the case folder unchanged. A case folder that git ignores gives a `PRIVATE:` line and no page. A case file that exists and is not valid UTF-8 or not valid JSON (or a JSON Lines file with a line that is not valid JSON) stops `publish` with exit 1, names the file (and the line), and changes no page. A file that does not exist gives no page and no error.
- The brain check has the rules `BC-schema`, `BC-id`, `BC-link`, `BC-required`, `BC-case`, `BC-run`, `BC-alias`, `BC-part`, `BC-source`, `BC-fresh`, `BC-upstream` and `BC-stale`.
- `scripts/probe-plugin.sh` is a copy of the file of the other brains.
- Tests: `test_schema.py`, `test_ops.py`, `test_check.py`, `test_publish.py`, `test_graph.py` and `test_release.py`.

## 0.6.1

- The plugin map routes `jtbd-market-discovery:discover` and `jtbd-market-discovery:wtp-check` to the skills of the same name, and the floor is `1.9.0` (STORY-121, D-393). Version 1.9.0 of `jtbd-market-discovery` removes the agents `orchestrator` and `wtp-check-runner`. The command starts these 2 routes with the `Skill` tool, as it does for the 2 routes of `competitive-intelligence`.
- The command has one `Skill(<route>)` grant for each of the 4 routes that are skills (`competitive-intelligence:discover`, `competitive-intelligence:analyze`, `jtbd-market-discovery:discover`, `jtbd-market-discovery:wtp-check`). Without the grant, Claude Code refused the `Skill` call of a route (verifier, PR 730). A test fails when a route has no grant, or when the line has a `Skill` grant for another skill.

## 0.6.0

The port to this marketplace.

- The coach calls `bc.py` with `uv run`. `bc.py` and `schemas/plugin_result_check.py` have a PEP 723 block (Python 3.9 or later, no package).
- The plugin has no text for a tool of the source repository. An automated run takes its values from the arguments: `/business-case:build <proposal> --automated --offering <name> --market <market> [--strategy <path>]`. Code still refuses each decision in an automated run.
- The command has no `name:` key and no `agent:` key. The plugin has no root `SKILL.md` and no `release.json`.
- The plugin map names the versions and the runners of the ported plugins. The two routes of `competitive-intelligence` are skills. `value-ip` is an optional plugin from outside this marketplace.
- The install check finds the plugins of the `cc-plugins` marketplace.
- The manifest has no email and no version number in its description.
- The tests read no file outside the plugin, and none is skipped.
- The prompt files have no finding of the prompt linter. They hold 618 instructions, 72 fewer than before the revision.
- The command gives the runners it starts the grants they need: the scripts of their plugin, the folder of their result files and the answers file of the case (STORY-168). The README lists the grants, and a test checks the list. The result-file grant is an `Edit` rule, because Claude Code checks a file write against the `Edit` rules. The README and ADR-006 state two limits: a `Bash` pattern matches any text, and no grant covers the run folder of a runner.
- The two `session` blocks of the command tell the model to keep the session ID as written. A made-up ID made the review report refuse the judge reply.

Versions 0.1.0 to 0.5.0 came before the port. They are in commit `c2a329f` of a private repository.
