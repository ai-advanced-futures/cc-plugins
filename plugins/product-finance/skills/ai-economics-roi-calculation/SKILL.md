---
name: ai-economics-roi-calculation
description: Calculate AI ROI with break-even analysis and investment recommendations
---

# AI ROI Calculation Skill

## Purpose

Calculate comprehensive AI ROI because demonstrating positive return on AI investment is essential for justifying continued AI development and scaling AI features.

## When to Use

- Making AI investment decisions
- Preparing CFO/board AI economics reports
- Evaluating AI feature profitability
- Comparing AI build vs. buy decisions
- Setting AI budget and targets

## What This Skill Provides

Comprehensive AI ROI analysis including:
- AI ROI percentage and ratio
- Net AI value calculation
- Break-even analysis
- Payback period calculation
- Investment recommendations
- CFO-ready reporting format

## Input Requirements

### AI Cost Data
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total_ai_cost | float | Yes | Total AI costs for the period |
| ai_interactions | int | Yes | Total AI interactions/API calls |
| active_users | int | Yes | Number of active users |
| total_revenue | float | Yes | Total revenue for the period |
| period_months | int | No | Period in months (default: 1) |

### AI Value Data
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ai_enabled_revenue | float | Yes | Revenue from AI-powered features |
| non_ai_revenue | float | Yes | Revenue from non-AI features |
| premium_pricing_uplift | float | No | Price premium for AI (%) |
| time_saved_hours | float | No | Hours saved through AI |
| employee_fully_loaded_cost | float | No | Cost per employee hour |
| ai_feature_churn_rate | float | No | Churn with AI features (%) |
| non_ai_churn_rate | float | No | Churn without AI (%) |
| ai_expansion_revenue | float | No | AI-driven expansion revenue |

## Formulas

### AI ROI Percentage
```
AI ROI (%) = ((AI Value - AI Cost) / AI Cost) × 100
```

### AI ROI Ratio
```
AI ROI Ratio = AI Value / AI Cost
```

Interpretation: A ratio of 3.0 means $3 in value for every $1 in AI cost.

### Net AI Value
```
Net AI Value = AI Value - AI Cost
```

### Break-Even Analysis
```
Monthly Net Value = (Annual AI Value - Annual AI Cost) / 12
Months to Break-Even = Annual AI Cost / Monthly Net Value
```

### Payback Period
```
Payback Period (months) = Total AI Investment / Monthly Net Value
```

## Benchmark Thresholds

### AI ROI Health
| ROI % | Status | Interpretation |
|-------|--------|----------------|
| < 0% | Critical | Losing money on AI investment |
| 0-50% | Warning | Marginal returns, needs improvement |
| 50-100% | Good | Positive returns, continue optimizing |
| 100-200% | Good | Strong returns, consider scaling |
| > 200% | Excellent | Excellent returns, invest more |

### ROI Ratio Interpretation
| Ratio | Interpretation |
|-------|----------------|
| < 1:1 | AI costs exceed value - unsustainable |
| 1:1 - 1.5:1 | Break-even to marginal |
| 1.5:1 - 2:1 | Positive but optimize |
| 2:1 - 3:1 | Good investment |
| > 3:1 | Excellent investment |

### Break-Even Timeline
| Timeline | Status | Action |
|----------|--------|--------|
| < 6 months | Excellent | Accelerate investment |
| 6-12 months | Good | Continue as planned |
| 12-18 months | Warning | Optimize before scaling |
| > 18 months | Critical | Reduce cost or improve value |

## Output Format

```json
{
  "ai_roi_summary": {
    "ai_roi_percentage": 250.0,
    "ai_roi_ratio": 3.5,
    "net_ai_value_annual": 525000.00,
    "break_even_months": 3.4,
    "payback_period_months": 3.4,
    "overall_health": "excellent"
  },
  "ai_costs": {
    "cost_per_interaction": 0.035,
    "cost_per_user_per_month": 3.50,
    "ai_cost_percentage_of_revenue": 7.0,
    "total_ai_cost": 35000.00,
    "annualized_ai_cost": 420000.00,
    "health_status": "good"
  },
  "ai_value": {
    "ai_enabled_revenue": 500000.00,
    "ai_revenue_percentage": 60.0,
    "total_ai_value": 685000.00,
    "value_breakdown": {
      "ai_enabled_revenue": 500000.00,
      "premium_pricing_value": 100000.00,
      "productivity_value": 50000.00,
      "retention_value": 15000.00,
      "expansion_value": 10000.00,
      "time_to_value_acceleration": 10000.00
    },
    "health_status": "excellent"
  },
  "recommendations": [
    "Excellent AI ROI (>200%): Strong business case. Consider expanding AI features.",
    "Document AI value attribution methodology for CFO and board presentations.",
    "Fast payback period: Excellent. Use this as evidence to justify additional AI investments."
  ]
}
```

