---
description: "Produce cost-coverage-readout Charter artifact (audience: internal) from pricing outputs + company financials"
argument-hint: "diagnosis_path=<path> amplifier_path=<path> gm_pct=<n> nrr_delta_pct=<n> forecast_variance_pct=<n> cost_per_interaction_baseline=<n> headline_price=<n> engagement_id=<uuid>"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# /product-finance:cost-coverage

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `uv run python`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because only the plugin's own scripts are tested.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

## Every run

0. **Read the start time and the version** — run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and keep its output as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. Never type a time yourself, because a typed time is a guess and not the time of the run. The result file needs both.
1. Do the work the rest of this file describes.
2. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/cost-coverage-agent.md` with the Read tool and follow its `## Result file` section, in every run.

Charter sub-spec 3 dispatcher. Produces a cost-coverage-readout.json handoff artifact (audience: internal) from:
- `agentic-pricing-diagnosis.json` (from pricing — provides archetype + arr_band)
- `cost-amplifier-readout.json` (from pricing — provides composite_p75)
- Company financial parameters (gm_pct, nrr_delta_pct, forecast_variance_pct, cost_per_interaction_baseline, headline_price)

## Required Inputs (from `$ARGUMENTS`, from the caller, or from the person)

| Field | Type | Source |
|---|---|---|
| `diagnosis_path` | path | pricing's agentic-pricing-diagnosis.json |
| `amplifier_path` | path | pricing's cost-amplifier-readout.json (audience must be "internal") |
| `gm_pct` | float | company financials |
| `nrr_delta_pct` | float | company financials |
| `forecast_variance_pct` | float | company financials |
| `cost_per_interaction_baseline` | float (>0) | P50 effective cost per interaction |
| `headline_price` | float (>0) | vendor's per-interaction billing price |
| `engagement_id` | UUID string | the caller or the person |
| `produced_at` | RFC3339 datetime | the caller or the person |

## Asking in a person's run

When a person runs the command and a field of the table is missing, ask for it, one field at a time. `produced_at` is not asked: it is the time of the run.

- AskUserQuestion [q: diagnosis_path]: where is pricing's `agentic-pricing-diagnosis.json` for this engagement?
- AskUserQuestion [q: amplifier_path]: where is pricing's `cost-amplifier-readout.json` (audience `internal`)?
- AskUserQuestion [q: gm_pct]: what is the company's gross margin, in percent?
- AskUserQuestion [q: nrr_delta_pct]: what is the change in net revenue retention, in percentage points?
- AskUserQuestion [q: forecast_variance_pct]: what is the revenue forecast variance, in percent?
- AskUserQuestion [q: cost_per_interaction_baseline]: what is the median effective cost of one interaction?
- AskUserQuestion [q: headline_price]: what price does the vendor bill per interaction?
- AskUserQuestion [q: engagement_id]: what is the engagement id, a lowercase UUID?

No field has a default, so the command fills in no value.

## Output

`.product-finance/{engagement_id}/cost-coverage-readout.json` — Charter §7.6 conformant.

## Agent Dispatch

Read `${CLAUDE_PLUGIN_ROOT}/agents/cost-coverage-agent.md` and follow it in this session. The agent asks nothing, so a person's run and a plugin run are the same run. Then do step 2 of `## Every run`.
