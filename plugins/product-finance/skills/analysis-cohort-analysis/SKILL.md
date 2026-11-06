---
name: analysis-cohort-analysis
description: Perform cohort retention and revenue analysis for customer lifecycle insights
---

# Cohort Analysis Skill

## Purpose

Perform cohort retention and revenue analysis because understanding customer behavior over time reveals true unit economics and identifies retention opportunities.

## When to Use

- Analyzing customer retention patterns
- Tracking revenue expansion/contraction by cohort
- Identifying churn risk factors
- Measuring product-market fit
- Evaluating onboarding effectiveness
- Preparing investor-grade retention metrics

## What This Skill Provides

Comprehensive cohort analysis including:
- Monthly/quarterly cohort retention curves
- Net revenue retention (NRR) by cohort
- Gross revenue retention (GRR) by cohort
- Cohort comparison and trends
- Lifetime value by cohort
- Churn pattern identification

## Input Requirements

### Cohort Data Structure
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cohort_date | date | Yes | Month/quarter the cohort started |
| customer_id | string | Yes | Unique customer identifier |
| initial_mrr | float | Yes | MRR at start of subscription |
| current_mrr | float | Yes | Current MRR (0 if churned) |
| churn_date | date | No | Date customer churned (if applicable) |
| expansion_mrr | float | No | MRR from upgrades/upsells |
| contraction_mrr | float | No | MRR lost from downgrades |

### Analysis Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| analysis_date | date | Yes | Date of analysis |
| cohort_period | enum | No | monthly, quarterly (default: monthly) |
| lookback_periods | int | No | Number of periods to analyze (default: 12) |

## Key Metrics

### Logo Retention (Customer Count)
```
Logo Retention % = (Customers Active at Period N) / (Customers in Original Cohort) × 100
```

### Gross Revenue Retention (GRR)
```
GRR = (Starting MRR - Churn - Contraction) / Starting MRR × 100
```

GRR excludes expansion - measures how well you retain existing revenue.

### Net Revenue Retention (NRR)
```
NRR = (Starting MRR - Churn - Contraction + Expansion) / Starting MRR × 100
```

NRR includes expansion - can exceed 100% if expansion > churn + contraction.

### Dollar-Based Net Retention (DBNR)
```
DBNR = (MRR from Same Customers at Period N) / (MRR at Period 0) × 100
```

Same as NRR but expressed over time for cohort curves.

## Output Format

### Retention Matrix
```
| Cohort  | M0    | M1   | M2   | M3   | M4   | M5   | M6   |
|---------|-------|------|------|------|------|------|------|
| Jan '24 | 100%  | 92%  | 88%  | 85%  | 83%  | 81%  | 80%  |
| Feb '24 | 100%  | 90%  | 86%  | 83%  | 80%  | 78%  | -    |
| Mar '24 | 100%  | 93%  | 89%  | 86%  | 84%  | -    | -    |
```

### NRR Matrix
```
| Cohort  | M0    | M3    | M6    | M12   |
|---------|-------|-------|-------|-------|
| Jan '24 | 100%  | 105%  | 112%  | 125%  |
| Feb '24 | 100%  | 102%  | 108%  | -     |
| Mar '24 | 100%  | 107%  | 115%  | -     |
```

### JSON Output
```json
{
  "cohort_analysis": {
    "summary": {
      "total_cohorts": 12,
      "average_m3_retention": 85.0,
      "average_m6_retention": 78.0,
      "average_m12_retention": 70.0,
      "average_nrr": 115.0,
      "average_grr": 88.0
    },
    "cohorts": [
      {
        "cohort_date": "2024-01",
        "initial_customers": 50,
        "initial_mrr": 75000,
        "retention_curve": [100, 92, 88, 85, 83, 81, 80],
        "nrr_curve": [100, 102, 105, 108, 112, 115, 118],
        "ltv_estimate": 11250
      }
    ],
    "trends": {
      "retention_improving": true,
      "nrr_trend": "stable",
      "churn_concentration": "Month 1-3"
    }
  }
}
```

## Process

1. **Group Customers by Cohort:**
   - Define cohort periods (monthly/quarterly)
   - Assign each customer to their start cohort
   - Track their status over time

2. **Calculate Retention for Each Period:**
   - Count active customers at each milestone
   - Calculate percentage of original cohort
   - Build retention curve

