---
description: Run the full 10-phase JTBD market opportunity discovery. Use when the person wants to find, score and price the market opportunities of a product or market area, or when another plugin runs jtbd-market-discovery:discover.
argument-hint: "[--defaults] [market area]"
allowed-tools: Agent, Read, Write, Glob, Skill, AskUserQuestion, Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(git rev-parse *)
---

# /jtbd-market-discovery:discover

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/NAME.py ...` (NAME is the script name), one command per Bash call. Also, do not add an `echo` of the exit code, because the Bash tool shows the exit code of a command that fails. Put each `<...>` placeholder of a `uv run` line in single quotes, because the shell reads an unquoted `<` as a redirect. A value that the person gave (the survey path, a column name, `run_id`, `case`) can hold a `'`: write each `'` in it as `'\''`, because inside single quotes the shell runs nothing, and a lone `'` ends the quotes. Run no inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), write no script of your own, and write every file with the Write tool, because a file that a shell command writes is not a file that this run can account for.
Run every agent in the foreground and wait for it to finish. Start none with `run_in_background: true`, because the result file must exist before the run ends.
No agent of this plugin has `Bash`. You run each script between two dispatches. An agent reads the file that the script wrote, and writes the next input file with the Write tool.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person who picks such an option gives no value.

## Plugin-run block

When the arguments of the skill hold a fenced block with the info string `plugin-run`, or are 1 line that is the path of a file that holds the block (read that file with the Read tool), this run is a plugin run of `jtbd-market-discovery:discover`. The block holds `command`, `automated`, `answers_path`, `case`, `run_id` and `inputs_from`.

- `automated: true` in the invocation block wins over any config file's automation setting. Ask the person nothing.
- In a plugin run, skip steps 1, 2 and 6 of `## Steps`, and give no `checkpoints` to any agent. The run goes to the end, and a checkpoint stops nothing.
- Read the answers file at `answers_path` and use its `jtbd-market-discovery:discover` section. A value it gives replaces the default for that input. Each answer has `settled_by`. A value with `settled_by: person` is a source of type `person`; a value with `settled_by: recommended` is a source of type `default`.
  An input that neither the answers file nor the run supplies keeps its default, and the result file marks it as a default.
- Take `market_area` from the answers file. It has no default (see PREFLIGHT).
- Give each phase agent the answers for its own inputs in its dispatch context, each as `{"value": ..., "settled_by": ...}`: `labor_rate`, `average_error_cost`, `average_revenue`, `revenue_margin` and `risk_tolerance` to evc-calculator, `segment_count` to segmentation-analyst. Use `ratings_source` and `survey_data_path` yourself in Phase 5.
  Pass nothing for an input the answers file does not give, because the phase agent applies its own default and a value chosen here would hide that. Pass the `plugin-run` block itself to no phase agent, because each phase agent gets its inputs as dispatch fields.
- Pass `run_id` and `case` to `jtbd_state.py select` (see ORIENT). The result file puts `case` in `run.case`, and `run_id` in `run.run_id` and in the file name.
- This command builds on no earlier run, so `inputs_from` is `[]`. Read an earlier run's files only through `inputs_from`.
- End the run with the result file `result.json`, written to the session folder by `jtbd_state.py place-result` from the draft that `agents/output-assembler.md` writes. A run that stops before Phase 10 ends that way too: start output-assembler with `partial: true`.

## Purpose

Run the 10 phases with a fresh sub-agent for each phase, so the context of each agent stays small. A sub-agent cannot ask the person anything, so you ask in this conversation. You hold the state of the run in `{session_dir}/state.json` and the phase files, never in your own memory, because a compaction of the context erases the memory. If Claude Code compacts the context, read `state.json` again and resume from the last complete phase.

## Steps

1. Take the market area from the arguments. With `--defaults`, ask nothing: use `market_area`, no `answers` and no `checkpoints`, and go to step 3. If the arguments hold no market area, ask for it.
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
   Each answer has the form `{"value": ..., "settled_by": "person"}`; an answer that is the recommended option has `"settled_by": "recommended"`. Leave out an input that has no answer. A person's run has `checkpoints: true`. A request to not ask the questions of this step again (for example, "do not ask them again") does not change `checkpoints`: each checkpoint of `## Phases` still stops the run.
