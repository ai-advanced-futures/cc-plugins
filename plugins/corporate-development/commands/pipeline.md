---
description: Run all 7 phases for one target, one agent for each phase, and ask the questions that the agents need.
argument-hint: "[company name] [--data-dir <folder>]"
---
# /corporate-development:pipeline

Run the complete M&A pipeline (Phase 0 to Phase 6) for one target. This command, in the main conversation, starts the phase agents. Each phase runs in its own agent with a fresh context window. Phase 3 and Phase 4 run in parallel. Only small handoff files (about 1 KB each) pass between the phases.

## When to use

- You want the full M&A pipeline without the phase-by-phase commands.
- The input data is ready in a folder (the `--data-dir` option).
- The context window must stay small.

## Method

1. Read `${CLAUDE_PLUGIN_ROOT}/docs/pipeline-inputs.md`. It lists the input fields of each phase and the rule for the slug. Read `${CLAUDE_PLUGIN_ROOT}/docs/phase-handoff.md`. It gives the shape of a handoff file.
2. Get the company name from the argument. If there is none, ask for it.
3. Make the slug with the rule in `pipeline-inputs.md`. If the rule gives an empty slug, say `the company name gives no slug: write it with the letters a-z or the digits 0-9` and ask for the name again.
4. Get the inputs:
   - With `--data-dir <folder>`: ask nothing. The inputs file is `<folder>/pipeline_inputs.json`.
   - Without it: ask the intake questions, 1 phase at a time and not more than 4 questions in 1 call. Write the answers to `.corporate-development/targets/<slug>/pipeline_inputs.json`.
5. Run the phases (see "Run the phases").
6. If a phase agent returned a line that starts with `QUESTIONS:`, read the questions file of that phase. When Phase 3 or Phase 4 asked, also read the questions file of the other of these 2 phases, if it exists and that phase has no handoff file (`handoffs/phase_N_questions.md` is answered when `handoffs/phase_N_handoff.json` exists). Read no other questions file: the questions file of another phase is old, because that phase ran on its answers or did not run in this round. Ask the questions with `AskUserQuestion`. If `AskUserQuestion` is refused or is not available (for example in a `claude -p` run), do not ask in the chat, because no person answers there in such a run: show the summary JSON of "Outputs" in a `json` block, with `stopped_at` set to the name of the phase that asked and `questions_path` set to the path of its questions file, and end the turn. Write each answer into the object `phase_N` of the inputs file (`pipeline_inputs.json`): the number N in `phase_N_questions.md` names it. That phase wrote no handoff, so it runs again on the answers. Go back to step 5. The command skips each phase that has a handoff file. Repeat until no phase asks. If the same questions file comes back 2 times with no change, stop and show it to the person.
7. Show the person the summary JSON of "Outputs" in a `json` block, and below it the gates of the phases, the final gate, and the paths of the artifacts.

Read a questions file of the target only in step 6, and only an open one. Before the first run of the phases, read no questions file.

To run all phases again, delete the folder `.corporate-development/targets/<slug>/handoffs/` and run the command.

## Run the phases

| Phase | Agent | Command file | Name of the phase |
|---|---|---|---|
| 0 | `corporate-development:readiness-assessor` | `${CLAUDE_PLUGIN_ROOT}/commands/readiness.md` | Phase 0: Acquisition Readiness |
| 1 | `corporate-development:deal-sourcer` | `${CLAUDE_PLUGIN_ROOT}/commands/discover.md` | Phase 1: Deal Sourcing |
| 2 | `corporate-development:target-assessor` | `${CLAUDE_PLUGIN_ROOT}/commands/assess.md` | Phase 2: Target Assessment |
| 3 | `corporate-development:operational-auditor` | `${CLAUDE_PLUGIN_ROOT}/commands/audit.md` | Phase 3: Operational Due Diligence |
| 4 | `corporate-development:financial-analyst` | `${CLAUDE_PLUGIN_ROOT}/commands/analyze.md` | Phase 4: Financial Due Diligence |
| 5 | `corporate-development:integration-planner` | `${CLAUDE_PLUGIN_ROOT}/commands/plan.md` | Phase 5: Integration Planning |
| 6 | `corporate-development:deal-advisor` | `${CLAUDE_PLUGIN_ROOT}/commands/recommend.md` | Phase 6: Deal Decision |

Start the agents with the `Agent` tool, in this order: Phase 0, Phase 1 and Phase 2 one at a time; Phase 3 and Phase 4 together; then Phase 5; then Phase 6.

