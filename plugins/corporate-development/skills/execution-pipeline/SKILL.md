---
name: execution-pipeline
description: Run the complete 7-phase M&A pipeline end-to-end with context-efficient phase isolation and parallel Phase 3+4
---

# M&A Pipeline Orchestration

Runs the complete corporate development pipeline from Phase 0 (Acquisition Readiness) through Phase 6 (Deal Decision) as a single coordinated workflow. Each phase executes in an isolated context window; only compact PhaseHandoff summaries (~1KB each) are passed between phases. Phase 3 and Phase 4 run in parallel.

## What It Does

- The command asks the intake questions for all 7 phases (the agents ask nothing)
- Dispatches each phase to its own agent (fresh context window per phase)
- Asks again when a phase agent writes a questions file, and then continues the pipeline
- Runs Phase 3 (Operational DD) and Phase 4 (Financial DD) simultaneously
- Stops on a NO_GO gate, because later phases build on a failed result; a CONDITIONAL gate lets the pipeline continue
- Returns a compact `PipelineResult` with gate decisions, scores, and artifact paths for all phases

## How to Use

### Interactive Mode (recommended for first-time users)

```bash
/corporate-development:pipeline
```

The command will:
1. Ask for the target company name
2. Ask the intake questions, 1 phase at a time, and save the answers to `pipeline_inputs.json`
3. Dispatch the `pipeline-orchestrator` agent

### Data folder (for repeat runs)

```bash
/corporate-development:pipeline --data-dir .corporate-development/targets/acme-corp/
```

Reads `pipeline_inputs.json` from the specified folder. The command asks nothing and dispatches the agent at once. The input fields are in `${CLAUDE_PLUGIN_ROOT}/docs/pipeline-inputs.md`.

## Phase Input Summary

| Phase | Required Inputs |
|-------|----------------|
| 0 — Acquisition Readiness | `company_name`, `ceo_readiness` (attitude/aptitude/action 0–10), `strategic_targets`, `organizational_capacity`, `financial_readiness`, `governance` |
| 1 — Deal Sourcing | `target_markets` (list), `strategic_focus`, `budget_range` |
| 2 — Target Assessment | `company_name` + one of: `industry` or `strategic_motivation` |
| 3 — Operational DD | `company_name` + dimension objects: `team`, `technology`, `product`, `operations`, `market_position` |
| 4 — Financial DD | `company_name`, `income_statement` (revenue/COGS/opex/net_income), `balance_sheet` (assets/liabilities/equity) |
| 5 — Integration Planning | Derived from Phase 3+4 handoffs (`operational_health`, `financial_health`) — no extra user input |
| 6 — Deal Decision | Synthesized from full handoff chain — no extra user input |

## Outputs

### PhaseHandoff (per phase, ~1KB each)

```json
{
  "phase_num": 3,
  "phase_name": "Phase 3: Operational Due Diligence",
  "gate": "CONDITIONAL",
  "score": 67.0,
  "critical_risks": ["CEO key-person dependency", "Monolith architecture at scale limits"],
  "artifact_paths": {"operational_dd_report": ".corporate-development/targets/acme-corp/phase_3/..."},
  "next_phase_inputs": {"operational_health": 67, "operational_gate": "CONDITIONAL", "operational_critical_count": 2}
}
```

### PipelineResult.to_summary()

```json
{
  "final_gate": "CONDITIONAL",
  "stopped_at": null,
  "questions_path": null,
  "phases_completed": 7,
  "phase_gates": {
    "Phase 0: Acquisition Readiness": "GO",
    "Phase 1: Deal Sourcing": "GO",
    "Phase 2: Target Assessment": "GO",
    "Phase 3: Operational Due Diligence": "CONDITIONAL",
    "Phase 4: Financial Due Diligence": "GO",
    "Phase 5: Integration Planning": "CONDITIONAL",
    "Phase 6: Deal Decision": "CONDITIONAL"
  },
  "phase_scores": {
    "Phase 0: Acquisition Readiness": 82.0,
    "Phase 2: Target Assessment": 71.0,
    "Phase 3: Operational Due Diligence": 67.0,
    "Phase 4: Financial Due Diligence": 74.0
  },
  "artifact_paths": {
    "phase0_readiness_assessment": ".corporate-development/targets/acme-corp/phase_0/readiness_assessment.json",
    "phase3_operational_dd": ".corporate-development/targets/acme-corp/phase_3/operational_dd.json"
  }
}
```

## Gate Behavior

| Gate | Pipeline Effect |
|------|----------------|
| GO | Continue to next phase |
| CONDITIONAL | Continue; document conditions for Phase 6 synthesis |
| NO_GO (Phase 0–5) | Stop immediately; report which phase blocked |
| NO_GO (Phase 6) | Pipeline completes with NO_GO recommendation |

## Slug Derivation

All artifact paths use a slug derived from the target company name. The rule is in `${CLAUDE_PLUGIN_ROOT}/docs/pipeline-inputs.md`. Example: `"Acme Corp"` gives `acme-corp`, with artifacts at `.corporate-development/targets/acme-corp/`.

## Error Handling

- **Agent crash:** Treat as CONDITIONAL; log error in handoff chain; continue pipeline
- **Missing handoff file:** Treat as CONDITIONAL with `phase_N_handoff: "MISSING"` logged in summary
- **Missing input:** The phase agent writes `handoffs/phase_N_questions.md`; the command asks and dispatches again
- **Pydantic ValidationError in Phase 0:** Treated as NO_GO (malformed required inputs)
- **Optional plugin unavailable:** Graceful skip; phase continues with available data

## Gate Thresholds Reference

See `${CLAUDE_PLUGIN_ROOT}/docs/methodologies/gate-thresholds.md` for per-phase GO/CONDITIONAL/NO_GO thresholds with hard-stop triggers and rationale.

## Used By

- Command: `/corporate-development:pipeline`
- Agent: `pipeline-orchestrator`
- Programmatic: `main.run_pipeline(user_input)` → `PipelineResult.to_summary()`

## Related Skills

- `skills/evaluation-ceo-readiness/` — Phase 0 CEO assessment
- `skills/due-diligence-operational-dd/` — Phase 3 methodology
- `skills/due-diligence-financial-dd/` — Phase 4 methodology
- `skills/execution-integration-planning/` — Phase 5 playbook generation
- `skills/execution-deal-recommendation/` — Phase 6 synthesis
