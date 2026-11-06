---
name: phase-1-job-identification
description: Phase 1 of JTBD discovery — identify and validate the stable, outcome-focused job customers are trying to accomplish using Socratic dialogue
---

# Phase 1: Job Identification

**Goal:** Define the main job customers are trying to accomplish
**Duration:** 30-45 minutes
**Output:** Validated job statement → written to `.jtbd-market-discovery/{session}/p1.json`

## Job Statement Formula

`[ACTION VERB] + [OBJECT OF ACTION] + [CONTEXTUAL CLARIFIER]`

**Examples:**
- "Get to destinations on time"
- "Ensure adequate team coverage during absences"
- "Maintain visibility into project progress"

## Quality Criteria

A good job statement is:
1. **Stable** — existed 10 years ago, will exist 10 years from now
2. **Outcome-focused** — describes result, not solution
3. **Action-oriented** — starts with an action verb
4. **Context-specific** — includes qualifiers that narrow scope
5. **Solution-agnostic** — multiple products could address it

## Socratic Dialogue Approach

Ask these questions to surface the job:
- "What outcome are they trying to achieve?"
- "What would success look like?"
- "If all current solutions disappeared, what would they still need?"
- "What are they hiring products to do?"

## Common Pitfalls

- **Too broad:** "Be successful in business" → narrow with context
- **Solution-focused:** "Use project management software" → "Track project progress"
- **Multiple jobs combined:** Split into separate jobs and study each
- **Feature-focused:** "Get push notifications" → "Stay aware of upcoming deadlines"

## Output Schema (p1.json)

```json
{
  "job_statement": "Ensure adequate team coverage during absences",
  "job_category": "management",
  "context": "B2B, HR managers, 50-500 employee companies",
  "trigger": "employee requests time off during critical periods"
}
```

## Next Phase

After validating the job statement, proceed to Phase 2: Job Decomposition.
