---
name: wtp-check
description: Check a price against what customers will pay, with the 6-layer willingness-to-pay framework. Use when the person wants to test a price after a discover run, or when another plugin runs jtbd-market-discovery:wtp-check.
allowed-tools: Read, Write, Glob, Skill, AskUserQuestion, Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(git rev-parse *)
---

# /jtbd-market-discovery:wtp-check

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/NAME.py ...` (NAME is the script name), one command per Bash call. Also, do not add an `echo` of the exit code, because the Bash tool shows the exit code of a command that fails. Put each `<...>` placeholder of a `uv run` line in single quotes, because the shell reads an unquoted `<` as a redirect. A value that the person gave (the survey path, a column name, `run_id`, `case`) can hold a `'`: write each `'` in it as `'\''`, because inside single quotes the shell runs nothing, and a lone `'` ends the quotes. Run no inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), write no script of your own, and write every file with the Write tool, because a file that a shell command writes is not a file that this run can account for.
This skill starts no agent: you run the check in this conversation, and the scripts give the numbers.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person who picks such an option gives no value.

## Plugin-run block

When the arguments of the skill hold a fenced block with the info string `plugin-run`, or are 1 line that is the path of a file that holds the block (read that file with the Read tool), this run is a plugin run of `jtbd-market-discovery:wtp-check`. The block holds `command`, `automated`, `answers_path`, `case`, `run_id` and `inputs_from`.

- Read the answers file at `answers_path` and use its `jtbd-market-discovery:wtp-check` section. A value it gives replaces the default for that input. Each answer has `settled_by`. A value with `settled_by: person` is a source of type `person`; a value with `settled_by: recommended` is a source of type `default`.
- `automated: true` in the invocation block wins over any config file's automation setting. Ask the person nothing.
- In a plugin run, skip steps 1 and 10 of `## Steps`: take each input from the answers file.
- Read an earlier run's files only through `inputs_from`. The upstream session is `.jtbd-market-discovery/<run_id>/` under the git root, where `<run_id>` is the `run_id` of the `inputs_from` entry whose `plugin` is `jtbd-market-discovery`. Use it as `input_dir` only when all four hold:
  1. the `run_id` in that session's `state.json` equals the entry's `run_id`;
  2. the `run.run_id` of the file at the entry's `result_file` equals the entry's `run_id`;
  3. the `case` in that session's `state.json` equals the block's `case`;
  4. the `run.case` of that result file equals the block's `case`.
- When any of the four fails, read no file of that session. Write no willingness-to-pay or customer-value result, and record two gaps: `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "upstream jtbd run_id or case does not match inputs_from"}` and `{"kind": "customer_value", "label": "Customer value", "why": "upstream jtbd run_id or case does not match inputs_from"}`.
- When `inputs_from` has no `jtbd-market-discovery` entry, there is no `input_dir`: work from the answers alone. Write no `customer_value` result; record the gap `{"kind": "customer_value", "label": "Customer value", "why": "inputs_from names no jtbd-market-discovery run"}`.
  When the answers give no `target_price`, write no willingness-to-pay result either; record the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "no jtbd-market-discovery run and no price in the answers"}`.
- Read `p7.json` and `p8.json` from `input_dir`. Your own session is `.jtbd-market-discovery/<run_id of the block>/`: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py select --base '<base>' --run-id '<run_id>' --case '<case>'` and use the folder it prints as `session_dir`. Write `p9.json` and `competitive-pricing.json` to that own session. This run writes nothing into the upstream session, because that session belongs to the run that made it.
- Put `case` in `run.case` and `run_id` in `run.run_id` and in the file name.
- End the run with the result file `result.json`, written to its own session folder by `jtbd_state.py place-result` from the draft that `agents/wtp-validator.md` describes in its `## Result file` section.

## Purpose

Test a price against what customers will pay. The check is skeptical by design: it challenges the price before you go to market. It needs a finished discover run, because it reads the economic value (`p7.json`) and the segments (`p8.json`) of that run.

## Inputs

| Input | Required | Description |
|---|---|---|
| `target_price` | Yes, except in a plugin run that gives no price | The price per month to test |
| `target_segment` | No | The customers the price is for, by role and industry |
| `market_context` | No | `b2b` or `b2c` |
| `evc_estimate` | No | The economic value per customer per month |
| `wtp_survey_path` | No | The path of the willingness-to-pay survey file |
| `competitor_pricing` | No | The direct competitors, their prices, and the free alternatives |

## Steps

