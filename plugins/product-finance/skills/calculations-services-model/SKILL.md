---
name: calculations-services-model
description: Financial modeling for consulting and professional services businesses including utilization, capacity, pipeline, and scenario analysis
---

# Services Model Calculation Skill

## Purpose

Calculate comprehensive financial metrics for consulting and professional services businesses because services firms have fundamentally different economics than SaaS — revenue is capacity-constrained, project-based, and tied directly to headcount utilization rather than recurring subscriptions.

## When to Use

- Modeling revenue capacity for a services or consulting business
- Planning headcount and hiring triggers based on utilization
- Building pipeline math from outreach through close
- Running break-even analysis on fixed costs vs. gross margin per deal
- Scenario planning across conservative, base, and stretch targets
- Preparing financial projections for investors or board meetings
- Evaluating whether to hire before or after hitting capacity ceiling

## What This Skill Provides

Comprehensive services financial modeling including:
- Utilization rate calculation and benchmarking
- Billable capacity computation
- Revenue capacity ceiling
- Project-based revenue modeling
- Full-funnel pipeline math with stage conversion rates
- Break-even analysis
- Capacity-driven hiring triggers
- Three-scenario modeling (conservative / base / stretch)

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| team_size | int | Yes | Number of billable team members |
| hours_per_person_per_year | int | No | Total working hours per person per year (default: 2,080) |
| utilization_rate_percent | float | Yes | Target utilization rate percentage (0-100) |
| average_billing_rate | float | Yes | Average hourly billing rate |
| average_deal_size | float | Yes | Average project deal size |
| num_deals_target | int | No | Target number of deals per period |
| monthly_fixed_costs | float | Yes | Total monthly fixed costs (salaries, rent, tools, etc.) |
| gross_margin_percent | float | Yes | Gross margin percentage per deal (0-100) |
| outreach_per_month | int | No | Monthly outreach volume (emails, calls, etc.) |
| outreach_to_meeting_rate | float | No | Conversion rate: outreach to meeting (0-100) |
| meeting_to_proposal_rate | float | No | Conversion rate: meeting to proposal (0-100) |
| proposal_to_close_rate | float | No | Conversion rate: proposal to close (0-100) |
| period_months | int | No | Analysis period in months (default: 12) |

## Formulas

### Utilization Rate
```
Utilization Rate = Billable Hours / Total Available Hours
Target range: 65-75% for healthy services firms
```

### Billable Capacity
```
Billable Capacity (hours) = Team Size x Hours per Person per Year x (Utilization Rate / 100)
```

### Revenue Capacity Ceiling
```
Revenue Capacity Ceiling = Billable Capacity x Average Billing Rate
```
This is the maximum revenue the current team can generate at target utilization.

### Project-Based Revenue
```
Projected Revenue = Number of Deals x Average Deal Size
```
Note: Services revenue is project-based, not MRR. Revenue recognition follows project delivery milestones.

### Pipeline Math
```
Meetings = Outreach per Month x (Outreach-to-Meeting Rate / 100)
Proposals = Meetings x (Meeting-to-Proposal Rate / 100)
Closes = Proposals x (Proposal-to-Close Rate / 100)
Pipeline Revenue = Closes x Average Deal Size
```

Typical conversion benchmarks for B2B services:
| Stage | Benchmark Range |
|-------|----------------|
| Outreach to Meeting | 2-5% |
| Meeting to Proposal | 30-50% |
| Proposal to Close | 25-40% |

### Break-Even Analysis
```
Monthly Break-Even Revenue = Monthly Fixed Costs / (Gross Margin % / 100)
Break-Even Deals per Month = Monthly Break-Even Revenue / Average Deal Size
Annual Break-Even Revenue = Monthly Break-Even Revenue x 12
```

### Capacity Planning (Hiring Trigger)
```
Revenue per Billable Person = (Hours per Person per Year x Utilization Rate / 100) x Average Billing Rate
Hire-Next Trigger = Current Revenue Capacity Ceiling x 0.85
```
When projected revenue exceeds 85% of capacity ceiling, it is time to begin hiring. Account for 2-3 month ramp time for new hires.

### Scenario Modeling
```
Conservative: 80% of base deal count, 90% of base deal size
Base: Target deal count x average deal size
Stretch: 120% of base deal count, 110% of base deal size
```

## Benchmark Thresholds

### Utilization Rate Health
| Rate | Status | Notes |
|------|--------|-------|
| < 50% | Critical | Significant underutilization; review pipeline or reduce headcount |
| 50-65% | Warning | Below target; focus on sales pipeline and project scheduling |
| 65-75% | Good | Healthy target range for sustainable services businesses |
| 75-85% | Excellent | High efficiency; monitor for burnout risk |
| > 85% | Warning | Risk of burnout, quality issues, and no capacity for new deals |

### Gross Margin per Deal
| Margin | Status | Notes |
|--------|--------|-------|
| < 30% | Critical | Unsustainable; pricing or cost structure needs overhaul |
| 30-40% | Warning | Thin margins; limited room for error |
| 40-55% | Good | Healthy for most consulting firms |
| 55-70% | Excellent | Strong margins; typical of specialized or strategic consulting |
| > 70% | Excellent | Premium positioning; ensure pricing is defensible |

### Break-Even Timeline
| Timeline | Status | Notes |
|----------|--------|-------|
| < 3 months | Excellent | Lean operation with fast path to profitability |
| 3-6 months | Good | Reasonable for early-stage services firms |
| 6-12 months | Warning | Extended runway needed; tighten costs or accelerate sales |
| > 12 months | Critical | Unsustainable without external funding |

## Output Format

