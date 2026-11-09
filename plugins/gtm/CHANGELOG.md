# Changelog

## 1.11.1

- The file `caller-grants.json` and a block in the README name the grants that the session which starts a runner must give: the script, the output folder, the plugin files, the answers file, and the optional web and MCP tools. `tests/unit/test_caller_grants.py` checks the list (STORY-168).
- The README says that a person's command can write any path in the project, because its grant is `Write`.

## 1.11.0

- No gtm agent starts an agent, calls a skill or runs a shell command. Each agent has a `tools:` line of plain tool names (STORY-146, FEATURE-26). `/gtm:run` now starts each agent itself, in the foreground: the waves, the integrity passes, the schema checks, the floor breach question and the open questions move from `agents/orchestrator.md` to `commands/run.md`. The orchestrator profiles the person, prepares `gtm-context.json`, applies the PMF gate, and ends with `READY: gtm` (or `DONE: gtm` at the PMF stop).
- `/gtm:run` runs `scripts/plugin_integrator.py` (new option `--out <file>`) and gives the orchestrator the path of its output. It also calls the skills `enterprise-search` and `customer-support` before the dispatch of `knowledge-agent`, and gives the answers as `skill_outputs`.
- The 3 runner agents become the skills `marketing-launch-runner`, `marketing-brand-runner` and `marketing-funnel-runner`, with the same names. Each skill approves only the calls of its `allowed-tools` and removes the 4 publishing tools. A runner skill runs with the model of the conversation that calls it; the runner agents had `model: sonnet`. The plugin has 10 agents and 33 skills. Update `business-case` to 0.7.1 or later together with this version: an older `business-case` starts the 3 routes with the `Agent` tool, and each one fails with "agent type not found".
- `/gtm:run` skips a finished agent only on a resume. When an earlier run left a completion flag that is true, the command asks for the run mode: `resume` (go on with the earlier run) or `full` (run each agent again). The new flag `--resume` answers `resume`. A full run sets the flags of the earlier run back to false and starts each agent again. A `rerun` choice runs its agent again although its flag is true.
- A floor holds until the content agent writes new drafts. On band floor, `truth_tier_validator.py` keeps the scored audit and the sha256 of each draft in `.gtm/audit/<agent>-floor-hold.json`, and sets `completion_flags.<agent>` to false. On a later call, while that flag is not true or no draft has changed, the script writes the kept audit back, gives no new score, and exits 4 with the gap `floor_holds`. A resume after a stopped integrity pass calls the content agent again before the pass. Before, `/gtm:run --resume` after a floor stop could audit the drafts that the first audit had cleaned, and write brand files with score 1.0.
- A plugin run of a runner skill does not end the turn of the coach. The skill runs in the conversation of the coach, so in a plugin run it writes 1 line with the path of the result file and then does the next step of the command that called it, in the same reply. Only a person's run stops with the path as the final line. Before, the text said to stop when the result file exists, and in 3 of 3 runs of `/business-case:build` the turn ended after the first gtm route. A runner skill also takes the `plugin-run` block as 1 line with the path of a file that holds the block.
- `/gtm:run` writes `{"status": "answered"}` to `.gtm/open-questions.json` before it runs the agent of the answer again, so a new question of that agent stays in the file. It gives the orchestrator no `plugin_outputs_path` when `plugin_integrator.py` failed.
- `marketing-agent`, `sales-agent` and `funnel-agent` call no other plugin. Each one keeps its own path and names the optional plugin in its output. The sales comp gate agent writes `.gtm/sales-comp-gate-input.json` and ends with `INPUT: ...`; the skill `sales-comp-gate-review` runs the emitter.
- New test: `tests/unit/test_agent_grants.py`. ADR-001, ADR-002, ADR-003 and ADR-005 record the change.

## 1.10.3

- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).

## 1.10.2