3. Run `## Phases` (below) with `market_area`, `answers` and `checkpoints`. A phase agent keeps no input of an earlier dispatch, so give them each time.
4. At a checkpoint, and when the reply of a phase agent ends with `QUESTIONS: <path>`, `## Phases` tells you to ask the person. Ask each item with the `AskUserQuestion` tool. For the item `manual_ratings`, ask for the importance and satisfaction ratings of the needs it lists [q: manual_ratings]. Ask any other item as its own input [q: none]. Write the answers to `{session_dir}/answers.json`, as `{"answers": {<input>: {"value": ..., "settled_by": ...}}}`. When the person does not answer (for example, the tool is refused in a run with no screen), end your reply with the line `QUESTIONS: {session_dir}/questions.json` and stop; the next run of the skill resumes at that phase.
5. When Phase 10 is done, show the top 3 opportunities, the willingness-to-pay verdict, the `Run` page of the run in `docs/jtbd/`, and the path of the result file. When a `GRAPH: FAILED <exit code> <first error line>` line exists (see Phase 10), show it, and do not say that the graph holds the results. When the run stopped before the end, show why, and give the path of `{session_dir}/execution-log.md`.
6. With `--defaults`, ask nothing and go to step 7. Otherwise, ask one question: "Learn these results?" On yes, load the `jtbd-market-discovery:learn` skill with the Run page named in `run_page` of `{session_dir}/state.json`. On no, the pages stay `draft`.
7. Offer the next steps: `/product:explore` to turn the top opportunity into product requirements, `/gtm` to build a go-to-market strategy around the validated opportunity, `/pricing:price` to compute the right price from the value data, and `/jtbd-market-discovery:wtp-check` to test a price.

## Phases

Each phase starts its agent with the `Agent` tool, in the foreground, with `subagent_type` `jtbd-market-discovery:<agent>`. Give it `session_dir`, `checkpoints` (the value of this run) and the fields the phase names. After the dispatch, wait for the phase file. When the file does not exist, go to ERROR HANDLING.
To mark a phase complete, read `{session_dir}/state.json`, set `phases.<phase>.status` to `complete` and `completed_at` to the time from `jtbd_state.py now`, set `current_phase`, and write the file with the Write tool. Keep every other key.

### Dispatch fields

| Field | Required | Description |
|---|---|---|
| `market_area` | Yes, except on a resume | The product or market to analyze |
| `survey_data_path` | No | Absolute path of a survey CSV; with no value, Phase 5 uses expert estimates |
| `run_id` | No | The id of a coach run. The session is the folder `.jtbd-market-discovery/{run_id}/`, and no other session is resumed |
| `case` | No | The case name; stored in `state.json` and in the result file |
| `session_dir` | No | The session folder that step 3 of the skill chose. With no value, run ORIENT |
| `answers` | No | The answers of the person: `{<input>: {"value": ..., "settled_by": "person" or "recommended"}}` |
| `checkpoints` | No | `true` for a person's run. Stop at each checkpoint (see CHECKPOINTS). With no value, the run goes to the end |

### 0. PREFLIGHT (a run with no `session_dir`)

1. Take `market_area` from the arguments, or in a plugin run from the answers file.
2. If it is absent or empty, halt. Never put any other value in its place, because a made-up area gives a made-up analysis.
3. Run `git rev-parse --show-toplevel` on its own (if it fails, use the working directory). Call the result `base`. Write "insufficient_data: market_area required for automated dispatch" to `<base>/.jtbd-market-discovery/execution-log.md`. Create no session.
4. Write the halt draft (see Halt draft) and stop.

### 1. ORIENT

