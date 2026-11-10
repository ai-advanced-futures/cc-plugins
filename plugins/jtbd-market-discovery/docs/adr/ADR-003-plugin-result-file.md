# ADR-003: Adopt the plugin result file

**Status:** Accepted
**Date:** 2026-10-31
**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Adopts:** the plugin result standard, `docs/plugin-result/PLUGIN_RESULT_FILE.md`

---

## Context

Business-case reads what the producer plugins found. Until now, each plugin wrote its own files in its own shape, and the reader could not tell a measured value from a built-in constant. The standard `docs/plugin-result/PLUGIN_RESULT_FILE.md` fixes one shape, the rules R1 to R7, and the invocation block a coach uses. Two jtbd-market-discovery commands are on its list of adopting commands: `jtbd-market-discovery:discover` and `jtbd-market-discovery:wtp-check`.

Three facts of this plugin shaped the adoption:

1. A discover run is many agents, and it keeps its state in a session folder. The eight files that `skills/discover/SKILL.md` promises sit at the folder root, and each run overwrites them.
2. `wtp-check` builds on an earlier discover run: it needs that run's `p7.json` (customer value) and `p8.json` (segments).
3. `wtp-validator` serves two masters. It is Phase 9 of discover, and it is the agent named by `skills/wtp-check/procedure.md`.

## Decision

1. **Adopt the standard.** Both commands write one result file at the end of every run, a partial or halted one too (R1). `agents/output-assembler.md` writes it for `discover`, and `agents/wtp-validator.md` holds the rules for `wtp-check`. `result-file.json` names the writers and the defaults registry. `questions/discover.json` and `questions/wtp-check.json` list the inputs. 2026-11 (STORY-113, D-056): the result file is `result.json` in the session folder, and no file stays beside the graph.

2. **A session per run.** A coach run with a `run_id` uses the session `.jtbd-market-discovery/<run_id>/` and never another one. `jtbd_state.py select` decides, so the rule lives in code and not in each agent's text. A person's run without a `run_id` resumes only a person's own unfinished session, one with no `run_id` and no `case`, and otherwise starts a new one.

3. **wtp-check has its own session.** With a block, `wtp-check` reads the upstream session named by the `jtbd-market-discovery` entry of `inputs_from`. It does so only when four values match: the session's `state.json` `run_id`, the upstream result file's `run.run_id`, the session's `case` and that result file's `run.case`. It writes `p9.json` into its own session, `.jtbd-market-discovery/<its run_id>/`, and never into the upstream one. When the match fails, it records the gap `"upstream jtbd run_id or case does not match inputs_from"` and writes no willingness-to-pay result. A person's `wtp-check` reads the newest finished session, one with no `run_id` and no `case` that holds `p7.json` and `p8.json`. It writes `p9.json` into a new folder that `jtbd_state.py wtp-folder` makes, and when no session has finished it halts and writes its result file.

4. **wtp-check's command scope.** The `## Plugin-run block` of the skill `skills/wtp-check/SKILL.md` applies only to a block whose `command` is `jtbd-market-discovery:wtp-check`. Started as Phase 9 of discover, wtp-validator receives no block, uses the `session_dir` the `discover` skill passes, and writes no result file: output-assembler writes that run's draft. The route of `wtp-check` is the skill itself, which runs the steps of the procedure in the main conversation, starts no agent, and runs `jtbd_state.py place-result` on the draft that the `## Result file` section of wtp-validator describes. The runner agent `wtp-check-runner` is gone (v1.9.0), because no agent has `Bash`.

5. **`detail` points into the session.** Each result's `detail` is the phase file in the run's own session, such as `.jtbd-market-discovery/acme-0006/p9.json`. The files at the folder root are overwritten by the next run, so a `detail` that named them would point at another run's data. A resumed old session keeps its own path. The result file goes to the new folder, and its `detail` names that old session's path under `.jtbd/`.

6. **Defaults are recorded where they are applied.** Each phase agent records how each input was settled under `assumption_sources` in its phase file: `person`, `recommended`, `asked`, `model` or `default`. output-assembler turns those into sources and markers. A missing `market_area` is not a default: an automated run halts, and its result file records the gap.

## Consequences

- A coach can run either command with answers and read one checked file back. Task 9 (pricing) reads the `willingness_to_pay` and `customer_value` results of `wtp-check`.
- `tests/unit/test_plugin_result_contract.py` holds both commands to the standard through `scripts/plugin_result_conformance.py`. The written fixtures in `tests/fixtures/plugin-result/` are real result files from harness runs.
- The phase agents gained one more duty: to record `assumption_sources`. A phase agent that forgets it leaves the assembler to guess, and the reviewer of a written fixture is the check on that.
- `segment_count = 4` decides the count only when the elbow and silhouette results do not move it. In a run where they do, the marker is absent, and that is correct.
