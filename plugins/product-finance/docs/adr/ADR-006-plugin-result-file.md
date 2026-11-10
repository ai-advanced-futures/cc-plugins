# ADR-006: Adopt the plugin result file

**Status:** Accepted
**Date:** 2026-11-01
**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Adopts:** the repository standard for the plugin result file (repo ADR-001)
**Plugin:** product-finance v0.8.0, amended in v0.9.0, v0.11.0, v0.12.0 and v0.13.0

---

## Context

Business-case reads what the producer plugins found. Until now, each command of this plugin wrote its own JSON file to `.product-finance/` in its own shape. A reader could not tell a figure the person gave from one the plugin filled in. The repository standard (a copy is in `tests/support/PLUGIN_RESULT_FILE.md`) fixes one shape, the rules R1 to R7, and the invocation block a coach uses. Five commands of this plugin are on its list of adopting commands: `product-finance:discover`, `:feature-roi`, `:unit-economics`, `:ai-economics` and `:cost-coverage`.

Five facts shaped the adoption:

1. The spike of plan 4 part A (its "Recorded routes") showed that none of the five agents the commands name, dispatched directly, ran its command's steps.
2. In the spike, `feature-roi` made up a build cost and a revenue because the answers gave none.
3. The cost-coverage readout script could not run from an installed plugin folder: it needs the plugin root on the path, `pydantic` and `jsonschema`. The spike's runner wrote the readout by hand.
4. Three commands told the model to run `uv run python -m scripts.<name>`, which runs code from the working folder.
5. `discover` and `setup` read jtbd data from the first result files of jtbd only. The amendments below replace this read.

## Decision

1. **Adopt the standard.** Each of the five commands writes one result file to `.product-finance/results/` at the end of every run, a halt and a partial run too, and a person's run too (R1). `result-file.json` names the writer of each command, the defaults registry, the template leaves ruled not to be defaults, and two `scan_also` files: `commands/setup.md` and `templates/auto-config.template.json`. `questions/<command>.json` lists the inputs, and each AskUserQuestion line of the files a command reaches carries its `[q: <input>]` id. The commands asked their questions in prose; each `**Question:**` line now names AskUserQuestion with its id. `discover`, `unit-economics` and `ai-economics` gained one question each, for the subject of the run (`market`, `product`, `ai_product`); `cost-coverage` gained a list of the questions a person's run asks for a missing field.

2. **A thin runner is the route of each command.** `agents/<command>-runner.md` reads the command file, does the work of its `## Agent Dispatch` section itself and dispatches no agent, then writes the result file by the rules in the `## Result file` section of the agent the command names: `market-analyzer`, `roi-calculator`, `financial-analyst`, `ai-economist` and `cost-coverage-agent`. Run as itself, none of those agents writes a result file. No runner asks the person: a subagent has no tool to ask (see the amendment of v0.11.0). `tests/unit/test_agent_structure.py` holds every agent file, the runners included, to this rule.

3. **A plugin run uses only what it was given.** It reads an earlier run's files only through `inputs_from`, and reads no `.product-finance/assumptions.json`. It writes each file the command names into its own run folder, `.product-finance/<run_id>/`, so it never overwrites a person's files, and a result's `detail` names that copy. Where a step needs a value that neither the answers nor a default the command file states gives, the run leaves the figure out and records a gap. An input the answers do not give, which the run fills from a stated default, is a `default` source, never `model`, and its marker goes in `defaults`. The registry holds 25 entries for 23 input names: the discount rate is stated in the command and in the agent, and `target_payback_months` is registered for feature-roi and for unit-economics. For `feature-roi`, the build method, weeks, engineers, engineer cost, non-engineering time, ongoing cost, the four revenue dimensions and the urgency now have stated defaults, so a run with no answers prices a 4-week build with no revenue and marks every part of it. The ongoing cost default is a rule (15% of build cost a year), so its question has no default value.

4. **No result is graded above its sources.** No result is called validated, measured or actual unless a source is `customer_data` or `published`. A `unit_economics` result in `projected` or `hybrid` mode never has a `customer_data` source.

