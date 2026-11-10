---
description: Comprehensive unit economics analysis including CAC, LTV, LTV:CAC ratio, CAC payback period, Magic Number, and cohort analysis for customer profitability assessment
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py *), Edit(/.product-finance/**)
---

# Unit Economics Command

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `uv run python`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because only the plugin's own scripts are tested.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

## Every run

0. **Read the start time and the version** — run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and keep its output as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. Never type a time yourself, because a typed time is a guess and not the time of the run. The result file needs both.
1. Do the work the rest of this file describes.
2. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/financial-analyst.md` with the Read tool and follow its `## Result file` section, in every run.

## Purpose

The unit-economics command provides comprehensive customer-level financial analysis to assess the profitability and efficiency of your customer acquisition and retention strategy. It calculates key unit economics metrics including Customer Acquisition Cost (CAC), Lifetime Value (LTV), LTV:CAC ratio, CAC Payback Period, Magic Number, and performs cohort analysis to evaluate retention curves and long-term customer value.

This command enables product teams and executives to make data-driven decisions about sales and marketing efficiency, customer profitability, and sustainable growth strategies.

## When to Use

- **Sales & Marketing Efficiency:** Evaluating whether customer acquisition spending is efficient and sustainable
- **Growth Planning:** Determining how much to invest in customer acquisition
- **Fundraising:** Demonstrating healthy unit economics to investors (LTV:CAC, payback period)
- **Pricing Strategy:** Validating that pricing supports healthy unit economics
- **Cohort Analysis:** Understanding customer retention patterns and lifetime value trends
- **Strategic Decisions:** Deciding between growth vs. profitability priorities
- **Channel Optimization:** Comparing customer acquisition efficiency across different channels
- **Board Reporting:** Reporting key SaaS metrics for board meetings
- **Health Checks:** Periodic assessment of business model sustainability

## What It Does

1. **Calculates CAC (Customer Acquisition Cost):**
   - CAC = (Sales + Marketing Spend) / New Customers
   - Breakdowns by acquisition channel (inbound, outbound, self-service, partner)
   - Fully-loaded vs. variable CAC options
   - Time period analysis (monthly, quarterly, annual)

2. **Calculates LTV (Lifetime Value):**
   - LTV = (Average Revenue per Customer × Gross Margin %) / Churn Rate
   - Alternative: LTV = ARPC × Gross Margin % × Average Customer Lifetime
   - Cohort-based LTV calculations for more accuracy
   - Handles both monthly and annual calculations

3. **Analyzes LTV:CAC Ratio:**
   - Excellent: >5:1 (strong profitability, room to invest in growth)
   - Good: 3-5:1 (healthy economics, sustainable growth)
   - Acceptable: 1-3:1 (marginal, needs improvement)
   - Unhealthy: <1:1 (losing money on each customer)
   - Benchmarks by industry and company stage

4. **Determines CAC Payback Period:**
   - Months to recover customer acquisition cost
   - Target: <12 months (good), <18 months (acceptable)
   - Calculation: CAC / (ARPC × Gross Margin %)
   - Impact on cash flow and runway

5. **Calculates Magic Number (Sales Efficiency):**
   - Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend
   - Note: Prior quarter S&M spend is used (not current quarter) to capture the lag between spending and revenue generation.
   - Excellent: >1.0 (highly efficient growth)
   - Good: 0.75-1.0 (efficient growth)
   - Acceptable: 0.5-0.75 (moderate efficiency)
   - Poor: <0.5 (inefficient, need to optimize or pause growth)

6. **Performs Cohort Analysis:**
   - Revenue retention by customer cohort over time
   - Churn curves and retention rates
   - Cohort-specific LTV calculations
   - Month-over-month cohort performance
   - Identifies improving vs. degrading cohorts

7. **Generates Recommendations:**
   - Actionable insights based on metric benchmarks
   - Channel-specific optimization opportunities
   - Growth vs. efficiency trade-off guidance
   - Pricing and packaging recommendations

8. **Saves Results:**
   - Structured data: `.product-finance/unit-economics.json`
   - Executive dashboard: `.product-finance/unit-economics-dashboard.md`
   - Historical tracking for trend analysis

## Command Behavior

### Two Analysis Modes

**Mode 1: Current State Analysis**
- Analyze current unit economics based on recent data
- Use trailing 3-month, 6-month, or 12-month periods
- Ideal for ongoing monitoring and optimization

**Mode 2: Projected/Target Analysis**
- Model future unit economics with different assumptions
- Test pricing changes, CAC reduction scenarios, churn improvements
- Support fundraising and strategic planning

The command defaults to current state analysis. Projected mode available via prompt.

## Question Flow

### Phase 1: Analysis Context

**Question** (AskUserQuestion [q: product]): "Which product or company are these figures for?"
- **Type:** text

**Question** (AskUserQuestion [q: analysis_period]): "What time period would you like to analyze?"

**Options:**
- `last_3_months` - Trailing 3-month period (most recent data)
- `last_6_months` - Trailing 6-month period (smooths seasonality)
- `last_12_months` - Trailing 12-month period (annual view)
- `current_quarter` - Current quarter to date
- `custom` - Specify custom date range

**Why we need this:** Time period affects data accuracy and seasonal factors.

**Question** (AskUserQuestion [q: data_type]): "Are you analyzing actual data or modeling projections?"

**Options:**
- `actual` - Based on real historical data
- `projected` - Modeling future scenarios or targets
- `hybrid` - Mix of actuals and projections
- **Default:** `actual`, when nobody says which: the command defaults to current state analysis

**Why we need this:** Determines confidence levels and recommendation approach.

### Phase 2: Customer Acquisition Cost (CAC)

**Introduction:**
```
Customer Acquisition Cost (CAC) Analysis
=========================================
CAC measures the fully-loaded cost to acquire a new customer.
We'll calculate CAC across different acquisition channels.

Formula: CAC = (Sales + Marketing Spend) / New Customers Acquired
```

**Question** (AskUserQuestion [q: sm_spend]): "What was your total Sales & Marketing spend for the period?"
- **Type:** number
- **Guidance:** "Include all S&M expenses: salaries, commissions, tools, advertising, events, etc."
- **Example:** "$250,000 for Q4 2025"
- **Help:** "Fully-loaded S&M costs including team, tools, campaigns, events, partner costs"

**Question** (AskUserQuestion [q: new_customers]): "How many new customers did you acquire in this period?"
- **Type:** integer
- **Guidance:** "Total new paying customers (not trials or signups)"
- **Example:** "125 new customers"

**Auto-calculate:** Blended CAC = Total S&M Spend / New Customers

**Question** (AskUserQuestion [q: cac_by_channel]): "Do you want to break down CAC by acquisition channel?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: channel_customer_split]): "What percentage of new customers came from each channel?"

**Channels:**
- Inbound (marketing-driven): percentage
- Outbound (sales-driven): percentage
- Self-service (product-led): percentage
- Partner/referral: percentage
- Other: percentage

**Question** (AskUserQuestion [q: channel_spend_split]): "What percentage of S&M spend was allocated to each channel?"

**Input for each channel:**
- S&M spend allocation percentage: number

**Auto-calculate:**
- CAC per channel = (S&M Spend × Channel %) / (New Customers × Channel %)
- Weighted average CAC
- Most efficient and least efficient channels

**Question** (AskUserQuestion [q: cost_basis]): "Include only variable costs or fully-loaded costs?"

**Options:**
- `fully_loaded` - All S&M costs including salaries, overhead (recommended)
- `variable_only` - Only variable costs like advertising, commissions

**Why we need this:** Fully-loaded CAC gives true economic picture; variable CAC useful for marginal decisions.

### Phase 3: Lifetime Value (LTV)

**Introduction:**
```
Lifetime Value (LTV) Calculation
=================================
LTV estimates the total gross profit generated from a customer
over their entire relationship with your company.

Two calculation methods:
1. Traditional: LTV = (ARPC × Gross Margin %) / Churn Rate
2. Cohort-based: LTV = Sum of actual revenue from customer cohorts

We'll use the Traditional method, or Cohort-based if you have detailed data.
```

**Question** (AskUserQuestion [q: arpc]): "What is your Average Revenue Per Customer (ARPC)?"
- **Type:** number
- **Guidance:** "Average monthly recurring revenue per customer"
- **Example:** "$500/month"
- **Check:** Pull from assumptions.json if available
- **Help:** "Total MRR / Total Customers"

**Question** (AskUserQuestion [q: gross_margin_percent]): "What is your Gross Margin percentage?"
- **Type:** number (0-100)
- **Guidance:** "Gross Margin % = (Revenue - COGS) / Revenue × 100"
- **Example:** "75% (typical for SaaS: 70-85%)"
- **Check:** Pull from assumptions.json if available
- **Help:** "COGS includes hosting, support, third-party services directly tied to delivery"

**Question** (AskUserQuestion [q: monthly_churn_percent]): "What is your monthly customer churn rate?"
- **Type:** number (0-100 percent)
- **Guidance:** "Monthly churn % = (Customers Lost / Starting Customers) × 100"
- **Example:** "3% per month"
- **Check:** Pull from assumptions.json if available
- **Validation:** Warn if >10% (very high churn)

**Auto-calculate:**
- Average customer lifetime (months) = 1 / Monthly Churn Rate
  - Example: 1 / 0.03 = 33.3 months
- LTV = ARPC × Gross Margin % × Average Customer Lifetime
  - Example: $500 × 75% × 33.3 = $12,487.50

**Alternative formula display:**
- LTV = (ARPC × Gross Margin %) / Monthly Churn Rate
  - Example: ($500 × 0.75) / 0.03 = $12,500

**Question** (AskUserQuestion [q: has_cohort_data]): "Do you have cohort-specific retention data?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: cohort_count]): "How many customer cohorts would you like to analyze?"
- **Type:** integer (1-24)
- **Guidance:** "Typically analyze 6-12 monthly cohorts"
- **Example:** "12 cohorts (last 12 months)"

**For each cohort:**

**Question** (AskUserQuestion [q: cohorts]): "Cohort {month-year}: How many customers started?"
- **Type:** integer
- **Example:** "January 2025: 50 customers"

**Question** (AskUserQuestion [q: cohorts]): "What percentage remained after each month?"

**Input retention curve:**
- Month 1: percentage retained
- Month 2: percentage retained
- Month 3: percentage retained
- ... (up to current month)

**Auto-calculate for each cohort:**
- Cumulative revenue per customer
- Projected lifetime value based on retention curve
- Cohort health score (improving vs. degrading)

**Final LTV Calculation:**
- If cohort data provided: Use weighted average of cohort LTVs
- If no cohort data: Use traditional formula

### Phase 4: LTV:CAC Ratio Analysis

**Auto-calculate:** LTV:CAC Ratio = LTV / CAC

**Example:** $12,500 / $2,000 = 6.25:1

**Benchmark Assessment:**

**Excellent (>5:1):**
- Strong profitability margins
- Room to invest more in customer acquisition
- Potential to accelerate growth
- Risk: May be under-investing in growth

**Good (3-5:1):**
- Healthy, sustainable unit economics
- Balanced growth and profitability
- Typical for mature SaaS companies
- Sweet spot for most businesses

**Acceptable (1-3:1):**
- Marginal economics, needs improvement
- Limited profitability per customer
- Growth constrained by unit economics
- Focus on reducing CAC or improving LTV

**Unhealthy (<1:1):**
- Losing money on each customer
- Unsustainable without external funding
- Need immediate intervention
- Options: Raise prices, reduce CAC, improve retention

**Question** (AskUserQuestion [q: company_stage]): "What stage is your company?"

**Options:**
- `early_stage` - Pre-seed, Seed, Series A (0-$5M ARR)
- `growth_stage` - Series B, C (>$5M-$50M ARR)
- `scale_stage` - Series D+ (>$50M ARR)

**Why we need this:** Acceptable LTV:CAC varies by stage. Early-stage companies (1-2:1) acceptable if growing fast; later-stage should be 3:1+.

**Context-specific guidance:**
- Early-stage (<$5M ARR): 1.5-3:1 acceptable (prioritize growth)
- Growth-stage ($5M-$50M ARR): 3-4:1 target (balance growth and efficiency)
- Scale-stage (>$50M ARR): 4-6:1 target (optimize efficiency)

### Phase 5: CAC Payback Period

**Auto-calculate:** CAC Payback Period = CAC / (ARPC × Gross Margin %)

**Example:** $2,000 / ($500 × 0.75) = 5.3 months

**Benchmark Assessment:**

**Excellent (<6 months):**
- Very fast payback, minimal cash flow strain
- Can scale customer acquisition aggressively
- Low risk for investors

**Good (6-12 months):**
- Healthy payback period
- Standard for most SaaS companies
- Reasonable cash flow requirements

**Acceptable (12-18 months):**
- Slower payback, requires more capital
- Common for enterprise SaaS
- Need strong cash reserves or funding

**Poor (>18 months):**
- Very slow payback, high cash burn
- Difficult to scale without significant funding
- Risk to runway and sustainability
- Need to improve ARPC, reduce CAC, or improve margins

**Impact Analysis:**
- Monthly cash needed to support growth
- Runway implications based on current cash reserves
- Comparison to industry benchmarks

**Question** (AskUserQuestion [q: target_payback_months]): "What is your company's target CAC payback period?"
- **Type:** number (months)
- **Guidance:** "Maximum acceptable months to recover CAC"
- **Default:** 12 months
- **Check:** Pull from assumptions.json if available

**Auto-calculate:**
- Variance from target: Actual - Target
- Status: Ahead/behind target
- Cash flow impact of variance

### Phase 6: Magic Number (Sales Efficiency)

**Introduction:**
```
Magic Number - Sales Efficiency Metric
=======================================
The Magic Number measures sales efficiency by comparing
net new revenue generated to the S&M investment required.

Formula: Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend

Note: Prior quarter S&M spend is used (not current quarter) to capture the lag between spending and revenue generation.

A Magic Number of 1.0 means you generated $1 of new ARR
for every $1 spent on sales and marketing.
```

**Question** (AskUserQuestion [q: net_new_arr]): "What was your Net New ARR for the period?"
- **Type:** number
- **Guidance:** "New ARR from new customers + expansion ARR from existing customers"
- **Example:** "$600,000 net new ARR in Q4"
- **Help:** "Include both new logo ARR and expansion ARR, exclude churn"

**Auto-calculate:** Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend

**Example:** ($150,000 × 4) / $250,000 = 2.4

**Benchmark Assessment:**

**Excellent (>1.0):**
- Highly efficient growth engine
- Generating more than $1 ARR per $1 S&M spend
- Can aggressively scale S&M investment
- Strong indicator of product-market fit

**Good (0.75-1.0):**
- Efficient, sustainable growth
- Solid ROI on S&M investment
- Room to increase S&M spend
- Healthy growth trajectory

**Acceptable (0.5-0.75):**
- Moderate efficiency, needs optimization
- ROI on S&M is positive but low
- Be cautious about scaling S&M too fast
- Focus on improving conversion, pricing, or reducing CAC

**Poor (<0.5):**
- Inefficient growth, losing money on S&M
- Need to pause growth and fix economics
- Options: Improve product-market fit, reduce CAC, increase prices
- Not ready to scale aggressively

**Time Period Note:**
The Magic Number is typically calculated on a quarterly basis, with a one-quarter lag:
- Q4 Net New ARR / Q3 S&M Spend
- This accounts for the time lag between S&M investment and revenue generation

**Question** (AskUserQuestion [q: magic_number_lag]): "Should we apply a one-quarter lag to the Magic Number calculation?" (yes/no)
- **Default:** yes (recommended)
- **If yes:** Use previous quarter's S&M spend with current quarter's net new ARR
- **If no:** Use same period S&M spend and net new ARR

**Auto-calculate with lag:**
- If quarterly analysis: Q(n) ARR / Q(n-1) S&M Spend
- If monthly: Use rolling quarterly average

### Phase 7: Cohort Analysis

**Question** (AskUserQuestion [q: cohort_analysis]): "Would you like to perform detailed cohort retention analysis?" (yes/no)

**If yes (and cohort data was provided in Phase 3):**

**Cohort Retention Curve Analysis:**

For each cohort, display:
- Starting customer count
- Month-by-month retention percentage
- Revenue retention percentage
- Cumulative LTV to date
- Projected LTV based on curve
- Cohort health trend (improving/stable/degrading)

**Cohort Comparison Matrix:**

| Cohort | Starting Customers | M3 Retention | M6 Retention | M12 Retention | LTV | Health |
|--------|-------------------|--------------|--------------|---------------|-----|--------|
| Jan 2025 | 50 | 92% | 85% | 78% | $13,200 | ✓ Good |
| Feb 2025 | 48 | 94% | 88% | 81% | $14,100 | ✓ Improving |
| Mar 2025 | 52 | 90% | 82% | 75% | $12,000 | ⚠ Degrading |

**Key Insights:**
- Average retention rate across cohorts
- Trend direction (retention improving or worsening over time)
- Best performing cohort and why
- Worst performing cohort and potential causes
- Correlation between cohort characteristics and retention

**Retention Curve Visualization (text-based):**

```
Cohort Retention Curve (Last 12 Months)
========================================

100% |●●●●
 90% |    ●●●●
 80% |        ●●●●
 70% |            ●●●
 60% |               ●●
 50% |                 ●
     +-------------------->
     M0 M3 M6 M9 M12 M15

● = Average retention across cohorts
Target: >80% at M6, >70% at M12
```

**Question** (AskUserQuestion [q: cohort_factors]): "What factors do you think influenced retention for each cohort?"

**Options for each cohort:**
- `product_updates` - Major product improvements
- `pricing_changes` - Pricing or packaging changes
- `support_quality` - Customer success initiatives
- `market_conditions` - External market factors
- `competition` - Competitive pressure
- `onboarding` - Onboarding process changes
- `unknown` - No specific factor identified

**Auto-calculate:**
- Correlation between factors and retention rates
- Recommendations for improving future cohort retention

### Phase 8: Summary and Recommendations

**Processing:**
1. Calculate all unit economics metrics
2. Compare to benchmarks and targets
3. Assess overall health of unit economics
4. Identify key strengths and weaknesses
5. Generate prioritized recommendations
6. Calculate impact of potential improvements
7. Create executive dashboard and structured data

**Scenario Modeling (Optional):**

**Question** (AskUserQuestion [q: model_scenarios]): "Would you like to model improvement scenarios?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: scenario_metrics]): "Which metrics would you like to improve?"

**Options (select multiple):**
- Reduce CAC by X%
- Increase ARPC by X%
- Reduce churn by X percentage points
- Improve gross margin by X percentage points
- Increase Magic Number to target level

**For each selected improvement:**

**Question** (AskUserQuestion [q: scenario_improvement]): "By how much can you realistically improve {metric}?"
- **Type:** number or percentage
- **Guidance:** "Be conservative - what's achievable in 6-12 months?"

**Auto-calculate impact:**
- New LTV with improvements
- New LTV:CAC ratio
- New payback period
- New Magic Number
- Revenue and profitability impact
- Recommendations for achieving improvements

## Output

### File 1: `.product-finance/unit-economics.json`

Structured data following schema:

```json
{
  "analysis": {
    "period": {
      "type": "last_6_months",
      "start_date": "2025-07-01",
      "end_date": "2025-12-31",
      "custom_label": "H2 2025"
    },
    "mode": "actual",
    "analysis_date": "2026-01-23T10:00:00Z",
    "company_stage": "growth_stage"
  },
  "cac": {
    "total_sm_spend": 500000,
    "new_customers_acquired": 250,
    "blended_cac": 2000,
    "calculation_type": "fully_loaded",
    "by_channel": {
      "inbound": {
        "percentage_customers": 40,
        "percentage_spend": 35,
        "cac": 1750,
        "efficiency_ranking": 1
      },
      "outbound": {
        "percentage_customers": 30,
        "percentage_spend": 40,
        "cac": 2667,
        "efficiency_ranking": 3
      },
      "self_service": {
        "percentage_customers": 20,
        "percentage_spend": 15,
        "cac": 1500,
        "efficiency_ranking": 1
      },
      "partner": {
        "percentage_customers": 10,
        "percentage_spend": 10,
        "cac": 2000,
        "efficiency_ranking": 2
      }
    },
    "most_efficient_channel": "self_service",
    "least_efficient_channel": "outbound"
  },
  "ltv": {
    "arpc_monthly": 500,
    "gross_margin_pct": 75,
    "monthly_churn_rate_pct": 3,
    "average_customer_lifetime_months": 33.3,
    "ltv_traditional": 12500,
    "calculation_method": "traditional",
    "formula": "(ARPC × Gross Margin %) / Monthly Churn Rate",
    "components": {
      "monthly_gross_profit_per_customer": 375,
      "lifetime_gross_profit": 12500
    }
  },
  "ltv_cac_ratio": {
    "ratio": 6.25,
    "status": "excellent",
    "benchmark": {
      "target_min": 3.0,
      "target_ideal": 5.0,
      "company_stage_guidance": "4-6:1 for growth-stage"
    },
    "assessment": "Strong profitability margins with room to invest more in customer acquisition",
    "recommendations": [
      "Unit economics support aggressive growth investment",
      "Consider increasing S&M spend by 25-50% to accelerate growth",
      "Strong margins indicate product-market fit and pricing power"
    ]
  },
  "cac_payback_period": {
    "payback_months": 5.3,
    "status": "excellent",
    "calculation": "CAC / (ARPC × Gross Margin %)",
    "target_months": 12,
    "variance_from_target": -6.7,
    "benchmark": {
      "excellent": "<6 months",
      "good": "6-12 months",
      "acceptable": "12-18 months",
      "poor": ">18 months"
    },
    "cash_flow_impact": {
      "monthly_cash_required_per_100_customers": 106000,
      "description": "With 5.3-month payback, need $106K working capital per 100 new customers"
    },
    "assessment": "Very fast payback minimizes cash flow strain and enables aggressive scaling"
  },
  "magic_number": {
    "value": 4.8,
    "quarterly_net_new_arr": 600000,
    "prior_quarter_sm_spend": 500000,
    "efficiency_interpretation": "Magic Number: 4.80",
    "health_status": "excellent",
    "benchmark_notes": "Strong sales efficiency (>1.0). Consider increasing S&M investment."
  },
  "cohort_analysis": {
    "cohorts_analyzed": 12,
    "cohorts": [
      {
        "cohort_id": "2025-01",
        "cohort_label": "January 2025",
        "starting_customers": 50,
        "retention_curve": {
          "m0": 100,
          "m1": 96,
          "m2": 92,
          "m3": 90,
          "m6": 85,
          "m9": 82,
          "m12": 78
        },
        "revenue_retention_m12": 81,
        "ltv_to_date": 8200,
        "projected_ltv": 13200,
        "health_status": "good",
        "trend": "stable",
        "key_factor": "product_updates"
      },
      {
        "cohort_id": "2025-02",
        "cohort_label": "February 2025",
        "starting_customers": 48,
        "retention_curve": {
          "m0": 100,
          "m1": 98,
          "m2": 94,
          "m3": 92,
          "m6": 88,
          "m9": 85,
          "m12": 81
        },
        "revenue_retention_m12": 85,
        "ltv_to_date": 8900,
        "projected_ltv": 14100,
        "health_status": "excellent",
        "trend": "improving",
        "key_factor": "onboarding"
      }
    ],
    "summary": {
      "average_m3_retention_pct": 91,
      "average_m6_retention_pct": 86,
      "average_m12_retention_pct": 79,
      "trend_direction": "improving",
      "best_cohort": "2025-02",
      "worst_cohort": "2025-03",
      "retention_benchmark_target_m6": 80,
      "retention_benchmark_target_m12": 70,
      "status_vs_benchmark": "above_target"
    }
  },
  "overall_assessment": {
    "health_score": 92,
    "health_status": "excellent",
    "key_strengths": [
      "LTV:CAC ratio of 6.25:1 significantly exceeds 3:1 benchmark",
      "CAC payback of 5.3 months enables fast scaling with minimal cash strain",
      "Magic Number of 4.8 demonstrates highly efficient growth engine",
      "Cohort retention trending upward (avg 79% at M12)"
    ],
    "key_weaknesses": [
      "Outbound channel CAC ($2,667) is 78% higher than self-service ($1,500)",
      "Monthly churn of 3% still has room for improvement to extend LTV"
    ],
    "top_priorities": [
      {
        "priority": 1,
        "action": "Scale S&M investment by 30-50%",
        "rationale": "Strong unit economics support aggressive growth",
        "expected_impact": "Accelerate customer acquisition with positive ROI"
      },
      {
        "priority": 2,
        "action": "Optimize outbound sales channel",
        "rationale": "Outbound CAC 78% higher than self-service",
        "expected_impact": "Reduce blended CAC by 10-15% or reallocate to higher-ROI channels"
      },
      {
        "priority": 3,
        "action": "Implement churn reduction initiatives",
        "rationale": "Reducing churn from 3% to 2.5% increases LTV by 20%",
        "expected_impact": "LTV increases from $12,500 to $15,000, LTV:CAC improves to 7.5:1"
      }
    ]
  },
  "scenario_modeling": {
    "baseline": {
      "ltv": 12500,
      "cac": 2000,
      "ltv_cac_ratio": 6.25,
      "payback_months": 5.3,
      "magic_number": 4.8
    },
    "scenarios": [
      {
        "scenario_name": "Reduce CAC by 15%",
        "changes": {
          "cac_reduction_pct": 15
        },
        "results": {
          "new_cac": 1700,
          "ltv_cac_ratio": 7.35,
          "payback_months": 4.5,
          "impact": "Improves LTV:CAC by 1.1 points, payback by 0.8 months"
        },
        "feasibility": "medium",
        "timeframe": "6-12 months"
      },
      {
        "scenario_name": "Reduce churn from 3% to 2.5%",
        "changes": {
          "churn_reduction_pct": 0.5
        },
        "results": {
          "new_ltv": 15000,
          "ltv_cac_ratio": 7.5,
          "payback_months": 5.3,
          "impact": "Increases LTV by $2,500 (20% improvement)"
        },
        "feasibility": "high",
        "timeframe": "6-9 months",
        "tactics": [
          "Improve onboarding process",
          "Increase customer success touchpoints",
          "Implement health score monitoring"
        ]
      },
      {
        "scenario_name": "Increase ARPC by 10%",
        "changes": {
          "arpc_increase_pct": 10
        },
        "results": {
          "new_arpc": 550,
          "new_ltv": 13750,
          "ltv_cac_ratio": 6.88,
          "payback_months": 4.8,
          "impact": "Increases LTV by $1,250, improves payback by 0.5 months"
        },
        "feasibility": "high",
        "timeframe": "3-6 months",
        "tactics": [
          "Introduce premium tier or add-ons",
          "Implement usage-based pricing",
          "Annual contract incentives"
        ]
      },
      {
        "scenario_name": "Combined: Churn -0.5% + ARPC +10%",
        "changes": {
          "churn_reduction_pct": 0.5,
          "arpc_increase_pct": 10
        },
        "results": {
          "new_ltv": 16500,
          "ltv_cac_ratio": 8.25,
          "payback_months": 4.8,
          "impact": "Increases LTV by $4,000 (32% improvement), LTV:CAC to 8.25:1"
        },
        "feasibility": "medium",
        "timeframe": "9-12 months",
        "recommended": true
      }
    ]
  },
  "metadata": {
    "analysis_date": "2026-01-23T10:00:00Z",
    "plugin_version": "1.0.0",
    "confidence_level": "high",
    "data_source": "actual",
    "assumptions_source": ".product-finance/assumptions.json",
    "next_review_date": "2026-04-23"
  }
}
```

### File 2: `.product-finance/unit-economics-dashboard.md`

Executive dashboard:

```markdown
# Unit Economics Dashboard

**Analysis Period:** H2 2025 (July - December)
**Analysis Date:** January 23, 2026
**Company Stage:** Growth Stage
**Data Source:** Actual

**Overall Health Score:** 92/100 (Excellent)

---

## Executive Summary

Your unit economics are **excellent** with strong profitability margins and efficient customer acquisition. Key metrics significantly exceed industry benchmarks:

- **LTV:CAC Ratio:** 6.25:1 (Target: 3-5:1) ✓ **Excellent**
- **CAC Payback Period:** 5.3 months (Target: <12 months) ✓ **Excellent**
- **Magic Number:** 4.8 (Target: >0.75) ✓ **Excellent**
- **Customer Lifetime:** 33 months (Churn: 3%/month)

**Key Insight:** Your strong unit economics support aggressive growth investment. Consider scaling S&M spend by 30-50% to accelerate customer acquisition while maintaining healthy profitability.

---

## Customer Acquisition Cost (CAC)

**Blended CAC:** $2,000 per customer
**S&M Spend:** $500,000 (H2 2025)
**New Customers:** 250

### CAC by Channel

| Channel | % Customers | % S&M Spend | CAC | Efficiency |
|---------|-------------|-------------|-----|------------|
| Self-Service | 20% | 15% | $1,500 | ⭐ Best |
| Inbound | 40% | 35% | $1,750 | ✓ Good |
| Partner | 10% | 10% | $2,000 | ○ Average |
| Outbound | 30% | 40% | $2,667 | ⚠ Least Efficient |

**Insight:** Outbound sales CAC is 78% higher than self-service. Opportunity to optimize outbound efficiency or reallocate budget to higher-performing channels.

**Calculation:**
```
Blended CAC = Total S&M Spend / New Customers
            = $500,000 / 250
            = $2,000 per customer
```

---

## Lifetime Value (LTV)

**LTV:** $12,500 per customer

### Components

- **ARPC (Average Revenue Per Customer):** $500/month
- **Gross Margin:** 75%
- **Monthly Churn Rate:** 3%
- **Average Customer Lifetime:** 33.3 months
- **Lifetime Gross Profit:** $12,500

**Calculation:**
```
LTV = (ARPC × Gross Margin %) / Monthly Churn Rate
    = ($500 × 75%) / 3%
    = $375 / 0.03
    = $12,500

Or alternatively:
LTV = ARPC × Gross Margin % × Customer Lifetime
    = $500 × 0.75 × 33.3 months
    = $12,500
```

---

## LTV:CAC Ratio

**Ratio:** 6.25:1
**Status:** ⭐ **Excellent**

For every $1 spent on customer acquisition, you generate $6.25 in lifetime gross profit.

### Benchmark Analysis

| Range | Status | Description |
|-------|--------|-------------|
| >5:1 | **Excellent** ← You are here | Strong profitability, room to invest in growth |
| 3-5:1 | Good | Healthy, sustainable unit economics |
| 1-3:1 | Acceptable | Marginal economics, needs improvement |
| <1:1 | Unhealthy | Losing money on each customer |

**Stage-Specific Guidance:**
- Growth Stage Target: 4-6:1 ✓ You exceed this

**Recommendations:**
- ✓ Unit economics support aggressive growth investment
- ✓ Consider increasing S&M spend by 25-50% to accelerate growth
- ✓ Strong margins indicate product-market fit and pricing power
- ⚠ Monitor ratio as you scale - don't let it fall below 3:1

---

## CAC Payback Period

**Payback Period:** 5.3 months
**Status:** ⭐ **Excellent**
**Target:** <12 months ✓ **7 months ahead of target**

You recover customer acquisition costs in 5.3 months, enabling fast scaling with minimal cash flow strain.

**Calculation:**
```
Payback Period = CAC / (ARPC × Gross Margin %)
               = $2,000 / ($500 × 0.75)
               = $2,000 / $375
               = 5.3 months
```

### Benchmark Analysis

| Range | Status | Assessment |
|-------|--------|------------|
| <6 months | **Excellent** ← You are here | Very fast payback, minimal cash strain |
| 6-12 months | Good | Healthy payback period |
| 12-18 months | Acceptable | Slower payback, requires more capital |
| >18 months | Poor | Very slow payback, high cash burn |

### Cash Flow Impact

**Monthly cash required to support 100 new customers:**
- Initial investment: $200,000 (100 × $2,000 CAC)
- Recovered by month 6: $200,000
- Net cash requirement: $106,000 peak working capital

**Insight:** Your fast payback enables you to scale customer acquisition aggressively without straining cash reserves.

---

## Magic Number (Sales Efficiency)

**Magic Number:** 4.8
**Status:** ⭐ **Excellent**

Your annualized Magic Number is 4.8 — strong sales efficiency (>1.0).

**Calculation:**
```
Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend
             = ($600,000 × 4) / $500,000
             = 4.8
```

### Benchmark Analysis

| Range | Status | Description |
|-------|--------|-------------|
| >1.0 | **Excellent** ← You are here | Highly efficient growth engine |
| 0.75-1.0 | Good | Efficient, sustainable growth |
| 0.5-0.75 | Acceptable | Moderate efficiency, needs optimization |
| <0.5 | Poor | Inefficient growth, pause and fix |

**Recommendations:**
- ✓ Sales efficiency supports aggressive S&M scaling
- ✓ Consider increasing S&M budget by 30-50% in next quarter
- ✓ Maintain current go-to-market strategy while scaling
- ⚠ Monitor Magic Number as you scale to ensure efficiency holds

---

## Cohort Analysis

**Cohorts Analyzed:** 12 (January 2025 - December 2025)

### Average Retention Rates

- **Month 3:** 91% (Target: >85%) ✓
- **Month 6:** 86% (Target: >80%) ✓
- **Month 12:** 79% (Target: >70%) ✓

**Trend:** ↗ **Improving** (retention rates increasing over time)

### Top Performing Cohorts

| Cohort | M12 Retention | LTV | Health | Key Factor |
|--------|---------------|-----|--------|------------|
| Feb 2025 | 81% | $14,100 | Excellent | Improved onboarding |
| Jan 2025 | 78% | $13,200 | Good | Product updates |
| Apr 2025 | 80% | $13,800 | Good | Support quality |

### Retention Curve (Average Across Cohorts)

```
100% |●
 95% |  ●
 90% |    ●
 85% |      ●●
 80% |        ●●
 75% |          ●●
     +--------------->
     M0 M1 M3 M6 M9 M12

● = Average retention rate
Target: >80% at M6, >70% at M12 ✓
```

**Key Insights:**
- Retention rates are above benchmark targets
- Recent cohorts showing improved retention (onboarding and product improvements)
- February 2025 cohort is your best-performing cohort (81% M12 retention)
- No cohort shows concerning degradation patterns

---

## Overall Assessment

### Key Strengths

✓ **LTV:CAC ratio of 6.25:1** significantly exceeds 3:1 benchmark
✓ **CAC payback of 5.3 months** enables fast scaling with minimal cash strain
✓ **Magic Number of 4.8** demonstrates highly efficient growth engine
✓ **Cohort retention trending upward** (avg 79% at M12)
✓ **Strong gross margins** (75%) typical of healthy SaaS business

### Key Weaknesses

⚠ **Outbound channel CAC ($2,667)** is 78% higher than self-service ($1,500)
⚠ **Monthly churn of 3%** still has room for improvement to extend LTV
⚠ **Channel concentration** - 40% of spend on least efficient channel

---

## Top 3 Priorities

### Priority 1: Scale S&M Investment by 30-50%

**Rationale:** Strong unit economics support aggressive growth
**Expected Impact:** Accelerate customer acquisition with positive ROI
**Action Items:**
- Increase marketing budget by $75K-$125K per quarter
- Hire 2-3 additional sales reps
- Expand into new acquisition channels
- Maintain Magic Number above 0.75

### Priority 2: Optimize Outbound Sales Channel

**Rationale:** Outbound CAC 78% higher than self-service
**Expected Impact:** Reduce blended CAC by 10-15% or reallocate to higher-ROI channels
**Action Items:**
- Analyze outbound sales process for inefficiencies
- Improve lead qualification to increase conversion rates
- Test reducing outbound budget by 20%, reallocate to inbound/self-service
- Implement sales enablement tools to improve rep efficiency

### Priority 3: Implement Churn Reduction Initiatives

**Rationale:** Reducing churn from 3% to 2.5% increases LTV by 20%
**Expected Impact:** LTV increases from $12,500 to $15,000, LTV:CAC improves to 7.5:1
**Action Items:**
- Improve onboarding process (copy best practices from Feb 2025 cohort)
- Increase customer success touchpoints in first 90 days
- Implement health score monitoring to identify at-risk customers
- Launch customer education program

---

## Scenario Modeling

### Baseline (Current State)

- LTV: $12,500
- CAC: $2,000
- LTV:CAC: 6.25:1
- Payback: 5.3 months
- Magic Number: 4.8

### Scenario 1: Reduce CAC by 15%

**Changes:** Optimize outbound sales, improve conversion rates
**Results:**
- New CAC: $1,700 (-$300)
- LTV:CAC: 7.35:1 (+1.1)
- Payback: 4.5 months (-0.8 months)

**Feasibility:** Medium | **Timeframe:** 6-12 months

### Scenario 2: Reduce Churn from 3% to 2.5%

**Changes:** Improve onboarding, increase CS touchpoints
**Results:**
- New LTV: $15,000 (+$2,500, 20% increase)
- LTV:CAC: 7.5:1 (+1.25)
- Payback: 5.3 months (unchanged)

**Feasibility:** High | **Timeframe:** 6-9 months

**Tactics:**
- Improve onboarding process
- Increase customer success touchpoints
- Implement health score monitoring

### Scenario 3: Increase ARPC by 10%

**Changes:** Premium tier or add-ons, annual contracts
**Results:**
- New ARPC: $550 (+$50)
- New LTV: $13,750 (+$1,250)
- LTV:CAC: 6.88:1 (+0.63)
- Payback: 4.8 months (-0.5 months)

**Feasibility:** High | **Timeframe:** 3-6 months

**Tactics:**
- Introduce premium tier or add-ons
- Implement usage-based pricing
- Annual contract incentives

### Scenario 4: Combined (RECOMMENDED)

**Changes:** Churn -0.5% + ARPC +10%
**Results:**
- New LTV: $16,500 (+$4,000, 32% increase)
- LTV:CAC: 8.25:1 (+2.0)
- Payback: 4.8 months (-0.5 months)

**Feasibility:** Medium | **Timeframe:** 9-12 months

**Expected Impact:** Dramatically improves unit economics, increases profitability per customer by $4,000

---

## Next Steps

### Immediate Actions (Next 30 Days)

1. **Approve S&M budget increase** for Q1 2026 (30% increase = +$250K)
2. **Launch outbound sales optimization project** to reduce CAC
3. **Analyze February 2025 cohort** to identify retention success factors

### Short-Term (Next 90 Days)

4. **Hire 2-3 additional sales reps** to support growth scaling
5. **Implement customer health score monitoring** to reduce churn
6. **Launch premium tier or add-ons** to increase ARPC by 10%

### Medium-Term (6-12 Months)

7. **Reduce churn from 3% to 2.5%** through CS initiatives
8. **Optimize outbound CAC** to match inbound efficiency
9. **Scale S&M investment** while maintaining Magic Number >0.75

---

## Monitoring & Review

**Next Review Date:** April 23, 2026 (Quarterly)

**Metrics to Track:**
- LTV:CAC ratio (maintain above 4:1)
- CAC payback period (keep below 6 months)
- Magic Number (maintain above 1.0)
- Monthly churn rate (target: <2.5%)
- Cohort retention (M6 >85%, M12 >75%)
- Channel-specific CAC trends

**Alert Thresholds:**
- ⚠ LTV:CAC falls below 4:1
- ⚠ CAC payback exceeds 8 months
- ⚠ Magic Number falls below 0.75
- ⚠ Monthly churn exceeds 3.5%

---

*Unit Economics Dashboard - Product Finance Plugin*
*Analysis Confidence: High | Data Source: Actual H2 2025*
*Next Review: April 2026 (Quarterly)*
```

### Console Output

**Summary displayed to user:**

```
Unit Economics Analysis Complete!
==================================

Analysis Period: H2 2025 (July - December)
Data Source: Actual
Company Stage: Growth Stage

OVERALL HEALTH: 92/100 (EXCELLENT) ✓

Key Metrics
-----------
LTV:CAC Ratio: 6.25:1 (EXCELLENT - Target: 3-5:1)
CAC Payback Period: 5.3 months (EXCELLENT - Target: <12 months)
Magic Number: 4.8 (EXCELLENT - Target: >0.75)

Customer Acquisition Cost (CAC)
--------------------------------
Blended CAC: $2,000
S&M Spend: $500,000
New Customers: 250

CAC by Channel:
  ⭐ Self-Service: $1,500 (Best)
  ✓ Inbound: $1,750 (Good)
  ○ Partner: $2,000 (Average)
  ⚠ Outbound: $2,667 (Least Efficient - 78% higher than best)

Lifetime Value (LTV)
--------------------
LTV: $12,500
ARPC: $500/month
Gross Margin: 75%
Monthly Churn: 3%
Customer Lifetime: 33.3 months

LTV:CAC Analysis
----------------
Ratio: 6.25:1 (EXCELLENT)
Status: Strong profitability margins, room to invest in growth

For every $1 spent on customer acquisition, you generate $6.25 in lifetime gross profit.

CAC Payback Period
------------------
Payback: 5.3 months (EXCELLENT)
Target: <12 months ✓ 7 months ahead of target
Cash Flow Impact: $106K peak working capital per 100 customers

Magic Number
------------
Magic Number: 4.8 (EXCELLENT)
Net New ARR: $600,000
S&M Spend: $500,000

Your annualized Magic Number is 4.8 — strong sales efficiency (>1.0).

Cohort Analysis
---------------
Cohorts Analyzed: 12 (Jan-Dec 2025)
Average M3 Retention: 91% (Target: >85%) ✓
Average M6 Retention: 86% (Target: >80%) ✓
Average M12 Retention: 79% (Target: >70%) ✓
Trend: ↗ Improving

Best Cohort: February 2025 (81% M12 retention, $14,100 LTV)

Key Strengths
-------------
✓ LTV:CAC ratio of 6.25:1 significantly exceeds 3:1 benchmark
✓ CAC payback of 5.3 months enables fast scaling with minimal cash strain
✓ Magic Number of 4.8 demonstrates highly efficient growth engine
✓ Cohort retention trending upward (avg 79% at M12)
✓ Strong gross margins (75%) typical of healthy SaaS business

Key Weaknesses
--------------
⚠ Outbound channel CAC ($2,667) is 78% higher than self-service ($1,500)
⚠ Monthly churn of 3% still has room for improvement to extend LTV

Top 3 Priorities
----------------
1. Scale S&M Investment by 30-50%
   → Strong unit economics support aggressive growth
   → Expected impact: Accelerate customer acquisition with positive ROI

2. Optimize Outbound Sales Channel
   → Outbound CAC 78% higher than self-service
   → Expected impact: Reduce blended CAC by 10-15%

3. Implement Churn Reduction Initiatives
   → Reducing churn from 3% to 2.5% increases LTV by 20%
   → Expected impact: LTV increases from $12,500 to $15,000

Scenario Modeling
-----------------
Baseline: LTV $12,500 | CAC $2,000 | LTV:CAC 6.25:1

Scenario 1: Reduce CAC by 15%
  → New LTV:CAC: 7.35:1 | Feasibility: Medium (6-12 months)

Scenario 2: Reduce Churn to 2.5%
  → New LTV: $15,000 (+20%) | Feasibility: High (6-9 months)

Scenario 3: Increase ARPC by 10%
  → New LTV: $13,750 (+10%) | Feasibility: High (3-6 months)

Scenario 4: Combined (RECOMMENDED)
  → New LTV: $16,500 (+32%) | LTV:CAC: 8.25:1
  → Feasibility: Medium (9-12 months)

Files Generated
---------------
✓ .product-finance/unit-economics.json
✓ .product-finance/unit-economics-dashboard.md

Next Steps
----------
1. Approve S&M budget increase for Q1 2026 (+30% = $250K)
2. Launch outbound sales optimization project
3. Analyze February 2025 cohort success factors
4. Implement customer health score monitoring
5. Launch premium tier or add-ons to increase ARPC

Next Review: April 23, 2026 (Quarterly)

Related Commands
----------------
- Run `/product-finance:health-check` for overall financial health
- Run `/product-finance:feature-roi` to prioritize growth investments
- Run `/product-finance:ai-economics` if AI features impact unit economics
```

## Implementation Notes

### For Claude Code Agent

**Interactive Data Collection:**
- Use progressive disclosure: start with essential metrics (CAC, LTV basics)
- Explain why each metric matters for decision-making
- Provide examples and industry benchmarks
- Pre-populate from `.product-finance/assumptions.json` when available
- Allow skipping optional cohort analysis if data unavailable

**Validation:**
- CAC must be positive number and reasonable (warn if >$10K for SMB SaaS)
- LTV must be greater than CAC (warn if LTV:CAC <1:1)
- Churn rate must be 0-100% (warn if >10% monthly)
- Gross margin must be 0-100% (warn if <60% for SaaS)
- Magic Number calculations must use one-quarter lag by default

**Calculation Logic:**

**CAC:**
```
Blended CAC = Total S&M Spend / New Customers Acquired
Channel CAC = (S&M Spend × Channel %) / (New Customers × Channel %)
```

**LTV:**
```
Traditional: LTV = (ARPC × Gross Margin %) / Monthly Churn Rate
Alternative: LTV = ARPC × Gross Margin % × (1 / Monthly Churn Rate)
Cohort-based: LTV = Σ(Revenue by month × Retention curve)
```

**LTV:CAC Ratio:**
```
LTV:CAC Ratio = LTV / CAC
```

**CAC Payback Period:**
```
Payback Period (months) = CAC / (ARPC × Gross Margin %)
```

**Magic Number:**
```
Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend
Where: Net New ARR = New Logo ARR + Expansion ARR - Churned ARR
Note: Prior quarter S&M spend is used (not current quarter) to capture the lag between spending and revenue generation.
```

**Benchmarks and Status Logic:**

**LTV:CAC Ratio:**
- Excellent: >5:1
- Good: 3-5:1
- Acceptable: 1-3:1
- Unhealthy: <1:1

**Stage-specific guidance:**
- Early-stage (<$5M ARR): 1.5-3:1 acceptable
- Growth-stage ($5M-$50M ARR): 3-4:1 target
- Scale-stage (>$50M ARR): 4-6:1 target

**CAC Payback Period:**
- Excellent: <6 months
- Good: 6-12 months
- Acceptable: 12-18 months
- Poor: >18 months

**Magic Number:**
- Excellent: >1.0
- Good: 0.75-1.0
- Acceptable: 0.5-0.75
- Poor: <0.5

**Cohort Health:**
- Excellent: Retention improving month-over-month
- Good: Stable retention meeting benchmarks
- Acceptable: Retention meeting minimum thresholds
- Poor: Retention degrading or below benchmarks

**File Naming:**
- JSON: `unit-economics.json` (one canonical file, overwrite each analysis)
- Dashboard: `unit-economics-dashboard.md` (one canonical file, overwrite each analysis)
- Archive previous versions if needed with timestamps

**Integration with assumptions.json:**
- Read: Pricing, ARPC, churn rate, gross margin, S&M costs, targets
- Update: Write back calculated CAC, LTV, payback period for other commands to reference
- Maintain: Historical unit economics for trend tracking

**Cohort Analysis Details:**

If cohort data available:
1. Calculate retention curve for each cohort (M0, M1, M3, M6, M9, M12)
2. Calculate revenue retention (different from logo retention if expansion/contraction)
3. Project LTV based on retention curve trend
4. Identify best/worst cohorts
5. Analyze factors influencing cohort performance
6. Generate cohort comparison matrix

If cohort data unavailable:
- Use traditional LTV formula
- Recommend setting up cohort tracking for future analyses
- Provide simplified retention analysis

**Scenario Modeling:**

Allow users to model improvements:
1. Reduce CAC by X%
2. Increase ARPC by X%
3. Reduce churn by X percentage points
4. Improve gross margin by X%
5. Combined scenarios

For each scenario:
- Calculate new metrics
- Show impact vs. baseline
- Assess feasibility
- Suggest tactics to achieve improvements
- Recommend timeframe

**Health Score Calculation:**

Overall Health Score (0-100):
- LTV:CAC ratio: 30 points (>5:1 = 30, 3-5:1 = 25, 1-3:1 = 15, <1:1 = 0)
- CAC Payback: 25 points (<6mo = 25, 6-12mo = 20, 12-18mo = 15, >18mo = 0)
- Magic Number: 25 points (>1.0 = 25, 0.75-1.0 = 20, 0.5-0.75 = 15, <0.5 = 0)
- Cohort Retention: 20 points (>80% M6 = 20, 70-80% = 15, 60-70% = 10, <60% = 0)

Health Status:
- 90-100: Excellent
- 75-89: Good
- 60-74: Acceptable
- <60: Needs Improvement

### Text Charts

**Retention Curve:**
Use ASCII art to show cohort retention curve over time

**Channel Efficiency:**
Use bar chart or table to compare CAC by channel

**Scenario Comparison:**
Use table to show baseline vs. scenario results side-by-side

## Examples

Worked examples are in `${CLAUDE_PLUGIN_ROOT}/references/unit-economics-examples.md`.

## Success Criteria

1. **Accurate metrics:** CAC, LTV, LTV:CAC, payback, Magic Number all calculated correctly
2. **Benchmarked insights:** Each metric compared to industry standards and company stage
3. **Actionable recommendations:** Specific, prioritized actions with expected impact
4. **Cohort analysis:** Deep dive into retention patterns and customer lifetime value
5. **Scenario modeling:** Test impact of improvements before implementation
6. **Channel efficiency:** Identify most/least efficient acquisition channels
7. **Executive-ready output:** Dashboard suitable for board presentations
8. **Historical tracking:** Enable trend analysis over time

## Agent Dispatch

Read `${CLAUDE_PLUGIN_ROOT}/agents/financial-analyst.md` and follow it in this session.

**Process:**
1. Agent loads assumptions from `.product-finance/assumptions.json`
2. Agent collects S&M spend, customer acquisition, revenue, and churn data
3. Agent uses skills: cac-calculation, ltv-calculation, magic-number, cohort-analysis
4. Agent models improvement scenarios and calculates impact
5. Agent generates unit economics dashboard with recommendations

**Skills Used:**
- `cac-calculation` - Calculate CAC blended and by channel (inbound, outbound, PLG, partner)
- `ltv-calculation` - Calculate LTV using traditional and cohort-based methods
- `ltv-cac-analysis` - Evaluate LTV:CAC ratio with stage-appropriate benchmarks
- `payback-calculation` - Determine CAC payback period and cash flow impact
- `magic-number` - Calculate sales efficiency with one-quarter lag
- `cohort-analysis` - Analyze retention curves and cohort-specific LTV
- `scenario-modeling` - Model improvements to CAC, churn, ARPC with impact projections

**Output:**
- `.product-finance/unit-economics.json` - Structured unit economics data
- `.product-finance/unit-economics-dashboard.md` - Executive dashboard
- Console summary with key metrics, channel efficiency, and priorities

**User Interaction:** Medium (provides S&M data, confirms metrics, reviews scenarios)

---

## References

- **Framework:** `BRAINSTORMING.md` - Unit economics methodology and benchmarks
- **Assumptions Schema:** `templates/assumptions.json` - Baseline data structure
- **Thought Leadership:**
  - David Skok (Matrix Partners) - SaaS Playbook: CAC, LTV, churn
  - Tomasz Tunguz (Theory Ventures) - LTV:CAC and growth benchmarks
  - SaaS Capital - Annual surveys on SaaS metrics
- **Integration:** Other product-finance commands for holistic financial analysis

---

**Financial Intelligence as Code** - Make customer economics transparent, measurable, and optimizable.
