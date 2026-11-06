---
name: calculations-rule-of-40
description: Calculate standard and weighted Rule of 40 for SaaS financial health assessment
---

# Rule of 40 Calculation Skill

## Purpose

Calculate Rule of 40 metrics because this is the gold standard for evaluating the balance between SaaS growth and profitability.

## When to Use

- Assessing overall SaaS company health
- Preparing for IPO or fundraising
- Benchmarking against public SaaS companies
- Evaluating growth vs. profitability trade-offs
- Setting strategic targets for finance OKRs

## What This Skill Provides

Comprehensive Rule of 40 analysis including:
- Classic Rule of 40 score
- Weighted Rule of 40 (growth-adjusted)
- Growth vs. profitability balance analysis
- Stage-appropriate benchmarking
- Trend analysis (with historical data)
- Actionable recommendations

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| revenue_growth_rate | float | Yes | Revenue growth rate as percentage (e.g., 50 for 50%) |
| ebitda_margin | float | Yes | EBITDA margin as percentage (can be negative) |
| company_stage | enum | No | early, growth, scale, or mature |
<!-- See docs/METHODOLOGY.md — Company Stage Definitions for ARR-to-stage mapping -->
| previous_period_growth | float | No | Previous period growth for trend analysis |
| previous_period_margin | float | No | Previous period margin for trend analysis |
| arr | float | No | Annual Recurring Revenue for context |

## Formulas

### Classic Rule of 40
```
Rule of 40 Score = Revenue Growth Rate (%) + EBITDA Margin (%)
```

Example: 50% growth + (-10%) EBITDA margin = 40% (meets Rule of 40)

### Weighted Rule of 40
```
Weighted Rule of 40 = (1.33 × Revenue Growth %) + (0.67 × EBITDA Margin %)
```

The weighted formula reflects that growth is valued ~2x more than profitability in public markets.

## Benchmark Thresholds

### Standard Thresholds (Default)
| Score | Status | Interpretation |
|-------|--------|----------------|
| >= 40 | Excellent | IPO-ready, top quartile |
| 30-40 | Good | Solid performance, above median |
| 20-30 | Warning | Below expectations, needs improvement |
| < 20 | Critical | Significant issues, urgent action needed |

### Stage-Adjusted Thresholds

**Early Stage (Pre-PMF):**
| Score | Status |
|-------|--------|
| >= 30 | Excellent |
| 20-30 | Good |
| 10-20 | Warning |
| < 10 | Critical |

**Growth Stage (Post-PMF):**
| Score | Status |
|-------|--------|
| >= 40 | Excellent |
| 30-40 | Good |
| 20-30 | Warning |
| < 20 | Critical |

**Scale/Mature Stage:**
| Score | Status |
|-------|--------|
| >= 50 | Excellent |
| 40-50 | Good |
| 30-40 | Warning |
| < 30 | Critical |

## Output Format

```json
{
  "rule_of_40_score": 45.0,
  "weighted_rule_of_40": 57.2,
  "revenue_growth_rate": 50.0,
  "ebitda_margin": -5.0,
  "health_status": "excellent",
  "benchmark_notes": "Classic Rule of 40: 45.0%\nWeighted Rule of 40: 57.2%\nExceeds the Rule of 40 threshold...",
  "balance_analysis": "Balance Type: Hypergrowth with investment (growth-first strategy)\nGrowth Rate: 50.0%\nEBITDA Margin: -5.0%",
  "recommendations": [
    "Maintain excellent performance - you're in the top quartile of SaaS companies.",
    "As growth naturally slows, begin gradually improving profitability to maintain Rule of 40 compliance."
  ],
  "trend_analysis": "Rule of 40 improved by 5.0 points (40.0% -> 45.0%) - Positive trend!"
}
```

## Process

1. **Collect Input Data:**
   - Gather current revenue growth rate
   - Calculate EBITDA margin
   - Determine company stage (optional)

2. **Calculate Rule of 40:**
   - Add growth rate to EBITDA margin
   - Calculate weighted version
   - Compare to thresholds

3. **Analyze Balance:**
   - Categorize growth vs. profitability strategy
   - Assess appropriateness for company stage
   - Identify trade-off concerns

4. **Assess Health:**
   - Apply the thresholds of the company's growth stage
   - Generate benchmark comparison
   - Identify quartile performance

5. **Generate Recommendations:**
   - Based on score and stage
   - Actionable improvement guidance
   - Strategic direction suggestions

6. **Trend Analysis (if historical data):**
   - Calculate score change
   - Analyze growth vs. margin shifts
   - Identify trajectory

## Balance Type Classifications

| Growth Rate | EBITDA Margin | Balance Type |
|-------------|---------------|--------------|
| > 40% | < 0% | Hypergrowth with investment |
| > 30% | < 10% | Growth-focused with moderate burn |
| < 20% | > 20% | Profitability-focused |
| Similar values | Similar values | Balanced growth and profitability |

## Reference Implementation

See `scripts/rule_of_40.py` for the complete Python implementation with:
- Pydantic validation models
- Stage-appropriate health assessment
- Trend analysis functions
- JSON and Markdown output formatters

## Example Calculation

**Scenario 1: Growth Company**
```
Revenue Growth: 80%
EBITDA Margin: -30%
Rule of 40: 80 + (-30) = 50% (EXCELLENT)
Weighted: (1.33 × 80) + (0.67 × -30) = 86.3% (EXCELLENT)
```

**Scenario 2: Struggling Company**
```
Revenue Growth: 15%
EBITDA Margin: -10%
Rule of 40: 15 + (-10) = 5% (CRITICAL)
Weighted: (1.33 × 15) + (0.67 × -10) = 13.2% (CRITICAL)
```

**Scenario 3: Mature Company**
```
Revenue Growth: 20%
EBITDA Margin: 25%
Rule of 40: 20 + 25 = 45% (EXCELLENT)
Weighted: (1.33 × 20) + (0.67 × 25) = 43.4% (EXCELLENT)
```

## Strategic Implications

- **Score < 20:** Urgent action needed - fix unit economics or accelerate growth
- **Score 20-40:** Focus on improving both metrics incrementally
- **Score > 40:** Maintain balance, prepare for scale
- **Score > 60:** Consider increasing investment in growth

## Industry Context

Based on Brad Feld's Rule of 40 framework and benchmarks from:
- McKinsey & Company SaaS analysis
- The SaaS CFO industry surveys
- Public SaaS company financials
