---
name: phase-2-job-decomposition
description: Phase 2 of JTBD discovery — decompose the main job into 8-15 universal steps using the UNDERSTAND→PLAN→EXECUTE→ASSESS→REVISE→CONCLUDE framework
---

# Phase 2: Job Decomposition

**Goal:** Break the job into 8-15 ordered steps customers follow
**Duration:** 45-60 minutes
**Output:** Job steps map → written to `.jtbd-market-discovery/{session}/p2.json`

## Universal Job Steps Framework

Every job has 6 phases containing specific steps:

| Phase | Focus | Example (Team Coverage) |
|-------|-------|------------------------|
| UNDERSTAND | Gather information | Review team calendar, check deadlines |
| PLAN | Organize and sequence | Identify gaps, plan coverage assignments |
| EXECUTE | Do the core work | Assign coverage, notify team |
| ASSESS | Evaluate progress | Monitor coverage quality in real-time |
| REVISE | Adjust plan | Reassign coverage if gaps emerge |
| CONCLUDE | Complete and wrap up | Confirm all shifts filled, document |

## Job Steps Quality Criteria

Each step must be:
- **Specific** — not vague
- **Actionable** — something a customer actually does
- **Sequential** — logical order preserved
- **Solution-agnostic** — no product references
- **Consistent granularity** — similar level of detail across all steps

## Target

8-15 steps total. If >15 steps, the job may contain multiple jobs — split them.

## Output Schema (p2.json)

```json
{
  "job_statement": "Ensure adequate team coverage during absences",
  "total_steps": 11,
  "job_steps": [
    {"id": "S01", "phase": "UNDERSTAND", "description": "Review upcoming team absences and duration"},
    {"id": "S02", "phase": "UNDERSTAND", "description": "Assess workload requirements during absence period"}
  ]
}
```
