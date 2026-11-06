---
name: sales-comp-gate-review
description: Run the Phase-3 sales-comp precondition gate. Ask the person for the 5 preconditions, emit a deterministic proceed, pause, or re_pause cliff recommendation, and report the result.
audience: internal
---

# Sales-Comp Gate Review

This skill runs in the main conversation. A dispatched agent cannot ask the person, but this skill can.

## Steps

1. Read `${CLAUDE_PLUGIN_ROOT}/agents/sales-comp-gate-agent.md` (the `gtm:sales-comp-gate-agent` agent). Follow its workflow in this conversation.
2. Ask the person for the 5 Phase-3 preconditions with `AskUserQuestion`:
   `ae_comp_impact_modeled`, `top_3_quota_retention_completed`, `hire_back_runway_filled`, `competitor_comp_benchmarked`, `executive_sponsor_named`.
   Also ask for `top_quintile_at_risk_pct`, `prior_recommendation`, and `re_pause_trigger_fired`.
3. Write the answers to `.gtm/sales-comp-gate-input.json`.
4. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/sales_comp_gate_emitter.py --input .gtm/sales-comp-gate-input.json --output-dir .`. The emitter calls `classify_cliff` of `${CLAUDE_PLUGIN_ROOT}/scripts/sales_comp_gate.py`. It writes `.gtm/sales-comp-precondition-gate.json` and `.gtm/sales-comp-gate-handoff.json`. The first file follows `${CLAUDE_PLUGIN_ROOT}/schemas/sales-comp-precondition-gate.schema.json`. When the command exits with a code that is not 0, show its error output to the person and stop. Do not read the handoff file.
5. Read `status` and `cliff_recommendation` in `.gtm/sales-comp-gate-handoff.json`. Tell the person both values and the reasons.
6. If a `p15-trigger-event.json` file is present, hand off to the skill `agentic-pricing-comms` to draft the mapped comms.

## The deterministic rule

The gate code applies this rule. The model does not judge it.
- prior `proceed` + `re_pause_trigger_fired` → `re_pause`
- any precondition unmet OR `top_quintile_at_risk_pct` > 15.0 → `pause`
- otherwise → `proceed`
