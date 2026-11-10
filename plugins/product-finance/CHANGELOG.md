# Changelog

## 0.13.4

- Each command and agent names each script that it runs in its Bash grant (`scripts/<file> *`). Before, the grant `scripts/*` also permitted `uv run` of a file outside the scripts folder through a path with `..`, also a file of the project (STORY-283).

## 0.13.3

- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).

## 0.13.2

- The file `caller-grants.json` and a block in the README name the grants that the session which dispatches a runner must give: the 5 scripts (the result check is in `scripts/plugin_result/`), the output folder, the plugin files, and the answers file. `tests/unit/test_caller_grants.py` checks the list (STORY-168).
- Each of the 9 commands has the grant `Edit(/.product-finance/**)` in its `allowed-tools`. 3 of them had no `allowed-tools` line.

## 0.13.1

- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).

## 0.13.0

- **fix:** `discover` checks its result file. After the write, it runs `scripts/plugin_result/plugin_result_check.py result` on the file. On a refusal, it corrects the named keys and writes the file once more. On a second refusal, it stops and names each error.
- **fix:** a person's run leaves out the `detail` key and never writes `"detail": null`. The `discover` section has an example of a person's run, and the person-run example of `feature-roi` has no `detail`.
- **fix:** when `discover` has no value for `sam` or `som`, it writes no `market_size` result and records a gap that names each input it lacks.
- **change:** the checker of the result file and its schemas are in `scripts/plugin_result/`, so the plugin ships them. They are byte copies of the files of business-case.

## 0.12.0

- **feat:** `discover` and `setup` read the jtbd graph of the project. The new script `scripts/jtbd_read.py` finds the jtbd plugin, runs its save code, and writes the jtbd run as a file in `.product-finance/upstream/`. A plugin run writes it in `.product-finance/<run_id>/upstream/`.
- **feat:** a person's run reads the newest jtbd run that holds a segment or a willingness-to-pay result. A plugin run reads the jtbd run with the `run_id` of its `inputs_from` entry and the `case` of its block.
- **feat:** when the project has no jtbd plugin, no jtbd graph, or no fitting run, the script prints a `NO-JTBD:` line with the reason. `discover` then sizes the market from your answers. `setup` asks the market-sizing question again, with only the options `manual` and `skip`.
- **change:** the plugin has `scripts/probe-plugin.sh`, a byte copy of the file in the other plugins of this repository.
- **change:** no file of the plugin names an old output folder of the jtbd plugin. `wtp_source` and `--jtbd-data` name the file in `.product-finance/upstream/`.
- **change:** `setup` can run the scripts of this plugin without a question.

## 0.11.0

This is the first version in this repository. Versions 0.1.0 to 0.10.1 came before the port, from commit `c2a329f` of a private repository.

- **feat:** the plugin works when you install it. It has no outside server, no handoff file, and no read of a path outside its own folder.
- **change:** an agent no longer asks the person a question. A subagent has no tool to ask. The commands hold each question, and an agent takes the answer from its command or from the answers file. When an answer is absent, the agent uses the default that the command states, or leaves out the figure and records a gap.
- **change:** the questions `accept_before_after` and `confirm_high_roi` moved to the commands `ai-economics` and `feature-roi`.
- **change:** the `cost-coverage` command reads its agent and follows it in the same session. It has an `argument-hint`.
- **change:** each script runs as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. Each script has a PEP 723 block.
- **change:** the 14 skills are one folder deep. Their names are `<group>-<folder>`, for example `calculations-magic-number`.
- **change:** a command has no `name`, `agent` or `command` key in its front matter.
- **change:** the three Charter schemas are in `schemas/agentic-pricing/`. The checker of the result file and its schemas are in `tests/support/`.
- **fix:** `result_name.py` refuses a `run_id` and a command part that is not a plain name (1 to 64 of A-Z, a-z, 0-9, `.`, `_`, `-`; not `.` or `..`), and `result_name.py run-id <value>` checks one value. Each agent that names a `run_id` runs this check first. A plugin run with a bad `run_id` runs with no `run_id` and records a gap. The engagement id of the cost-coverage readout is matched with `fullmatch`, so a final new line fails.
- **change:** the tool grants are narrow. An agent has `Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)` and `Bash(git rev-parse --show-toplevel)`, and a command has the first. No agent has a bare `Bash`, `Skill` or `Agent`, and the instrumentation planner has no `Bash`. An agent reads a skill file with `Read`. The time comes from `result_name.py now`, not `date`. The `Glob` tool stays only in the instrumentation planner.
- **remove:** the outside server, the release file, the root skill file, and the handoff option with its file.
- **remove:** the sections about other plugins from the methodology and integration guides, and the steps that make a presentation.
- **docs:** the README, the C4 diagram, and ADR-001, ADR-002, ADR-005, ADR-006 and ADR-007 are written again for this repository. The ADR numbers 003 and 004 are not used.
- **prompt:** the prompt files have 0 findings from the prompt linter, and fewer instructions than before the port.
