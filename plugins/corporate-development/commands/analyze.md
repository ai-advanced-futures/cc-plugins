---
description: Phase 4. Do the financial due diligence of one target.
argument-hint: "[--target <id or name>]"
---
# /corporate-development:analyze

Perform financial due diligence: evaluate revenue quality, unit economics, growth sustainability, and valuation appropriateness.

## When to use

- After operational audit confirms acceptable integration risk
- Validating financial assumptions from discovery
- Building financial models for deal pricing
- Assessing business quality and predictability
- Before creating integration and investment plans

## What it does

1. **Financial Data Collection** - Gathers revenue, expenses, unit economics data
2. **Revenue Quality Assessment** - Analyzes recurring revenue, customer concentration, churn rates
3. **Unit Economics Analysis** - Calculates CAC, LTV, payback period, efficiency metrics
4. **Growth Sustainability** - Evaluates whether growth rate is sustainable
5. **Rule of 40 Scoring** - Calculates business quality using Rule of 40 framework
6. **Valuation Analysis** - Assesses whether asking price is reasonable

## Required Input

```bash
/corporate-development:analyze --target TARGET_ID
```

Or run interactively:
```bash
/corporate-development:analyze
```

You'll provide financial data and business metrics:
- Annual revenue and growth trajectory
- Revenue breakdown (recurring vs one-time)
- Customer acquisition and retention metrics
- Profitability and margin analysis
- Cash flow characteristics

## Interactive Flow

```
Which target would you like to analyze?
Target ID or name: target_001

Financial Overview:
1. Current annual revenue ($M): 25
2. Last 2 years revenue growth (%): 35% YoY
3. Recurring revenue (%): 75%
4. One-time revenue (%): 25%

Customer Metrics:
1. Total customers: 150
2. Average deal size: $167K
3. Customer concentration (top 5 customers % of revenue): 35%
4. Annual churn rate (%): 8%
5. Gross retention rate (%): 95%

Sales & Marketing Metrics:
1. Annual sales/marketing spend ($M): 8
2. Annual new customer count: 45
3. Customer acquisition cost (CAC) ($K): 35
4. CAC payback period (months): 14
5. Lifetime value (LTV) ($K): 280

Profitability Analysis:
1. Gross margin (%): 75%
2. EBITDA ($M): 3
3. EBITDA margin (%): 12%
4. Operating expenses breakdown:
   - S&M: 32% of revenue
   - R&D: 24% of revenue
   - G&A: 12% of revenue

Valuation Information:
1. Asking price ($M): 150
2. Preferred exit multiple: 6x revenue
```

The command analyzes all metrics and generates financial health scores.

## Outputs

**financial_analysis.json** - Detailed financial findings
```json
{
  "analysis_date": "2026-02-03",
  "target": {
    "id": "target_001",
    "company_name": "Example Inc",
    "annual_revenue": 25
  },
  "revenue_quality": {
    "recurring_revenue_pct": 75,
    "recurring_revenue_dollars": 18.75,
    "one_time_revenue_dollars": 6.25,
    "customer_concentration": 35,
    "top_5_customers_pct": 35,
    "annual_churn_rate": 0.08,
    "gross_retention_rate": 0.95,
    "net_retention_rate": 1.02,
    "revenue_quality_score": 78
  },
  "unit_economics": {
    "customer_acquisition_cost": 35000,
    "lifetime_value": 280000,
    "ltv_cac_ratio": 8.0,
    "cac_payback_months": 14,
    "cac_efficiency_score": 8,
    "average_deal_size": 167000,
    "total_customers": 150,
    "annual_new_customers": 45,
    "unit_economics_score": 82
  },
  "profitability": {
    "gross_margin_pct": 75,
    "gross_profit": 18.75,
    "ebitda": 3.0,
    "ebitda_margin_pct": 12,
    "operating_margin_pct": 8,
    "profitability_score": 65
  },
  "growth_analysis": {
    "revenue_growth_rate": 35,
    "growth_sustainability": "SUSTAINABLE",
    "market_sizing": "$50B TAM",
    "market_share": 0.05,
    "growth_rate_justification": "Strong product-market fit, expanding use cases",
    "growth_score": 88
  },
  "rule_of_40": {
    "growth_rate": 35,
    "ebitda_margin": 12,
    "rule_of_40_score": 47,
    "business_quality": "ABOVE_AVERAGE",
    "classification": "Healthy SaaS business"
  },
  "valuation_assessment": {
    "asking_price": 150,
    "asking_multiple_revenue": 6.0,
    "comparable_multiples": {
      "median_saas_multiple": 5.8,
      "high_growth_multiple": 7.2,
      "comparable_range": "5.0x - 6.5x"
    },
    "valuation_assessment": "FAIR",
    "recommended_entry_price": 135,
    "recommended_range": "125-145",
    "valuation_note": "Price reasonable given growth and quality"
  },
  "financial_health_score": 78,
  "recommendation": "PROCEED",
  "next_step": "plan"
}
```