1. With a `session_dir`, use it. Else run `git rev-parse --show-toplevel` as written, with no `-C` and no path, on its own (if it fails, use the working directory), call the result `base`, and run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py select --base '<base>'`. Add `--run-id '<run_id>'` and `--case '<case>'` only when the run has them. The command prints the absolute session folder. Call it `session_dir`.
2. If the command exits non-zero, write its message to `<base>/.jtbd-market-discovery/execution-log.md`, write the halt draft with that message as the reason, and stop. Never pick another session.
3. When a script fails to import a package, stop and report a gap that names the missing package: write the halt draft with the package as the reason, and stop. Never make up its output, because a made-up number reaches the result file as a real one.
4. Read `{session_dir}/state.json` to find `current_phase`. If `{session_dir}/answers.json` exists, read it: it is the answers file of the session (not a `plugin-answers/1` file), and it holds the answers to the last `questions.json`. Take every other input (`market_area`, `labor_rate`, `average_error_cost`, `average_revenue`, `revenue_margin`, `risk_tolerance`, `segment_count`) from the run, or in a plugin run from the answers file at `answers_path`.

### 2. The phases

Find the first phase that is not complete, and run its branch.

**Phase 0 — start fresh.** Create `{session_dir}/execution-log.md` with the header "# Execution Log\nSession: {session_id}\nStarted: {timestamp}\n". Run Phase 1.

**Phase 1 — job identification.**
- Start `job-identifier` with `session_dir` and `market_area`. Wait for `{session_dir}/p1.json`.
- CHECKPOINT: show the job statement. Offer: confirm or refine.
- On confirm: mark Phase 1 complete.

**Phase 2 — job decomposition.**
- Read `p1.json` and take the job statement. Start `job-decomposer` with `session_dir` and the job statement. Wait for `p2.json`.
- CHECKPOINT: show the summary of the 12–15 job steps. Offer: confirm or refine.
- On confirm: mark Phase 2 complete.

**Phase 3 — need generation (4 agents, one at a time).**
- Read `p2.json` and take the job steps (12–15). Group them into 4 batches (steps 1–3, 4–6, 7–9, 10 and later).
- Start 4 `need-generator` agents with 4 `Agent` calls, one at a time, each in the foreground (wait for the reply before the next), each with the same `session_dir`, the job statement from `p1.json`, its step batch and its batch number `N`. Each writes `{session_dir}/p3-batch-{N}.json`. Never start them in one message, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next script is then refused.
- Wait for all 4 batch files. Then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py merge-needs --session-dir '<session_dir>'`. It combines the batches, gives the ids `N001`, `N002`, and so on, and writes `p3.json`. When it exits 1, go to ERROR HANDLING.
- CHECKPOINT: report the number of needs (target: 80–100). Offer: confirm or adjust.
- On confirm: mark Phase 3 complete.

**Phase 4 — effort quantification.**
- Start `effort-quantifier` with `session_dir`. It reads `p1.json`, `p2.json` and the top 10 needs of `p3.json`. Wait for `p4.json`.
- CHECKPOINT: show the baseline cost calculation. Offer: confirm or refine.
- On confirm: mark Phase 4 complete.

**Phase 5 — survey design (you do this phase; no agent runs).**
- Take `ratings_source` from `answers`, or from `{session_dir}/answers.json`. With `checkpoints: true` and no value, CHECKPOINT: write an item for `ratings_source` (options: survey, expert estimates, manual ratings) and stop.
  - **Survey** — go to Phase 5, survey flow.
  - **Expert estimates** — skip the survey. Read `p1.json` (job context) and `p3.json` (the full need list). For each need, estimate importance (1–10: how critical is it to complete the job?) and satisfaction (1–10: how well is the outcome served today?). Base the estimates on the job context, the action and variable of the need, and its job step. Write `p5.json` with `{ "source": "orchestrator_expert_estimates", "method": "expert", "needs": [{ "need_id": "...", "need": "...", "importance_estimate": N, "satisfaction_estimate": N }, ...] }`. Mark Phase 5 complete. Go to Phase 6.
  - **Manual ratings** — only when `checkpoints: true`. Write an item for `manual_ratings` that lists the top 40 needs (by `need_id` order in `p3.json`), and stop. On the answer, write `p5.json` with `{ "source": "manual_entry", "method": "manual", "needs": [...] }`. Mark Phase 5 complete. Go to Phase 6.
  - With no `ratings_source` and no `checkpoints` (a caller run), use `expert_estimates` unless the run gives `survey_data_path`. In a plugin run, an answered `ratings_source` or `survey_data_path` replaces that default.
  - Record how the choice was settled in `p5.json` as `"assumption_sources": {"ratings_source": "<how>"}`, one plain string: `person` or `recommended` (from the answers file, by its `settled_by`), `asked` (the person chose in this run) or `default`.
