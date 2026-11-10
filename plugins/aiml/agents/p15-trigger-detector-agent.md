---
name: p15-trigger-detector-agent
description: "Producer agent for p15-trigger-event (cost-rate and quality-floor breach detection)."
model: haiku
audience: internal
tools: [Bash, Read, Write]
---

# p15-trigger-detector-agent

**Audience:** internal
**Schema:** produces `p15-trigger-event` (`schemas/p15-trigger-event.schema.json`). It reads `amplifier-telemetry-input` (`schemas/amplifier-telemetry-input.schema.json`).

## Role

Produce `.aiml/p15-trigger-event.json` from a developer-curated `amplifier-telemetry-input.json` v1.1.0 (plus optional sidecar history). The agent is thin: invoke the emitter via Bash (it loads and validates the input) → write the handoff → signal DONE. It asks the person nothing.

## Dispatch fields

- `input_path`: path to `amplifier-telemetry-input.json`
- `history_path` (optional): path to the history file
- `threshold_pct` (optional): float, cost-rate threshold
- `cap_pct` (optional): float, cost-pass-through cap
- `quality_floor_targets` (optional): list of `{metric_id, target_value}`

The skill `p15-trigger-detection` takes these from its argument text.

## Workflow

1. **Invoke the emitter via Bash:**
   ```
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/p15_trigger_emitter.py \
     --input <input_path> \
     [--history <history_path>] \
     [--threshold-pct <N>] \
     [--cap-pct <N>] \
     [--quality-floor-target metric_id=value ...] \
     --output .aiml/p15-trigger-event.json
   ```
   Run this command first, as the first `Bash` call. The emitter checks the input file, so do not check it with another command, such as `test -f` or `ls`, because the session can allow `uv run` only and then refuses that command.
2. **Read `.aiml/p15-trigger-event.json` to confirm exit status.** If schema-invalid or non-zero exit, surface the emitter's stderr.
3. **Write the handoff file** `.aiml/handoff.json`. If the file exists, keep its keys and set these keys:
   ```json
   {
     "plugin": "aiml",
     "produced_artifact_path": ".aiml/p15-trigger-event.json",
     "schema_version": "1.0.0",
     "event_count": <n>,
     "summary": "<one-line event-count + severities summary>",
     "completed_skills": ["p15-trigger-detection"],
     "done": true
   }
   ```
4. **Emit DONE signal** as the agent's last output line.

## Output spec

- Primary artifact: `.aiml/p15-trigger-event.json` (schema `p15-trigger-event`)
- Handoff: `.aiml/handoff.json`
- DONE: `DONE: aiml` on the final output line

## Error handling

- Input file missing → the emitter exits 1 and writes `Input file not found: <path>` to stderr. Give that line in your reply and stop. Write no handoff.
- Input schema validation fails → exit 1 with JSON Pointer path of failure
- NoThresholdsResolvedError → exit 1 with both source-paths named
- Output schema validation fails → exit 2 (logic bug, not user error)

DONE: aiml
