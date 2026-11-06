# ADR-001: Corporate Development Plugin Architecture

**Status:** Accepted
**Deciders:** Luis F. Amadeo
**Plugin:** corporate-development

---

## Context

Corporate development leaders, private equity analysts and CEOs who buy companies need to:

1. Check the readiness of their own organization before they search for a target
2. Find and screen targets against strategic criteria
3. Run operational and financial due diligence
4. Write an integration playbook that is based on the due diligence findings
5. Combine all findings into a GO, NO_GO or CONDITIONAL recommendation

Single-purpose plugins cover some analysis areas. None gives one M&A workflow with gate logic.

Constraints:
- The plugin has no external dependency at install time except Pydantic and pandas.
- The context window is finite. If one agent holds the output of 7 phases, the window overflows.
- Phase 3 (Operational DD) and Phase 4 (Financial DD) do not depend on each other. A sequential run wastes time.
- The Python layer must be testable with deterministic scoring. The agent layer needs enough structure to produce consistent handoffs.
- Only the commands can ask the person a question. A subagent cannot do it.

---

## Decision Drivers

- **Start small:** Build the 7-phase pipeline first. Add parallel runs and context isolation when the phase logic is proven.
- **One agent for each phase:** The command `pipeline`, in the main conversation, starts each phase in its own agent. Each phase has a fresh context window. No agent starts an agent.
- **A person decides:** A gate is a recommendation. A person approves each major step.
- **Cheap, exact scoring:** Python engines do all scoring. Agents do the reasoning and the narrative.
- **Structured handoffs:** Each phase feeds the next with a small handoff. Phase 6 combines the full chain.
- **Separation of concerns:** Deterministic scoring is in Python (`HealthScorer`, `EarningsCalculator`, `RiskAnalyzer`). Narrative and gate reasoning are in the agents.

---

## Considered Options

### Option A: Skills only (no Python, no agents)

Claude does all scoring, gate logic and artifact writing in natural language.

**Pros:** Simplest to build. No dependency.
**Cons:** Scoring formulas change between model versions. Gate logic is applied in an inconsistent way. No regression tests. Weighted scores can be wrong.

### Option B: Python pipeline with little agent work

Python runs all 7 phases. An agent writes only the final narrative.

**Pros:** Deterministic, fast, testable.
**Cons:** Target assessment, deal decision and the narrative outputs need strategic reasoning. Intake needs conversation. Integration planning is generative work.

### Option C: Two layers, Python scoring and agent reasoning (chosen)

Python does the deterministic work: Pydantic validation, weighted scoring and artifact files. The agents and the commands do the conversational work: intake, strategic narrative and gate synthesis. Both layers use the same phase implementations. Python has two orchestrators:
- `MAOrchestrator`: sequential, with full test coverage
- `PipelineOrchestrator`: Phase 3 and Phase 4 in parallel, with a handoff chain that keeps the context small

---

## Decision Outcome

**Chosen: Option C.**

### Architecture

#### 7-Phase Pipeline

| Phase | Name | Gate type | Score |
|-------|------|-----------|-------|
| 0 | Acquisition Readiness | Hard requirements and weighted score | 0-100 |
| 1 | Deal Sourcing | Valid inputs give GO | null |
| 2 | Target Assessment | Weighted score | 0-100 |
| 3 | Operational Due Diligence | 5-dimension weighted score | 0-100 |
| 4 | Financial Due Diligence | 5-dimension weighted score | 0-100 |
| 5 | Integration Planning | Qualitative complexity rating | null |
| 6 | Deal Decision | Synthesis of all prior gates | null |

The gate values are `GO`, `CONDITIONAL` and `NO_GO`. `docs/methodologies/gate-thresholds.md` gives the threshold of each phase.

#### Run order

1. The command `pipeline` reads `docs/pipeline-inputs.md`. It asks the intake questions, 1 phase at a time, and writes `pipeline_inputs.json`. With `--data-dir`, it asks nothing.
2. The command starts the phase agents in file-based mode: `readiness-assessor` for Phase 0, then `deal-sourcer`, `target-assessor`, `operational-auditor`, `financial-analyst`, `integration-planner` and `deal-advisor`. It starts Phase 3 and Phase 4 in one message with 2 `Agent` calls. It skips each phase that has a handoff file.
3. A phase agent that needs an answer writes `handoffs/phase_<N>_questions.md` and no handoff. The command starts no later phase, asks, adds the answers to `pipeline_inputs.json`, and runs the phases again.
4. The command shows the `PipelineResult.to_summary()` form of the result.

Only the commands ask the person. No agent has the `AskUserQuestion` tool.

#### Agent roster

