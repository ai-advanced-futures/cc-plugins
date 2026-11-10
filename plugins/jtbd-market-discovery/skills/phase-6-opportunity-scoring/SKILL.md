---
name: phase-6-opportunity-scoring
description: Phase 6 of JTBD discovery — calculate ODI opportunity scores for all customer needs and rank underserved opportunities using Importance + max(Importance - Satisfaction, 0)
---

# Phase 6: Opportunity Scoring

**Goal:** Calculate ODI opportunity scores for all 80-100 needs and rank top opportunities
**Duration:** 15-30 minutes
**Output:** Ranked opportunities → written to `.jtbd-market-discovery/{session}/p6.json`

## Opportunity Formula (Additive, Default)

`ODI Score = Importance + max(Importance - Satisfaction, 0)`

**Score Interpretation:**

| Score | Market Status |
|-------|--------------|
| 15-20 | Extremely underserved — high priority |
| 12-15 | Underserved — solid opportunity |
| 10-12 | Appropriately served — niche |
| < 10 | Overserved — skip |

## Calculation Example

Need: "Minimize time to identify traffic delays"
- Importance: 9.2 | Satisfaction: 3.1
- ODI Score: 9.2 + max(9.2 - 3.1, 0) = **15.3** ← Extremely underserved

## Output Schema (p6.json)

```json
{
  "opportunities": [
    {
      "need_id": "N001",
      "need": "Minimize time to identify traffic delays",
      "importance": 9.2,
      "satisfaction": 3.1,
      "opportunity_score": 15.3,
      "status": "extremely_underserved",
      "rank": 1
    }
  ],
  "top_10": ["N001", "N017", "N023"]
}
```

## After Scoring

Phase 6 completion triggers Phase 7 (EVC); Phase 8 (Segmentation) runs after it, sequentially.