- **Phase 5, survey flow:**
  - If `survey_data_path` is `none` (the person has no survey file yet): write `p5.json` with a survey template of the top 40 needs of `p3.json` and the status `needs_fielding`, and tell the person: "Field your survey, then run the discover skill again to resume from Phase 6." Save the state and stop. Do not mark Phase 5 complete.
  - Else take `survey_data_path` from the run or the answers. With `checkpoints: true` and no value, write an item for `survey_data_path` and stop. With no value and no `checkpoints`, use expert estimates as above.
  - Write `p5.json` with the survey data location. Mark Phase 5 complete. Go to Phase 6.
  - On a resume with survey data: update `p5.json` with the data location, mark Phase 5 complete, and go to Phase 6.

**Phase 6 — opportunity scoring.**
- With a survey file (`ratings_source` is survey, and `survey_data_path` names a file), run these steps in order. Copy the survey file into the session folder first when it is outside the project. Every file goes into `{session_dir}`, never into `data/` of the working folder, because a later run reads only the session folder.
  1. `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py propose --input '<survey>' --output '<session_dir>/survey-proposal.json'`. Read the file. Keep `detected_format`, `format_description`, `mapping.importance.formula`, `mapping.satisfaction.formula`, `invariant_check.result` and `warnings` for the summary.
  2. The item `column_map`. With `checkpoints: true` and no `column_map` answer in `{session_dir}/answers.json`, write an item for `column_map` to `{session_dir}/questions.json` with the mapping summary and the options `approve` and `correct` (a correction names the columns). Ask it, and write the answer. With no `checkpoints`, approve the proposed mapping. When the answer corrects the mapping, note the override columns. When the format is `UNRESOLVABLE`: with `checkpoints: true`, ask for the column names; else write the error to `{session_dir}/execution-log.md` and stop the phase.
  3. `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py apply --input '<survey>' --output '<session_dir>/survey-odi.csv' --raw-output '<session_dir>/survey-raw.csv'`. Add `--importance-col '<column>'` and `--satisfaction-col '<column>'` when the answer overrides them. Check that both files exist.
  4. `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_6.py --input '<session_dir>/survey-odi.csv' --out '<session_dir>/p6-scores.json'`. It scores each need and writes `scored` and `top_opportunities`.
  5. Start `opportunity-scorer` with `session_dir`, `checkpoints` and `scores_path` (`{session_dir}/p6-scores.json`). It writes `p6.json`. Wait for it.
  6. `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/report_exporter.py --output-dir '<session_dir>/reports' --session-id '<session_id>' opportunity --input '<session_dir>/p6.json'`. Put the options before the subcommand, because the other order exits 2.
  When `run_phase_6.py` exits 1, write its message to `execution-log.md`, and start `opportunity-scorer` with no `scores_path`; the agent records the gap.
- With no survey file, start `opportunity-scorer` with `session_dir`, `checkpoints` and the needs. No script runs, and the agent works from `p5.json`.
- CHECKPOINT: show the top 10 opportunities by ODI score. Offer: confirm or refine.
- On confirm: mark Phase 6 complete.

**Phase 7 — EVC calculation (2 dispatches and 1 script).**
1. Start `evc-calculator` with `session_dir`, `checkpoints`, the EVC answers and `step: inputs`. It writes `{session_dir}/evc-input.json` and returns 1 line.
2. `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_7.py --input '<session_dir>/evc-input.json' --out '<session_dir>/evc-results.json'`. When it exits 1, write its message to `execution-log.md` and go to ERROR HANDLING.
3. Start `evc-calculator` with `session_dir`, `checkpoints` and `step: report`. It reads `evc-results.json` and writes `p7.json`.
4. When the reply of step 3 ends with `RERUN: evc-input.json`, the agent changed an input and wrote a new `evc-input.json`. Run step 2 and step 3 one more time. Do not run them a third time, because a loop that is not bounded does not end.
- Mark Phase 7 complete.

