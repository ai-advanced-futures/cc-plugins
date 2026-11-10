# Changelog

All notable changes to the pricing plugin will be documented in this file.

The first heading is the version in `.claude-plugin/plugin.json`. A test checks that they agree.

## 1.13.4

- `probe-plugin.sh` finds another plugin in the Claude config folder: `$CLAUDE_CONFIG_DIR` when it is set, else `~/.claude`. Before, a session with the variable set found no install of another plugin, and the step that needed it gave no result and no error (STORY-281).

## 1.13.3

- The skills `audit`, `package` and `value-metric` have the grant `Edit(/.pricing/**)`, because each of them writes a file in the output folder. The test `tests/unit/test_output_grant.py` now looks for the path `.pricing/` in each skill, and not for the word `Write` (STORY-168, found in the review of PR 1103).

## 1.13.2

- The file `caller-grants.json` and a block in the README name the grants that the session which dispatches `price-runner` must give: the 3 scripts, the output folder, the plugin files, and the answers file. `tests/unit/test_caller_grants.py` checks the list (STORY-168).
- The `price` skill has the grant `Edit(/.pricing/**)`, so a run can write its output folder.

## 1.13.1

- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).

## 1.13.0

- Pricing reads the jtbd graph and the competitive-intelligence graph. The new script `scripts/brain_read.py` has the operations `wtp`, `outcomes`, `moats` and `status`. It calls the save script of the writer plugin and reads the JSON that it prints. It reads no page file, and it never runs a save script that the opened project holds. A writer plugin that is installed only in the project folder (`.claude/plugins/<name>`) is not found (STORY-90, ADR-011).
- The Path A gate reads the run that `inputs_from` names with `brain_read.py wtp --run-id --case`. A person's run takes the newest run that holds a willingness to pay and asks the person to confirm it. A price cites a snapshot that `wtp --out` writes under `.pricing/`.
- When a graph is not there, pricing shows a plain message and goes on with no input (Path B, or no moat context). The gap texts are `jtbd run_id or case not in the jtbd graph` and `jtbd graph missing or unreadable`.
- The session-start hook runs `brain_read.py status`. It prints a note only for a graph that holds usable data.
- The reads of the value-metric and package skills, the auditor, and the moats step use `brain_read.py`. The files that the writer plugins wrote before the graphs are not read any more. The script that found the newest jtbd result is removed.
- New file `scripts/probe-plugin.sh`, a copy of the file in the other plugins.
- `automated: true` skips only a question. A run of `/pricing:price` with no block still runs `brain_read.py wtp` (Step 2) and `brain_read.py moats` (Step 5), also when the inputs already give the competitors. A live run showed that a skill with `automated: true` ran neither call.

## 1.12.2

- The `run-id` form of `scripts/result_name.py` and the `run_id` of a file name use the `_RUN_ID` pattern of the result-file checker: 4 to 64 of a-z, 0-9 and `-`, with a-z or 0-9 first and last. A value such as `Run_1`, `ab` or `a..b` now exits 2, as the checker refuses it (STORY-164). The command part keeps the plain-name rule.
- A new test compares the pattern of the script with the pattern of the checker, and compares the answers of the 2 for 5 values.

## 1.12.1

- A person's run of pricing states no confirmation that the person did not give. The session-start hook only says that a jtbd result exists. A confirmation in a dispatch prompt changes nothing: the pricer reads the file, names it in its reply, and uses Path B (STORY-171).
- The pricer run as itself writes no result file. Only a run of `pricing:price` writes one.

## 1.12.0

- The pricing commands quote `run_id` and the JSON arguments. The pricer checks the `run_id` as the runner does, and `price-runner.md` quotes the plugin path. Each JSON argument has the rule to write each `'` as `'\''` (STORY-160).
- The session-start hook says that a jtbd result exists. It prints no file name.
- When the calculator cannot run, the run stops. It computes no figure, writes no price file, writes the result file with the gap `Pricing calculator`, and ends with `BLOCKED: pricing calculator <function>: <reason>`. The old rule to work the figure out by hand is gone (STORY-157).
- A new script finds the newest jtbd result in the main conversation. A dispatched agent reads only the file that `inputs_from` or the new dispatch field `jtbd_result` names, and lists no folder. It takes `jtbd_result` only as a plain name in that folder, with no `..`; else it records a gap and uses Path B.

## 1.11.0

- This plugin now lives in the marketplace `cc-plugins`. It ports the private plugin at version 1.10.1.
- The agents run without a person. Only the skills ask questions. When an agent has no value for a required input, it writes `.pricing/open-questions.json` and ends with `DONE: pricing OPEN: .pricing/open-questions.json`.
- Scripts run with `uv run`. Each script holds its own list of packages.
- The files that the plugin needs from the old repository root now live in the plugin: the schemas in `schemas/agentic-pricing/`, the vocabulary checker in `vocabulary_linter/`, and the result-file check in `tests/support/`.
- The plugin writes no handoff file for another system. Each agent writes its own files in `.pricing/`.
- The agents and skills pass `/prompt:revise`: 0 findings and 222 instructions in the 16 files (before the review: 234 instructions and 39 findings).

## v1.6.0 — 2026-05-30

- **Charter §17 publication gate.** New `pricing/lib/charter_publication_gate.py` scanner and a test that runs in CI. Forbidden patterns: `multiplicative score`, `pricing power index`, `pricing risk index`, `single numeric pricing risk` (literal, not case-sensitive).
- **`check42-allow:` directive.** A match on the same line or the line before is allowed when the directive gives a reason. A directive with no reason is a violation. A 4-step parser handles trailing comment-close markers (`-->`, `*/`, `"""`).
- **ADR-008.** 8 numbered decisions: the gate belongs to the pricing plugin, the parser for Contract A, and why the patterns are long.
- **Charter v1.1.0 to v1.2.0.** New §17, a clearer §15.1, and a §15.5 entry for v1.2.0.
- **pyproject.toml.** A test (`test_pricing_v1_6_0_lockstep`) checks that the version in `pyproject.toml` agrees with `plugin.json`.
- `test_charter_contracts.py` expects 8 schemas. `CHARTER_MATRIX` has `amplifier-telemetry-input`, as Charter v1.1.0 says.