- On band floor, the orchestrator does step 3 of the integrity pass (phase `write` of `integrity-agent`) before it stops, so the run writes `.gtm/audit/<agent>-integrity-BREACH.json` and the `error_log.<agent>_integrity` object. Before, in 1 of 3 floor runs, it stopped after the script and wrote `error_log` itself as a string (STORY-194).
- New test: `test_floor_breach_order.py`.

## 1.10.1

- `knowledge-agent`, `brand-agent` and `codebase-scanner` have the Edit tool, as the orchestrator tells them. Before, each of 6 verifier runs of `/gtm:run` got "No such tool available: Edit" from `knowledge-agent`, and 4 of them saved nothing and stopped in Wave 0 (STORY-210). Each of the 6 agents that set a completion flag now has Edit.
- Each of the 3 agents names its keys of `gtm-context.json` at its write step and changes only those keys with the Edit tool.
- `knowledge-agent` (new step 9) and `codebase-scanner` (new step 13) write `completion_log.<key>` and set `completion_flags.<key>`. Before, they set no flag, so Wave 0 could not see that they ran. A knowledge run that ends with `OPEN:` does not do step 9, so a resume dispatches it again.
- New test file: `test_context_writers.py` (4 tests).

## 1.10.0

- gtm reads the knowledge graphs of `jtbd-market-discovery` and `competitive-intelligence`, not their old output files (STORY-92). New `scripts/brain_read.py` runs the save code of each writer (`jtbd_graph.py`, `ci_graph.py`) as a subprocess and writes the pages to `.gtm/upstream/<graph>/`. It finds the writer with its own copy of `scripts/probe-plugin.sh`.
- `plugin_integrator.py --root` prints the keys `jtbd` and `competitive_intelligence` from the graphs. A graph that gives no input writes 1 line on stderr (`NO-GRAPH:` or `GRAPH-READ-FAILED:`), and its key is absent. The orchestrator writes `plugin_inputs` again at each step 3. The script also writes the lines to `.gtm-graph-notes.txt` in the project folder (an empty file when there is none, written on each read), and `/gtm:run` shows each line of that file, because the reply of the orchestrator can shorten them.
- `PLUGIN_PATTERNS` keeps only `value_ip` and `pricing: ["*right-price*"]`. The `customer_support` pattern for churn files now starts at the file name (`churn*`), so a file of another plugin with churn in its name gives no key. No old output file gives a key.
- The marketing, brand and sales agents read the graph pages. The research agent runs its competitor step when the project has no competitive-intelligence graph. The integrity agent attributes a page with the link `<graph>:/<page>`.
- The cause in a note line is the last line of the stderr of the save code (a Python traceback ends with the error). A `NO-GRAPH:` line has the fix text only when the graph or its folder is absent, not when the registry cannot be read.
- The script writes each file under `.gtm/upstream/` as a new file that replaces the target, so a link at a file never changes the file it points to. When `.gtm` or `.gtm/upstream` is a link or is not a folder inside the project, the script writes nothing there and gives 1 `GRAPH-READ-FAILED:` line for each graph. The lines still go to `.gtm-graph-notes.txt`, so `/gtm:run` shows the refusal.
- Set `GTM_GRAPH_PYTHON` to choose the Python that runs the save code. Else `uv run --quiet`, else `python3`.
- ADR-001 and ADR-002 record the change. New tests: `test_brain_read.py`, `test_graph_inputs.py`, `test_graph_reader_text.py`, `test_no_old_output.py`. The job `gtm` of `ci.yml` installs the dev packages of the two writer plugins.

## 1.9.1

- An audit with 0 claims has no integrity score. `scripts/truth_tier_validator.py` exits 3 with the gap `no_claims` and writes nothing, and the orchestrator stops the run with no file in `gtm-output/` (STORY-187). Before, 0 claims gave the score 1.00 and the band `pass`, so a run that checked nothing wrote its output as checked.
- When the integrity agent finds no claim, it writes `"claims": []` and adds no claim to get a score. `/gtm:audit` gives no score for an artifact with no claims.
- `definitions/integrity-score.md`, `definitions/truth-tiers.md` and ADR-001 state the rule. New tests: `test_no_claims.py` and 1 live test.

