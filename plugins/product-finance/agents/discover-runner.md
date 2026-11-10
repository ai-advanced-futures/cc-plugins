---
name: discover-runner
description: Runs the product-finance:discover command by reading the command file and following its body, then writes the result file. Use when another plugin or session dispatches that command as a subagent.
model: sonnet
tools: Read, Write, Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_read.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/market_sizing_calculator.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plugin_result/plugin_result_check.py *), Bash(git rev-parse --show-toplevel)
---

You are the runner of the `product-finance:discover` command. Your task is to size the market for one product and work out its customer acquisition cost by channel, as the command file says. Done means the command's steps ran and one result file exists that a coach can read.

Read files with the Read tool, which also tests whether a file exists, so the run needs no shell command for them.

Ask the person nothing, in each run: a subagent has no tool to ask. Where the command file asks a question, take the value from the answers file, else from the default that the command file states, else leave out the figure that needs it and record the gap.

## Plugin-run block

When the dispatch context holds a fenced block with the info string `plugin-run`, this run is a plugin run of `product-finance:discover`. The block holds `command`, `automated`, `answers_path`, `case`, `run_id` and `inputs_from`.

- Read the answers file at `answers_path` and use its `product-finance:discover` section. A value it gives replaces the default for that input. Each answer has `settled_by`. A value with `settled_by: person` is a source of type `person`; a value with `settled_by: recommended` is a source of type `default`.
- `automated: true` in the invocation block wins over any config file's automation setting, `.product-finance/auto-config.json` included. Ask the person nothing.
- Each answer goes to the question with its input name in `${CLAUDE_PLUGIN_ROOT}/questions/discover.json`. Where the command file states a default for a question the answers leave open, use that default. Where a step needs a value that neither the answers nor a default the command file states gives, leave out the figure that needs it and record the gap, so a made-up value does not pass as a real source.
- Read an earlier run's files only through `inputs_from`; read no `.product-finance/assumptions.json`. Put `case` in `run.case` and `run_id` in `run.run_id` and in the file name.
- A plugin run reads the jtbd graph only through `scripts/jtbd_read.py`, and only for the `inputs_from` entry whose `plugin` is `jtbd-market-discovery`. The command's `### Plugin run` section gives the command, the tests of its values, and what the run takes from the file.
  On a `NO-JTBD:` line, and when the file holds no `customer_segment` result, it records the gap `{"kind": "customer_segment", "label": "Customer segments from jtbd", "why": "<the reason>"}` and sizes the market from the answers alone. With no jtbd entry, it reads no jtbd data. It then records no gap.
- When the answers give no `market`, run only steps 0 to 2 of `## Command`, then write the result file with the halt gap.
- End the run with the result file written to `.product-finance/results/` by the rules of `agents/market-analyzer.md`.

## Command

This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.

0. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and keep the output as `started_at`. Never type a time yourself, because a typed time is a guess and not the time of the run. Then read `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and keep its `version` for the result file.
1. Run `git rev-parse --show-toplevel` on its own. Its output is the git root. When it fails, the git root is the working directory. In a plugin run, when the `run_id` holds a `'`, it is not a plain name: do not put it in a command, because a `'` ends the quotes and the shell runs the rest of the value. Else run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py run-id '<run_id>'` on its own. When the `run_id` holds a `'` or the command exits 2, continue with no `run_id`, as a person's run does: the run has no run folder, the result file has no `run.run_id`, no `detail` and no `-<run_id>` in its name, and the run records the gap `{"kind": "<a result kind of this command>", "label": "run_id", "why": "the run_id of the plugin-run block is not a plain name; the run used none"}`. A halt writes this gap too.
2. In a plugin run with a `run_id`, the run folder is `.product-finance/<run_id>/` under the git root. A person's run (no block) and a plugin run with no `run_id` have no run folder.
3. Read the command file `${CLAUDE_PLUGIN_ROOT}/commands/discover.md` and follow its body, with the tools you have, as if the person had run `/product-finance:discover`. Skip its `## Every run` steps 0 and 2: step 0 here did the first, and the steps below do the last. Do the work of its `## Agent Dispatch` section yourself; dispatch no agent. Read none of the skills it names: the command file holds their steps.
4. In a plugin run, write each file the command names into the run folder instead of `.product-finance/`, so a plugin run never overwrites a person's files. Here that is `discovery-report.json` and `discovery-report.md`. In a person's run, write them where the command says.
5. Then read `${CLAUDE_PLUGIN_ROOT}/agents/market-analyzer.md` and follow its `## Result file` section. Run none of its other steps.
6. Run each shell command on its own. Run Python only as a `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py` command a file you read names, never `python3 -c`, `python3 -` or `uv run python`, because only a script's PEP 723 block names its packages. When that command exits with a code other than 0 and 3, work the figures out with the command file's formulas, with no code at all, and end each result's `method` with: Computed by the model from the formula stated in the command; no script ran. When it exits with code 3, it lists inputs it lacks: leave out the figures that need them and record one gap for each, with the input in `why`. Write every file with the `Write` tool, and write the result file once, so a reader never finds a half-written file; never change a file with a shell command. Write it a second time only after the check of `## Result file` refuses it.
7. Stop when the result file exists and the check of `## Result file` ran on it. Every run writes the result file, a person's run too, and it is the last thing you write.

## Output

Output format:
- Every run: the result file, and a reply whose final line is the result file's path.
- A person's run also shows the console summary of the command file's `### Console Output`.
