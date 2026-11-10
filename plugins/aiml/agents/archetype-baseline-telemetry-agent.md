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

Produce `.aiml/archetype-baseline-telemetry.json` from a collector-curated `archetype-cost-samples.json`. The agent is thin: invoke the emitter via Bash (it checks and validates the input) → write the handoff → signal DONE. It asks the person nothing: the emitter is deterministic.

## Dispatch fields

- `input_path`: path to `archetype-cost-samples.json` (the skill `archetype-baseline-telemetry` takes it from its argument)

## Workflow

1. **Invoke the emitter via Bash.** Pass `--out` as a bare relative path:
   ```
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/archetype_baseline_emitter.py \
     --input <input_path> \
     --out .aiml/archetype-baseline-telemetry.json
   ```
   Run this command first, as the first `Bash` call. The emitter checks the input file, so do not check it with another command, such as `test -f` or `ls`, because the session can allow `uv run` only and then refuses that command.
2. **Read `.aiml/archetype-baseline-telemetry.json` to confirm exit status.** If schema-invalid or non-zero exit, surface the emitter's stderr.
3. **Write the handoff file** `.aiml/handoff.json`. If the file exists, keep its keys and set these keys:
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
4. **Emit DONE signal** as the agent's last output line.

## Output spec

- Primary artifact: `.aiml/archetype-baseline-telemetry.json` (schema `archetype-baseline-telemetry`)
- Handoff: `.aiml/handoff.json`
- DONE: `DONE: aiml` on the final output line

## Error handling

- Input file missing → the emitter exits 1 and writes `Input file not found: <path>` to stderr. Give that line in your reply and stop. Write no handoff.
- Input schema validation fails → exit 1
- Output schema validation fails → exit 2 (logic bug, not user error)

DONE: aiml
