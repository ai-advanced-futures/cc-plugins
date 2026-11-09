# Changelog

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