3. **Calculate Revenue Metrics:**
   - Track MRR at each milestone
   - Separate expansion, contraction, churn
   - Calculate GRR and NRR

4. **Compare Cohorts:**
   - Identify best/worst performing cohorts
   - Look for patterns (seasonality, product changes)
   - Calculate averages and trends

5. **Generate Insights:**
   - Identify churn concentration points
   - Highlight expansion opportunities
   - Compare to benchmarks

## Benchmark Thresholds

### Logo Retention Benchmarks
| Period | Excellent | Good | Warning | Critical |
|--------|-----------|------|---------|----------|
| Month 3 | > 90% | 80-90% | 70-80% | < 70% |
| Month 6 | > 85% | 75-85% | 65-75% | < 65% |
| Month 12 | > 75% | 65-75% | 55-65% | < 55% |

### NRR Benchmarks (B2B SaaS)
| NRR | Status | Interpretation |
|-----|--------|----------------|
| > 130% | Excellent | Best-in-class expansion |
| 110-130% | Good | Healthy growth from existing customers |
| 100-110% | Warning | Minimal expansion, some churn |
| < 100% | Critical | Net revenue loss from existing customers |

### GRR Benchmarks
| GRR | Status | Interpretation |
|-----|--------|----------------|
| > 95% | Excellent | Very low churn |
| 90-95% | Good | Healthy retention |
| 85-90% | Warning | Moderate churn |
| < 85% | Critical | High churn, retention crisis |

## Churn Pattern Analysis

### Where Churn Happens
- **Month 1:** Onboarding failure, bad fit customers
- **Month 2-3:** Failed to achieve first value
- **Month 6:** Didn't expand usage
- **Month 12:** Contract renewal decision

### Intervention Points
| Period | Churn Cause | Intervention |
|--------|-------------|--------------|
| M1 | Onboarding friction | Better activation flow |
| M2-3 | No value realized | Success milestones, health scoring |
| M6 | Limited adoption | Feature discovery, training |
| M12 | Price/value mismatch | Retention offers, account reviews |

## Cohort Comparison Use Cases

### Product Impact
Compare cohorts before/after feature launch:
```
Pre-Launch Cohorts (Jan-Mar): 75% M6 retention
Post-Launch Cohorts (Apr-Jun): 82% M6 retention
Feature Impact: +7% retention improvement
```

### Segment Comparison
Compare cohorts by customer segment:
```
Enterprise Cohorts: 90% M12 retention
SMB Cohorts: 65% M12 retention
Focus: Improve SMB onboarding or shift ICP to Enterprise
```

### Channel Comparison
Compare cohorts by acquisition source:
```
Inbound Cohorts: 85% M6 retention
Outbound Cohorts: 78% M6 retention
Action: Qualify outbound leads more strictly
```

## LTV Calculation from Cohorts

Using observed cohort retention to calculate LTV:
```
LTV = ARPU × Sum(Retention Rates for all periods)

Example:
ARPU: $1,000/month
Retention: [100%, 92%, 88%, 85%, 83%, 81%, 80%, 78%, 77%, 76%, 75%, 75%]
LTV = $1,000 × (1 + 0.92 + 0.88 + ... + 0.75) = $1,000 × 10.07 = $10,070
```

This is more accurate than formula-based LTV when you have sufficient cohort data.

## Implementation Considerations

### Data Requirements
- Minimum 6 months of cohort data for meaningful analysis
- At least 30 customers per cohort for statistical relevance
- Consistent tracking of MRR changes (expansion, contraction)

### Frequency
- Calculate monthly for operational review
- Quarterly deep-dive for strategic planning
- Annual for investor reporting

### Visualization
- Retention heatmaps
- Cohort curves overlaid
- NRR waterfall charts
- Trend lines for improvement

## Advanced Analysis

### Predictive Churn
Use cohort patterns to predict churn:
```
If cohort typically loses 15% by Month 3:
- Customers in Month 2 with low engagement are high churn risk
- Trigger intervention before typical churn point
```

### Revenue Forecasting
Use NRR curves for revenue projection:
```
Existing MRR: $100,000
Average 12-month NRR: 115%
Projected MRR from existing customers in 12 months: $115,000
```