## Process

1. **Calculate AI Costs:**
   - Aggregate all AI-related costs
   - Include API, infrastructure, development
   - Annualize for consistent comparison

2. **Calculate AI Value:**
   - Sum all value sources
   - Revenue, productivity, retention, expansion
   - Annualize for consistent comparison

3. **Calculate ROI:**
   - Apply ROI formula
   - Calculate net value
   - Determine ratio

4. **Break-Even Analysis:**
   - Calculate monthly net value
   - Determine break-even timeline
   - Assess payback period

5. **Generate Recommendations:**
   - Based on ROI level
   - Investment guidance
   - Optimization priorities

## ROI Framework Visualization

```
┌─────────────────────────────────────────────────┐
│                AI ROI Calculation                │
├─────────────────────────────────────────────────┤
│                                                  │
│  AI Value (Annual):        $  945,000.00        │
│  AI Costs (Annual):      - $  210,000.00        │
│                           ════════════════       │
│  Net AI Value:             $  735,000.00        │
│                                                  │
│  AI ROI = (Value - Cost) / Cost × 100           │
│  AI ROI = ($945,000 - $210,000) / $210,000      │
│  AI ROI = 350%                                   │
│                                                  │
│  Return Ratio = 4.5x                             │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Investment Decision Framework

### Invest More If:
- AI ROI > 200%
- Break-even < 6 months
- AI revenue growing faster than costs
- Competitive advantage from AI

### Maintain Investment If:
- AI ROI 50-200%
- Break-even 6-12 months
- Value stable or growing
- No better investment alternatives

### Optimize Before Scaling If:
- AI ROI 0-50%
- Break-even 12-18 months
- Costs growing faster than value
- Optimization opportunities exist

### Reconsider Investment If:
- AI ROI < 0%
- Break-even > 18 months
- Value declining
- Better alternatives available

## CFO Presentation Format

### Executive Summary
```
AI Investment Analysis - Q4 2024

BOTTOM LINE: $3.50 return for every $1 invested in AI

Key Metrics:
- Annual AI Cost: $420,000
- Annual AI Value: $1,470,000
- Net AI Contribution: $1,050,000
- AI ROI: 250%
- Payback Period: 3.4 months

Recommendation: INCREASE AI INVESTMENT by 25%
Expected Impact: Additional $350,000 in annual value
```

### Supporting Analysis
1. Cost breakdown by provider/feature
2. Value breakdown by source
3. Trend over past 4 quarters
4. Comparison to industry benchmarks
5. Risks and mitigation strategies

## Sensitivity Analysis

### Cost Sensitivity
```
If AI costs increase 20%:
- New AI Cost: $504,000
- New ROI: 192% (still positive)
- Break-even: 4.1 months
```

### Value Sensitivity
```
If AI value decreases 20%:
- New AI Value: $1,176,000
- New ROI: 180% (still positive)
- Break-even: 4.3 months
```

### Combined Stress Test
```
Costs +20%, Value -20%:
- ROI: 133% (still positive)
- Break-even: 5.6 months
- Assessment: Investment remains justified
```

## Reference Implementation

See `scripts/ai_roi_calculator.py` for the complete Python implementation with:
- `AIROIInput` model combining cost and value
- `calculate_ai_roi()` comprehensive function
- Break-even and payback calculation
- Recommendation generation
- JSON and Markdown formatters

## Example Calculation

**Scenario: AI-Powered SaaS Product**

**Costs (Monthly):**
- API Costs: $35,000
- Infrastructure: $5,000
- Total Monthly: $40,000
- Annualized: $480,000

**Value (Annual):**
- AI-Enabled Revenue: $1,200,000
- Premium Pricing Value: $200,000
- Productivity Savings: $100,000
- Retention Value: $50,000
- Total Value: $1,550,000

**ROI Calculation:**
```
Net AI Value = $1,550,000 - $480,000 = $1,070,000
AI ROI = ($1,070,000 / $480,000) × 100 = 223%
ROI Ratio = $1,550,000 / $480,000 = 3.2x
Break-Even = $480,000 / ($1,070,000/12) = 5.4 months
```

**Recommendation:** Excellent ROI. Consider increasing AI investment by 30% to accelerate growth.