5. **Python runs rooted, through `uv run`.** Every script a file of a command's scan set names runs as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`, never `python3 -c`, `python3 -`, `python -m` or `uv run python`. Each script has a PEP 723 block that names its packages. `market_sizing_calculator.py`, `ai_roi_calculator.py`, `unit_economics.py` and `rule_of_40.py` put their own plugin root on the path when run by path, and the last 3 take `--input <file>`, so no shell redirection is needed. `market_sizing_calculator.py`, `ai_roi_calculator.py`, `unit_economics.py` and `rule_of_40.py` need only the standard library. Of the four commands whose figures are arithmetic, only `ai-economics` runs a script in a plugin run: `feature-roi` and `unit-economics` name no script, and `discover`'s script needs `assumptions.json`, which a plugin run never reads. Every result whose figures no script computed ends its `method` with "Computed by the model from the formula stated in the command; no script ran."

6. **The cost-coverage math moved to a standard-library command.** `scripts/cost_coverage_core.py` holds the constants and the math as plain functions and a command line with the readout script's flags. It needs only Python's standard library. `cost_coverage_readout.py` wraps the same functions in its pydantic models and still checks the Charter schema. The command prints one JSON line with the readout path and `coverage_ratio`, the headline price divided by the base scenario's effective cost per interaction, which the result copies as written. A test runs the command with `-I -S` from another folder and holds its output byte-identical to the pydantic serializer's.

7. **jtbd reads take the new folder first (O6). Superseded by the amendment below.** Every reader of a jtbd file names the new result folder of jtbd first and falls back to the old one. `market_sizing_calculator.py` records the jtbd file it read, not a fixed old path. The amendments below replace this decision for every reader in this plugin: no read of an old folder is left.

## Consequences

- A coach can run any of the five commands with an answers file and read one result file that marks each default. A plugin run with few answers produces fewer results and more gaps, never a made-up figure.
- `feature-roi` with no answers recommends "DON'T BUILD": no revenue is counted unless the person says so.
- Known limit: the figures of `discover`, `feature-roi` and `unit-economics` are worked out by the model in every plugin run, and those of `ai-economics` whenever `uv` cannot run its script or its script refuses an input (exit code 3). When a corrected run of that script fails, the run stops with no figure. Each such result says so in its `method`. Two runs on one answers file gave different returns (639% and 684%) because the command left the ramp shape and the discount period open; both are now stated. `market_sizing_calculator.py`, `ai_roi_calculator.py`, `unit_economics.py` and `rule_of_40.py` are standard-library calculators, though no command runs the last 2. A standard-library calculator for `feature-roi`, and running `unit_economics.py` in `unit-economics` and `rule_of_40.py` in `health-check`, as `cost_coverage_core.py` runs in cost-coverage, are a follow-up. `cost-coverage` computes by code in every run, and `ai-economics` in every run whose script exits with code 0.
- The `discover` read of two files jtbd never writes was filed in the ledger. The amendments below fix it.
- Five more agent files. The C4 diagram counts them.

## Amendment (plan 4 part B): every jtbd read names a file jtbd writes

**Date:** 2026-11-02.

**Superseded in part.** Decisions 1 and 2 now read the jtbd graph: see the amendment of STORY-91 below. Decisions 3 and 4 stay.

**Context.** `discover` read `market-analysis.json` or `discovery-report.json` from the result folder of jtbd, else from the old folder of jtbd. jtbd writes neither file, so market sizing never got the true job's segments or willingness to pay. A plugin run read no jtbd file at all.

**Decision.**

1. **A plugin run** reads only the `result_file` of the `inputs_from` entry whose `plugin` is `jtbd-market-discovery`, and only when its `run.run_id` and `run.case` match the entry and the block. Otherwise it records a `customer_segment` gap and sizes the market from the answers. Each result that uses a jtbd value copies that jtbd result's `sources` and `defaults` and cites it.
2. **A person's run** reads the newest result file of jtbd (by `run.finished_at`) that holds a `customer_segment` or `willingness_to_pay` result. It passes that file to the calculator as `--jtbd-data`, and the calculator records only its path.
3. **The merge rule.** A person's run sets `willingness_to_pay` and `wtp_source` on the person's segment of the same name in `.product-finance/assumptions.json`. It never replaces a value the person wrote. It names a jtbd segment that has no match, and does not add it. jtbd's willingness to pay is monthly, so the yearly value is 12 times it.
4. **No fallback to the old folder.** Result files began in plan 4 part A. No version of jtbd wrote `market-analysis.json` or `discovery-report.json` in either folder. So an old-folder read can find nothing that jtbd wrote, and decision 7's fallback does not apply to this read.
5. **A total check holds the rule.** The test `test_no_old_jtbd_output.py` (STORY-91) replaces the first check. It scans every product-finance file, the tests too, for a path of an old jtbd output folder. A line that names `market-analysis.json` or `discovery-report.json` after the word jtbd also fails.

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


