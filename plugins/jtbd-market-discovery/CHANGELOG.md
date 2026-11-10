# Changelog

## 1.11.9

- **fix:** a very long whole number (about 310 digits or more) in an EVC input gives 1 line that names the field, with exit 1 and no file. This holds for `run_phase_7.py` and for `write-run`. Before, `float()` of the number raised `OverflowError`, and the run ended with a traceback. `is_default` compares the number with `==` and calls no `float()`, and `_number` of `run_phase_7.py` says `<field> is too large for a number`.

## 1.11.8

- **fix:** `write-run` finds the step of a need whose `step` text is a number, a space and text, with no mark after the number (for example `7 Reconcile invoice details with order and receipt records`). The text must agree with the title of that step: one is the start of the other, and the shorter one ends at the end of a word. A text with a number and other text (for example `9 hours to check each invoice`) names no step. Before, a run with this form ended with `GRAPH: FAILED 1 ERROR: the need 'N001' names no step of p2.json` and wrote no page (STORY-320).

## 1.11.7

- **fix:** Phase 7 uses the default of an assumption when nobody gave a value, and takes no rate from `p4.json`. `run_phase_7.py` refuses an assumption that is marked `default` and does not have the default value, and `write-run` stops on a `p7.json` or a `customer_value` result with that fault. Before, a run could use an estimate of Phase 4 (for example a labor rate of 35.5) and name it a default rate in the result file (STORY-287).

## 1.11.6

- Each skill names each script that it runs in its Bash grant (`scripts/<file> *`). Before, the grant `scripts/*` also permitted `uv run` of a file outside the scripts folder through a path with `..`, also a file of the project (STORY-283).

## 1.11.5

- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).

## 1.11.4

