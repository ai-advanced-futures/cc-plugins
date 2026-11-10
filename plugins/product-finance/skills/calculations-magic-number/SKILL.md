---
name: calculations-magic-number
description: Calculate Magic Number (sales efficiency) with annualization logic
---

# Magic Number Calculation Skill

## Purpose

Calculate the Magic Number because it measures sales and marketing efficiency - how much new ARR is generated for each dollar spent on sales and marketing.

## When to Use

- Evaluating sales and marketing efficiency
- Determining optimal investment levels
- Benchmarking against industry standards
- Making budget allocation decisions
- Assessing readiness to scale go-to-market

## What This Skill Provides

Comprehensive sales efficiency analysis including:
- Magic Number calculation
- Annualization for non-annual periods
- Efficiency interpretation
- Investment recommendations
- Trend analysis

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| quarterly_net_new_arr | float | Yes | Net new ARR added in the most recent quarter (can be negative) |
| prior_quarter_sm_spend | float | Yes | Sales & Marketing spend in the prior quarter (must be > 0) |

## Formula

### Canonical Magic Number (lag-adjusted quarterly, annualized via ×4)
```
Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend
```

Annualizing the quarterly ARR (×4) before dividing normalizes the metric against
annual S&M spend, aligning with the standard SaaS benchmark where a score of
0.75 or more indicates healthy sales efficiency. Prior-quarter S&M spend is used to reflect the
1-quarter lag between spend and the ARR it produces.

## Benchmark Thresholds

| Magic Number | Status | Interpretation |
|--------------|--------|----------------|
| < 0 | Critical | ARR is declining - churn exceeds new sales |
| 0 up to 0.5 | Critical | Very inefficient - burning cash without results |
| 0.5 up to 0.75 | Warning | Below average efficiency |
| 0.75 up to 1.0 | Good | Average efficiency, sustainable growth |
| 1.0 up to 1.5 | Excellent | High efficiency, strong unit economics |
| 1.5 or more | Excellent | Very high efficiency (may be under-investing) |

## Strategic Interpretation

### Magic Number under 0.5
- **Diagnosis:** Sales/marketing spend is not producing adequate returns
- **Actions:**
  - Review lead quality and ICP definition
  - Optimize conversion rates
  - Evaluate sales team productivity
  - Consider reducing spend until efficiency improves

### Magic Number 0.5 up to 0.75
- **Diagnosis:** Below target but not critical
- **Actions:**
  - Optimize go-to-market strategy
  - Improve sales productivity
  - Focus on higher-quality leads
  - Test channel efficiency

### Magic Number 0.75 up to 1.0
- **Diagnosis:** Healthy, sustainable growth engine
- **Actions:**
  - Maintain current strategy
  - Test incremental spend increases
  - Monitor for degradation

### Magic Number 1.0 up to 1.5
- **Diagnosis:** Highly efficient - each $1 produces $1 or more of new ARR
- **Actions:**
  - Consider increasing investment
  - Test scaling acquisition
  - Expand to new channels/markets

### Magic Number 1.5 or more
- **Diagnosis:** May be under-investing in growth
- **Actions:**
  - Increase sales and marketing budget
  - Hire more sales capacity
  - Expand marketing programs

## Output Format

```json
{
  "magic_number": {
    "value": 0.85,
    "quarterly_net_new_arr": 212500.00,
    "prior_quarter_sm_spend": 1000000.00,
    "health_status": "good",
    "efficiency_interpretation": "Magic Number: 0.85",
    "benchmark_notes": "Healthy sales efficiency (0.75 up to 1.0). On track."
  },
  "investment_recommendation": {
    "current_efficiency": "sustainable",
    "recommended_action": "Consider testing 10-20% increase in S&M spend",
    "expected_impact": "With 0.85 efficiency, $100K additional spend should yield ~$85K new ARR"
  }
}
```

When the Magic Number is an estimate, `benchmark_notes` is null.

## Process

1. **Collect Input Data:**
   - Gather the net new ARR of the most recent quarter
   - Gather the Sales & Marketing spend of the quarter before it
   - Note measurement period

2. **Calculate Magic Number:**
   - Multiply quarterly net new ARR by 4, then divide by prior-quarter S&M spend
   - Account for any one-time costs

3. **Assess Efficiency:**
   - Compare to benchmarks
   - Determine health status
   - Interpret efficiency level

4. **Generate Recommendations:**
   - Based on efficiency level
   - Investment guidance
   - Optimization suggestions

## Quarterly Calculation Example

```
Q3 Net New ARR: $250,000
Prior-Quarter S&M Spend: $1,000,000
Magic Number = ($250,000 × 4) / $1,000,000 = 1.0 (EXCELLENT)
```

The ×4 annualizes the quarterly net new ARR against the prior quarter's annual-scale
S&M spend, capturing the standard one-quarter spend→ARR lag.

## Common Pitfalls

1. **Including one-time costs:** Strip out one-time expenses (events, rebranding) for ongoing efficiency measurement

2. **Ignoring timing:** S&M spend has a lag before producing ARR - consider 1-3 month delay

3. **Mixing gross and net ARR:** Always use NET new ARR (new sales minus churn)

4. **Not segmenting:** Calculate by channel/segment for optimization insights

## Reference Implementation

See `scripts/utils/magic_number.py` function:
- `calculate_magic_number()` - the canonical implementation

`scripts/unit_economics.py::calculate_magic_number()` is a thin delegating wrapper
that adapts the canonical `MagicNumberOutcome` into `MagicNumberResult`.

## Example Calculation

```
Quarterly Net New ARR: $2,000,000
Prior-Quarter S&M Spend: $2,500,000

Magic Number = ($2,000,000 × 4) / $2,500,000 = 3.2 (EXCELLENT)
```

**Interpretation:** For every $1 spent on sales and marketing last quarter, the
company generated $3.20 in annualized new recurring revenue. This is an excellent
growth engine — well above the 1.0 threshold for aggressive scaling.

**Investment Guidance:** At 3.2 efficiency, a $500K increase in S&M spend should
yield approximately $1.6M in annualized net new ARR.

## Relationship to Other Metrics

| Metric | Relationship |
|--------|--------------|
| CAC | Magic Number = 1 / (CAC × Months to Recover) × 12 |
| LTV:CAC | Higher LTV:CAC generally correlates with higher Magic Number |
| Rule of 40 | Both measure efficiency; Magic Number focuses on S&M specifically |

## Industry Benchmarks

| Company Stage | Target Magic Number |
|---------------|---------------------|
| Early Stage | 0.5 or more |
| Growth Stage | 0.75 or more |
| Scale Stage | 0.75 or more |
| Public Companies | 0.6 - 1.2 (median ~0.8) |
