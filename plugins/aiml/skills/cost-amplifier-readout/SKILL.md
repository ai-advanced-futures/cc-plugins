---
name: cost-amplifier-readout
description: Use when you have measured P75 and P95 multipliers for each cost amplifier from production (Datadog, Grafana, wandb, Trackio or manual logs). Produces .aiml/cost-amplifier-readout.json in telemetry-enriched mode from an amplifier-telemetry-input.json file.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cost_amplifier_readout_emitter.py *), Edit(/.aiml/**)
---

# /aiml:cost-amplifier-readout

Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background, because an agent that runs in the background returns in a new turn that does not have the `allowed-tools` of this skill, and the next step is then refused.

Produces a telemetry-enriched cost-amplifier readout.

## When to use

Use it when you have **measured** per-amplifier P75 and P95 multipliers from your production environment. If you have only framework defaults, use the `rule_of_thumb` mode of the pricing plugin.

## Invocation

```
/aiml:cost-amplifier-readout <path-to-amplifier-telemetry-input.json>
```

## Steps

1. Read the path in the argument text. If there is none, ask the person for the path with `AskUserQuestion`.
2. Run the emitter first, before you start any agent. Run this command on its own, with no other command and no echo. Put the path in single quotes, and write each `'` inside the path as `'\''`. The emitter checks the input file, so check it with no other command, because the grant allows this script only, and a session refuses any other command. The Bash tool reports a non-zero exit code.

   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cost_amplifier_readout_emitter.py --input '<input_path>' --out .aiml/cost-amplifier-readout.json --verbose`

3. If the exit code is not 0, show the lines on standard error to the person. Start no agent, write no file, and stop.
4. Start the agent with the `Agent` tool in the foreground (`subagent_type: aiml:cost-amplifier-readout-agent`, `run_in_background: false`). Wait for it to end. The prompt gives the field `output_path`: `.aiml/cost-amplifier-readout.json`.
5. Read the last line of the agent reply.
   - `DONE: aiml`: show the path of `.aiml/cost-amplifier-readout.json` and the one-line summary from `.aiml/handoff.json`.
   - Any other last line: show the reply to the person, and stop.

## Input format

See `schemas/amplifier-telemetry-input.schema.json` in the plugin folder. A small sample is `tests/fixtures/agentic-pricing/sample-input.json` in the same folder.

## Result

- `.aiml/cost-amplifier-readout.json`: the readout, in telemetry-enriched mode. The schema is `schemas/cost-amplifier-readout.schema.json`.
- `.aiml/handoff.json`: the handoff with the composite summary.

## Agent

`cost-amplifier-readout-agent` (haiku, deterministic). It has no `Bash` tool. This skill runs `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cost_amplifier_readout_emitter.py` (step 2); the agent reads the output and writes the handoff. `uv` must be installed.

## Related

- The `/pricing:cost-amplifier-readout` skill of the pricing plugin produces the `rule_of_thumb` mode from framework defaults.
- The two files can exist together. A reader picks one, based on the data it has.
