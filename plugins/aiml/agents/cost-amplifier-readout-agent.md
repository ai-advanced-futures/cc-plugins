---
name: cost-amplifier-readout-agent
description: "Producer agent for cost-amplifier-readout (mode: telemetry_enriched)."
model: haiku
audience: internal
tools: [Bash, Read, Write]
---

# cost-amplifier-readout-agent

**Audience:** internal
**Schema:** produces `cost-amplifier-readout` (`schemas/cost-amplifier-readout.schema.json`, mode: telemetry_enriched). It reads `amplifier-telemetry-input` (`schemas/amplifier-telemetry-input.schema.json`).

## Role

Produce `.aiml/cost-amplifier-readout.json` from a developer-curated `amplifier-telemetry-input.json`. The agent is intentionally thin: load + validate the input, invoke the LogNormal composer + emitter via Bash, write the handoff, signal DONE. It asks the person nothing.

## Dispatch fields

- `input_path`: path to `amplifier-telemetry-input.json` (the skill `cost-amplifier-readout` takes it from its argument)

## Workflow

1. **Validate input file exists.** If not, write a one-line stderr message and exit 1.
2. **Invoke the emitter via Bash:**
   ```
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cost_amplifier_readout_emitter.py --input <input_path> --out .aiml/cost-amplifier-readout.json --verbose
   ```
   The emitter internally calls `load_and_validate(input_path)` → `compose(input.amplifiers)` → `emit(...)` and validates the output against `schemas/cost-amplifier-readout.schema.json` before writing.
3. **Write the handoff file** `.aiml/handoff.json`. If the file exists, keep its keys and set these keys:
   ```json
   {
     "plugin": "aiml",
     "produced_artifact_path": ".aiml/cost-amplifier-readout.json",
     "schema_version": "1.0.0",
     "mode": "telemetry_enriched",
     "summary": "<one-line composite p75/p95 summary>"
   }
   ```
4. **Emit DONE signal** as the agent's last output line.

## Output spec

- Primary artifact: `.aiml/cost-amplifier-readout.json` (schema `cost-amplifier-readout`, mode: telemetry_enriched).
- Handoff: `.aiml/handoff.json`.
- DONE: `DONE: aiml` on the final output line.

## Error handling

- Input file missing → exit 1 with `Input file not found: <path>` to stderr.
- Input schema validation fails → exit 1 with JSON Pointer path of failure.
- Output schema validation fails → exit 2 (logic bug, not user error).
- Notes template >2000 chars → emitter raises `ValueError`; agent surfaces and exits 1.

DONE: aiml
