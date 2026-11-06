---
name: phase-8-segmentation
description: Phase 8 of JTBD discovery — identify 3-5 behavioral customer segments using multi-dimensional clustering (needs + circumstances + behavioral patterns)
---

# Phase 8: Customer Segmentation

**Goal:** Identify 3-5 distinct behavioral segments with different opportunity profiles
**Duration:** 30-60 minutes (runs after Phase 7, sequentially)
**Output:** Segment profiles → written to `.jtbd-market-discovery/{session}/p8.json`

## Three Segmentation Dimensions

| Dimension | Data Source |
|-----------|------------|
| Needs-based | ODI importance ratings (p6) |
| Circumstances | Survey context questions |
| Behavioral | Observable patterns (tools, frequency) |

## Algorithm

**Claude Code:** K-means clustering (scikit-learn), elbow method for optimal count
**Claude.ai Web:** AI-powered conceptual clustering (~80% accuracy)

## Segment Validation

Each segment must be:
- **Observable** — identifiable in real life
- **Actionable** — different marketing/pricing possible
- **Substantial** — min. 15-20% of market
- **Stable** — consistent over time

## Example Segments (Team Coverage)

| Segment | % Market | Key Need |
|---------|---------|----------|
| Crisis Avoiders | 43% | Prevent coverage gaps proactively |
| Compliance-Focused | 31% | Document decisions for audit trail |
| Efficiency-Driven | 26% | Minimize manager time on planning |

## Output Schema (p8.json)

```json
{
  "total_segments": 3,
  "segments": [
    {
      "id": "S001",
      "name": "Crisis Avoiders",
      "size_pct": 43,
      "top_opportunity_score": 16.2,
      "top_needs": ["N012", "N045", "N063"]
    }
  ]
}
```
