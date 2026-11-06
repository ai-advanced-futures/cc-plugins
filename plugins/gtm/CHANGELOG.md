# Changelog

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
