---
name: calculations-unit-economics
description: Calculate CAC, LTV, and comprehensive unit economics for SaaS businesses
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/unit_economics.py *), Edit(/.product-finance/unit-economics-input.json)
---

# Unit Economics Calculation Skill

## Purpose

Calculate comprehensive unit economics metrics because healthy unit economics are the foundation of sustainable SaaS growth and profitability.

## When to Use

- Calculating Customer Acquisition Cost (CAC)
- Calculating Customer Lifetime Value (LTV)
- Analyzing LTV:CAC ratio health
- Determining CAC payback period
- Evaluating overall unit economics health
- Preparing investor or board presentations on efficiency

## What This Skill Provides

Comprehensive unit economics analysis including:
- CAC calculation with benchmark comparison
- LTV calculation with average customer lifespan
- LTV:CAC ratio with health assessment
- CAC payback period analysis
- Overall health status and recommendations

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sales_costs | float | Yes | Total sales team costs (salaries, commissions, benefits) |
| marketing_costs | float | Yes | Total marketing spend (advertising, content, events) |
| new_customers | int | Yes | Number of new customers acquired |
| arpu | float | Yes | Average Revenue Per User per month |
| gross_margin_percent | float | Yes | Gross margin percentage (0-100) |
| churn_rate_percent | float | Yes | Monthly churn rate percentage (0-100) |
| net_new_arr | float | No | Net new ARR (for Magic Number calculation) |
| prior_quarter_sm_spend | float | No | S&M spend of the quarter before the quarterly net_new_arr (estimated when absent) |
| period_months | int | No | Period in months (default: 12) |

## Formulas

### Customer Acquisition Cost (CAC)
```
CAC = (Sales Costs + Marketing Costs) / New Customers
```

### Lifetime Value (LTV)
```
LTV = ARPU × (Gross Margin % / 100) / (Churn Rate % / 100)
```

Alternative form:
```
LTV = Monthly Gross Profit × Average Customer Lifespan
Average Customer Lifespan = 1 / Monthly Churn Rate
```

### LTV:CAC Ratio
```
LTV:CAC Ratio = LTV / CAC
```

### CAC Payback Period
```
CAC Payback (months) = CAC / (ARPU × Gross Margin %)
```

## Benchmark Thresholds

### CAC Health
| Threshold | Status | Notes |
|-----------|--------|-------|
| < $100 | Excellent | Viral B2C products |
| $100-$500 | Good | SMB B2C/B2B SaaS |
| $500-$2,000 | Warning | Ensure LTV:CAC > 3:1 |
| $2,000-$10,000 | Warning | Only for high-ACV enterprise |
| > $10,000 | Critical | Requires very high ACV |

### LTV:CAC Ratio Health
| Ratio | Status | Interpretation |
|-------|--------|----------------|
| < 1:1 | Critical | Losing money per customer |
| 1:1 - 3:1 | Warning | Marginally viable |
| 3:1 - 5:1 | Good | Target range |
| 5:1 - 8:1 | Excellent | Very efficient |
| > 8:1 | Warning | May be under-investing in growth |

### CAC Payback Health
| Payback | Status | Notes |
|---------|--------|-------|
| < 6 months | Excellent | Enables rapid scaling |
| 6-12 months | Good | Acceptable for most SaaS |
| 12-18 months | Warning | Limits growth velocity |
| > 18 months | Critical | Too long to scale profitably |

## Output Format

```json
{
  "cac": {
    "value": 8000.00,
    "total_acquisition_costs": 800000.00,
    "new_customers": 100,
    "health_status": "warning",
    "benchmark_notes": "High CAC ($2,000-$10,000). Acceptable only for high-ACV enterprise deals."
  },
  "ltv": {
    "value": 40000.00,
    "arpu": 1000.00,
    "gross_margin_percent": 80.0,
    "churn_rate_percent": 2.0,
    "average_customer_lifespan_months": 50.0,
    "health_status": "excellent",
    "benchmark_notes": "Excellent LTV (>$10,000). Strong foundation for growth."
  },
  "ltv_cac_ratio": {
    "ratio": 5.00,
    "formatted": "5.00:1",
    "health_status": "excellent",
    "benchmark_notes": "Excellent: LTV:CAC 5:1 to 8:1. Very efficient. Strong growth potential."
  },
  "cac_payback": {
    "payback_months": 10.0,
    "monthly_gross_profit": 800.00,
    "health_status": "good",
    "benchmark_notes": "Good: Payback 6-12 months. Acceptable for most SaaS businesses."
  },
  "overall_health": "good",
  "recommendations": [
    "Unit economics are healthy! Focus on scaling efficiently while maintaining these metrics."
  ]
}
```

## Process

1. **Collect Input Data:**
   - Gather sales and marketing costs
   - Count new customers for period
   - Determine ARPU, gross margin, and churn rate

2. **Calculate CAC:**
   - Sum total acquisition costs
   - Divide by new customers
   - Assess against benchmarks

3. **Calculate LTV:**
   - Apply LTV formula
   - Calculate average customer lifespan
   - Assess against benchmarks

4. **Calculate LTV:CAC Ratio:**
   - Divide LTV by CAC
   - Compare to 3:1 target
   - Identify if under/over-investing

5. **Calculate CAC Payback:**
   - Divide CAC by monthly gross profit
   - Compare to 12-month target

6. **Generate Recommendations:**
   - Based on health status of each metric
   - Prioritize critical issues
   - Provide actionable guidance

## Run the Script

Do these steps only when this skill runs as `/product-finance:calculations-unit-economics`. When a command or an agent tells you to read this page, do not do these steps: follow the steps of that command or agent, because it has its own steps for the figures.

1. Write the inputs that the person gave to `.product-finance/unit-economics-input.json` with the Write tool: 1 JSON object, with the field names of the Input Requirements table. Write each number as a JSON number. Leave out each input that the person did not give.
2. Run this command 1 time, as the only command of the Bash call:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/unit_economics.py --input .product-finance/unit-economics-input.json --format markdown
   ```

3. Show the output of the script to the person. An exit with code 3 lists each input that the script refused, one on each line. When a listed value is a number that you wrote as text, or an input that you wrote under another name, write it again as a JSON number under the name of the line, and run the command again 1 time. When a listed value is the value that the person gave, show the lines to the person and ask for a value that the script accepts, because only the person can change an input. When a run exits with a code other than 0 and 3, work out the figures with the formulas of this page, and tell the person that no script ran. Do not read a file of the plugin, because this page gives each input name.

## Example Calculation

**Input:**
- Sales costs: $500,000
- Marketing costs: $300,000
- New customers: 100
- ARPU: $100/month
- Gross margin: 80%
- Monthly churn: 2%

**Calculation:**
```
CAC = ($500,000 + $300,000) / 100 = $8,000
LTV = $100 × 0.80 / 0.02 = $4,000
LTV:CAC = $4,000 / $8,000 = 0.5:1 (CRITICAL!)
Payback = $8,000 / ($100 × 0.80) = 100 months (CRITICAL!)
```

**Recommendation:** This example shows poor unit economics - LTV:CAC < 1:1 means losing money on every customer.
