---
name: due-diligence-financial-dd
description: Analyze unit economics, revenue quality, and financial health
---

# Financial Due Diligence

In-depth financial analysis of the target company to evaluate revenue quality, unit economics, profitability, and financial sustainability to inform valuation and acquisition decision-making.

## What It Does

- Calculates key unit economics metrics: CAC, LTV, payback period, magic number (NDR/CAC)
- Analyzes revenue composition, quality, and sustainability
- Performs Rule of 40 scoring to assess growth-profitability balance
- Evaluates gross margins, operating margins, and profitability trajectory
- Assesses cash flow generation and working capital requirements
- Reviews debt obligations and financing structure
- Analyzes customer retention and churn metrics
- Evaluates pricing power and pricing strategy
- Identifies revenue risks and concentration issues
- Provides valuation benchmarking

## How to Use

Financial Due Diligence is a core component of the comprehensive investigation phase. It provides the financial foundation for understanding deal economics and informs pricing negotiations. Results directly impact the integration planning process and help identify cost synergy opportunities.

## Inputs

```json
{
  "financial_data": {
    "revenue_last_12m": "number",
    "gross_profit": "number",
    "operating_expenses": "number",
    "net_income": "number",
    "customer_acquisition_cost": "number",
    "lifetime_value": "number"
  },
  "revenue_data": {
    "mrr_or_arr": "number",
    "customer_count": "number",
    "arpu": "number",
    "growth_rate_yoy": "number"
  },
  "sustainability_metrics": {
    "churn_rate": "number",
    "ndr_rate": "number",
    "repeat_purchase_rate": "number"
  }
}
```

## Outputs

```json
{
  "unit_economics": {
    "customer_acquisition_cost": "number",
    "lifetime_value": "number",
    "ltv_cac_ratio": "number",
    "payback_period_months": "number",
    "magic_number": "number",
    "assessment": "string"
  },
  "revenue_quality": {
    "revenue_composition": {
      "recurring_percentage": "number",
      "one_time_percentage": "number"
    },
    "revenue_concentration": {
      "top_10_customers_percentage": "number",
      "top_customer_percentage": "number",
      "risk_level": "string"
    },
    "revenue_sustainability": "string"
  },
  "profitability_analysis": {
    "gross_margin": "number",
    "gross_margin_trend": "string",
    "operating_margin": "number",
    "net_margin": "number",
    "rule_of_40_score": "number"
  },
  "growth_metrics": {
    "revenue_growth_yoy": "number",
    "growth_sustainability": "string",
    "growth_drivers": ["string"]
  },
  "cash_flow_analysis": {
    "free_cash_flow": "number",
    "cash_conversion": "number",
    "working_capital_needs": "number"
  },
  "financial_health_score": "number",
  "valuation_benchmarks": {
    "ev_revenue_multiple": "number",
    "ev_ebitda_multiple": "number",
    "comparable_companies": ["string"]
  },
  "financial_risks": {
    "key_risks": ["string"],
    "revenue_at_risk": "string",
    "profitability_concerns": ["string"]
  }
}
```

## Dual-Scoring Design

This skill's scoring methodology and the interactive `/corporate-development:analyze` command both feed the same Python `HealthScorer` (`corporate_development/financial_dd/`), but at different abstraction levels:

- **This skill** operates on raw financial inputs (revenue, COGS, customer metrics) and applies algorithmic sub-metric weights directly.
- **The analyze command** collects LLM-guided narrative assessments from practitioners, aggregates them into component buckets, then calls the same underlying scorer.

Sub-metric weights differ between the two layers because the data available at each layer differs. This is intentional architecture — not a contradiction.

## Scoring Methodology

- **Unit Economics (1-10)**: LTV/CAC ratio (40%), payback period (30%), magic number (20%), trend trajectory (10%)
  - Healthy: LTV/CAC >3, payback <12 months, magic number >0.7
- **Revenue Quality (1-10)**: Recurring revenue (40%), customer concentration (30%), sustainability (20%), growth stickiness (10%)
- **Profitability (1-10)**: Gross margin strength (30%), operating leverage (30%), net profitability (20%), trend (20%)
- **Rule of 40**: Revenue growth % + operating margin % should equal or exceed 40 for healthy SaaS companies

## Rule of 40 Framework

Companies scoring 40+ balance growth and profitability effectively:
- 40-50: Well-balanced, sustainable growth model
- 50-60: Strong execution with either growth or profitability advantage
- 60+: Exceptional performance (rare)
- <40: Requires optimization in growth or profitability

## Gate Logic

- **GO** - Financial health score >7, LTV/CAC >2.5, revenue quality >7, recurring revenue >70%
- **NO_GO** - Financial health <5, unsustainable unit economics, >50% revenue concentration in one customer
- **CONDITIONAL** - Proceed if scores 5-7 with clear path to profitability or unit economics improvement

## Integrations

- **product-finance** - Financial modeling, SaaS metrics analysis, subscription revenue models
- **tech-budget** - Cost structure analysis, R&D spending benchmarking

## Related Skills

- Operational Due Diligence - Cost structure and operational efficiency
- Customer Due Diligence - Retention and churn impacts on unit economics
- Product Due Diligence - Revenue sustainability tied to product differentiation

## Used By

- Command: `/corporate-development:analyze`
- Agent: `financial-analyst`

