---
name: phase-9-wtp-validation
description: Phase 9 of JTBD discovery — validate willingness-to-pay using a 6-layer framework (statistical, comparative, Van Westendorp, value economics, confidence, segment-specific)
---

# Phase 9: WTP Validation

**Goal:** Validate pricing hypotheses using 6-layer framework
**Duration:** 20-40 minutes
**Output:** WTP validation results → written to `.jtbd-market-discovery/{session}/p9.json`

## 6-Layer Framework

1. **Statistical outlier detection** — IQR method removes impossible price points
2. **Comparative benchmarking** — compare to known market prices for similar jobs
3. **Van Westendorp PSM** — 4-question psychological price boundaries (if survey collected)
4. **Value economics check** — 10–30% of EVC is the optimal value capture range
5. **Confidence scoring** — weight by sample size and response consistency
6. **Segment-specific benchmarks** — validate separately per segment

## B2B Typical WTP Benchmarks

| Company Size | WTP/Seat/Month |
|-------------|----------------|
| SMB | \$20-75 |
| Mid-market | \$50-150 |
| Enterprise | \$100-500 |

## Output Schema (p9.json)

```json
{
  "validation_result": "PASS",
  "validated_wtp": 75,
  "wtp_range": [60, 100],
  "confidence": "high",
  "layers_passed": [1, 2, 4, 5, 6],
  "segment_wtp": {
    "S001": {"range": [75, 100], "confidence": "high"},
    "S002": {"range": [40, 60], "confidence": "medium"}
  }
}
```

## Interpretation

- **PASS:** Pricing validated — proceed to Phase 10
- **CHALLENGED:** Some layers failed — adjust price or targeting
- **FAIL:** Fundamental mismatch — reconsider value proposition