1. Before you start a phase, look for `.corporate-development/targets/<slug>/handoffs/phase_<N>_handoff.json`. If the file exists, read it and skip the dispatch. This is how a run continues after the person answered questions.
2. After each dispatch, read the handoff file of the phase with the Read tool. Run no command to read it. Add its content to the handoff chain.
3. Stop at the first NO_GO gate. A CONDITIONAL gate does not stop the pipeline: write down the conditions and continue.
4. After Phase 6, or after a stop, go to step 6 of the Method if a phase asked, else to step 7.

### Phase prompt

Each phase agent gets a prompt with these parts. Put each part in the prompt in full.

```
You run {phase name} of the corporate-development M&A pipeline for {company_name}.
Slug: {slug}
Project root: {the absolute path of the current folder}. Write each path of this prompt under the project root. Use absolute paths.
Read the command file of the table and apply its method. Do not ask the person any question.
Phase inputs: {the object of this phase from pipeline_inputs.json}
Prior handoffs: {the next_phase_inputs that this phase needs, from the handoff chain}
If a required input is missing, write handoffs/phase_{N}_questions.md under .corporate-development/targets/{slug}/ and write no handoff. Return a line that starts with QUESTIONS: and gives the path.
Else write the artifacts to the artifact folder that the agent file names, and write the PhaseHandoff JSON to .corporate-development/targets/{slug}/handoffs/phase_{N}_handoff.json.
Return only the gate and the path of the handoff file.
```

For Phase 0, `{company_name}` is the buyer (`company_name` in the object `phase_0`). Add the line `assessment_date: {the date of today, YYYY-MM-DD}` to the prompt of Phase 0, because the agent has no tool that gives the date. For the other phases, `{company_name}` is the target.

The `next_phase_inputs` of the handoff chain are in `${CLAUDE_PLUGIN_ROOT}/docs/phase-handoff.md`.

### Phase 3 and Phase 4

Start Phase 3 and Phase 4 in one message with 2 `Agent` calls. Wait for both to finish, then read both handoff files. If you start Phase 3, wait, and then start Phase 4, the pipeline loses the time that the parallel run saves.

If one phase returns NO_GO, stop and name that phase. If both return GO or CONDITIONAL, go on to Phase 5. If a phase returns `QUESTIONS:`, start no later phase, and wait for both parallel phases.

### Phase 5

Merge the `next_phase_inputs` of Phase 3 and Phase 4 into one object. Give only this object, and not the handoff chain, to the Phase 5 agent:

```json
{
  "company_name": "<target>",
  "target_company": "<acquirer>",
  "operational_health_score": <Phase 3 operational_health>,
  "operational_gate": "<Phase 3 operational_gate>",
  "operational_critical_count": <Phase 3 operational_critical_count>,
  "operational_warning_count": <Phase 3 operational_warning_count>,
  "financial_health_score": <Phase 4 financial_health>,
  "financial_gate": "<Phase 4 financial_gate>",
  "financial_critical_count": <Phase 4 financial_critical_count>
}
```

### Phase 6

Give the Phase 6 agent the full handoff chain as a JSON array. Give it paths only, because the Phase 6 agent opens an artifact file itself when it needs one.

### Missing handoff

If a phase agent fails and returns no `QUESTIONS:` line and no handoff file exists:

- Treat the phase as CONDITIONAL, and not as NO_GO.
- Write `"phase_{N}_handoff": "MISSING - agent did not write the handoff file"` in the handoff chain.
- Continue, and include the gap in the summary.

### Rules

- Read `artifact_paths` from the handoffs. Open an artifact file only when the person asks.
- Pass `next_phase_inputs` from a handoff to the next phase. Pass the full chain only to Phase 6.
- Start one agent for each phase, because a fresh context window keeps each phase small. Phase 3 and Phase 4 are the one exception: they run in parallel.
- Continue after a CONDITIONAL gate, because only a NO_GO gate stops the pipeline.

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

Build this summary (the `PipelineResult.to_summary()` form) from the handoff files. `final_gate` is the gate of Phase 6, or NO_GO when the pipeline stopped at a NO_GO gate.

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

## Agents

The command starts the 7 phase agents: `readiness-assessor`, `deal-sourcer`, `target-assessor`, `operational-auditor`, `financial-analyst`, `integration-planner` and `deal-advisor`, each with the prefix `corporate-development:`. No agent of the plugin starts an agent.

## Optional plugins

A phase agent can use these plugins when Claude Code has them. The pipeline does not need any of them.

- `tech-contracts` and `team-assessment`: Phase 3
- `tech-budget`: Phase 3 and Phase 5
- `competitive-intelligence`: Phase 2
- `product-finance`: Phase 4
- `value-ip`: Phase 6
