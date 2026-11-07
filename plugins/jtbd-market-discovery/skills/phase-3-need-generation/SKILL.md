---
name: phase-3-need-generation
description: Phase 3 of JTBD discovery — generate 80-100 customer needs using the ACTION + VARIABLE formula across all job steps (4 agents by step group, started one after the other by the discover skill)
---

# Phase 3: Need Generation

**Goal:** Generate 80-100 customer needs across all job steps
**Duration:** 60-90 minutes (4 agents, one after the other)
**Output:** Customer needs → written to `.jtbd-market-discovery/{session}/p3-batch-{1..4}.json`

## Need Formula

`CUSTOMER NEED = ACTION + VARIABLE`

## Action Verbs Library

| Category | Verbs |
|----------|-------|
| Minimize negative | minimize, reduce, prevent, eliminate |
| Maximize positive | maximize, increase, improve, ensure, optimize |
| Determine | determine, identify, assess, calculate, evaluate, verify |

## Generating Needs Per Step

For each job step, ask:
1. What does the customer want to **minimize** here?
2. What does the customer want to **maximize** here?
3. What do they need to **determine/verify** here?
4. What do they want to **avoid** here?

Target: 5-10 needs per job step, 80-100 needs total.

## Quality Criteria

Each need must be:
- **Outcome-focused** — describes desired result, not solution
- **Measurable** — can be rated 1-10 for importance/satisfaction
- **Stable** — no product references
- **Singular** — one outcome per need (no "and")

## Batches (Discover Skill)

Phase 3 uses 4 agents, one for each batch. The skill starts them one at a time, then runs `jtbd_state.py merge-needs`:
- Batch 1: Steps 1-3 (UNDERSTAND phase)
- Batch 2: Steps 4-6 (PLAN phase)
- Batch 3: Steps 7-9 (EXECUTE + ASSESS)
- Batch 4: Steps 10+ (REVISE + CONCLUDE)

## Output Schema (p3-batch-N.json)

```json
{
  "batch": 1,
  "steps_covered": ["S01", "S02", "S03"],
  "needs": [
    {"id": "N001", "step_id": "S01", "need": "Minimize time required to identify upcoming absences"}
  ]
}
```