## Amendment (STORY-91): every jtbd read is a read of the jtbd graph

**Date:** 2026-11-06.

**Context.** The jtbd plugin now keeps what it finds in a knowledge graph. It writes no result file into a folder of the project. The graph has a save code, `scripts/jtbd_graph.py`, and the jtbd plugin gives it as the read interface. A reader that opens an old result file finds nothing.

**Decision.**

1. **One script reads the graph.** `scripts/jtbd_read.py` finds the jtbd plugin, runs `pages` and `results` of its save code, writes the printed document into a file of `.product-finance/`, and prints one line. The prompt files run it and read that file. The tests give it a fixture graph.
2. **The script finds the save code with `scripts/probe-plugin.sh`.** The file is a byte copy of the file in the other plugins of this repository. It changes only with them. The script runs the save code with the Python that `PRODUCT_FINANCE_JTBD_PYTHON` names, else with `uv run`. The plugin gets no `dependencies` key, because the jtbd plugin is optional.
3. **A person's run** lists the `Run` pages and walks them from the newest `finished_at`. It reads the first run that holds a `customer_segment` or a `willingness_to_pay` result. When two such runs end at the same time, it names both and reads neither.
4. **A plugin run** keeps the `Run` pages with the `run_id` of the `inputs_from` entry and the `case` of the block. It reads the run only when exactly one page fits. It opens no `result_file` of the entry. It only names that path in `cites`.
5. **The file goes in a folder of this plugin.** The name follows `scripts/result_name.py`. The folder is `.product-finance/upstream/` in a person's run and `.product-finance/<run_id>/upstream/` in a plugin run. The folder is never `.product-finance/results/`, because a reader of that folder takes each file there for a result of this plugin.
6. **`wtp_source` and `--jtbd-data` name that file.** The "Found JTBD analysis" line names the `Run` page too. The calculator does not change.
7. **No graph, no plugin, no run.** The script prints `NO-JTBD: <reason>`, writes no file, and exits 0. A person's run of `discover` then sizes the market from the answers. A plugin run records the `customer_segment` gap. `setup` asks the Phase 4 question again, with only `manual` and `skip`.
8. **The script stays inside the project.** It writes only inside `.product-finance/`. It starts the save code with the argument list, never through a shell. The prompt files test each value before it goes into a command.
9. **The old paths are gone.** No file of this plugin names the old output folders of jtbd. `test_no_old_jtbd_output.py` holds the rule.

**Consequences.** A project with no jtbd graph, or with no jtbd plugin, gets a plain line and a run with no jtbd input. A project with a graph gets the segments and the prices of its newest fitting run. The CI job of this plugin installs the packages of the jtbd plugin, because the tests run its real save code.

## Amendment (v0.13.0, STORY-184): discover checks its result file

**Date:** 2026-11-06.

**Context.** In 2 of 5 person runs of `discover`, the result file had `"detail": null`. In 2 plugin runs whose answers gave no SAM share, it had a `market_size` with only `tam`. The checker refused each file, but only the tests ran the checker, and the release does not ship `tests/`.

**Decision.**

1. **The plugin ships the checker.** The checker and its four schema files are in `scripts/plugin_result/`, not in `tests/support/`. The five files are byte copies of the files in `plugins/business-case/schemas/`, with its PEP 723 block. This replaces decision 3 of the amendment (v0.11.0) for the checker. The Charter schemas stay in `schemas/agentic-pricing/`.
2. **discover checks its result file.** After the Write, the run runs `plugin_result_check.py result` on the file. On a refusal, it corrects the named keys and writes the file once more. On a second refusal, it stops and names each error. It never reports a refused file as a pass.
3. **A person's run writes no `detail` key.** Each writer says so, and no example of a person's run has `detail`.
4. **A partial market size is a gap.** A `market_size` result needs `tam`, `sam` and `som`. With no value for one of them, the run writes no `market_size` result and records a gap that names each input it lacks, as decision 1 of the amendment (v0.11.0) says for each figure.

**Consequences.** A file that the checker refuses does not pass as a result: the run corrects it once, or the reply names the errors. The other four writers do not run the check yet.
