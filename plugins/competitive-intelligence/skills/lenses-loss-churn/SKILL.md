---
name: lenses-loss-churn
description: Runs when the lens executor or the skill analyze needs the loss and churn lens. It checks the other lens findings against real data on lost deals and lost customers.
user-invocable: false
---

# Loss/Churn Analysis Lens

## Purpose

Validate all other lens findings with actual customer decisions because loss and churn data represents ground truth that trumps speculation and marketing claims.

## Input Required

- `intelligence-data.json` - Including any loss/churn data
- The files named in `available_data`, when there are any
- `jtbd-analysis.json` - Performance findings to validate
- `forces-analysis.json` - Switching dynamics to validate
- `value-analysis.json` - Value claims to validate
- `strategic-analysis.json` - Strategic findings to validate
- `technology-disruption.json` - Disruption claims to validate

## Critical Role

This lens serves as **reality check** for the entire analysis:

```
Marketing claims say X → Loss data confirms/contradicts X
We think they lead on Y → Loss reasons validate/invalidate Y
Assumed switching dynamics → Actual switch patterns reveal truth
```

**Loss/Churn data trumps all other sources.**

## Data Types

### Competitive Losses

Deals lost to specific competitors:
- Which competitor won?
- Why did customer choose them?
- What was the deciding factor?
- Deal size and segment

### Non-Competitive Losses

Deals lost to:
- No decision (stayed with status quo)
- Built in-house
- Chose different approach entirely
- Budget/timing issues

### Competitive Churn

Customers who left for competitors:
- Which competitor did they go to?
- Cited reasons for leaving
- How long were they a customer?
- What triggered the evaluation?

### Non-Competitive Churn

Customers who left for other reasons:
- Business closed/changed
- Reduced need
- Budget cuts
- Internal solution

## Process

### 1. Loss Pattern Analysis

Group losses by competitor:
```
Competitor A: 23 losses (45%)
- Top reason: Speed (12)
- Second reason: AI features (7)
- Third reason: Price (4)

Competitor B: 15 losses (29%)
- Top reason: Enterprise features (8)
- Second reason: Integration (5)
- Third reason: Brand trust (2)
```

Identify patterns:
- Which competitors are we losing to most?
- What are consistent loss reasons?
- Are there segment patterns?

### 2. Churn Pattern Analysis

Group churn by destination:
```
To Competitor A: 8 customers (40%)
- Avg tenure before churn: 18 months
- Trigger: Competitor launched new feature
- Cited reasons: Needed AI capabilities

To No Solution: 5 customers (25%)
- Avg tenure: 6 months
- Trigger: Budget cuts
- Cited reasons: Not enough ROI proven
```

### 3. Cross-Lens Validation

Compare loss/churn data to other lens findings:

| Lens Finding | Loss Data Says | Validated? |
|-------------|----------------|------------|
| JTBD: Comp A leads on step 3 | 52% cite step 3 speed | ✓ YES |
| Forces: High switching anxiety | Only 3% cite migration fear | ✗ NO |
| Strategic: Comp B has strong moat | Comp B churn is low | ✓ YES |
| Tech: AI threat is high | 0% lost to AI platforms | ? MIXED |

Flag contradictions for investigation.

### 4. Reality Check Summary

What does actual customer behavior tell us?
- Are our assumptions validated?
- What surprised us?
- What should we investigate further?

## Output Format

Generate `loss-churn-analysis.json`:

```json
{
  "data_availability": {
    "competitive_losses": true,
    "non_competitive_losses": true,
    "competitive_churn": true,
    "non_competitive_churn": false,
    "data_period": "last 12 months",
    "total_records": 87,
    "confidence": "high"
  },
  "loss_analysis": {
    "by_competitor": {
      "competitor_a": {
        "count": 23,
        "percentage": 45,
        "reasons": [
          {"reason": "Speed/performance", "count": 12, "percentage": 52},
          {"reason": "AI features", "count": 7, "percentage": 30},
          {"reason": "Price", "count": 4, "percentage": 17}
        ],
        "segments": ["enterprise", "mid-market"],
        "avg_deal_size": 45000,
        "trend": "increasing"
      }
    },
    "top_loss_reasons_overall": [
      {"reason": "Speed/performance", "count": 25, "to_competitors": ["competitor_a", "competitor_c"]},
      {"reason": "Enterprise features", "count": 15, "to_competitors": ["competitor_b"]}
    ],
    "non_competitive_losses": {
      "no_decision": 18,
      "built_internal": 5,
      "budget_timing": 12
    }
  },
  "churn_analysis": {
    "by_destination": {
      "competitor_a": {
        "count": 8,
        "avg_tenure_months": 18,
        "trigger": "Competitor feature launch",
        "reasons": ["Needed AI capabilities", "Outgrew our solution"]
      }
    },
    "churn_rate": "8% annual",
    "competitive_churn_rate": "5% annual"
  },
  "cross_validation": {
    "validated_findings": [
      {
        "lens": "jtbd_performance",
        "finding": "Competitor A leads on job step 3 (speed)",
        "validation": "52% of losses cite speed as reason",
        "confidence_adjustment": "high → confirmed high"
      }
    ],
    "contradicted_findings": [
      {
        "lens": "forces_analysis",
        "finding": "High switching anxiety is barrier",
        "contradiction": "Only 3% cite migration concerns",
        "confidence_adjustment": "high → low",
        "investigation_needed": true
      }
    ],
    "unvalidated_findings": [
      {
        "lens": "technology_disruption",
        "finding": "AI platforms are significant threat",
        "data_gap": "No losses to AI platforms yet",
        "note": "May be leading indicator, not yet in loss data"
      }
    ]
  },
  "insights": {
    "key_insight": "Speed on job step 3 is the dominant loss driver - validated by 52% of competitive losses",
    "surprising_finding": "Switching anxiety is much lower than assumed - not a significant barrier",
    "recommended_investigation": "Why aren't AI platforms appearing in loss data yet? Early stage or not a real threat?"
  }
}
```

## Philosophy

### Ground truth

Loss/churn data is reality.
Marketing claims are aspirational.
Customer decisions reveal truth.

### Humble analysis

Be willing to invalidate your findings.
Contradictions are insights.
Data beats assumptions.

### Gaps are data

Missing loss/churn data is itself informative.
Acknowledge uncertainty.
Limit each claim to what the data shows.

## Cascading Outputs

This lens validates all others:
- Confirms or contradicts JTBD findings
- Validates or invalidates Forces dynamics
- Reality-checks Value claims
- Tests Strategic assessments
- Grounds Technology Disruption fears

## Completion Protocol

After writing all output files:

**Evaluate override condition:**
- If retention_risk = HIGH AND confidence >= MEDIUM → loss_churn_override_active = true
- Otherwise → loss_churn_override_active = false

**Write loss-churn-summary.json** to `data_dir` (from dispatch context):
{
  "lens": "loss-churn",
  "completed_at": "{ISO 8601 timestamp}",
  "competitors_analyzed": N,
  "headline": "Confirms {confirmed_claims}; contradicts {contradicted_claims}",
  "key_findings": [
    "Win rate trend: {improving|declining|stable} ({timeframe})",
    "Top loss reason: {reason} ({percentage}% of losses)",
    "Confirms: {lens_finding} from {lens_name}",
    "Contradicts: {lens_finding} from {lens_name}"
  ],
  "confidence": "{HIGH|MEDIUM|LOW|SPECULATIVE}",
  "loss_churn_override_active": true|false,
  "override_instruction": "Elevate loss/churn findings to top of all SWOT sections",
  "warnings": [],
  "data_file": "loss-churn-analysis.json"
}

Note: override_instruction field is always written but only acted on when loss_churn_override_active = true.

**Return to caller:** DONE: lens-loss-churn