- `setup`, `learn` and `ask` grant only the commands of their steps: the graph script and the router script by their paths, `git rev-parse`, and the `gh` commands of `learn`. `setup` had the whole shell, and `learn` and `ask` had each program that `uv run` can start. `ask` runs no `knowledge.py` command and has no `Agent` grant, because `knowledge:ask` runs them under its own grant (STORY-263, #1044).
- The router command of `setup` is on 1 line, with the template path and the router path in no quotes, because the grants name them with no quotes. The grant of the `sed` part names the default folder `docs/jtbd`: a `setup` with another folder asks the person to approve that command. A `Read` grant of the template lets `sed` take it on standard input, also in an install, where the plugin folder has a version folder.

## 1.11.3

- `write-run` gives a score to each scored need of `p6.json`. It reads each list of `p6.json` whose items have a need and a score field. Before, it read 6 fixed keys, and an agent run that gave its full list as `scored`, `all_scored_needs` or `additional_high_opportunity_needs` got a score on the Outcome pages of its top list only. When 2 lists give a field of the same need, the value of the later list is kept. The shapes of `opportunity-scorer` and `phase-6-opportunity-scoring` give the full list as `scored` (STORY-288).

## 1.11.2

- `setup` gives the template of the router block to `sed` on standard input. Before, the `sed` command named the template file, and Claude Code refused it as an edit of a sensitive file, because the file is in a loaded plugin. So setup made the graph and wrote no router block (STORY-261).

## 1.11.1

- `composite_scorer.py` reads `opportunity_score` from each opportunity of `p6.json`, and `odi_score` when `opportunity_score` is absent. Before, the agent `opportunity-scorer` wrote `odi_score`, so the ODI part (40%) of the composite score was 0 in each real run, and no error showed. `write-run` reads the same two keys for the score of an Outcome page (STORY-279).
- The `p6.json` examples of `opportunity-scorer`, `phase-6-opportunity-scoring`, `quick-validate`, `phase-10-output-integration` and `output-assembler` give `opportunity_score`. The `final-output.json` example of the README gives `odi_score_normalized` (STORY-279).

## 1.11.0

The plugin writes no old output file. The graph in `docs/jtbd/` is the only output of a run (STORY-113, D-056).

- The 4 files `customer-needs.json`, `opportunity-scores.json`, `evc-analysis.json` and `wtp-validation.json` at the top of `.jtbd-market-discovery/` are not written any more. The agent `output-assembler` has the section `## No file beside the graph` in place of `## Promised files`, and the skill `discover` names the graph as its output.
- The result file is `result.json` in the session folder, and not a file in `.jtbd-market-discovery/results/`. It is a state file of the session: the save code reads it, and it stays. A resumed run writes `result-2.json`, then `result-3.json`.
- `jtbd_state.py place-result` has the option `--session-dir`. With it, the command writes `result.json` (or the next number) in that folder. With no option, for a halt before a session folder, it writes the halt file in `.jtbd-market-discovery/` with the name that `result_name.py` gives, and it removes the draft that is in that folder.
- `write-run` with no `--session-dir` removes a result file when the file is at the top of `.jtbd-market-discovery/` and the write is clean. It prints `removed <path>`. After a failed write, the file stays. A result file in another place is never removed.
- `write-run` reads the upstream result file of a `wtp-check` run from the session folder of that run: `result.json`, `result-2.json`, and so on, in number order, and the last file that matches. It does not read `results/` any more. A discover session of an earlier version has its file in `results/`: the `wtp-check` of such a session stops with `no result file of the discover run ... is in its session folder`. Run discover again, or move that file into the session as `result.json`.
- The files of an earlier version (the `results/` folder and the 4 root files) are not removed and not read. A person can delete them.
- The conformance copy `tests/plugin_result_conformance.py` checks for the file name `result.json` in place of the folder `.jtbd-market-discovery/results/`.

## 1.10.5

- `learn`, Step 6, shows the full issue body in a fenced block after the first yes. It then asks a second question that says the repository `ai-advanced-futures/cc-plugins` is public. It opens the issue only after a yes to the second question, because the first yes is to the offer and not to the text (STORY-264).

## 1.10.4

- `write-run` reads a step text that starts with its number, in the forms "7. Check ...", "7) Check ...", "7: Check ..." and "Step 7: Check ...". The text after the number is matched to a step title first. The number is the last choice, so a text that equals a title wins over a different number. A need that names no step still stops the run. Before, each saved live session with such a need (`v1111-disc-0001`, `close-assistant-0001`, `s168-jtbd-0001`) stopped with "names no step of p2.json" (STORY-278).
- `write-run` writes the graph of a `wtp-check` with no upstream run. When the run has no Segment page and reads no input run, the WtpValidation page has no `segment` link, and `write-run` prints 1 warning for each segment. An input run that has Segment pages and no page of the segment name still stops the run (STORY-278).
- The `segment` link of a WtpValidation page is not required: `schema/jtbd.yaml`, `schema/jtbd.schema.json` and `REQUIRED_LINKS` change. `write-run` runs `upgrade` first, so the manifest of a graph that an older version made takes the new list (STORY-278).

## 1.10.2

- `jtbd_graph.py set` and `new --set` keep a value that YAML reads as a date or a time as the text that the person gave. Before, `set RUN-01 finished_at=2026-11-06T22:21:48Z` exited 1, because the schema wants a string, so the Run page got no `finished_at` and `verify-run` refused it (STORY-186).
- `learn`, Step 3, sets `finished_at` of a quick validation from `date` and confirms the run. It names the form of the `run` field and the schema file that lists the fields of each type (STORY-186).

## 1.10.1

- The file `caller-grants.json` and a block in the README name the grants that the session which starts a plugin run must give: the 9 scripts, the output folder, the plugin files, and the answers file. `tests/unit/test_caller_grants.py` checks the list (STORY-168).
- The README says that a person's command can write any path in the project, because its grant is `Write`.

## 1.10.0

- `run_phase_9.py --segment-column <column> [--p8 <p8.json>]` writes the survey numbers of each segment: the row count, the outlier layer, the `wtp_analysis` block of `p9.json`, the layer validation and the Van Westendorp points (PMC, OPP, IPP, PME and the acceptable range). wtp-check and discover pass the option when the survey has the column `segment_id`, and wtp-validator copies the numbers. Before, the model split the survey or estimated the numbers, and some of its commands were refused (STORY-224, STORY-193).
- `write-run` refuses a `p9.json` with no survey value when the session has a survey, and `verify-run` refuses a Run page with a survey count (the new slot `wtp_sample_size`) and no WtpValidation page with a survey value (STORY-193).
- `learn`, `ask` and `setup` run `git rev-parse --show-toplevel` on its own and write the path in each command, because Claude Code refuses a command with a command substitution or a shell variable. `learn` and `ask` say to run one command per Bash call (STORY-175).

## 1.9.2

- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).