## 1.9.0

- Each output of a pass agrees with its schema. Each content agent names the schema of each JSON file with `${CLAUDE_PLUGIN_ROOT}/schemas/<file>` at its write step, and the integrity agent names the 9 schemas of `gtm-output/` (STORY-166).
- `funnel-metrics.json`: `stages` is the map of the 5 conversion rates of the schema (a number from 0 to 1, or null). The stage table goes under `stages_detail`. `messaging-architecture.json`: `tagline` and `elevator_pitch` are 1 string each, and a note goes under `tagline_detail` or `elevator_pitch_detail`. `pipeline-playbook.json`: `entry_criteria` and `exit_criteria` are lists of strings.
- `_meta.sources.mcp_connections` is a list of the names of the connected servers (`[]` when `/gtm:setup` did not run), as `schemas/gtm-context.json` says.
- New script `scripts/output_check.py` (`--root`, and `--agent` or `--context`). The orchestrator runs it after each integrity pass, after an override, and once at the end. Exit 1 gives 1 more dispatch of the integrity agent with `schema_errors` (its new step SCHEMA FIX). An error that stays goes to the "Schema errors" list of the summary, and `/gtm:run` shows it. The run goes on.
- `scripts/integrity_manifest.py` has `OUTPUT_SCHEMAS`, `CONTEXT_FILE`, `CONSOLIDATED_AUDIT` and `get_checked_outputs()`.
- `_meta.dispatched_agents` gets each dispatched agent (`knowledge`, `codebase_scanner`, `brand`, `marketing`, `sales`, `funnel`) from 1 table, `DISPATCH KEYS`. Before, `funnel` was missing.
- New tests: `test_output_check.py`, `test_dispatch_keys.py`, and 9 samples in `tests/fixtures/output-check/`.

## 1.8.0

- The integrity score comes from `scripts/truth_tier_validator.py`, not from the model. An integrity pass has 3 steps: the integrity agent audits (phase `audit`), the orchestrator runs the script, and the integrity agent writes (phase `write`). The script writes `integrity_score`, `band` and 5 more keys into `.gtm/audit/<agent>-integrity.json` (STORY-177).
- 3 bands. Band `floor` (under 0.60) stops the run. Band `choice` (0.60 to 0.84) writes no file to `gtm-output/` and keeps the integrity flag false until the person chooses rerun or override. Band `pass` (0.85 and more) writes the files. Before, a score from 0.60 to 0.84 wrote the files.
- When the script does not run, the run writes no score, logs the reason, and stops.
- A resume with an open question runs no agent.
- ADR-001 records the change. New tests: `test_integrity_bands.py`, `test_truth_tier_validator_cli.py`, and 4 live tests.

## 1.7.1

- The `run-id` form of `scripts/result_name.py` and the `run_id` of a file name use the `_RUN_ID` pattern of the result-file checker: 4 to 64 of a-z, 0-9 and `-`, with a-z or 0-9 first and last. A value such as `Run_1`, `ab` or `a..b` now exits 2, as the checker refuses it (STORY-164). The command part keeps the plain-name rule.
- A new test compares the pattern of the script with the pattern of the checker, and compares the answers of the 2 for 5 values.

## 1.7.0

This version ports the plugin to this marketplace.