| Agent | Model | Tools | Role |
|-------|-------|-------|------|
| `readiness-assessor` | sonnet | Read, Write, Glob, Grep | Phase 0 acquisition readiness |
| `deal-sourcer` | sonnet | Read, Write, Glob, Grep, WebSearch | Phase 1 sourcing and qualification |
| `target-assessor` | sonnet | Read, Write, Glob, Grep, WebSearch | Phase 2 strategic fit |
| `operational-auditor` | sonnet | Read, Write, Glob, Grep, Skill | Phase 3 operational due diligence |
| `financial-analyst` | sonnet | Read, Write, Glob, Grep | Phase 4 financial due diligence |
| `integration-planner` | sonnet | Read, Write, Glob, Grep | Phase 5 integration plan |
| `deal-advisor` | sonnet | Read, Write, Glob, Grep, Skill | Phase 6 recommendation |

All agents use sonnet. No agent needs a larger model.

#### Python layer

```
corporate_development/
├── core/
│   ├── orchestrator.py        MAOrchestrator (sequential)
│   └── phase.py               PhaseInput, PhaseOutput, PhaseGate enum
├── pipeline/
│   ├── orchestrator.py        PipelineOrchestrator (Phase 3 and Phase 4 in parallel)
│   └── handoff.py             PhaseHandoff, PipelineResult dataclasses
├── phases/                    The 7 phase implementations
├── readiness_assessment/      Pydantic models and scorers for Phase 0
├── operational_dd/            Scoring engines for the Phase 3 dimensions
├── financial_dd/              EarningsCalculator, FinancingAnalyzer, HealthScorer
├── decision_framework/        ScoreAggregator, StrategyEvaluator
└── main.py                    run_investigation() and run_pipeline()
```

#### PhaseHandoff pattern

```json
{
  "phase_num": 3,
  "phase_name": "Phase 3: Operational Due Diligence",
  "gate": "CONDITIONAL",
  "score": 67.0,
  "critical_risks": ["CEO key-person dependency", "Monolith architecture limits scale"],
  "artifact_paths": {"operational_dd_report": ".corporate-development/targets/acme-corp/phase_3_operational_dd/summary.md"},
  "next_phase_inputs": {"operational_health": 67, "operational_gate": "CONDITIONAL", "operational_critical_count": 2}
}
```

A handoff is about 1 KB. The command holds at most 7 handoffs (about 7 KB). The full artifacts stay on disk. The command opens an artifact only when the person asks.

#### Phase 3 and Phase 4 in parallel

```python
# Python layer (PipelineOrchestrator)
with ThreadPoolExecutor(max_workers=2) as executor:
    f3 = executor.submit(self._run_phase, phase3, user_input)
    f4 = executor.submit(self._run_phase, phase4, user_input)
    result3 = f3.result()
    result4 = f4.result()
```

The agent layer dispatches both phases in one message with 2 `Agent` calls.

---

## Consequences

### Positive

- **Testable scoring:** The tests cover the phase scoring formulas. The gate logic has regression tests.
- **Small context:** The handoffs in the main conversation stay near 10 KB for any deal.
- **Parallel due diligence:** Phase 3 and Phase 4 run at the same time in both layers.
- **One result:** The command shows one `PipelineResult.to_summary()`.
- **Safe failure:** A missing handoff file gives CONDITIONAL, and not NO_GO. A crash of an agent is logged and the pipeline continues. A missing optional plugin is skipped.
- **Two entry points:** `run_pipeline()` and `run_investigation()` are in `main.py`.
- **Questions without a stop:** A phase agent writes its questions to a file. The command asks, and the run continues from the saved handoffs.

### Negative and trade-offs

- **Two places for scoring rules:** The Python weights and the scoring guidance in the commands and agents must stay equal. `docs/methodologies/gate-thresholds.md` is the reference.
- **No live data:** Phase 1 does not query a deal database. The practitioner gives the inputs.
- **Null score for Phase 5 and Phase 6:** Integration planning and the deal recommendation are qualitative. A number would show a precision that does not exist.

---

## Integration Map

| Plugin | Phase | Use |
|--------|-------|-----|
| competitive-intelligence | 2 | Competitive analysis for the target assessment |
| team-assessment | 3 | Leadership depth and retention risk |
| tech-budget | 3 | Technology cost structure |
| tech-contracts | 3, 6 | Contract risk review with `tech-contracts:review` |
| product-finance | 4 | Unit economics and synergy tracking |
| value-ip | 6 | IP claim check and moat assessment |

All plugins in this map are optional. A phase uses a plugin only when Claude Code has it. If the plugin is not there, the phase goes on and its report says which plugin it did not use.