1. Ask the questions of `${CLAUDE_PLUGIN_ROOT}/questions/wtp-check.json`, one question for each `AskUserQuestion` call [q: none]. A person can skip a question.
   - `AskUserQuestion`: the target price per month [q: target_price]
   - `AskUserQuestion`: the target segment (role, industry) [q: target_segment]
   - `AskUserQuestion`: B2B or B2C [q: market_context]
   - `AskUserQuestion`: the economic value the offering creates per customer per month, if known [q: evc_estimate]
   - `AskUserQuestion`: the path to WTP survey data, if there is any [q: wtp_survey_path]
   - `AskUserQuestion`: the direct competitors, what they charge, and any free alternatives [q: competitor_pricing]
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py now` on its own and keep the output as `started_at`. Read `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and keep its `version` for the result file.
3. Run `git rev-parse --show-toplevel` on its own. Its output is the git root; when it fails, the git root is the working directory. Call it `base`.
4. Find the sessions.
   - A person's run: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py finished --base '<base>'`. `input_dir` is the session it prints. Read `p7.json` and `p8.json` from `input_dir`. When it exits 1, no discover run has finished: halt, write no `p9.json`, and write the result file with `results: []` and the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "no finished jtbd discover session: none holds p7.json and p8.json"}` (step 7 shows how). Otherwise run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py wtp-folder --base '<base>'`. `session_dir` is the folder it prints. A person's run writes into no session that it did not start, because that session belongs to another run. The result file is still written, with no `run_id` part.
   - A plugin run: follow `## Plugin-run block`.
   When a script fails to import a package, stop and report a gap that names the missing package. Never make up its output, because a made-up number reaches the result file as a real one.
5. When the run has a `wtp_survey_path` and an `input_dir`, read line 1 of the survey file with the Read tool (`limit: 1`). When that line names the column `segment_id`, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_9.py --input '<wtp_survey_path>' --p7 '<input_dir>/p7.json' --p8 '<input_dir>/p8.json' --segment-column 'segment_id' --out '<session_dir>/wtp-results.json'`. When it does not, leave out `--p8` and `--segment-column`. The script writes the outlier layer and the layer validation of the full survey to the file, and with `--segment-column` the numbers of each segment: the row count, the outlier layer, the `wtp_analysis` block of `p9.json`, the layer validation and the Van Westendorp points. Run it 1 time on the full file. Do not split the file, and run no other command on it (no `cat`, `cut`, `sort`, `grep` or loop), because the script gives the count and the numbers of each segment, and Claude Code refuses a pipe or a shell variable. When it exits 1 (for example, the file has no data), write its message as a gap `willingness_to_pay`, and work from the estimates of Phase 8. When `wtp-results.json` exists, use the numbers in it, and estimate none that it gives.
6. Read `${CLAUDE_PLUGIN_ROOT}/skills/wtp-check/procedure.md` and follow Steps 1 to 9 of its body. Skip its Step 0 (steps 2 to 4 here are that step) and its Step 10 (step 7 here is that step). Take each input from the answers; ask for nothing in a plugin run. Then follow the step of `${CLAUDE_PLUGIN_ROOT}/agents/wtp-validator.md` that writes `p9.json`, with the numbers of `wtp-results.json` when it exists.
7. Write the result file. Read `${CLAUDE_PLUGIN_ROOT}/agents/wtp-validator.md` and follow its `## Result file` section: write the draft to `{session_dir}/result-draft.json`, with no `run.finished_at`. Then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py place-result --draft '<session_dir>/result-draft.json' --base '<base>' --session-dir '<session_dir>'`. It sets `run.finished_at`, writes `result.json` in the session folder (`result-2.json` when the folder holds `result.json`) and prints its path. Every run writes the result file, a person's run too. When no session exists (the halt above), write the draft to `<base>/.jtbd-market-discovery/result-draft.json` and run `place-result` on it with no `--session-dir`: the halt file goes to `.jtbd-market-discovery/` and the draft goes away. Exit 3 means that a run with the same `run_id` wrote the name already: say so, and stop.
8. Write the pages of the run: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<base>' write-run --session-dir '<session_dir>' --result-file '<result file>'`. In a halt with no session, leave out `--session-dir`. When it exits 1 or 2, keep the line `GRAPH: FAILED <exit code> <first error line>`.
9. Show the validation report of Step 8 of the procedure and the path of the result file. When a `GRAPH: FAILED` line exists, show it, and do not say that the graph holds the results, because the pages are missing.
10. Ask one question: "Learn these results?" On yes, load the `jtbd-market-discovery:learn` skill with the Run page named in `run_page` of the session folder of the check. On no, the pages stay `draft`.
11. Offer the next steps: `/jtbd-market-discovery:discover` with a B2B segment, and `/product:explore` to update the product requirements with the validated price.
