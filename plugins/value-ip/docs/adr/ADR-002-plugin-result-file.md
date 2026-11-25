# ADR-002: Adopt the plugin result file and the mission-control block

**Status:** Accepted
**Date:** 2026-11-01
**Author:** Luis F. Amadeo
**Adopts:** repo ADR-001, `docs/standards/adr/ADR-001-plugin-result-file.md`
**Plugin:** value-ip v1.3.0

---

## Context

Business-case reads what the producer plugins found. Until now, `value-ip:analyze` wrote a scorecard and a devil's advocate report to `output/`, which the next run overwrites, and no file told a reader what the debate found or what it rested on. value-ip also had no `mission_control_integration` block, so mission-control could not dispatch it. The repo standard `docs/standards/PLUGIN_RESULT_FILE.md` fixes one result shape, the rules R1 to R7 and the invocation block a coach uses. `value-ip:analyze` is on its list of adopting commands.

Four facts shaped the adoption:

1. The spike (`docs/superpowers/specs/2026-10-31-plan-4-part-a-spike.md`, "Recorded routes") dispatched `agents/synthesizer.md`, the agent the command names. It wrote no state file and dispatched no framework agent: it did not run the command. A thin runner that read the command file dispatched the four framework agents (two agent layers).
2. The command's only input is the artifact. With no artifact named, `config/pipeline-defaults.json` (`auto_answers.artifact_selection`) makes the run auto-detect one in the working directory.
3. The debate's findings are judgements by the model. No customer record and no published source stands behind them.
4. `framework_failure_policy` `skip_and_continue` lets a run finish with fewer than four frameworks.

## Decision

1. **Adopt the standard.** `value-ip:analyze` writes one result file to `.value-ip/results/` at the end of every run, a halt and a partial run too, and a person's run too (R1). `result-file.json` names the writer, `agents/synthesizer.md`, and the defaults registry. `questions/analyze.json` lists the one input, `artifact`.
2. **The route is a thin runner.** `agents/analyze-runner.md` is the route a coach dispatches with the `plugin-run` block. It reads the start time and `plugin.json` first, reads the command file, dispatches the agents the command names, and tells each of them to ask nothing. It never writes the result file itself. `release.json` `preferred_invocation` is `value-ip:analyze-runner`.
3. **One writer, reached from both routes.** The synthesizer's `## Result file` section is the only writer text. A person's `/value-ip:analyze` reaches it through the command's Step 5, and a halt through Step 2; the runner reaches it through the same steps. The section is scoped to `value-ip:analyze`: dispatched for `/value-ip:guard` or `/value-ip:challenge`, the synthesizer writes no result file (R6).
4. **The block wins over `auto_mode`.** When the dispatch holds a `plugin-run` block, the run behaves as if `auto_mode` were `true`, whatever the config says. `run.mode` is `automated` only when the block is present.
5. **Results and their grade.** One `differentiator` result for each IP claim that survived the debate, and one `right_to_win` result from the overall verdict. Each holds a `model` source, and its `method` names the frameworks behind it. No result is called validated, measured or actual. The verdict rests on a mean the model computed, so its `method` ends with the standard sentence, and the command states the one formula.
6. **Defaults and gaps.** The registry holds one entry: an auto-detected artifact is a `default` source with the marker `artifact = the first artifact auto-detected in the working directory`. It is a rule, so the question has no `default` value. Every other config leaf is ruled not a default in `not_defaults`. Each skipped framework is a gap; so is a debate in which no IP claim survived.
7. **Run folder.** In a plugin run, every working file goes in `.value-ip/<run_id>/`: `.value-ip-state.json`, `debate-context/` and `output/`, so a coach run never reads another run's files. Each agent writes inside the work folder its dispatch names. A person's run keeps its working files in `.value-ip/<started_at as YYYYMMDDTHHMMSSZ>/`, never the project root, and never reuses a work folder another run left behind. The command builds `ran` and `skipped` lists from this run's dispatch results, and the synthesizer reads and names only the frameworks in `ran`. A plugin run reads no other plugin's files and auto-detects no artifact inside a dot-folder. A debate below its minimum rounds is recorded as first-analysis scores, a gap and a `partial` handoff.
8. **Mission-control.** The block declares `dpo_reporting_protocol` `file-based`, `done_signal` `DONE: value-ip` and `handoff_file` `.value-ip/value-ip-handoff.json`. After the result file, the synthesizer writes `value-ip-handoff.json` with the plugin, version, result file and status. The runner prints the bare line `DONE: value-ip` last, after the synthesizer returns.
9. **Earlier runs.** A run reads an earlier run's files only through `inputs_from`. `value-ip:analyze` reads none today.

## Consequences

- A coach can run the debate, and read its verdict and its surviving claims, from one file per run.
- The debate coordinator writes each round's responses, and `debate_rounds` is the round count it reports; `method` attributes the scores to the debate coordinator's record. Framework agents' round dispatch at depth 3 has not been observed.
- The command file now passes each framework agent the rooted path of its lens file, and the synthesizer reads its method file by the rooted path. A live run showed that no framework agent found its lens file from the working directory.
- The command no longer offers an inline `python3 -c` call to the detection scripts. The run reads the scripts and applies their logic.
- Tests: `tests/unit/test_plugin_result_contract.py` holds the standard's checks and pins the sentences above. The written fixtures in `tests/fixtures/plugin-result/` are real results of harness runs.
