---
name: orchestrate
description: Use to run the next step of the aiml pipeline, or a step you name. Reads .aiml/handoff.json, picks the first pipeline step that is not complete (or the one in the argument), and runs that skill. For a single step you know, run its skill directly.
---

# /aiml:orchestrate

Routes to the next skill of the aiml pipeline. It runs in the main conversation, so each skill can ask the person its questions.

## Usage

```
/aiml:orchestrate [phase]
```

- `/aiml:orchestrate decide`: run `/aiml:decide`.
- `/aiml:orchestrate`: find the next step from `.aiml/handoff.json`.

## Steps

1. Read `.aiml/handoff.json` if it exists. Take `completed_skills`, `phase`, `project_type` and `done`.
2. Choose the phase:
   - Use the phase in the argument, if there is one.
   - Else use the first phase of the pipeline that is not in `completed_skills`.
   - If `done` is `true`, tell the person that the pipeline is complete, and ask which phase to run again.
   - If you have no argument and no handoff file, ask the person which phase to start with, with `AskUserQuestion`.
3. Run the skill `aiml:<phase>` with the `Skill` tool.
4. Read `.aiml/handoff.json` again, and tell the person the next phase. Ask if it should run; run it only after a yes.

## Pipeline

`decide` → `design` → `plan` → `simulate` → `scaffold` → `tune` → `evaluate` → `ops`

These three skills are not part of the pipeline order. Run them only when the argument names them: `cost-amplifier-readout`, `p15-trigger-detection`, `archetype-baseline-telemetry`.
