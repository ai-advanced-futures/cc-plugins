---
name: phase-10-output-integration
description: Phase 10 of JTBD discovery — assemble final output from all phase files, rank opportunities by composite score, and generate executive summary + structured JSON
---

# Phase 10: Output Integration

**Goal:** Assemble all phase outputs into ranked opportunities + executive summary
**Duration:** 15-20 minutes
**Output:** `.jtbd-market-discovery/{session}/final-output.json` + executive summary

## Composite Scoring

`Composite = (ODI Score × 0.4) + (Financial Score × 0.35) + (Segment Score × 0.25)`

Where:
- **ODI Score** — from p6.json `odi_score` (normalize: `odi_score / 20 × 100`)
- **Financial Score** — from p7.json: `this_need_total_evc / max(all_needs_total_evc) × 100`
- **Segment Score** — from p8.json `percentage` × confidence weight: `high`=1.0, `medium`=0.5, `low`=0.25 → `percentage × weight × 100`

## Output Schema (final-output.json)

```json
{
  "job_statement": "Ensure adequate team coverage during absences",
  "top_opportunities": [
    {
      "rank": 1,
      "need": "Prevent coverage gaps from forming during critical periods",
      "odi_score": 16.2,
      "evc_monthly": 1530,
      "wtp_validated": 75,
      "segment": "Crisis Avoiders (43%)",
      "composite_score": 87
    }
  ],
  "segments": [],
  "recommendations": []
}
```

## Downstream Integration

After Phase 10, the discover skill offers:
- `/product:explore` — turn the top opportunity into product requirements
- `/gtm` — build GTM strategy around validated opportunity
- `/pricing:price` — compute RIGHT_PRICE from EVC data
