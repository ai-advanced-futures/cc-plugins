---
name: archetype-baseline-telemetry
description: Use when you have an archetype-cost-samples.json file (raw cost-per-interaction samples for each archetype) and need the telemetry-derived baseline file .aiml/archetype-baseline-telemetry.json. Computes the median baseline for each archetype. The pricing plugin reads the result.
---

# /aiml:archetype-baseline-telemetry

Turns raw cost-per-interaction samples into a baseline for each archetype.

## Invocation

```
/aiml:archetype-baseline-telemetry --input <path-to-archetype-cost-samples.json> [--out <output-path>]
```

## Steps

1. Read the path after `--input` in the argument text. If there is none, ask the person for the path with `AskUserQuestion`.
2. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:archetype-baseline-telemetry-agent`. The prompt gives the field `input_path`.
3. Read the last line of the agent reply.
   - `DONE: aiml`: show the path of `.aiml/archetype-baseline-telemetry.json` and the one-line summary from `.aiml/handoff.json`.
   - Any other last line: show the reply to the person, and stop.

## What it does

Reads an `archetype-cost-samples.json` v1.0.0 file (raw `cost_samples[]` for each archetype, the measurement window, and the telemetry source). Computes the median baseline cost-per-interaction for each archetype. Writes `.aiml/archetype-baseline-telemetry.json`. The schemas are in the folder `schemas/` of the plugin: `archetype-cost-samples.schema.json` (input) and `archetype-baseline-telemetry.schema.json` (output).

## Result

`.aiml/archetype-baseline-telemetry.json`. The field `baselines` is `{}` when no archetype is present. The file is always written. The pricing plugin reads this file and uses its values in place of its inferred baselines. Without the file, pricing uses the inferred baselines.

## Agent

`archetype-baseline-telemetry-agent` (haiku, deterministic). It runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/archetype_baseline_emitter.py`. `uv` must be installed.
