---
description: Run the full 10-phase JTBD market opportunity discovery. Use when the person wants to find, score and price the market opportunities of a product or market area, or when another plugin dispatches jtbd-market-discovery:discover.
argument-hint: "[--defaults] [market area]"
allowed-tools: Agent, Read, Write, Glob, Skill, AskUserQuestion, Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(git rev-parse *)
---

# /jtbd-market-discovery:discover

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

## Purpose

Run the orchestrator, which coordinates the 10 phases with a fresh sub-agent for each phase. A sub-agent cannot ask the person anything, so you ask in this conversation. The orchestrator stops at each checkpoint and writes a questions file; you ask the items and dispatch it again.

## Steps

1. Take the market area from the arguments. With `--defaults`, ask nothing: dispatch the orchestrator with `market_area` and no `answers` and no `checkpoints`, and go to step 6. If the arguments hold no market area, ask for it.
2. Ask the questions of `${CLAUDE_PLUGIN_ROOT}/questions/discover.json`. Ask not more than 4 questions in one `AskUserQuestion` call [q: none]. Offer the default of each question as the recommended option. A person can skip a question.
   - `AskUserQuestion`: the product or market area to analyze [q: market_area]
   - `AskUserQuestion`: where the importance and satisfaction ratings come from: a survey file, estimates, or ratings typed in by hand [q: ratings_source]
   - `AskUserQuestion`: the path of the survey file, only when the answer is a survey [q: survey_data_path]
   - `AskUserQuestion`: the hourly labor rate of the customer [q: labor_rate]
   - `AskUserQuestion`: the average cost of one error [q: average_error_cost]
   - `AskUserQuestion`: the average revenue of one sale [q: average_revenue]
   - `AskUserQuestion`: the revenue margin [q: revenue_margin]
   - `AskUserQuestion`: the risk tolerance of the customer [q: risk_tolerance]
   - `AskUserQuestion`: the number of segments to find [q: segment_count]
3. Run `git rev-parse --show-toplevel` on its own. Its output is the git root; when it fails, the git root is the working directory. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py select --base <git root>`. Its output is the `session_dir`. When the script fails to import a package, stop and report a gap that names the missing package; never make up its output, because a made-up number reaches the result file as a real one.
4. Dispatch `jtbd-market-discovery:orchestrator` with the `Agent` tool, in the foreground. Give it `session_dir`, `market_area`, `answers` and `checkpoints: true`. Each answer has the form `{"value": ..., "settled_by": "person"}`; an answer that is the recommended option has `"settled_by": "recommended"`. Leave out an input that has no answer.
5. While the reply of the orchestrator ends with `QUESTIONS: <path>`:
   1. Read the file at `<path>`. Show its `summary`.
   2. Ask each item of `questions` with the `AskUserQuestion` tool. For the item `manual_ratings`, ask for the importance and satisfaction ratings of the needs it lists [q: manual_ratings]. Any other item names its own input.
   3. Write the answers to `{session_dir}/answers.json`, as `{"answers": {<input>: {"value": ..., "settled_by": ...}}}`.
   4. Dispatch the orchestrator again with `session_dir`, `market_area`, the `answers` of step 2 and `checkpoints: true`. A dispatch keeps no input of an earlier dispatch, so give them each time.
6. When the orchestrator ends with a `DONE: jtbd-market-discovery` line, show the top 3 opportunities, the willingness-to-pay verdict, the paths of the output files below, and the path of the result file in `.jtbd-market-discovery/results/`. When the reply holds a line `GRAPH: FAILED <exit code> <first error line>`, show it, and do not say that the graph holds the results. When the reply has no `DONE:` line and no `QUESTIONS:` line, show the reply, say that the run stopped before the end, and give the path of `{session_dir}/execution-log.md`.
7. With `--defaults`, ask nothing and go to step 8. Otherwise, Ask one question: "Learn these results?" On yes, load the `jtbd-market-discovery:learn` skill with the Run page named in `run_page` of `{session_dir}/state.json`. On no, the pages stay `draft`.
8. Offer the next steps: `/product:explore` to turn the top opportunity into product requirements, `/gtm` to build a go-to-market strategy around the validated opportunity, `/pricing:price` to compute the right price from the value data, and `/jtbd-market-discovery:wtp-check` to test a price.

## Resuming a session

Run the skill again. The orchestrator finds the session with an unfinished `state.json` and continues from the next open phase. All earlier phase files stay in `.jtbd-market-discovery/{session}/`.

## The 10 phases

| Phase | Agent | Mode |
|-------|-------|------|
| 1 — Job Identification | `job-identifier` | Sequential |
| 2 — Job Decomposition | `job-decomposer` | Sequential |
| 3 — Need Generation | `need-generator` ×4 | Parallel |
| 4 — Effort Quantification | `effort-quantifier` | Sequential |
| 5 — Survey Design | orchestrator inline | N/A |
| 6 — Opportunity Scoring | `opportunity-scorer` | Sequential |
| 7 — EVC Calculation | `evc-calculator` | Sequential |
| 8 — Segmentation | `segmentation-analyst` | Sequential, after Phase 7 |
| 9 — WTP Validation | `wtp-validator` | Sequential |
| 10 — Output Assembly | `output-assembler` | Sequential |

## Deliverables

- `.jtbd-market-discovery/customer-needs.json`
- `.jtbd-market-discovery/opportunity-scores.json`
- `.jtbd-market-discovery/evc-analysis.json`
- `.jtbd-market-discovery/wtp-validation.json`

The result file in `.jtbd-market-discovery/results/` and the pages of the run in `docs/jtbd/` (the `jtbd` graph) are also output. The job, the steps, the segments and the integrated output are pages of the graph. The files of a session stay in `.jtbd-market-discovery/{session}/`.

Each file carries `subject`, `session_id`, `case` and `run_id` at the top level, so a reader can tell which run wrote it.