- The plugin works when you install it. No agent asks you a question, because a subagent cannot ask one. Each command asks its questions in the main conversation.
- `/gtm:run` asks the role, the business stage, the goal, the PMF gate, and the codebase scan. It then starts the orchestrator. When a score is in the open range, the orchestrator writes `.gtm/open-questions.json` and ends with `OPEN: .gtm/open-questions.json`. `/gtm:run` asks you and starts the orchestrator again.
- The command `/gtm` is now `/gtm:run`.
- The skills `learn` and `setup` are gone. The commands `/gtm:learn` and `/gtm:setup` hold their text.
- The 28 skills that were two folders deep are now one folder deep. For example, `skills/frameworks/kotler-stp/` is now `skills/frameworks-kotler-stp/`. The skill `sales-comp-gate` is now `sales-comp-gate-review`.
- Each skill, agent, and command name has no `gtm:` prefix and no `name:` or `agent:` key in a command.
- The plugin has no `.mcp.json` file. It starts no outside server. `/gtm:setup` shows how to add each of the seven servers, and the servers are optional. A server that you add has tools named `mcp__<server>__<tool>`.
- The optional plugins `value-ip`, `tech-contracts`, `enterprise-search`, `customer-support`, `sales`, `marketing`, and `data` are optional. An agent calls a skill of such a plugin only when the plugin is in the session. Without it, the agent uses its own short path.
- The `value-ip` scorecard is found at `.value-ip/*/output/value-ip-scorecard.md`. A file that is not a scorecard of `value-ip` is no longer read as one.
- The step that made a slide deck is gone. `pitch-deck.json` stays.
- Script calls use `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. The scripts list their packages in a PEP 723 block.
- The two handoff schemas are now in `schemas/`, and the result-file checker is in `tests/plugin_result/`. No file of the plugin reads a path outside the plugin folder.
- The files `release.json`, `.mcp.json`, `check_mcp_status.py`, the root `SKILL.md`, and the question blocks of the agents are gone.
- A `run_id` and the command part go into a result file name, so each must be a plain name: 1 to 64 of letters, digits, `.`, `_` and `-`, and not `.` or `..`. `result_name.py` exits 2 for any other value, and has the new form `result_name.py run-id <value>`. A runner checks the `run_id` in step 2. A run with a bad `run_id` goes on with no `run_id` and records a gap.
- `/gtm:marketing:brand` runs the Truth Tier audit in the session, with the steps of `/gtm:audit`. It has no `Agent` tool, so it could not start `integrity-agent`, which only the orchestrator starts. A test checks that each command that names an agent has the `Agent` tool.
- In Wave 2, two agents change `gtm-context.json` at the same time. `marketing-agent`, `sales-agent` and `integrity-agent` now change only their own keys with the Edit tool, and have that tool. They do not write the whole file, so a later agent no longer removes the keys of an earlier one.
- A second `/gtm:run` dispatch sends the fields of step 5 again. When a content agent fails, the orchestrator names it and still ends with `DONE: gtm`, and `/gtm:run` says so first. `sales-comp-gate-review` stops when the emitter exits with an error, and does not read an old handoff file.
- `brand-agent` asks no question and writes no question file of its own. A missing input becomes a `[placeholder]` with the recommended value next to it, and the run goes on. It reads `brief.md` in full. The orchestrator has the Edit tool, changes the keys of `gtm-context.json` with it, and writes no helper script in the project of the person.
- `funnel-agent` has the Edit tool and sets its own `completion_flags.funnel` and `completion_log.funnel`, so a resume does not run it again.
- No agent has a tool that deletes a file. After the person answers, the orchestrator overwrites `.gtm/open-questions.json` with `{"status": "answered"}`. `integrity-agent` and the orchestrator overwrite a breach file with `{"status": "resolved"}`.
- The audit across the four agents is now `gtm-output/consolidated-audit.json`, with its own schema `schemas/consolidated-audit.json`. `truth-tier-audit.json` keeps the shape of one artifact. A stage rate in `funnel-metrics.json` may be `null` when no rate was measured.
- Tests run in CI with no skips.
- The version in `plugin.json` and in the result-file examples is 1.7.0.

Versions 1.0.0 to 1.6.0 came before the port. They come from commit `c2a329f` of a private repository.