## 1.9.1

The commands that read the graph stop on a page or a folder that they cannot read (STORY-214, FEATURE-26).

- `results`, `pages`, `resolve`, `verify-run`, `set`, `body`, `link`, `unlink` and `remove` exit 1 with 1 line on stderr that names the file, when a page of the graph does not parse, has no type or cannot be read, or when a folder of the graph cannot be listed. Before, they skipped such a page or folder and gave a wrong answer with exit 0, and a page file with no read access gave a traceback.
- `check` names a folder that it cannot list as `J-schema`, and it gives no traceback for a file that it cannot read.

## 1.9.0

No agent runs code that the model writes, and each agent has a narrow `tools:` line (STORY-121, FEATURE-26).

- No agent has the `Bash` tool. The skills `discover` and `wtp-check` run the scripts with `uv run` between the agent starts, and the agents read the result files.
- The agents `orchestrator` and `wtp-check-runner` are removed. The `discover` skill runs the 10 phases, and the `wtp-check` skill runs the price check and writes its result file.
- The grants are `Read, Write` for seven agents, and `Read, Write, Glob` for `output-assembler` and `wtp-validator`.
- The skill starts the 4 `need-generator` agents one at a time, in the foreground, because an agent that runs in the background returns in a new turn that has no tool grant from the skill. A run of Phase 3 is slower than before.
- New scripts: `run_phase_6.py` to `run_phase_9.py`, `jtbd_state.py merge-needs` and `jtbd_state.py place-result`. `composite_scorer.py` has `--out`.
- `evc-calculator` has two steps, `inputs` and `report`. It writes `evc-input.json`, the skill runs `run_phase_7.py`, and the agent reads `evc-results.json`. When the agent changes an input, it ends with `RERUN: evc-input.json` and the skill runs the script one more time.
- The agents no longer write the Excel and PNG secondary files. The skill writes the CSV reports with `report_exporter.py`.
- The skill writes the pages of the graph (`jtbd_graph.py write-run`) after `place-result` has written the result file.
- A value that the person gave (the survey path, a column name, `run_id`, `case`) goes into a command in single quotes, and each `'` in it is written as `'\''` (issue #742).
- Tests: `tests/unit/test_agent_grants.py` fails when an agent has `Bash`, `Agent`, `Skill`, an `mcp__` tool or `general-purpose`, and when a `uv run` line of a skill has an unquoted `<...>` placeholder.
- `composite_scorer.py` counts a segment with `"size_percent": null` as 0, and no longer stops with a `TypeError`.
- The skill `discover` says that a request to not ask the questions of step 2 again does not change `checkpoints`, and that a reply the person types in the chat is written to `answers.json` before the next phase.
- The live tier loads the `knowledge` plugin that `plugin.json` depends on (`--plugin-dir` and `--add-dir`). The Phase 8 live test agrees with the skill: with no survey file, no `run_phase_8.py` runs and the dispatch of `segmentation-analyst` holds the segment count of the person.

## 1.8.0

A run writes its output as the `jtbd` graph. This version has the hook, the three skills and the write flow of the agents.

- The agents `output-assembler` and `wtp-validator` call `jtbd_graph.py write-run` at the end of a run. When it fails, the agent writes the line `GRAPH: FAILED <exit code> <first error line>`.
- New skills: `setup` adds the router block to `CLAUDE.md`, `ask` answers a question from the graph, and `learn` confirms a run or saves other results.
- `jtbd_graph.py verify-run` sets `status: stable` and a `verified` entry on a run and its pages.
- The skills `discover`, `wtp-check` and `quick-validate` end with the question "Learn these results?".
- A hook runs `regen` and both checks after a write. `hooks/brain-hook.sh` is a copy of the file in `system-design`.
- Four files are not written at the root of `.jtbd-market-discovery/` any more: `job-statement.json`, `job-steps.json`, `customer-segments.json` and `final-output.json`. Four stay, because other plugins read them.
- `remove` stops when a page that stays links to a page that goes. It matches the run with `==` and not with `in`.
- The input session of a `wtp-check` run must be a folder beside the session folder. The registry path must stay in the project.
- The folder name of the graph may hold only letters, digits, and the characters `.`, `_`, `/` and `-` (at most 100). The skills `setup` and `learn` test each text before they put it in a command.
- ADR-004 records the decision.

## 1.7.0

The plugin has a brain of the knowledge standard: one graph in `docs/jtbd/`. This version has the schema, the save code and the brain check. The skills `setup`, `learn` and `ask`, the hook, and the write flow of the agents come in the next version.

- `schema/jtbd.yaml` has 7 page types: `Run`, `Job`, `JobStep`, `Outcome`, `Segment`, `WtpValidation` and `Result`. `scripts/gen-schema.sh` makes the JSON files from it.
- `scripts/jtbd_graph.py` is the save code. The operations of the standard are `init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check` and `log`.
- `write-run` writes all pages of one run from the session folder and the result file. It runs `init` when the project has no graph. A `wtp-check` run links to the `discover` run that it read. A halt before a session writes one `Run` page.
- `results` prints the `Result` pages of one run in the shape of a result file. `pages` prints the pages of one type.
- The brain check has the rules `J-schema`, `J-run`, `J-tree`, `J-score`, `J-rank`, `J-finished`, `J-result` and `J-once`.
- `plugin.json` names the plugin `knowledge` as a dependency. `scripts/probe-plugin.sh` is a copy of the file in `system-design`.

## 1.6.0

First version in this repository. Versions 1.0.0 to 1.5.1 came before it, from commit c2a329f of a private repository.

- Three skills replace the three commands: `discover`, `wtp-check` and `quick-validate`. The skills ask the questions. An agent of the plugin cannot ask the person anything, because Claude Code removes `AskUserQuestion` from each subagent.
- The orchestrator stops at each checkpoint when the dispatch has `checkpoints: true`. It writes `questions.json` and ends with a `QUESTIONS:` line. The `discover` skill asks the items, writes `answers.json`, and dispatches the orchestrator again. A dispatch with no `checkpoints` field never stops.
- Scripts run with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. Each script has a PEP 723 block with its packages. `uv` must be on the path of the person.
- Agents are dispatched as `jtbd-market-discovery:<agent>` with the `Agent` tool. Each agent has a `tools:` line that names only the tools it needs.
- The plugin result standard, its checker and its conformance test are now inside the plugin folder. The result file registry `result-file.json` lists seven defaults.
- The blocks for the team tool of the source repository, and the hand-off file for other plugins, are removed.
- The end of a run offers `/product:explore`, `/gtm` and `/pricing:price`, and `/jtbd-market-discovery:wtp-check`.
- The author, the homepage and the repository in `plugin.json` name this repository. The plugin has a `NOTICE` file with the MIT notice of the source plugin.
