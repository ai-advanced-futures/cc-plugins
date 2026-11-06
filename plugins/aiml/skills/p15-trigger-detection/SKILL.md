---
name: p15-trigger-detection
description: Use when you have amplifier and quality telemetry (an amplifier-telemetry-input.json file) and need to detect Pattern P15 trigger events (a cost-rate breach, a quality-floor breach, or both). Produces .aiml/p15-trigger-event.json for the gtm and pricing plugins.
---

# /aiml:p15-trigger-detection

Detects Pattern P15 trigger events from telemetry.

## Invocation

```
/aiml:p15-trigger-detection \
  --input <path-to-amplifier-telemetry-input.json> \
  [--history <path-to-history.json>] \
  [--output <output-path>] \
  [--threshold-pct N] \
  [--cap-pct M] \
  [--quality-floor-target metric_id=value ...]
```

## Steps

1. Read the options in the argument text. If there is no `--input`, ask the person for the path with `AskUserQuestion`.
2. Dispatch the agent with the `Agent` tool: `subagent_type: aiml:p15-trigger-detector-agent`. The prompt gives the fields `input_path`, `history_path`, `threshold_pct`, `cap_pct` and `quality_floor_targets`. Leave out a field that has no value.
3. Read the last line of the agent reply.
   - `DONE: aiml`: show the path of `.aiml/p15-trigger-event.json` and the one-line summary from `.aiml/handoff.json`.
   - Any other last line: show the reply to the person, and stop.

## What it does

Reads an `amplifier-telemetry-input.json` v1.1.0 file (cost amplifiers, optional `quality_metrics[]`, and `contractual_thresholds`). Optionally reads a history file (an array of v1.1.0 inputs for the cost-rate baseline). Resolves each threshold in this order: the command line, the input top level, the entry itself, then an error. Writes `.aiml/p15-trigger-event.json`. The schemas are `schemas/amplifier-telemetry-input.schema.json` and `schemas/p15-trigger-event.schema.json` in the plugin folder.

## Result

`.aiml/p15-trigger-event.json` (or the `--output` path). The field `events` is `[]` when there is no breach. The key `detection_notes` is absent when it is empty.

## Agent

`p15-trigger-detector-agent` (haiku, deterministic). It runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/p15_trigger_emitter.py`. `uv` must be installed.
