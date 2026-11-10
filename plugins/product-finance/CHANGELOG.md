# Changelog

## 0.15.0

- **feat:** `rule_of_40.py` takes an optional `target` of exactly 40, 50 or 60. The default is 40 for each product, and no other input selects the target. The script grades each margin that you give against the target, on its own line: `ebitda_margin` always, and the new optional `fcf_margin` when you give it. Each line reads `met` or `short by N`. The status is `met`, `short`, `split` or `not_graded`. A short margin gets the line "closes with N points of growth or N points of margin". The script names no lever.
- **feat:** a ladder shows the score minus 40, 50 and 60 for each margin, and labels each bar with its source: Feld (2015) for 40, "No published benchmark found. A bar you set." for 50, and Vista (2026), "an emerging aspiration, not a universal baseline", for 60.
- **feat:** new optional inputs `months_of_revenue`, `nrr` and `gross_margin`. Write `fcf_margin`, `nrr` and `gross_margin` as percentages: 12.5, not 0.125. At 12 months of revenue or less, the report gives no verdict, because growth is not a year-on-year rate before the thirteenth month. NRR and gross margin print as reference lines, and the score never uses them. Gross margin prints with the cohort figures of Bessemer, The State of AI 2025. Under $25M ARR, the report prints the ICONIQ caution and still grades the product.
- **change:** the JSON adds `target`, `target_source` (`default` or `chosen`), `target_status`, `target_lines`, `target_notes`, `ladder` and `reference_lines` beside `health_status`. For each input that is valid in 0.14.1, the values of `rule_of_40_score`, `weighted_rule_of_40`, `revenue_growth_rate`, `ebitda_margin`, `health_status` and `magic_number` do not change. `health_status` is the old stage band. It has no published source, and it is not the verdict.
- **change:** the Rule of 40 markdown has no Health Status line, and no line with no source: the quartile lines, the stage and ARR-band advice, the Balance Type line, the trend judgment lines, and each old recommendation, also "Target: >50% growth rate" and "reduce burn by 30-50%". The weighted score has the label "plugin convention, not graded".
- **change:** an input with `target`, `fcf_margin`, `months_of_revenue`, `nrr` or `gross_margin` at a value that the checker refuses exits with code 3 and names the key. Before, the script ignored the key. For example, a `target` of 45 prints `- target = 45: not one of 40, 50, 60`.
- **fix:** an estimated Magic Number of `unit_economics.py` prints no band Notes sentence: the JSON `benchmark_notes` is `null`, and the markdown has no Notes line. `/product-finance:unit-economics` tells the model to show the band, but not the sentence of the band.
- **refactor:** `limits(one_of=...)` of `scripts/input_check.py` works also on a whole-number field.
- **docs:** the rule-of-40 skill, the Rule of 40 section of `docs/KPI_DEFINITIONS.md`, `--help` and the interactive prompts describe the target, the 2 margins (also how stock-based pay counts) and the sources. `setup` tells the person that `rule_of_40.py` does not read its stored target. The health check does not change and takes no target. ADR-010 records the targets, with its amendments. ADR-005, ADR-008 and ADR-009 change.

## 0.14.2

- **fix:** each result figure of `ai-economics` comes from `ai_roi_calculator.py`, and its `method` names the script. The new `--format result` prints the 3 monthly figures under the keys that the result rules name. Before, the rules named keys that the script did not print, so the model worked the figures out and wrote "no script ran".
- **feat:** the script takes the optional inputs `infrastructure_monthly_cost` (multiplied by the months of the period), and `ai_engineers` with `ai_engineer_annual_cost` (the monthly development cost).
- **fix:** the command lists the script input of each answer, so the model does not read the script to find the names. A run in the default mode refused each such read, and in 2 runs it wrote no result file.
- **fix:** each result keeps the key `defaults`, `[]` when there is none. The 5 runners run `git rev-parse --show-toplevel` with no `-C`.
- **test:** `tests/unit/test_ai_economics_result_keys.py` fails when a result rule names a key that the script does not print, or when the input list leaves out an answer.

## 0.14.1

- **fix:** in a headless run in the default mode, each command can read the plugin files that it needs. The `allowed-tools` line of 8 commands has 1 `Read(/${CLAUDE_PLUGIN_ROOT}/<file>)` rule for each such file, and no other `Read` rule. Before, Claude Code refused the read of `plugin.json` and of the agent file, and the run wrote no result file.
- **docs:** each command names a plugin file with `${CLAUDE_PLUGIN_ROOT}/` before it.
- **test:** `tests/unit/test_plugin_file_read.py` fails when a command reads a plugin file with no rule for it, or has a `Read` rule for no read.

## 0.14.0

