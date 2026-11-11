---
name: archetype-baseline-telemetry
description: Use when you have an archetype-cost-samples.json file (raw cost-per-interaction samples for each archetype) and need the telemetry-derived baseline file .aiml/archetype-baseline-telemetry.json. Computes the median baseline for each archetype. The pricing plugin reads the result.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/archetype_baseline_emitter.py *), Edit(/.aiml/**)
---

# /aiml:archetype-baseline-telemetry

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

Turns raw cost-per-interaction samples into a baseline for each archetype.

## Invocation

```
/aiml:archetype-baseline-telemetry --input <path-to-archetype-cost-samples.json> [--out <output-path>]
```

## Steps

1. Read the path after `--input` in the argument text. If there is none, ask the person for the path with `AskUserQuestion`.
2. Run the emitter first, before you start any agent. Run this command on its own, with no other command and no echo. Put the path in single quotes, and write each `'` inside the path as `'\''`. The emitter checks the input file, so check it with no other command, because the grant allows this script only, and a session refuses any other command. The Bash tool reports a non-zero exit code.

   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/archetype_baseline_emitter.py --input '<input_path>' --out .aiml/archetype-baseline-telemetry.json`

3. If the exit code is not 0, show the lines on standard error to the person. Start no agent, write no file, and stop.
4. Start the agent with the `Agent` tool in the foreground (`subagent_type: aiml:archetype-baseline-telemetry-agent`, `run_in_background: false`). Wait for it to end. The prompt gives the field `output_path`: `.aiml/archetype-baseline-telemetry.json`.
5. Read the last line of the agent reply.
   - `DONE: aiml`: show the path of `.aiml/archetype-baseline-telemetry.json` and the one-line summary from `.aiml/handoff.json`.
   - Any other last line: show the reply to the person, and stop.

## What it does

Reads an `archetype-cost-samples.json` v1.0.0 file (raw `cost_samples[]` for each archetype, the measurement window, and the telemetry source). Computes the median baseline cost-per-interaction for each archetype. Writes `.aiml/archetype-baseline-telemetry.json`. The schemas are in the folder `schemas/` of the plugin: `archetype-cost-samples.schema.json` (input) and `archetype-baseline-telemetry.schema.json` (output).

## Result

`.aiml/archetype-baseline-telemetry.json`. The field `baselines` is `{}` when no archetype is present. The file is always written when the emitter exits 0. The pricing plugin reads this file and uses its values in place of its inferred baselines. Without the file, pricing uses the inferred baselines.

## Agent

`archetype-baseline-telemetry-agent` (haiku, deterministic). It has no `Bash` tool. This skill runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/archetype_baseline_emitter.py` (step 2); the agent reads the output and writes the handoff. `uv` must be installed.
