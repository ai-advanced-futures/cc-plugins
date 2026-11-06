# ADR-006: Adopt the plugin result file

**Status:** Accepted
**Date:** 2026-11-01
**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Adopts:** the repository standard for the plugin result file (repo ADR-001)
**Plugin:** product-finance v0.8.0, amended in v0.9.0 and v0.11.0

---

## Context

Business-case reads what the producer plugins found. Until now, each command of this plugin wrote its own JSON file to `.product-finance/` in its own shape. A reader could not tell a figure the person gave from one the plugin filled in. The repository standard (a copy is in `tests/support/PLUGIN_RESULT_FILE.md`) fixes one shape, the rules R1 to R7, and the invocation block a coach uses. Five commands of this plugin are on its list of adopting commands: `product-finance:discover`, `:feature-roi`, `:unit-economics`, `:ai-economics` and `:cost-coverage`.

Five facts shaped the adoption:

1. The spike of plan 4 part A (its "Recorded routes") showed that none of the five agents the commands name, dispatched directly, ran its command's steps.
2. In the spike, `feature-roi` made up a build cost and a revenue because the answers gave none.
3. The cost-coverage readout script could not run from an installed plugin folder: it needs the plugin root on the path, `pydantic` and `jsonschema`. The spike's runner wrote the readout by hand.
4. Three commands told the model to run `uv run python -m scripts.<name>`, which runs code from the working folder.
5. `discover` and `setup` read jtbd data from the old `.jtbd/` folder only. The amendment below replaces this read.

## Decision

1. **Adopt the standard.** Each of the five commands writes one result file to `.product-finance/results/` at the end of every run, a halt and a partial run too, and a person's run too (R1). `result-file.json` names the writer of each command, the defaults registry, the template leaves ruled not to be defaults, and two `scan_also` files: `commands/setup.md` and `templates/auto-config.template.json`. `questions/<command>.json` lists the inputs, and each AskUserQuestion line of the files a command reaches carries its `[q: <input>]` id. The commands asked their questions in prose; each `**Question:**` line now names AskUserQuestion with its id. `discover`, `unit-economics` and `ai-economics` gained one question each, for the subject of the run (`market`, `product`, `ai_product`); `cost-coverage` gained a list of the questions a person's run asks for a missing field.

2. **A thin runner is the route of each command.** `agents/<command>-runner.md` reads the command file, does the work of its `## Agent Dispatch` section itself and dispatches no agent, then writes the result file by the rules in the `## Result file` section of the agent the command names: `market-analyzer`, `roi-calculator`, `financial-analyst`, `ai-economist` and `cost-coverage-agent`. Run as itself, none of those agents writes a result file. No runner asks the person: a subagent has no tool to ask (see the amendment of v0.11.0). `tests/unit/test_agent_structure.py` holds every agent file, the runners included, to this rule.

3. **A plugin run uses only what it was given.** It reads an earlier run's files only through `inputs_from`, and reads no `.product-finance/assumptions.json`. It writes each file the command names into its own run folder, `.product-finance/<run_id>/`, so it never overwrites a person's files, and a result's `detail` names that copy. Where a step needs a value that neither the answers nor a default the command file states gives, the run leaves the figure out and records a gap. An input the answers do not give, which the run fills from a stated default, is a `default` source, never `model`, and its marker goes in `defaults`. The registry holds 25 entries for 23 input names: the discount rate is stated in the command and in the agent, and `target_payback_months` is registered for feature-roi and for unit-economics. For `feature-roi`, the build method, weeks, engineers, engineer cost, non-engineering time, ongoing cost, the four revenue dimensions and the urgency now have stated defaults, so a run with no answers prices a 4-week build with no revenue and marks every part of it. The ongoing cost default is a rule (15% of build cost a year), so its question has no default value.

4. **No result is graded above its sources.** No result is called validated, measured or actual unless a source is `customer_data` or `published`. A `unit_economics` result in `projected` or `hybrid` mode never has a `customer_data` source.

5. **Python runs rooted, through `uv run`.** Every script a file of a command's scan set names runs as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`, never `python3 -c`, `python3 -`, `python -m` or `uv run python`. Each script has a PEP 723 block that names its packages. `market_sizing_calculator.py` and `ai_roi_calculator.py` put their own plugin root on the path when run by path, and `ai_roi_calculator.py` gained `--input <file>`, so no shell redirection is needed. `ai_roi_calculator.py` still needs `pydantic`; `market_sizing_calculator.py` needs only the standard library. Of the four commands whose figures are arithmetic, only `ai-economics` runs a script in a plugin run, so only it depends on `pydantic`: `feature-roi` and `unit-economics` name no script, and `discover`'s script needs `assumptions.json`, which a plugin run never reads. Every result whose figures no script computed ends its `method` with "Computed by the model from the formula stated in the command; no script ran."

6. **The cost-coverage math moved to a standard-library command.** `scripts/cost_coverage_core.py` holds the constants and the math as plain functions and a command line with the readout script's flags. It needs only Python's standard library. `cost_coverage_readout.py` wraps the same functions in its pydantic models and still checks the Charter schema. The command prints one JSON line with the readout path and `coverage_ratio`, the headline price divided by the base scenario's effective cost per interaction, which the result copies as written. A test runs the command with `-I -S` from another folder and holds its output byte-identical to the pydantic serializer's.

