---
description: Run all 7 phases for one target, one agent for each phase, and ask the questions that the agents need.
argument-hint: "[company name] [--data-dir <folder>]"
---
# /corporate-development:pipeline

Run the complete M&A pipeline (Phase 0 to Phase 6) for one target. Each phase runs in its own agent with a fresh context window. Phase 3 and Phase 4 run in parallel.

## When to use

- You want the full M&A pipeline without the phase-by-phase commands.
- The input data is ready in a folder (the `--data-dir` option).
- The context window must stay small.

## Method

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/pipeline-inputs.md`. It lists the input fields of each phase and the rule for the slug.
2. Get the company name from the argument. If there is none, ask for it.
3. Make the slug with the rule in `pipeline-inputs.md`.
4. Get the inputs:
   - With `--data-dir <folder>`: ask nothing. The inputs file is `<folder>/pipeline_inputs.json`.
   - Without it: ask the intake questions, 1 phase at a time and not more than 4 questions in 1 call. Write the answers to `.corporate-development/targets/<slug>/pipeline_inputs.json`.
5. Dispatch the agent `corporate-development:pipeline-orchestrator` with the fields `company_name`, `slug` and `inputs_path`.
6. Read the summary that the agent returns.
   - If `questions_path` is set, read the file of `questions_path`. When `stopped_at` is Phase 3 or Phase 4, also read the questions file of the other of these 2 phases, if it exists and that phase has no handoff file (`handoffs/phase_N_questions.md` is answered when `handoffs/phase_N_handoff.json` exists). Read no other questions file: the questions file of another phase is old, because that phase ran on its answers or did not run in this round. Ask the questions. Add each answer to the object of the phase that asked: the number N in `phase_N_questions.md` names it. That phase wrote no handoff, so it runs again on the answers. Dispatch the agent again with the same 3 fields. The agent skips each phase that has a handoff file. Repeat until `questions_path` is null. If the same questions file comes back 2 times with no change, stop and show it to the person.
   - If the reply has `FAILED`, show the reply and stop.
   - Else show the person the gates of the phases, the final gate, and the paths of the artifacts.

Read a questions file of the target only in step 6, and only an open one. Before step 5, read no questions file.

To run all phases again, delete the folder `.corporate-development/targets/<slug>/handoffs/` and run the command.

## The phases

| Phase | Name | Gate rule |
|---|---|---|
| 0 | Acquisition Readiness | NO_GO stops the pipeline |
| 1 | Deal Sourcing | collects information, GO when the inputs are valid |
| 2 | Target Assessment | NO_GO stops the pipeline |
| 3 | Operational Due Diligence | runs with Phase 4 |
| 4 | Financial Due Diligence | runs with Phase 3 |
| 5 | Integration Planning | uses the results of Phase 3 and Phase 4 |
| 6 | Deal Decision | final gate |

| Gate | Action |
|---|---|
| `GO` | Go on to the next phase. |
| `CONDITIONAL` | Go on, and write down the conditions. |
| `NO_GO` | Stop. The field `stopped_at` names the phase. |

## Outputs

The agent returns this summary:

```json
{
  "final_gate": "CONDITIONAL",
  "stopped_at": null,
  "questions_path": null,
  "phases_completed": 7,
  "phase_gates": {
    "Phase 0: Acquisition Readiness": "GO",
    "Phase 3: Operational Due Diligence": "CONDITIONAL"
  },
  "phase_scores": {
    "Phase 0: Acquisition Readiness": 82.0,
    "Phase 3: Operational Due Diligence": 67.0
  },
  "artifact_paths": {
    "phase0_readiness_assessment": ".corporate-development/targets/acme/phase_0_readiness/readiness_assessment.json"
  }
}
```

Each phase writes its files to `.corporate-development/targets/<slug>/phase_<N>_<name>/`. Each phase writes a handoff file to `.corporate-development/targets/<slug>/handoffs/phase_<N>_handoff.json`. A phase that needs an answer writes `handoffs/phase_<N>_questions.md`.

## Next steps

1. `final_gate` is GO: go on to the term sheet and the closing.
2. `final_gate` is CONDITIONAL: read the phase artifacts for the conditions to meet.
3. `stopped_at` is set: fix the cause of the NO_GO, delete the handoff file of that phase, and run the command again.

## Related commands

- `/corporate-development:readiness` runs Phase 0 alone.
- `/corporate-development:audit` runs Phase 3 alone.
- `/corporate-development:analyze` runs Phase 4 alone.
- `/corporate-development:recommend` runs Phase 6 alone.

## Agent

`corporate-development:pipeline-orchestrator` dispatches each phase to its own agent and passes a small handoff file between the phases.