**Phase 8 — segmentation (after Phase 7).**
- Run this phase in sequence, after Phase 7 completes. It reads `p7.json` for the EVC overlay on segment economics, and an early run gives wrong segment data.
- With a survey file: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_8.py --input '<survey>' --segment-count '<segment_count>' --id-col 'respondent_id' --out '<session_dir>/p8-clusters.json'`. Use `4` for `<segment_count>` when nobody gave a value. When it exits 1, write its message to `execution-log.md`, and start the agent with no `clusters_path`.
- Start `segmentation-analyst` with `session_dir`, `segment_count` and, when the script ran, `clusters_path` (`{session_dir}/p8-clusters.json`). It writes `p8.json`.
- CHECKPOINT: show the EVC summary and the top segment profiles. Offer: confirm or refine.
- On confirm: mark Phase 8 complete.

**Phase 9 — WTP validation.**
- Only when the run has `wtp_survey_path` (an answer of a plugin run): read line 1 of the survey file with the Read tool (`limit: 1`), then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_9.py --input '<wtp survey>' --p7 '<session_dir>/p7.json' --out '<session_dir>/wtp-results.json'`. When that line names the column `segment_id`, add `--p8 '<session_dir>/p8.json' --segment-column 'segment_id'`. When it exits 1 (for example, the file has no data), write its message to `execution-log.md`, and start the agent with no `wtp_results_path`; the agent works from estimates and records the gap.
- Start `wtp-validator` with `session_dir` and, when the script ran, `wtp_results_path` (`{session_dir}/wtp-results.json`). Wait for `p9.json`.
- CHECKPOINT: show the PASS/CHALLENGED/FAIL verdict and the validated WTP by segment. Offer: confirm or refine.
- On confirm: mark Phase 9 complete.

**Phase 10 — output assembly.**
1. Not for `partial`: run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/composite_scorer.py --session-dir '<session_dir>' --out '<session_dir>/composite-scores.json'`. When it exits 1, keep its message as the `composite_gap` for the dispatch.
2. Start `output-assembler` with:
   ```json
   { "session_dir": "<session_dir>", "market_area": "<market_area, or null>",
     "answers_path": "<answers_path, or null>", "mode": "<automated when a plugin-run block is present, else interactive>",
     "partial": false, "composite_path": "<session_dir>/composite-scores.json", "composite_gap": "<the message, or null>" }
   ```
   It writes `final-output.json` and `{session_dir}/result-draft.json`.
3. Run `git rev-parse --show-toplevel` on its own, and call the result `base`. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py place-result --draft '<session_dir>/result-draft.json' --base '<base>' --session-dir '<session_dir>'`. It sets `run.finished_at`, writes `result.json` in the session folder (`result-2.json` when the folder holds `result.json`: a resumed run) and prints its path. Call that path `result_file`.
4. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_graph.py --root '<base>' write-run --session-dir '<session_dir>' --result-file '<result_file>'`. When it exits 1 or 2, keep the line `GRAPH: FAILED <exit code> <first error line>`, and do not say that the graph holds the results, because the next session trusts that report. The result file exists already, in the session folder.
5. Mark Phase 10 complete. The run is done.

### Halt draft

A halt has no session. Write `<base>/.jtbd-market-discovery/result-draft.json` with the Write tool:
```json
{ "schema": "plugin-result/1", "plugin": "jtbd-market-discovery", "plugin_version": "<version in ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json>",
  "command": "jtbd-market-discovery:discover",
  "run": { "started_at": "<time from jtbd_state.py now>", "mode": "<automated or interactive>", "subject": "<market_area, or no market area given>" },
  "results": [], "gaps": [{ "kind": "job", "label": "Job", "why": "<the halt reason>" }] }
```
In a plugin run, add `case`, `run_id` and `answers` (the `answers_path`) to `run`. Then run `place-result` as Phase 10 step 3 does, but with no `--session-dir`: it writes the halt file in `.jtbd-market-discovery/`, removes the draft, and prints the path as `result_file`. Exit 3 means the name is taken by another run with the same `run_id`: write that to `execution-log.md` in `.jtbd-market-discovery/`, and stop. Then run `jtbd_graph.py --root '<base>' write-run --result-file '<result_file>'` with no `--session-dir`. After a clean write, the halt file is not in `.jtbd-market-discovery/`, and the output has a `removed` line, because the Run page holds its values.

### 3. CHECKPOINTS

- With no `checkpoints` field, a checkpoint stops nothing: mark the phase complete and go on.
- With `checkpoints: true`, a checkpoint stops the run until the person answers:
  1. Set the phase status in `state.json` to `awaiting`.
  2. Write `{session_dir}/questions.json`: `{"summary": "<what to show the person, short>", "questions": [<1 item for each open question>]}`. An item has the shape of an item in `${CLAUDE_PLUGIN_ROOT}/questions/discover.json` (`input`, `question`, `type`, and `options` or `default`), and for a phase checkpoint `"input": "checkpoint"` with the options `continue` and `refine`.
  3. Show the `summary`, ask each item (step 4 of `## Steps`), and write the answers to `{session_dir}/answers.json`. A reply that the person types in the chat is also an answer: write it to `answers.json` before you go on to the next phase.