**financial_summary.md** - Executive summary with:
- Revenue quality and recurring revenue analysis
- Unit economics scorecard (CAC, LTV, payback)
- Growth sustainability assessment
- Profitability and margin analysis
- Rule of 40 score and business quality classification
- Valuation appropriateness and pricing recommendation

## Financial Health Scoring

> **Dual-scoring design note:** This section describes the LLM-guided scoring used by the interactive command. The `financial-dd` skill (`skills/due-diligence-financial-dd/SKILL.md`) exposes the same scoring formula as a reusable skill component with its own sub-metric weightings. Both layers feed the same Python `HealthScorer` in `corporate_development/financial_dd/`. The sub-metric weights differ slightly because the skill uses raw financial inputs while the command aggregates LLM-collected narrative scores into component buckets first. This is intentional — the command layer adapts the scoring to what a practitioner can actually observe.

Overall financial health score (0-100) combines:

```
Revenue Quality (30%):
  - Recurring revenue %: 0-10
  - Customer concentration (inverted): 0-10
  - Churn rate (inverted): 0-10
  - Net retention: 0-10

Unit Economics (25%):
  - LTV/CAC ratio: 0-10 (target >5)
  - CAC payback: 0-10 (target <12 months)
  - Average deal size health: 0-10
  - Growth in customer count: 0-10

Profitability (20%):
  - Gross margin: 0-10 (target >70%)
  - EBITDA margin: 0-10
  - Operating margin: 0-10
  - Margin trend: 0-10

Growth (15%):
  - Growth rate sustainability: 0-10
  - Market opportunity: 0-10
  - Market share position: 0-10

Valuation (10%):
  - Price to ARR multiple reasonableness: 0-10
  - Discount to comparables: 0-10

Overall Health = (Quality × 0.30) + (UE × 0.25) + (Profit × 0.20) + (Growth × 0.15) + (Valuation × 0.10)
```

## Rule of 40 Analysis

Rule of 40 = Growth Rate (%) + EBITDA Margin (%)

```
Score ≥ 40: Excellent - Well-balanced growth and profitability
Score 30-39: Good - Acceptable balance
Score 20-29: Fair - Need to improve either growth or profitability
Score < 20: Poor - Business needs restructuring

Example:
Growth Rate: 35% + EBITDA Margin: 12% = Rule of 40 Score: 47
Classification: ABOVE_AVERAGE - Strong business quality
```

## Revenue Quality Framework

```
High Quality (Score 75+):
  - ≥70% recurring revenue
  - <15% customer concentration
  - <10% annual churn
  - Positive net retention

Medium Quality (Score 50-74):
  - 50-70% recurring revenue
  - 15-30% concentration
  - 10-20% churn
  - Neutral/positive retention

Low Quality (Score <50):
  - <50% recurring revenue
  - >30% concentration
  - >20% churn
  - Negative retention
```

## Unit Economics Thresholds

**Healthy SaaS business targets:**
- LTV/CAC Ratio: ≥ 5 (ideally >8)
- CAC Payback: ≤ 12 months (ideally <10)
- Gross Margin: ≥ 70%
- Magic Number: ≥ 0.75 (incremental ARR / incremental S&M spend)

## Growth Sustainability Assessment

Rated as: SUSTAINABLE → CHALLENGED → UNSUSTAINABLE

- **SUSTAINABLE** - Growth backed by market opportunity, strong product-market fit, predictable expansion
- **CHALLENGED** - Growth slowing or dependent on few customers/markets
- **UNSUSTAINABLE** - Growth dependent on unsustainable sales/marketing spend or customer concentration

## Valuation Decision Framework

```
Asking Price Analysis:

Fair → Recommended Entry: Ask Price
  (Market comparables support multiple)

High → Recommended Entry: -10% to -15%
  (Multiple above market, request discount)

Very High → Recommended Entry: -20% or Pass
  (Multiple significantly above market)

Low → Proceed with Confidence
  (Opportunity discount relative to market)
```

## Next Steps

After analyze completes:

1. **If PROCEED**:
   - Create integration and investment plan
   ```bash
   /corporate-development:plan --target target_001
   ```

2. **If CONDITIONAL**:
   - Address specific financial concerns
   - Re-run analysis with adjusted assumptions
   - Develop mitigation strategies

3. **If PASS**:
   - Document reasons
   - Return to discover for alternatives
   - Review quarterly for changed conditions

## Related Skills

- `/corporate-development:assess` - Strategic assessment
- `/corporate-development:audit` - Operational audit
- `/corporate-development:plan` - Integration planning
- `/corporate-development:recommend` - Final recommendation synthesis
- SaaS financial metrics and modeling frameworks

## Integrations

- Financial data platforms (SaaS metrics databases)
- Revenue analysis and benchmarking tools
- Customer database for churn/retention analysis
- Comparable company valuation databases
- Financial modeling and scenario planning tools

## Evidence rules

- Churn is measured over 3 or more years of history.
- The growth stress test reduces growth by 20% and recomputes profitability.
