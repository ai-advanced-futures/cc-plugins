---
name: phase-7-evc-calculation
description: Phase 7 of JTBD discovery — calculate Economic Value to Customer (EVC) across 4 dimensions (time, errors, revenue, risk) to quantify dollar value of top opportunities
---

# Phase 7: EVC Calculation

**Goal:** Quantify dollar value created by solving top opportunities
**Duration:** 30-45 minutes
**Output:** EVC analysis → written to `.jtbd-market-discovery/{session}/p7.json`

## EVC Formula

`EVC = Time Value + Error Value + Revenue Value + Risk Value`

### Time Value
`Hours Saved/Month × Hourly Rate`

### Error Value
`Errors Avoided/Month × Cost per Error`

### Revenue Value
`Revenue Increase/Month × Margin`

### Risk Value
`Probability Reduction × Cost of Adverse Event`

## EVC Benchmarks

| Market | Typical Monthly EVC |
|--------|---------------------|
| B2C consumer | \$10-200 |
| SMB B2B | \$200-2000 |
| Enterprise B2B | \$1000-10000 |

## Pricing Rule of Thumb

Sustainable price = 10-20% of EVC

## Output Schema (p7.json)

```json
{
  "baseline_evc": 1530,
  "premium_evc": 2200,
  "components": {
    "time_value": 510,
    "error_value": 900,
    "revenue_value": 120,
    "risk_value": 0
  },
  "recommended_price_range": [150, 300],
  "confidence": "high"
}
```

## Integration

Phase 8 (Segmentation) runs after it, sequentially. Both feed Phase 9 (WTP Validation).
