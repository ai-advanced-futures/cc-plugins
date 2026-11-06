---
name: calculations-ltv-cac
description: Calculate LTV:CAC ratio and payback period for customer acquisition efficiency
---

# LTV:CAC Ratio Calculation Skill

## Purpose

Calculate LTV:CAC ratio and payback period because these metrics determine whether customer acquisition is sustainable and profitable.

## When to Use

- Evaluating customer acquisition efficiency
- Setting CAC budgets by channel
- Determining if growth investments are sustainable
- Preparing unit economics for investors
- Comparing acquisition channel effectiveness

## What This Skill Provides

Comprehensive LTV:CAC analysis including:
- LTV:CAC ratio with health assessment
- CAC payback period in months
- Investment efficiency interpretation
- Channel-specific recommendations
- Sustainability analysis

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ltv | float | Yes | Customer Lifetime Value |
| cac | float | Yes | Customer Acquisition Cost |
| arpu | float | No | ARPU for payback calculation |
| gross_margin_percent | float | No | Gross margin for payback calculation |

## Formulas

### LTV:CAC Ratio
```
LTV:CAC Ratio = LTV / CAC
```

### CAC Payback Period
```
CAC Payback (months) = CAC / (ARPU × Gross Margin)
```

Or equivalently:
```
CAC Payback (months) = CAC / Monthly Gross Profit per Customer
```

### Inverse: Maximum CAC
```
Maximum CAC = LTV / Target Ratio
```

For a 3:1 target ratio:
```
Maximum CAC = LTV / 3
```

## Benchmark Thresholds

### LTV:CAC Ratio Health

LTV:CAC Health Thresholds (source: constants.py::LTV_CAC_THRESHOLDS):
- Excellent: > 5:1
- Good:      3:1 – 5:1 (inclusive at 3:1)
- Warning:   1:1 – 3:1
- Critical:  < 1:1

| Ratio | Status | Interpretation | Action |
|-------|--------|----------------|--------|
| < 1:1 | Critical | Losing money on every customer | Stop acquisition, fix fundamentals |
| 1:1 – 3:1 | Warning | Not sustainable; below healthy threshold | Reduce CAC or improve LTV urgently |
| 3:1 – 5:1 | Good | Healthy SaaS unit economics (inclusive at 3:1) | Maintain and scale |
| > 5:1 | Excellent | Very efficient acquisition | Consider increasing growth investment |

### CAC Payback Health
| Payback | Status | Interpretation |
|---------|--------|----------------|
| < 6 months | Excellent | Highly efficient, enables aggressive growth |
| 6-12 months | Good | Standard SaaS benchmark |
| 12-18 months | Warning | Limits growth velocity |
| 18-24 months | Critical | Very long, cash flow strain |
| > 24 months | Critical | Unsustainable without external capital |

## Output Format

```json
{
  "ltv_cac_ratio": {
    "ratio": 4.50,
    "formatted": "4.50:1",
    "ltv": 9000.00,
    "cac": 2000.00,
    "health_status": "good",
    "investment_efficiency": "Healthy unit economics - $1 invested returns $4.50 in customer value",
    "benchmark_notes": "Good: LTV:CAC 3:1 to 5:1 (inclusive at 3:1). Healthy unit economics. Excellent is > 5:1."
  },
  "cac_payback": {
    "payback_months": 10.0,
    "monthly_gross_profit": 200.00,
    "health_status": "good",
    "cash_flow_impact": "Cash neutral in 10 months per customer"
  },
  "recommendations": [
    "LTV:CAC is in healthy range. Consider scaling acquisition spend.",
    "Maintain focus on retention to protect LTV.",
    "Test increasing CAC slightly to accelerate growth."
  ]
}
```

## Process

1. **Calculate LTV:CAC Ratio:**
   - Divide LTV by CAC
   - Format as X:1 ratio
   - Assess against benchmarks

2. **Calculate CAC Payback:**
   - Determine monthly gross profit
   - Divide CAC by monthly gross profit
   - Express in months

3. **Assess Investment Efficiency:**
   - Determine if ratio supports growth
   - Identify if under/over-investing
   - Evaluate cash flow implications

4. **Generate Recommendations:**
   - Based on ratio health
   - Based on payback period
   - Strategic growth guidance

## Interpretation Matrix

| LTV:CAC | Payback | Recommendation |
|---------|---------|----------------|
| < 3:1 | > 12 mo | Critical - Fix unit economics before growth |
| < 3:1 | < 12 mo | Focus on LTV improvement |
| 3:1 - 5:1 | > 12 mo | Optimize payback with annual contracts |
| 3:1 - 5:1 | < 12 mo | Healthy - scale confidently |
| > 5:1 | Any | Consider increasing growth investment |

## Strategic Considerations

### Low LTV:CAC (< 3:1)
**Improve LTV by:**
- Reducing churn through better onboarding
- Increasing ARPU through upsells/cross-sells
- Expanding to higher-value segments

**Reduce CAC by:**
- Optimizing acquisition channels
- Improving conversion rates
- Focusing on organic/referral growth

### High LTV:CAC (> 8:1)
**Consider:**
- Increasing CAC budget
- Expanding to new channels
- Testing higher-cost, higher-quality acquisition
- Accelerating growth rate

### Long Payback (> 12 months)
**Strategies:**
- Offer annual contracts with discount
- Increase upfront pricing
- Focus on larger customers
- Improve gross margins

## Channel-Specific Application

Different channels have different acceptable thresholds:

| Channel | Target LTV:CAC | Typical Payback |
|---------|----------------|-----------------|
| Organic/Referral | > 10:1 | < 3 months |
| Inbound Marketing | > 5:1 | 6-9 months |
| PLG | > 8:1 | 3-6 months |
| Outbound Sales | > 3:1 | 9-12 months |
| Enterprise Sales | > 2:1 | 12-18 months |
| Partnerships | > 4:1 | 6-12 months |

## Reference Implementation

See `scripts/unit_economics.py` functions:
- `calculate_ltv_cac_ratio()` - Core ratio calculation
- `calculate_cac_payback()` - Payback period calculation

## Example Calculations

**Example 1: Healthy SaaS**
```
LTV: $12,000
CAC: $3,000
LTV:CAC = 4:1 (GOOD)

ARPU: $400/month
Gross Margin: 80%
Monthly Gross Profit: $320
Payback = $3,000 / $320 = 9.4 months (GOOD)
```

**Example 2: Struggling SaaS**
```
LTV: $2,000
CAC: $2,500
LTV:CAC = 0.8:1 (CRITICAL - losing money!)

ARPU: $100/month
Gross Margin: 70%
Monthly Gross Profit: $70
Payback = $2,500 / $70 = 35.7 months (CRITICAL)
```

## Maximum CAC Calculator

Given LTV and target ratio, calculate maximum allowable CAC:

```
Target Ratio: 3:1
LTV: $9,000
Maximum CAC = $9,000 / 3 = $3,000
```

This helps set channel-specific CAC caps.