```json
{
  "utilization": {
    "rate_percent": 70.0,
    "billable_hours": 29120,
    "total_available_hours": 41600,
    "team_size": 20,
    "health_status": "good",
    "benchmark_notes": "Utilization at 70% is within the healthy 65-75% target range."
  },
  "revenue_capacity": {
    "ceiling": 4368000.00,
    "billable_capacity_hours": 29120,
    "average_billing_rate": 150.00,
    "headroom_percent": 25.0,
    "health_status": "good",
    "benchmark_notes": "Current team can generate up to $4.37M at target utilization."
  },
  "project_revenue": {
    "projected_annual": 3000000.00,
    "num_deals": 30,
    "average_deal_size": 100000.00,
    "capacity_utilization_percent": 68.7,
    "health_status": "good",
    "benchmark_notes": "Projected revenue at 68.7% of capacity ceiling. Room to grow before hiring."
  },
  "pipeline": {
    "monthly_outreach": 500,
    "monthly_meetings": 15,
    "monthly_proposals": 6,
    "monthly_closes": 2,
    "monthly_pipeline_revenue": 200000.00,
    "annual_pipeline_revenue": 2400000.00,
    "conversion_rates": {
      "outreach_to_meeting": 3.0,
      "meeting_to_proposal": 40.0,
      "proposal_to_close": 33.0
    },
    "health_status": "good"
  },
  "break_even": {
    "monthly_fixed_costs": 150000.00,
    "gross_margin_percent": 50.0,
    "monthly_break_even_revenue": 300000.00,
    "annual_break_even_revenue": 3600000.00,
    "break_even_deals_per_month": 3.0,
    "months_to_break_even": 4,
    "health_status": "good",
    "benchmark_notes": "Break-even at $300K/month requires 3 deals per month at current deal size."
  },
  "capacity_planning": {
    "revenue_per_person": 218400.00,
    "hire_trigger_revenue": 3712800.00,
    "current_projected_revenue": 3000000.00,
    "months_until_hire_needed": 8,
    "health_status": "good",
    "benchmark_notes": "At current growth, next hire needed in approximately 8 months."
  },
  "scenarios": {
    "conservative": {
      "deals": 24,
      "deal_size": 90000.00,
      "revenue": 2160000.00,
      "margin": 1080000.00
    },
    "base": {
      "deals": 30,
      "deal_size": 100000.00,
      "revenue": 3000000.00,
      "margin": 1500000.00
    },
    "stretch": {
      "deals": 36,
      "deal_size": 110000.00,
      "revenue": 3960000.00,
      "margin": 1980000.00
    }
  },
  "overall_health": "good",
  "recommendations": [
    "Utilization is healthy at 70%. Maintain current scheduling discipline.",
    "Pipeline generates $2.4M annually vs. $3M target — increase outreach or improve conversion rates.",
    "Break-even requires 3 deals/month; pipeline currently produces 2/month — gap needs attention.",
    "Next hire trigger at $3.7M revenue. Begin recruiting pipeline when approaching $3.2M run rate."
  ]
}
```

## Process

1. **Collect Input Data:**
   - Gather team size, billing rates, and utilization targets
   - Collect fixed cost structure and gross margin data
   - Obtain pipeline activity metrics and conversion rates

2. **Calculate Utilization and Capacity:**
   - Compute billable hours from team size and utilization rate
   - Determine revenue capacity ceiling
   - Assess headroom vs. projected demand

3. **Model Project Revenue:**
   - Calculate projected revenue from deal count and deal size
   - Compare against revenue capacity ceiling
   - Identify capacity constraints or surplus

4. **Build Pipeline Math:**
   - Walk through outreach to close funnel
   - Apply conversion rates at each stage
   - Calculate pipeline-implied revenue vs. target

5. **Run Break-Even Analysis:**
   - Divide fixed costs by gross margin per deal
   - Determine deals and revenue needed to break even
   - Estimate timeline to break-even

6. **Determine Hiring Triggers:**
   - Calculate revenue per billable person
   - Set 85% capacity threshold as hiring trigger
   - Estimate months until trigger is reached

7. **Build Scenario Models:**
   - Conservative (80% deals, 90% deal size)
   - Base (target assumptions)
   - Stretch (120% deals, 110% deal size)
   - Calculate margin impact for each scenario

8. **Generate Recommendations:**
   - Prioritize critical issues (break-even gaps, pipeline shortfalls)
   - Provide actionable guidance for each metric area
   - Flag hiring timing and capacity planning decisions

## Example Calculation

**Input:**
- Team size: 10
- Hours per person per year: 2,080
- Utilization rate: 70%
- Average billing rate: $175/hr
- Average deal size: $75,000
- Monthly fixed costs: $120,000
- Gross margin: 55%
- Monthly outreach: 400
- Outreach to meeting: 3%
- Meeting to proposal: 40%
- Proposal to close: 30%

**Calculation:**
```
Billable Capacity = 10 x 2,080 x 0.70 = 14,560 hours
Revenue Ceiling = 14,560 x $175 = $2,548,000
Pipeline: 400 outreach -> 12 meetings -> 4.8 proposals -> 1.44 closes/month
Annual Pipeline Revenue = 1.44 x $75,000 x 12 = $1,296,000
Break-Even Revenue/Month = $120,000 / 0.55 = $218,182
Break-Even Deals/Month = $218,182 / $75,000 = 2.9 deals

Conservative: 14 deals x $67,500 = $945,000
Base: 17 deals x $75,000 = $1,275,000
Stretch: 21 deals x $82,500 = $1,732,500
```

**Recommendation:** Pipeline produces 1.44 closes/month but break-even requires 2.9 deals/month. Either increase outreach volume by 2x, improve conversion rates, or increase average deal size to close the gap.
