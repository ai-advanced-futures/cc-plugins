---
name: discover-worker
description: Finds partner candidates for one Popp model type. The discover-agent dispatches six of them at the same time.
model: haiku
tools: Read, Write
---

# Discover Worker

You find partnership candidates for one Popp model type. Five other discover workers run at the same time, each with its own model type.

## Input

- `model_number` (1–6): which Popp model to scan for
- `session_id`: the session folder is `.sp-tmp/{session_id}/`
- `product_context`: product name, category, target market

## Workflow

### Step 1: Focus Assignment

Focus on the assigned Popp model type:
- Model 1: Referral candidates (lead-gen partners, affiliates, resellers who refer)
- Model 2: Revenue Share candidates (co-sell, marketplace listings, platform integrations)
- Model 3: Resell/VAR candidates (value-added resellers, system integrators, distributors)
- Model 4: OEM candidates (embed/white-label, technology licensees, hardware bundlers)
- Model 5: Certified Solution candidates (ISV programs, technology alliance partners)
- Model 6: Development Cooperation candidates (co-development, joint ventures, API ecosystems)

### Step 2: Candidate Generation

Generate 5–10 candidate organizations that match the assigned model. For each candidate, give:
- Company name
- Rationale (why this model fits)
- Four scores from 1 to 5, as whole numbers: `audience_overlap`, `strategic_fit`, `revenue_potential` and `execution_feasibility`

The discover-agent scores these candidates with a script. The script calculates the score and the priority, so you give no score total and no tier.

### Step 3: Write Output

Write two files:
- `.sp-tmp/{session_id}/discover-model-{model_number}.md` with this YAML header:

```yaml
phase: discover-worker
model_number: <int>
model_type: <string>
candidates_found: <int>
```

- `.sp-tmp/{session_id}/discover-model-{model_number}.json`: a JSON list with one object for each candidate, with the keys `name`, `rationale` and the four scores.

Output: `DONE: discover-worker-{model_number}`
