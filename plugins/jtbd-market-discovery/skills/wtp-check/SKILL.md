---
name: wtp-check
description: Check a price against what customers will pay, with the 6-layer willingness-to-pay framework. Use when the person wants to test a price after a discover run, or when another plugin dispatches jtbd-market-discovery:wtp-check.
allowed-tools: Agent, Read, Write, Glob, Skill, AskUserQuestion, Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(git rev-parse *)
---

# /jtbd-market-discovery:wtp-check

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

## Purpose

Test a price against what customers will pay. The check is skeptical by design: it challenges the price before you go to market. It needs a finished discover run, because it reads the economic value (`p7.json`) and the segments (`p8.json`) of that run.

## Steps

1. Ask the questions of `${CLAUDE_PLUGIN_ROOT}/questions/wtp-check.json`, one question for each `AskUserQuestion` call [q: none]. A person can skip a question.
   - `AskUserQuestion`: the target price per month [q: target_price]
   - `AskUserQuestion`: the target segment (role, industry) [q: target_segment]
   - `AskUserQuestion`: B2B or B2C [q: market_context]
   - `AskUserQuestion`: the economic value the offering creates per customer per month, if known [q: evc_estimate]
   - `AskUserQuestion`: the path to WTP survey data, if there is any [q: wtp_survey_path]
   - `AskUserQuestion`: the direct competitors, what they charge, and any free alternatives [q: competitor_pricing]
2. Dispatch `jtbd-market-discovery:wtp-check-runner` with the `Agent` tool, in the foreground. Give it the answers as dispatch fields: `target_price`, `target_segment`, `market_context`, `evc_estimate`, `wtp_survey_path` and `competitor_pricing`. Leave out a field that has no answer. The runner follows `${CLAUDE_PLUGIN_ROOT}/skills/wtp-check/procedure.md`.
3. Show the validation report and the path of the result file that the runner returns. When the reply holds a line `GRAPH: FAILED <exit code> <first error line>`, show it, and do not say that the graph holds the results, because the pages are missing.
4. Ask one question: "Learn these results?" On yes, load the `jtbd-market-discovery:learn` skill with the Run page named in `run_page` of `the session folder of the check`. On no, the pages stay `draft`.
5. Offer the next steps: `/jtbd-market-discovery:discover` with a B2B segment, and `/product:explore` to update the product requirements with the validated price.
