# ADR-011: Rule of 40 runs: setup's target and the health check

**Status:** Accepted (decided 2026-11-09; built in v0.16.0)
**Date:** 2026-11-09
**Builds on:** ADR-010, `ADR-010-rule-of-40-targets.md` (Rule of 40 targets); ADR-008 (the shared input checker); ADR-007 and ADR-006 (the assumptions file and plugin runs); ADR-005 (Magic Number)
**Plugin:** product-finance v0.16.0
**Decided here:** D-1046 and D-1047, 2026-11-11 (Pilo: changes 1, 2 and 4 of source PR #345, with the port rules); D-1057 (the command runs the script before the dispatch)

---

## Context

ADR-010 graded one Rule of 40 score against a target of 40, 50 or 60 in v0.15.0. Its pull request (#344) deferred five follow-ups. On 2026-11-09 the person decided four of them:

- No command or agent ran `rule_of_40.py`. `/product-finance:health-check` and the `financial-analyst` agent added growth and margin in the model and graded against a fixed 40 with quartile words.
- `setup` asked for the target as any number and stored it as `targets.rule_of_40_target`. Then it told the person that nothing read it.
- The Rule of 40 report printed the Magic Number band sentence. That sentence is a lever with no source.

The source spec is `docs/superpowers/specs/2026-11-09-pf-rule-of-40-followups-design.md` of source PR #345. The decisions below record what v0.16.0 built. Where the build changed a detail of the spec, the decision states the built behaviour.

## Decision

1. **Setup's target is read with `--assumptions`.** `rule_of_40.py` gains one optional flag, `--assumptions <path>`, and reads one key of that file: `targets.rule_of_40_target`. The order of work:
   - The script reads and checks the input first. It reports the input's problems as before.
   - When the input gives `target`, the script does not open the file. The input's target applies, and `target_source` is `chosen`.
   - When the input gives no `target` and the flag is given, the script reads the file. A file that cannot be read exits 1 with `Error: the assumptions file <path> cannot be read: <reason>`. A file that does not parse exits 1 with `Error: the assumptions file <path> is not valid JSON: <reason>`. A file with problems exits 3 with the header `Error: Invalid assumptions file <path>:` and one line per problem, in the words of `input_check` (ADR-008).
   - A stored `targets.rule_of_40_target` applies, and `target_source` is `setup`. When the key is absent, the default of 40 applies, and `target_source` is `default`.
   - Without the flag, the script reads no file.

   The file is checked against two small classes, `AssumptionsTargets` and `RuleOf40Targets`. They ignore every other key, and they are not in `INPUT_CLASSES`. The stored target goes to the calculation as a keyword parameter, `calculate_rule_of_40(data, stored_target=...)`, never as an input key, so no JSON input can claim `setup`. `--assumptions` is read as a `Path`, as `--input` is, so `./a.json` prints as `a.json` in an error line. The script never reads `target_rule_of_40` in `templates/auto-config.template.json`: that key is the answer setup uses in automated mode, not a stored value.
2. **`target_source` has a third value, `setup`.** The values are `default`, `chosen` and `setup`. The markdown Target line for setup's target reads `- **Target**: 50 (set in setup)`. For one target, a report from setup's target and a report with that target on the run differ only in the Target line and in `target_source`.
3. **A stored target that is not 40, 50 or 60 stops the run only when it would apply.** When the input gives no `target`, such a stored target exits 3 with `targets.rule_of_40_target = 45: not one of 40, 50, 60` (45 as an example). A setup file from before 0.16.0 can hold such a number. When the input gives `target`, the script does not open the file, so it does not refuse the stored number (golden case `setup_target_input_wins`).
4. **Interactive mode reads the file before the prompts.** This is the one stated exception to the order of work in decision 1. In interactive mode with the flag, the script reads and checks the file before the first prompt, so that the target prompt can show the stored target. A problem in the file stops the run before the script asks anything, even if the person would then type a target. With a stored target, the prompt reads `Target Rule of 40 score (40, 50 or 60, or press Enter for <stored> from setup): `. An empty answer gives no input target, so the stored target applies. The comment in `main()` that cites ADR-011 points to this decision.
5. **Not in this repository.** The plugin has no root `SKILL.md` (STORY-256 row 10). The health check has the same rule in step 3 of its `## Rule of 40 Run`.
6. **The health check runs `rule_of_40.py`.** `/product-finance:health-check` runs the steps of its `## Rule of 40 Run` section in the main session: it writes `.product-finance/rule-of-40-input.json` and runs the script for JSON and then for markdown. It saves each output that exited 0 to `.product-finance/rule-of-40-run.json` and `.product-finance/rule-of-40-run.md`, and dispatches `financial-analyst`. The agent copies the output into the report and the health check JSON, and runs no script (D-266).
   - The target is `--target 40|50|60` when given. Without it, setup's target applies through `--assumptions .product-finance/assumptions.json` when that file exists. Without either, the target is 40. The health check asks no question about the target.
   - The health check writes no result file and has no `run_id`, so it is not a plugin run. ADR-006 decision 3 and ADR-007 decision 7 ("a plugin run reads no `assumptions.json`") do not change.
   - The run never repairs a problem in the assumptions file. It runs again without `--assumptions`, and the report and the JSON say `Setup's target was not used: <location>: <reason>. Run setup again to choose 40, 50 or 60.`
   - When no JSON run succeeds, the health check computes no Rule of 40. The report says that `rule_of_40.py` did not run successfully, with the run's reason, as the command defines it; the health check JSON's `rule_of_40` is `null`, and the health score treats it as `not_graded`.
   - Of the plugin's commands, only the health check runs `rule_of_40.py`. No command runs `unit_economics.py`. The skills `calculations-rule-of-40` and `calculations-unit-economics` run their script too (STORY-345).
7. **The health score's Rule of 40 points are a plugin convention.** The points come from `target_status`: met full, split half, short none. In `commands/health-check.md`, the Rule of 40 is 10 of the 20 Profitability points (met 10, split 5, short 0). When `target_status` is `not_graded`, or `rule_of_40` is `null`, the command scores Profitability out of the gross margin's 10 points and doubles it. In `agents/financial-analyst.md`, the target status is 40% of the Efficiency Health dimension (met 100, split 50, short 0). When `target_status` is `not_graded`, when `rule_of_40` is `null`, or when no Rule of 40 Run ran (every command but the health check), the agent gives Magic Number and burn multiple 50% each. No source sets these points, and both files say so.
8. **Not in this repository.** The port removed the MCP server (STORY-77).
9. **The Rule of 40 report drops the Magic Number band sentence.** The markdown loses the `- **Interpretation**: ...` line, and the JSON `magic_number` object holds `magic_number` and `health` only. `RuleOf40Result.magic_number` still holds `interpretation`. `scripts/utils/magic_number.py` and the unit economics report do not change (ADR-005, amendment in v0.16.0). This supersedes the last sentence of ADR-010 ruling 4.
10. **Test model: the sweep guard.** `tests/unit/test_rule_of_40_sweep.py` is total over its population and a word list over content.
    - The population is every `.md` and `.json` file of the plugin that git lists, outside `tests/`, `scripts/`, the history files and the lines of the `README.md` `## What's New in v*` sections. The test reads every scoped line of each file.
    - The content check is a list of words and patterns: quartile, percentile, `IPO`, goal patterns such as `60+`, and more. It cannot see a wrong figure, or a lever written in plain words.
    - Other tests check figures only where they name them. `test_health_check_rule_of_40_run.py` compares the health check JSON and report samples with the script's output, and pins each reworded health check line that holds a figure. `test_rule_of_40_example.py` compares the example report and JSON with the script's output, and checks each number on the example's Rule of 40 lines against that output. `test_financial_analyst_rule_of_40_prose.py` pins the agent's example line. Every other Rule of 40 line is checked for words only.
    - The table-header rule refuses a Rule of 40 row under a `Quartile`, `Median`, `Percentile` or `Top 25` header. It does not refuse a Rule of 40 row under a stage-band header (`Critical`, `Warning`, `Good`, `Excellent`). Such rows are removed by hand.
11. **Test model: the `EXTRA_EXEC_FILES` registry.** `EXTRA_EXEC_FILES` in `tests/unit/test_plugin_result_contract.py` lists each file outside the adopting commands' scan set that runs a script: today only `commands/health-check.md`. The scan of `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/` calls reads these files with the scan set, and a rot test checks that each listed file exists and holds such a call.
    - The `RUN_LINES` and `PROSE_MENTIONS` registries of the source are not in this repository. `tests/unit/test_script_grants.py` checks that each script call has its grant (`files_with_rules` in `script_grants.json`), and `tests/unit/test_skill_script_calls.py` checks that a skill names a script only in its own call.
12. **ADR-010 decision 11 is not re-triggered when the printed source text is unchanged.** No source text changes in 0.16.0, so the sources are not re-read, including where the same text now prints in new places: the health check report and the example. The Feld, Vista and ICONIQ texts come from `rule_of_40.QUOTES`. A changed source text calls for a new read; a new place for an unchanged text does not.

## Consequences

- A target chosen in setup now applies to every run that passes `--assumptions`, and the report says that it came from setup. A target given on the run still wins.
- A setup file from before 0.16.0 that stored another number, for example 45, is refused when it would apply. The health check then runs with 40 and says so. Running setup again fixes it.
- The Rule of 40 section of the health check report is the script's output. It holds the ladder, the margin lines and the sources, and no quartile words.
- The sweep guard finds a forbidden word on any Rule of 40 line of the plugin's docs, not only in the files this release changed. Outside the places decision 10 names, it cannot find a wrong figure.
- Not done in 0.16.0: `unit-economics` running `unit_economics.py`; quartile tables of metrics other than the Rule of 40; reading any setup key other than `targets.rule_of_40_target`.
