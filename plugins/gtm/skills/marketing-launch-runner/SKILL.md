---
name: marketing-launch-runner
description: Runs the gtm:marketing:launch command by reading the command file and following its body, then writes the result file. Use it only when a coach plugin gives a `plugin-run` block; a person runs `/gtm:marketing:launch`.
allowed-tools: Read, Write, Glob, Grep, WebSearch, Bash(date *), Bash(git rev-parse *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py *), mcp__ahrefs__get_keyword_ideas, mcp__ahrefs__get_search_volume
disallowed-tools: mcp__slack__slack_post_message, mcp__notion__notion-create-page, mcp__canva__generate_design, mcp__canva__autofill_template
---

This skill is the runner of the `gtm:marketing:launch` command. Your task is to build the launch plan the command file describes: its channels, their year-one targets and the growth motion. Done means the command's steps ran and one result file exists that a coach can read.

Read each file with the Read tool. This skill approves only the calls of its `allowed-tools`; each other call asks the person, and nobody answers in a coach run, so the call fails.

## Plugin-run block

A run is a plugin run of `gtm:marketing:launch` when the arguments of this skill hold a fenced block with the info string `plugin-run`, or when the arguments are 1 line that is the path of a file that holds that block (read the block from that file with the Read tool). The block holds `command`, `automated`, `answers_path`, `case`, `run_id` and `inputs_from`.

- Read the answers file at `answers_path` and use its `gtm:marketing:launch` section. A value it gives replaces the default for that input. Each answer has `settled_by`. A value with `settled_by: person` is a source of type `person`; a value with `settled_by: recommended` is a source of type `default`.
- `automated: true` in the invocation block wins over any config file's automation setting, `gtm-context.json` included. Ask the person nothing. This holds also when this session has the `AskUserQuestion` tool [q: none]. A coach calls this skill, so it accepts `automated` with any value and asks nothing.
- Each answer goes to the question with its input name in `${CLAUDE_PLUGIN_ROOT}/questions/marketing-launch.json`. Where the command file states a default for a question that the answers leave open, use that default. Where a step needs a value that neither the answers nor a default the command file states gives, do not make one up: leave out what needs it and record the gap.
- A made-up value looks like a real answer, because the coach cannot tell them apart.
- Read an earlier run's files only through `inputs_from`. In a plugin run, read and write no `gtm-context.json`, no file in `gtm-output/` and no file the command names at the project root: take each value the command reads from them from the answers instead. Put `case` in `run.case`, and put `run_id` in `run.run_id` and in the file name when it passed the check of step 2.
- When the answers give no `product_description`, run only steps 0 to 3 of `## Command`, then follow the `## Result file` section of `agents/marketing-agent.md` with the halt gap, and write the file once.
- End the run with the result file written to `.gtm/results/` by the rules of the `## Result file` section of `agents/marketing-agent.md`.
- A coach calls this skill with the `Skill` tool in its own conversation, so the end of this skill is not the end of the turn of the coach. When the result file exists, write 1 line with its path, and then do the next step of the command that called this skill, in the same reply. Do not end the turn after the result file, because the coach then records no run and starts no later route.

## Command

This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.

0. Run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep the output as `started_at`. When a `date` call is denied or fails, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and use its output as that time.
1. Read `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and keep its `version` for the result file.
2. Run `git rev-parse --show-toplevel` on its own. Its output is the git root. When it fails, the git root is the working directory. In a plugin run, when the `run_id` holds a `'`, it is not a plain name: do not put it in a command, because a `'` ends the quotes and the shell runs the rest of the value. Else run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py run-id '<run_id>'` on its own. When the `run_id` holds a `'` or the command exits 2, continue with no `run_id`, as a person's run does. The run folder is the one of a person's run, the result file has no `run.run_id` and no `-<run_id>` in its name, and it records the gap `{"kind": "channel", "label": "run_id", "why": "the run_id of the plugin-run block is not a plain name; the run used none"}`. The answers file and the `automated` rule stay. A halt writes this gap too.
3. Choose the run folder, under the git root. In a plugin run with a `run_id` that passed step 2 it is `.gtm/<run_id>/`. In a person's run (no block) it is `.gtm/<started_at as YYYYMMDDTHHMMSSZ>/`. In a person's run, `run_id` is absent, whatever the run folder is called.
4. Read the command file `${CLAUDE_PLUGIN_ROOT}/commands/marketing/launch.md` and follow its body from step 1 in this conversation, with the tools you have, as if the person had run `/gtm:marketing:launch`: steps 0 and 1 here did its step 0. Its `## Inputs` section names the questions.
5. This runner publishes nothing: skip the command's Canva, Notion and Slack steps. Dispatch no agent: where the command passes work to `integrity-agent`, check each claim you put in a result against `${CLAUDE_PLUGIN_ROOT}/definitions/truth-tiers.md` yourself, and leave out a Tier 5 claim.
6. In a plugin run, write each file the command names into the run folder instead, except `gtm-context.json`, which a plugin run never writes, so a plugin run never overwrites a person's files. In a person's run, write them where the command says, and a copy of each to the run folder.
7. The command's last step sends you to the `## Result file` section of `${CLAUDE_PLUGIN_ROOT}/agents/marketing-agent.md`: read that file and follow that section only; run none of its other steps.
8. Run each shell command on its own. Write every file with the `Write` tool, and write the result file once; never change a file with a shell command.
9. The `allowed-tools` of this skill cover only `git rev-parse`, `date` and `result_name.py`, so a shell write is outside them and asks. This skill removes the 4 publishing tools (Slack, Notion and Canva) for the run.
10. The work of this skill is done when the result file exists. Every run writes the result file, a person's run too, and it is the last file that this skill writes. In a person's run, stop there. In a plugin run, go on with the next step of the caller, as `## Plugin-run block` says.

## Output

Output format:
- Every run: the result file.
- A person's run: a reply whose final line is the result file's path.
- A plugin run: 1 line with the result file's path, and then the next step of the caller in the same reply.
