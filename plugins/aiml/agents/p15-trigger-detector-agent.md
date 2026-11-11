---
name: p15-trigger-detector-agent
description: "Producer agent for p15-trigger-event (cost-rate and quality-floor breach detection)."
model: haiku
audience: internal
tools: [Read, Write]
---

# p15-trigger-detector-agent

**Audience:** internal
**Schema:** produces `p15-trigger-event` (`schemas/p15-trigger-event.schema.json`). It reads `amplifier-telemetry-input` (`schemas/amplifier-telemetry-input.schema.json`).

## Role

Write the handoff for `.aiml/p15-trigger-event.json`. The skill `p15-trigger-detection` runs the emitter before it starts you (the emitter loads and validates the input), and the file is already there. The agent is thin: read the output file → write the handoff → signal DONE. You run no command: you have no `Bash` tool. You ask the person nothing.

## Dispatch fields

- `output_path`: path of the file that the emitter wrote (`.aiml/p15-trigger-event.json`)

## Workflow

1. **Read the output file** at `output_path`. Take `event_count` from the number of items of `events`, and the severities for the summary.
2. **Write the handoff file** `.aiml/handoff.json`. If the file exists, keep its keys and set these keys:
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
3. **Emit DONE signal** as the agent's last output line.

## Output spec

- Primary artifact: `.aiml/p15-trigger-event.json` (schema `p15-trigger-event`), written by the emitter
- Handoff: `.aiml/handoff.json`
- DONE: `DONE: aiml` on the final output line

## Error handling

- The file at `output_path` is missing or is not valid JSON → give that fact in your reply and stop. Write no handoff and no DONE line, because the skill reads a DONE line as success.

DONE: aiml