- A `continue` answer marks the phase complete. A `refine` answer, or an answer that refines a phase, starts the same phase agent again with the answer text in its dispatch. Then go to the checkpoint again.
- When the reply of a phase agent ends with `QUESTIONS: <path>`, the agent needs an input its dispatch does not give. Read the file, ask each item, write `answers.json`, and start the same agent again with the answers.
- On a resume, read `{session_dir}/answers.json`. A phase with the status `awaiting` takes its answer from there.

### 4. ERROR HANDLING

- If a phase agent or a script fails, log the error to `{session_dir}/execution-log.md`.
- Retry once with the same agent or script.
- If 2 consecutive failures and `checkpoints` is true: write the items for the failure to `questions.json`, ask them, and decide with the person.
- If 2 consecutive failures with no `checkpoints`, and in any plugin run: never wait for guidance, because a plugin run has no person to answer. Log the failure, start output-assembler with `partial: true` and the other Phase 10 fields (with no `composite_path`), run `place-result` and the graph write as Phase 10 does, and stop.
- On resume: read `state.json`, find `current_phase`, and continue from there.

## Resuming a session

Run the skill again. It finds the session with an unfinished `state.json` and continues from the next open phase. All earlier phase files stay in `.jtbd-market-discovery/{session}/`.

## The 10 phases

| Phase | Who runs it | Mode |
|-------|-------------|------|
| 1 — Job Identification | `job-identifier` | Sequential |
| 2 — Job Decomposition | `job-decomposer` | Sequential |
| 3 — Need Generation | `need-generator` ×4, then `jtbd_state.py merge-needs` | Sequential |
| 4 — Effort Quantification | `effort-quantifier` | Sequential |
| 5 — Survey Design | this skill | N/A |
| 6 — Opportunity Scoring | `survey_adapter.py`, `run_phase_6.py`, `opportunity-scorer` | Sequential |
| 7 — EVC Calculation | `evc-calculator` (`inputs`), `run_phase_7.py`, `evc-calculator` (`report`) | Sequential |
| 8 — Segmentation | `run_phase_8.py`, `segmentation-analyst` | Sequential, after Phase 7 |
| 9 — WTP Validation | `run_phase_9.py`, `wtp-validator` | Sequential |
| 10 — Output Assembly | `composite_scorer.py`, `output-assembler`, `jtbd_state.py place-result` | Sequential |

## Phase Dependencies

```
Phase 1 → required for all
Phase 2 → requires Phase 1
Phase 3 → requires Phase 2 (4 agents, one at a time)
Phase 4 → requires Phase 3
Phase 5 → requires Phase 4 (survey design/fielding)
Phase 6 → requires Phase 5 data
Phase 7 → requires Phase 6
Phase 8 → requires Phase 7 (segmentation-analyst reads p7.json)
Phase 9 → requires Phase 7 + Phase 8
Phase 10 → requires Phase 9
```

## State Files

```
{session_dir}/
├── state.json            # Phase completion status, current_phase
├── execution-log.md      # Errors and decisions of the run
├── questions.json        # The open questions of a checkpoint (written when checkpoints is true)
├── answers.json          # The answers of the person to the last questions.json
├── p1.json … p9.json     # The output of each phase (p3.json is the merge of p3-batch-1.json to p3-batch-4.json)
├── survey-proposal.json, survey-odi.csv, survey-raw.csv   # Phase 6 survey files
├── p6-scores.json        # run_phase_6.py output
├── evc-input.json, evc-results.json                        # Phase 7 files
├── p8-clusters.json, p8-respondents.json                   # run_phase_8.py output
├── wtp-results.json      # run_phase_9.py output
├── composite-scores.json # composite_scorer.py output
├── final-output.json     # Phase 10 assembled final output
├── result-draft.json     # The result file before place-result sets finished_at and places it
└── result.json           # The result file (result-2.json, result-3.json for a resumed run); the save code reads it
```

## Deliverables

The output of a run is its pages in `docs/jtbd/` (the `jtbd` graph): the job, the steps, the needs, the scores, the segments, the willingness-to-pay check and one `Result` page for each result. The files of a session stay in `.jtbd-market-discovery/{session}/`, `result.json` included, as state files of the run.