- **feat:** the Magic Number divides by the S&M spend of 1 quarter, from the new optional input `prior_quarter_sm_spend`. Without it, the script estimates the spend as (sales costs + marketing costs) × 3 / period months. It labels the figure as an estimate (`is_estimate`, `estimate_note`, `(estimate)`), and leaves the figure out of `overall_health` and its recommendations. One line tells the person to calculate the figure again.
- **change:** Magic Number figures become 4 times larger at a 12-month period, because the old spend was the spend of the full period. The sample case `poor` moves from warning to excellent.
- **feat:** the interactive run and `/product-finance:unit-economics` ask for the S&M spend of the prior quarter. A person who does not have it hears that the Magic Number cannot be calculated reliably. Automated mode asks nothing and uses the estimate.
- **change:** the question `net_new_arr` asks for the most recent quarter, because the formula multiplies this value by 4.
- **fix:** each printed figure of the unit economics, Rule of 40 and AI ROI scripts comes from exact math on the inputs as written, and rounds half away from zero only at output, to the same places as before. These printed figures change: CAC `4,170.81` becomes `4,170.82`, the weighted Rule of 40 `63.1` becomes `63.2` in 11 sample cases, LTV:CAC `0.62` becomes `0.63`, and a Magic Number of exactly 0.125 prints `0.13`. A `-0.0` input reads as 0. `market_sizing_calculator.py` keeps its figures.
- **fix:** a value exactly on a band edge gets the band of that edge. Growth 64.1 with margin -24.1 scores exactly 40 and gets `excellent`, where it got `good`. At a break-even of exactly 6 months, the `Fast payback` line does not print.
- **fix:** the Magic Number band text reads `1.0 or more`, `0.75 up to 1.0`, `0.5 up to 0.75` and `under 0.5` in the output and the docs.
- **fix:** the Rule of 40 gap prints to 1 place, or `less than 0.1`. A score of exactly 40 does not print `Improve score by 0 points`.
- **fix:** a figure above the float range prints `Infinity` or `-Infinity` in the JSON, where a ratio printed `NaN`.
- **fix:** a required field given as `null` prints `- <field>: null, a value is required`. An absent field still prints `missing`.
- **fix:** `discover` and its runner correct a mistyped command, path or JSON syntax of the assumptions file 1 time, from the error message of the script, and change no value. The unit economics and feature ROI runners say that their command runs no calculator script.
- **docs:** `ai_roi_calculator.py --help` shows the `--input` example. ADR-009 records exact figures. ADR-005 records the spend of 1 quarter and the estimate.

## 0.13.7

- **fix:** a `null` in a field with a default, such as `period_months`, now runs with the default and exits 0. Before, the script refused it as `missing` with exit code 3.
- **fix:** in `ai-economics` and its runner, when the first run of the AI ROI script exits with code 2, or with code 1 and `Error: cannot read` or `Error: Invalid JSON input:`, the model corrects the command, the path or the file and runs it 1 more time.
- **change:** when the run after a correction or a rewrite fails, `ai-economics` stops with no figure, 1 gap and a `BLOCKED` line. Before, the model worked out the figures by hand.
- **refactor:** the AI ROI, unit economics and Rule of 40 scripts share 1 input read and 1 refusal in `scripts/input_check.py`. Each other error text and exit code stays the same, and new tests pin them as bytes. Code that imported `checked_input` or `EXIT_INPUTS` from 1 of the 3 scripts now imports them from `scripts/input_check.py`, and `checked_input` takes the input class first.
- **docs:** ADR-006 and ADR-008 change. The docstrings of the checker do not name `pydantic`. The 3 test files of the scripts share 1 helper module.

## 0.13.6

- **fix:** `unit_economics.py` and `rule_of_40.py` need only the standard library, and `scripts/input_check.py` checks their input.
- **feat:** `unit_economics.py` and `rule_of_40.py` take `--input <file>`.
- **fix:** a refused input to these 2 scripts exits with code 3 and prints 1 plain line for each problem. An input that the script cannot read exits with code 1.
- **fix:** each script that uses `input_check.py` refuses `NaN`, `Infinity` and `-Infinity` with `not a finite number`.
- **change:** these 2 scripts refuse a number written as text, and `true` or `false`. A Magic Number value of `rule_of_40.py` needs its pair. No check remains on the sum of sales and marketing costs, but each cost keeps its own limit.
- **change:** interactive unit economics asks for quarterly net new ARR. Interactive Rule of 40 asks the 2 Magic Number questions, and refuses an unknown stage.
- **fix:** `ai-economics` rewrites only a plain number on exit code 3. It does not make a number from `n/a`.
- **docs:** `README.md` names the 2 scripts that need `pydantic`. ADR-006, ADR-007 and ADR-008 change.

## 0.13.5

- **fix:** `ai_roi_calculator.py` needs only the standard library, so `uv run` gets no package for it. `scripts/input_check.py` checks its input.
- **fix:** a refused input exits with code 3 and prints 1 plain line for each problem. An input that the script cannot read exits with code 1 and names the file.
- **change:** the script refuses a number written as text, and `true` or `false`. Each `provider_breakdown` value must be at least 0. Before this change, only a negative total was refused.
- **fix:** the markdown report shows `n/a` for a share of a zero total, and does not stop with a divide-by-zero error.
- **fix:** in interactive mode, an answer of 0 hours saved still asks for the employee cost, and each answer goes through the same check as an input file.
- **feat:** `scripts/input_check.py` has a lower limit (`ge`), limits on each value of a map (`each`), and a rule for 2 fields that go together.
- **docs:** `ai-economics` and its runner say what to do on exit code 3. ADR-006 changes, and ADR-008 records the shared input checker.

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