7. **jtbd reads take the new folder first (O6). Superseded by the amendment below.** Every reader of a jtbd file names `.jtbd-market-discovery/` first and falls back to `.jtbd/`. `market_sizing_calculator.py` records the jtbd file it read, not a fixed old path. The amendment below replaces this decision for every reader in this plugin: no `.jtbd/` read is left.

## Consequences

- A coach can run any of the five commands with an answers file and read one result file that marks each default. A plugin run with few answers produces fewer results and more gaps, never a made-up figure.
- `feature-roi` with no answers recommends "DON'T BUILD": no revenue is counted unless the person says so.
- Known limit: the figures of `discover`, `feature-roi` and `unit-economics` are worked out by the model in every plugin run, and those of `ai-economics` whenever `uv` cannot run its script. Each such result says so in its `method`. Two runs on one answers file gave different returns (639% and 684%) because the command left the ramp shape and the discount period open; both are now stated. `market_sizing_calculator.py` is a standard-library calculator; standard-library calculators for the other commands, as `cost_coverage_core.py` is for cost-coverage, are a follow-up. Only `cost-coverage` computes by code everywhere.
- The `discover` read of two files jtbd never writes was filed in the ledger. The amendment below fixes it.
- Five more agent files. The C4 diagram counts them.

## Amendment (plan 4 part B): every jtbd read names a file jtbd writes

**Date:** 2026-11-02.

**Context.** `discover` read `market-analysis.json` or `discovery-report.json` from `.jtbd-market-discovery/`, else from `.jtbd/`. jtbd writes neither file, so market sizing never got the true job's segments or willingness to pay. A plugin run read no jtbd file at all.

**Decision.**

1. **A plugin run** reads only the `result_file` of the `inputs_from` entry whose `plugin` is `jtbd-market-discovery`, and only when its `run.run_id` and `run.case` match the entry and the block. Otherwise it records a `customer_segment` gap and sizes the market from the answers. Each result that uses a jtbd value copies that jtbd result's `sources` and `defaults` and cites it.
2. **A person's run** reads the newest file in `.jtbd-market-discovery/results/` (by `run.finished_at`) that holds a `customer_segment` or `willingness_to_pay` result. It passes that file to the calculator as `--jtbd-data`, and the calculator records only its path.
3. **The merge rule.** A person's run sets `willingness_to_pay` and `wtp_source` on the person's segment of the same name in `.product-finance/assumptions.json`. It never replaces a value the person wrote. It names a jtbd segment that has no match, and does not add it. jtbd's willingness to pay is monthly, so the yearly value is 12 times it.
4. **No fallback to the old `.jtbd/` folder.** Result files began in plan 4 part A, which writes them only to `.jtbd-market-discovery/results/`. No version of jtbd wrote `market-analysis.json` or `discovery-report.json` in either folder. So an old-folder read can find nothing that jtbd wrote, and decision 7's fallback does not apply to this read.
5. **A total check holds the rule.** `test_no_jtbd_path_names_a_file_jtbd_does_not_write` scans every product-finance file except the ADRs, the README and the tests. It ignores the one sentence that bans the `.jtbd/` folder, and the `.product-finance/` paths of this plugin's own files. A jtbd path may name only `.jtbd-market-discovery/` or its `results/` folder. A line that names `market-analysis.json` or `discovery-report.json` after the word jtbd fails.

**Consequences.** A person who wrote their own willingness to pay keeps it when a jtbd result arrives. A person with no segment of a jtbd segment's name sees that segment named, and adds it themselves if they want it. A jtbd run from before part A gives `discover` nothing, because it wrote no result file.


## Amendment (v0.11.0): the port

**Date:** 2026-11-06.

**Context.** The plugin moved into this repository from a private one (see `NOTICE`). In the new place, a subagent has no tool to ask the person, and a plugin cannot read a path outside its own folder.

**Decision.**

1. **No agent asks the person.** Claude Code removes `AskUserQuestion` from every subagent. The commands hold each question: `accept_before_after` is in `commands/ai-economics.md`, and `confirm_high_roi` is in `commands/feature-roi.md`. An agent takes the value of an input from the command (a person's run) or from the answers (a plugin run). When the value is absent, it uses the default that the command states, else it leaves out the figure and records a gap. The five runners work the same way in each run. An exit with code 3 of the calculator is a gap, not a question.
2. **The cost-coverage command follows its agent in this session**, as the other four adopting commands do. The agent asks nothing, so a person's run and a plugin run are the same run.
3. **The plugin holds its own copies.** The Charter schemas are in `schemas/agentic-pricing/`. The conformance checker and its schemas are in `tests/support/`. No file reads a path outside the plugin folder.
4. **The handoff file is gone.** Only one outside tool read the handoff file. The readout `.product-finance/<engagement_id>/cost-coverage-readout.json` and the result file stay.

**Consequences.** A subagent run of a command with a missing answer gives a gap, where it gave a question before. business-case reads the gaps and asks the person.
