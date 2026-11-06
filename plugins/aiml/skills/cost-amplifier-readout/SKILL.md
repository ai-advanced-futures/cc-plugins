---
name: cost-amplifier-readout
description: Use when you have measured P75 and P95 multipliers for each cost amplifier from production (Datadog, Grafana, wandb, Trackio or manual logs). Produces .aiml/cost-amplifier-readout.json in telemetry-enriched mode from an amplifier-telemetry-input.json file.
---

# /aiml:cost-amplifier-readout

Produces a telemetry-enriched cost-amplifier readout.

## When to use

Use it when you have **measured** per-amplifier P75 and P95 multipliers from your production environment. If you have only framework defaults, use the `rule_of_thumb` mode of the pricing plugin.

## Invocation

```
/aiml:cost-amplifier-readout <path-to-amplifier-telemetry-input.json>
```

## Steps

1. Read the path in the argument text. If there is none, ask the person for the path with `AskUserQuestion`.
2. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:cost-amplifier-readout-agent`. The prompt gives the field `input_path`.
3. Read the last line of the agent reply.
   - `DONE: aiml`: show the path of `.aiml/cost-amplifier-readout.json` and the one-line summary from `.aiml/handoff.json`.
   - Any other last line: show the reply to the person, and stop.

## Input format

See `schemas/amplifier-telemetry-input.schema.json` in the plugin folder. A small sample is `tests/fixtures/agentic-pricing/sample-input.json` in the same folder.

## Result

- `.aiml/cost-amplifier-readout.json`: the readout, in telemetry-enriched mode. The schema is `schemas/cost-amplifier-readout.schema.json`.
- `.aiml/handoff.json`: the handoff with the composite summary.

## Agent

`cost-amplifier-readout-agent` (haiku, deterministic). It runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cost_amplifier_readout_emitter.py`. `uv` must be installed.

## Related

- The `/pricing:cost-amplifier-readout` skill of the pricing plugin produces the `rule_of_thumb` mode from framework defaults.
- The two files can exist together. A reader picks one, based on the data it has.
