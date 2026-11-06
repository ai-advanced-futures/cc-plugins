---
name: phase-4-time-task-analysis
description: Phase 4 of JTBD discovery — quantify baseline effort (time, errors, costs) for each job step to establish the before/after comparison used in EVC calculation
---

# Phase 4: Effort Quantification (Time-Task Analysis)

**Goal:** Quantify baseline effort for each job step in dollar terms
**Duration:** 30-45 minutes
**Output:** Baseline costs → written to `.jtbd-market-discovery/{session}/p4.json`

## What We Measure

For each job step, quantify:
1. **Time spent** — hours per occurrence × frequency per month
2. **Error rate** — how often mistakes occur × cost to fix
3. **Opportunity cost** — value of work displaced

## Hourly Rate Guidelines

| Segment | Typical Hourly Rate |
|---------|---------------------|
| B2C consumer | \$20-40/hr |
| SMB manager | \$50-100/hr |
| Enterprise executive | \$150-300/hr |
| Knowledge worker | \$75-150/hr |

## Dollar Value Calculation

`\$ Value = (Hours/Month × Hourly Rate) + (Error Rate × Cost per Error)`

## Output Schema (p4.json)

```json
{
  "target_user": "HR Manager",
  "hourly_rate": 85,
  "baseline_costs": {
    "total_hours_per_month": 18,
    "total_cost_per_month": 1530,
    "by_step": [
      {"step_id": "S01", "hours": 6, "cost": 510}
    ]
  }
}
```

## Why This Matters

Phase 4 output feeds Phase 7 (EVC Calculation) — baseline is current cost, EVC is how much your solution saves.
