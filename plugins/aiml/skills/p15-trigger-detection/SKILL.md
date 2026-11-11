---
name: p15-trigger-detection
description: Use when you have amplifier and quality telemetry (an amplifier-telemetry-input.json file) and need to detect Pattern P15 trigger events (a cost-rate breach, a quality-floor breach, or both). Produces .aiml/p15-trigger-event.json for the gtm and pricing plugins.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/p15_trigger_emitter.py *), Edit(/.aiml/**)
---

# /aiml:p15-trigger-detection

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

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
2. Run the emitter first, before you start any agent. Run this command on its own, with no other command and no echo. Put each value in single quotes, and write each `'` inside a value as `'\''`. Leave out an option that has no value. The emitter checks the input file, so check it with no other command, because the grant allows this script only, and a session refuses any other command. The Bash tool reports a non-zero exit code.

   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/p15_trigger_emitter.py --input '<input_path>' [--history '<history_path>'] [--threshold-pct '<N>'] [--cap-pct '<N>'] [--quality-floor-target '<metric_id=value>' ...] --output .aiml/p15-trigger-event.json`

3. If the exit code is not 0, show the lines on standard error to the person. Start no agent, write no file, and stop.
4. Start the agent with the `Agent` tool in the foreground (`subagent_type: aiml:p15-trigger-detector-agent`, `run_in_background: false`). Wait for it to end. The prompt gives the field `output_path`: `.aiml/p15-trigger-event.json`.
5. Read the last line of the agent reply.
   - `DONE: aiml`: show the path of `.aiml/p15-trigger-event.json` and the one-line summary from `.aiml/handoff.json`.
   - Any other last line: show the reply to the person, and stop.

## What it does

Reads an `amplifier-telemetry-input.json` v1.1.0 file (cost amplifiers, optional `quality_metrics[]`, and `contractual_thresholds`). Optionally reads a history file (an array of v1.1.0 inputs for the cost-rate baseline). Resolves each threshold in this order: the command line, the input top level, the entry itself, then an error. Writes `.aiml/p15-trigger-event.json`. The schemas are `schemas/amplifier-telemetry-input.schema.json` and `schemas/p15-trigger-event.schema.json` in the plugin folder.

## Result

`.aiml/p15-trigger-event.json`. The field `events` is `[]` when there is no breach. The key `detection_notes` is absent when it is empty.

## Agent

`p15-trigger-detector-agent` (haiku, deterministic). It has no `Bash` tool. This skill runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/p15_trigger_emitter.py` (step 2); the agent reads the output and writes the handoff. `uv` must be installed.
