---
name: archetype-baseline-telemetry-agent
description: "Producer agent for archetype-baseline-telemetry (telemetry-derived baseline cost-per-interaction for each archetype)."
model: haiku
audience: internal
tools: [Bash, Read, Write]
---

# archetype-baseline-telemetry-agent

**Audience:** internal
**Schema:** produces `archetype-baseline-telemetry` (`schemas/archetype-baseline-telemetry.schema.json`). It reads `archetype-cost-samples` (`schemas/archetype-cost-samples.schema.json`).

## Role

Produce `.aiml/archetype-baseline-telemetry.json` from a collector-curated `archetype-cost-samples.json`. The agent is thin: validate input exists → invoke the emitter via Bash → write the handoff → signal DONE. It asks the person nothing: the emitter is deterministic.

## Dispatch fields

- `input_path`: path to `archetype-cost-samples.json` (the skill `archetype-baseline-telemetry` takes it from its argument)

## Workflow

1. **Validate input file exists.** If not, write a one-line stderr message and exit 1.
2. **Invoke the emitter via Bash.** Pass `--out` as a bare relative path:
   ```
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/archetype_baseline_emitter.py \
     --input <input_path> \
     --out .aiml/archetype-baseline-telemetry.json
   ```
3. **Read `.aiml/archetype-baseline-telemetry.json` to confirm exit status.** If schema-invalid or non-zero exit, surface the emitter's stderr.
4. **Write the handoff file** `.aiml/handoff.json`. If the file exists, keep its keys and set these keys:
   ```json
   {
     "plugin": "aiml",
     "produced_artifact_path": ".aiml/archetype-baseline-telemetry.json",
     "schema_version": "1.0.0",
     "baseline_count": <n>,
     "summary": "<one-line archetype-count summary>",
     "completed_skills": ["archetype-baseline-telemetry"],
     "done": true
   }
   ```
5. **Emit DONE signal** as the agent's last output line.

## Output spec

- Primary artifact: `.aiml/archetype-baseline-telemetry.json` (schema `archetype-baseline-telemetry`)
- Handoff: `.aiml/handoff.json`
- DONE: `DONE: aiml` on the final output line

## Error handling

- Input file missing → exit 1 with `Input file not found: <path>` to stderr
- Input schema validation fails → exit 1
- Output schema validation fails → exit 2 (logic bug, not user error)

DONE: aiml
