---
description: Comprehensive financial health assessment with board-level KPIs, Rule of 40 analysis, unit economics evaluation, retention metrics, efficiency ratios, benchmark comparison, and strategic recommendations
---

# Health Check Command

## Purpose

The health-check command provides a comprehensive financial health assessment of your business, calculating all board-level KPIs that matter to investors, boards, and executive teams. It evaluates growth, profitability, unit economics, retention, and efficiency metrics to determine overall business health and provide strategic recommendations.

This command delivers a CFO-ready report with Rule of 40 compliance, unit economics assessment, benchmark comparisons, and actionable recommendations to improve financial performance.

## When to Use

- **Board preparation:** Monthly or quarterly board meeting prep with complete financial snapshot
- **Fundraising readiness:** Validate metrics before investor conversations
- **Strategic planning:** Annual or quarterly planning with comprehensive health assessment
- **Performance review:** Regular check-ins on business trajectory and metric trends
- **New leadership onboarding:** Provide comprehensive financial context to new executives
- **Post-launch assessment:** Evaluate overall business health after major product launches
- **Turnaround situations:** Diagnose financial issues and prioritize fixes

## What It Does

1. **Calculates Board-Level KPIs:**
   - Growth metrics (ARR, growth rate, new vs. expansion revenue)
   - Profitability metrics (gross margin, EBITDA margin, contribution margin)
   - Unit economics (CAC, LTV, LTV:CAC ratio, payback period, Magic Number)
   - Retention metrics (NRR, GRR, logo retention, churn rate)
   - Efficiency metrics (burn rate, runway, revenue per employee)

2. **Rule of 40 Compliance Check:**
   - Calculates Rule of 40 score (Growth % + EBITDA Margin %)
   - Determines compliance status (≥ 40% = healthy)
   - Weighted Rule of 40 variant (1.33 × Growth + 0.67 × EBITDA Margin)
   - Trend analysis (improving vs. declining)
   - Recommendations for improvement

3. **Unit Economics Health Assessment:**
   - CAC trend analysis (rising, stable, declining)
   - LTV:CAC ratio evaluation (target: ≥ 3.0)
   - CAC payback period (target: ≤ 12-18 months)
   - Magic Number analysis (target: ≥ 0.75)
   - Efficiency improvements needed

4. **Retention & Expansion Evaluation:**
   - NRR analysis (target: ≥ 100%, ideal: ≥ 120%)
   - GRR analysis (target: ≥ 85%, ideal: ≥ 90%)
   - Churn rate assessment (monthly and annual)
   - Expansion revenue contribution
   - Customer lifetime analysis

5. **Efficiency Ratio Analysis:**
   - Gross margin assessment (SaaS target: ≥ 70%)
   - Operating efficiency (sales efficiency, R&D efficiency)
   - Burn multiple (capital efficiency metric)
   - Revenue per employee benchmarking
   - Cost structure optimization opportunities

6. **Benchmark Comparison:**
   - Compare metrics to industry standards (public SaaS companies, peer benchmarks)
   - Stage-appropriate benchmarks (early-stage, growth-stage, mature)
   - Identify strengths (above benchmark) and weaknesses (below benchmark)
   - Percentile ranking where possible

7. **Strategic Recommendations:**
   - Prioritized action items to improve financial health
   - Trade-off analysis (growth vs. profitability optimization)
   - Specific metric improvement targets
   - Investment allocation suggestions
   - Risk mitigation strategies

8. **Saves Results:**
   - Structured data: `.product-finance/health-check.json`
   - Executive report: `.product-finance/health-report.md`
   - Timestamp and versioning for trend tracking
   - Historical comparison if previous reports exist

## Command Behavior

### Assessment Modes

**Mode 1: Full Health Check (Default)**
- Comprehensive assessment across all dimensions
- Collects all required data points
- Generates complete report with all KPIs

**Mode 2: Quick Check (Optional)**
- Focuses on critical metrics only (Rule of 40, LTV:CAC, NRR)
- Faster assessment for regular monitoring
- Abbreviated report

**Mode 3: Trend Analysis (Optional)**
- Requires historical health-check.json files
- Shows metric trends over time
- Identifies improving vs. declining metrics

The command defaults to Full Health Check. Quick Check and Trend Analysis available via flag or prompt.

## Data Collection Flow

### Phase 1: Assessment Context

**Question:** "What is the purpose of this health check?"

**Options:**
- `board_prep` - Preparing for board meeting or investor update
- `strategic_planning` - Annual or quarterly planning
- `fundraising` - Validating metrics before fundraising
- `performance_review` - Regular business review
- `diagnostic` - Investigating financial issues
- `routine` - Regular monthly/quarterly check-in

**Why we need this:** Purpose determines emphasis and recommendation tone.

**Question:** "What is your company stage?"

**Options:**
- `pre_revenue` - Pre-revenue or just launched
- `early_stage` - <$1M ARR, finding product-market fit
- `growth_stage` - $1M-$10M ARR, scaling go-to-market
- `scale_stage` - $10M-$50M ARR, optimizing unit economics
- `mature` - $50M+ ARR, profitability focus

**Why we need this:** Stage determines appropriate benchmarks and expectations.

**Question:** "Do you have historical health check data?" (yes/no)

**If yes:**
- Load previous `.product-finance/health-check.json`
- Enable trend analysis
- Show metric progression

### Phase 2: Growth Metrics

**Introduction:**
```
Growth Metrics Assessment
=========================
First, let's capture your revenue metrics - the foundation of all SaaS analysis.
We need both current state and historical data to calculate growth rates.
```

**Question:** "What is your current Annual Recurring Revenue (ARR)?"
- **Type:** number
- **Guidance:** "Total annualized recurring revenue from subscriptions"
- **Example:** "$5,000,000 ARR"
- **Help:** "ARR = MRR × 12, or sum of all annual contracts"

**Question:** "What was your ARR 12 months ago?"
- **Type:** number
- **Guidance:** "ARR exactly one year ago (for growth rate calculation)"
- **Example:** "$3,000,000 ARR"

**Auto-calculate:**
```
ARR Growth Rate = (Current ARR - Prior Year ARR) / Prior Year ARR × 100
Example: ($5M - $3M) / $3M × 100 = 66.7% growth
```

**Question:** "What was your ARR 3 months ago?"
- **Type:** number
- **Guidance:** "ARR one quarter ago (for quarterly growth trend)"
- **Optional:** Can skip if unavailable

**If provided, auto-calculate quarterly growth rate (QoQ)**

**Question:** "How much of your current ARR is from:"

**Breakdown:**
- New customers acquired in last 12 months: number
- Expansion revenue from existing customers: number
- Retained revenue from existing customers: number

**Validation:** Sum should approximately equal current ARR

**Auto-calculate:**
- New ARR percentage
- Expansion ARR percentage
- Retained ARR percentage
- ARR composition analysis

### Phase 3: Profitability Metrics

**Introduction:**
```
Profitability Assessment
========================
Now let's evaluate your profitability and margins.
These metrics determine your path to sustainable profitability.
```

**Question:** "What is your annual EBITDA (Earnings Before Interest, Taxes, Depreciation, Amortization)?"
- **Type:** number (can be negative)
- **Guidance:** "Operating profit before non-cash items. Revenue minus operating expenses."
- **Example:** "$500,000 EBITDA" or "-$1,500,000 EBITDA (burning)"
- **Help:** "If you don't have EBITDA, estimate: Revenue - (Sales & Marketing + R&D + G&A)"

**Auto-calculate:**
```
EBITDA Margin % = (EBITDA / ARR) × 100
Example: $500K EBITDA / $5M ARR = 10% EBITDA Margin
```

**Question:** "What is your gross margin?"
- **Type:** number (0-100 percent)
- **Guidance:** "Gross Margin % = (Revenue - COGS) / Revenue × 100"
- **Example:** "75% gross margin"
- **Help:** "COGS = hosting, infrastructure, support, AI costs directly tied to serving customers"

**If gross margin unknown, collect:**

**Question:** "What is your monthly Cost of Goods Sold (COGS)?"
- **Type:** number
- **Guidance:** "Direct costs to serve customers: hosting, infrastructure, AI APIs, support"
- **Example:** "$100,000/month COGS"

**Auto-calculate:**
```
Annual COGS = Monthly COGS × 12
Gross Margin % = (ARR - Annual COGS) / ARR × 100
```

**Question:** "What is your total annual operating expense (OpEx)?"
- **Type:** number
- **Guidance:** "Sales & Marketing + R&D + G&A expenses"
- **Example:** "$4,000,000 annual OpEx"
- **Optional:** If EBITDA already provided

**If provided, validate:**
```
EBITDA = (ARR - COGS) - OpEx
Check for consistency with earlier EBITDA input
```

### Phase 4: Unit Economics

**Introduction:**
```
Unit Economics Analysis
=======================
Let's analyze your customer acquisition and lifetime value economics.
These metrics determine long-term viability and scalability.
```

#### 4a. Customer Acquisition Cost (CAC)

**Question:** "What is your fully-loaded Customer Acquisition Cost (CAC)?"
- **Type:** number
- **Guidance:** "CAC = Total Sales & Marketing Spend / New Customers Acquired"
- **Example:** "$5,000 CAC per customer"

**If CAC unknown, collect:**

**Question:** "What is your total annual Sales & Marketing spend?"
- **Type:** number
- **Guidance:** "All sales team costs + marketing expenses + demand gen"
- **Example:** "$2,000,000 annual S&M spend"

**Question:** "How many new customers did you acquire in the last 12 months?"
- **Type:** integer
- **Guidance:** "Total new customer logos, not expansion from existing"
- **Example:** "400 new customers"

**Auto-calculate:**
```
CAC = Annual S&M Spend / New Customers
Example: $2M / 400 = $5,000 CAC
```

#### 4b. Lifetime Value (LTV)

**Question:** "What is your average Customer Lifetime Value (LTV)?"
- **Type:** number
- **Guidance:** "LTV = ARPC × Gross Margin % × (1 / Churn Rate)"
- **Example:** "$15,000 LTV"

**If LTV unknown, collect components:**

**Question:** "What is your Average Revenue Per Customer (ARPC) per month?"
- **Type:** number
- **Guidance:** "Total MRR / Total Customers"
- **Example:** "$500/month ARPC"

**Question:** "What is your monthly customer churn rate?"
- **Type:** number (0-100 percent)
- **Guidance:** "Percentage of customers who cancel each month"
- **Example:** "3% monthly churn"

**Auto-calculate:**
```
Annual ARPC = Monthly ARPC × 12
LTV = Annual ARPC × Gross Margin % / Annual Churn Rate
Annual Churn Rate = 1 - (1 - Monthly Churn Rate)^12

Example:
Annual ARPC = $500 × 12 = $6,000
Annual Churn = 1 - (1 - 0.03)^12 = 30.6%
LTV = $6,000 × 75% / 30.6% = $14,706
```

#### 4c. LTV:CAC Ratio and Payback Period

**Auto-calculate:**
```
LTV:CAC Ratio = LTV / CAC
CAC Payback Period (months) = CAC / (Monthly ARPC × Gross Margin %)

Example:
LTV:CAC = $15,000 / $5,000 = 3.0x (target met)
Payback = $5,000 / ($500 × 75%) = 13.3 months (slightly above 12-month target)
```

#### 4d. Magic Number (Sales Efficiency)

**Question:** "What was your quarterly net new ARR?"
- **Type:** number
- **Guidance:** "Net new ARR added in most recent quarter (new + expansion - churn)"
- **Example:** "$500,000 net new ARR in Q4"

**Question:** "What was your Sales & Marketing spend in the prior quarter?"
- **Type:** number
- **Guidance:** "S&M spend in quarter preceding the net new ARR"
- **Example:** "$600,000 S&M spend in Q3"

**Auto-calculate:**
```
Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend

Example: ($500K × 4) / $600K = 3.33
Magic Number = 3.33 (EXCELLENT - highly efficient sales & marketing)

Interpretation:
< 0.5 = Poor efficiency, need to optimize
0.5 - 0.75 = Acceptable, room for improvement
0.75 - 1.0 = Good efficiency
> 1.0 = Excellent efficiency
```

### Phase 5: Retention & Expansion Metrics

**Introduction:**
```
Retention & Expansion Analysis
===============================
Retention is the foundation of sustainable SaaS growth.
Let's measure how well you retain and expand customer revenue.
```

#### 5a. Net Revenue Retention (NRR)

**Question:** "What is your Net Revenue Retention (NRR)?"
- **Type:** number (percent)
- **Guidance:** "NRR = (Starting ARR + Expansion - Churn) / Starting ARR × 100"
- **Example:** "115% NRR" (expanded 15% from cohort)

**If NRR unknown, collect:**

**Question:** "Take a cohort of customers from 12 months ago. What was their ARR then?"
- **Type:** number
- **Guidance:** "Revenue from customers who existed 12 months ago"
- **Example:** "$2,000,000 from cohort"

**Question:** "What is the current ARR from that same cohort (excluding churned customers)?"
- **Type:** number
- **Guidance:** "Current revenue from surviving customers in cohort (includes expansion)"
- **Example:** "$2,300,000 current ARR from cohort"

**Auto-calculate:**
```
NRR = (Current Cohort ARR / Starting Cohort ARR) × 100
Example: ($2.3M / $2M) × 100 = 115% NRR
```

#### 5b. Gross Revenue Retention (GRR)

**Question:** "What is your Gross Revenue Retention (GRR)?"
- **Type:** number (percent)
- **Guidance:** "GRR = (Starting ARR - Churn) / Starting ARR × 100 (excludes expansion)"
- **Example:** "90% GRR"

**If GRR unknown, derive from NRR:**

**Question:** "From the same cohort, how much ARR was lost to churn?"
- **Type:** number
- **Guidance:** "Revenue lost from customers who canceled"
- **Example:** "$200,000 churned ARR"

**Auto-calculate:**
```
Retained ARR (no expansion) = Starting Cohort ARR - Churned ARR
GRR = (Retained ARR / Starting Cohort ARR) × 100

Example: ($2M - $200K) / $2M × 100 = 90% GRR

Expansion ARR = Current Cohort ARR - Retained ARR
Example: $2.3M - $1.8M = $500K expansion ARR
```

#### 5c. Logo Retention and Churn

**Question:** "How many customers did you have 12 months ago?"
- **Type:** integer
- **Example:** "500 customers"

**Question:** "How many of those customers are still active today?"
- **Type:** integer
- **Example:** "450 customers"

**Auto-calculate:**
```
Logo Retention Rate = (Surviving Customers / Starting Customers) × 100
Example: 450 / 500 = 90% logo retention

Logo Churn Rate = 100% - Logo Retention Rate
Example: 100% - 90% = 10% annual logo churn
```

**Question:** "What is your current total customer count?"
- **Type:** integer
- **Example:** "650 customers"

**Auto-calculate net customer growth:**
```
Net Customer Growth = Current Customers - Starting Customers
Example: 650 - 500 = 150 net new customers (+30% customer growth)
```

### Phase 6: Efficiency Metrics

**Introduction:**
```
Efficiency & Burn Analysis
==========================
Finally, let's evaluate capital efficiency and operational metrics.
```

#### 6a. Burn Rate and Runway

**Question:** "What is your current monthly burn rate?"
- **Type:** number (can be negative for profitable companies)
- **Guidance:** "Net cash consumed per month (negative = burning, positive = profitable)"
- **Example:** "-$250,000/month burn" or "+$100,000/month profit"

**If burn unknown but EBITDA known:**
```
Approximate Monthly Burn = EBITDA / 12 (negative EBITDA = burning)
```

**Question:** "What is your current cash balance?"
- **Type:** number
- **Guidance:** "Total cash and cash equivalents"
- **Example:** "$3,000,000 cash"

**Auto-calculate:**
```
Runway (months) = Cash Balance / Absolute(Monthly Burn Rate)
Example: $3M / $250K = 12 months runway

Runway Status:
< 6 months = CRITICAL - immediate action required
6-12 months = WARNING - fundraise or cut costs
12-18 months = ADEQUATE - monitor closely
> 18 months = HEALTHY - comfortable runway
```

#### 6b. Revenue Per Employee

**Question:** "What is your current total headcount?"
- **Type:** integer
- **Guidance:** "Total full-time employees across all functions"
- **Example:** "75 employees"

**Auto-calculate:**
```
Revenue Per Employee = ARR / Headcount
Example: $5M ARR / 75 employees = $66,667 per employee

Benchmark (SaaS):
$100K+ per employee = Efficient
$150K+ per employee = Highly efficient
$200K+ per employee = Best-in-class
```

#### 6c. Burn Multiple (Capital Efficiency)

**Auto-calculate:**
```
Burn Multiple = Net Burn / Net New ARR

Where:
Net Burn = Absolute value of negative EBITDA (if burning)
Net New ARR = ARR growth over period

Example:
Annual Burn = $1.5M (negative EBITDA)
Net New ARR = $2M (current $5M - prior $3M)
Burn Multiple = $1.5M / $2M = 0.75

Interpretation:
< 1.0 = Efficient (burning less than $1 to generate $1 ARR)
1.0 - 1.5 = Acceptable
1.5 - 2.0 = Inefficient
> 2.0 = Very inefficient - need to improve unit economics
```

### Phase 7: Calculate and Report

**Processing:**
1. Calculate all board-level KPIs
2. Determine Rule of 40 compliance and health score
3. Evaluate unit economics (LTV:CAC, payback, Magic Number)
4. Assess retention metrics (NRR, GRR, churn)
5. Analyze efficiency ratios (burn multiple, revenue per employee)
6. Compare against industry benchmarks for company stage
7. Generate overall health score and status
8. Create prioritized recommendations
9. Save structured data and executive report

## Output

### File 1: `.product-finance/health-check.json`

Structured data following schema:

```json
{
  "company": {
    "name": "Example SaaS Co",
    "stage": "growth_stage",
    "assessment_date": "2026-01-23T10:00:00Z",
    "assessment_purpose": "board_prep"
  },
  "growth_metrics": {
    "arr": {
      "current": 5000000,
      "prior_year": 3000000,
      "prior_quarter": 4500000,
      "growth_rate_yoy_pct": 66.7,
      "growth_rate_qoq_pct": 11.1,
      "status": "strong",
      "benchmark_comparison": "above_median"
    },
    "arr_composition": {
      "new_arr": 1500000,
      "new_arr_pct": 30.0,
      "expansion_arr": 700000,
      "expansion_arr_pct": 14.0,
      "retained_arr": 2800000,
      "retained_arr_pct": 56.0,
      "churned_arr": 200000,
      "churned_arr_pct": 4.0
    },
    "mrr": {
      "current": 416667,
      "growth_rate_mom_pct": 0.9
    }
  },
  "profitability_metrics": {
    "ebitda": {
      "annual": 500000,
      "margin_pct": 10.0,
      "status": "emerging_profitability"
    },
    "gross_margin": {
      "pct": 75.0,
      "annual_cogs": 1250000,
      "status": "healthy",
      "benchmark_comparison": "at_benchmark"
    },
    "operating_margin": {
      "pct": -20.0,
      "status": "investing_in_growth"
    }
  },
  "rule_of_40": {
    "score": 76.7,
    "growth_component": 66.7,
    "ebitda_margin_component": 10.0,
    "status": "EXCELLENT",
    "compliance": true,
    "weighted_rule_of_40": 95.4,
    "interpretation": "Strong Rule of 40 score driven by high growth rate. Company is efficiently scaling.",
    "benchmark_comparison": "top_quartile"
  },
  "unit_economics": {
    "cac": {
      "value": 5000,
      "annual_sm_spend": 2000000,
      "new_customers_12mo": 400,
      "status": "reasonable",
      "benchmark_comparison": "at_median"
    },
    "ltv": {
      "value": 15000,
      "annual_arpc": 6000,
      "gross_margin_pct": 75.0,
      "annual_churn_rate_pct": 30.6,
      "monthly_churn_rate_pct": 3.0,
      "status": "healthy"
    },
    "ltv_cac_ratio": {
      "ratio": 3.0,
      "status": "MEETS_TARGET",
      "target": 3.0,
      "interpretation": "Healthy unit economics. Each customer generates 3x their acquisition cost.",
      "benchmark_comparison": "at_benchmark"
    },
    "cac_payback_period": {
      "months": 13.3,
      "target_months": 12,
      "status": "SLIGHTLY_ABOVE_TARGET",
      "interpretation": "Payback period 1.3 months above target. Consider efficiency improvements.",
      "benchmark_comparison": "acceptable"
    },
    "magic_number": {
      "value": 3.33,
      "quarterly_net_new_arr": 500000,
      "prior_quarter_sm_spend": 600000,
      "status": "EXCELLENT",
      "interpretation": "Highly efficient sales & marketing. Generating $3.33 in ARR per $1 spent.",
      "benchmark_comparison": "top_decile"
    }
  },
  "retention_metrics": {
    "nrr": {
      "pct": 115.0,
      "cohort_starting_arr": 2000000,
      "cohort_current_arr": 2300000,
      "status": "STRONG",
      "target": 100.0,
      "interpretation": "Excellent net retention. Cohort expanded 15% through upsells.",
      "benchmark_comparison": "above_median"
    },
    "grr": {
      "pct": 90.0,
      "churned_arr": 200000,
      "status": "GOOD",
      "target": 85.0,
      "interpretation": "Good gross retention. Low revenue churn indicates product-market fit.",
      "benchmark_comparison": "above_median"
    },
    "expansion_arr": {
      "value": 500000,
      "pct_of_cohort": 25.0,
      "interpretation": "Strong expansion from existing customers driving NRR."
    },
    "logo_retention": {
      "pct": 90.0,
      "starting_customers": 500,
      "surviving_customers": 450,
      "churned_customers": 50,
      "annual_logo_churn_pct": 10.0,
      "status": "GOOD"
    },
    "customer_growth": {
      "starting_customers": 500,
      "current_customers": 650,
      "net_new_customers": 150,
      "growth_rate_pct": 30.0,
      "status": "strong"
    }
  },
  "efficiency_metrics": {
    "burn_rate": {
      "monthly": -250000,
      "annual": -3000000,
      "status": "burning"
    },
    "runway": {
      "months": 12,
      "cash_balance": 3000000,
      "status": "ADEQUATE",
      "recommendation": "Monitor closely. Consider fundraising in 6-9 months."
    },
    "revenue_per_employee": {
      "value": 66667,
      "headcount": 75,
      "status": "developing",
      "benchmark_comparison": "below_benchmark",
      "target": 100000
    },
    "burn_multiple": {
      "value": 0.75,
      "net_burn": 1500000,
      "net_new_arr": 2000000,
      "status": "EFFICIENT",
      "interpretation": "Burning $0.75 to generate $1 in new ARR. Capital efficient growth.",
      "benchmark_comparison": "above_median"
    }
  },
  "overall_assessment": {
    "health_score": 82,
    "health_status": "STRONG",
    "strengths": [
      "Excellent Rule of 40 score (76.7) driven by 67% growth",
      "Unit economics at target (LTV:CAC = 3.0x)",
      "Outstanding sales efficiency (Magic Number = 3.33)",
      "Strong retention (NRR = 115%, GRR = 90%)",
      "Capital efficient growth (Burn Multiple = 0.75)"
    ],
    "weaknesses": [
      "CAC payback period 1.3 months above target (13.3 vs 12 months)",
      "Revenue per employee below benchmark ($67K vs $100K+ target)",
      "Runway adequate but should plan fundraising (12 months)",
      "Monthly churn rate at 3% - opportunity to improve to 2% or below"
    ],
    "key_risks": [
      "Runway of 12 months requires fundraising planning in next 6-9 months",
      "Revenue per employee indicates need for productivity improvements",
      "Gross margin at 75% is healthy but has compression risk with scale"
    ]
  },
  "benchmarks": {
    "stage": "growth_stage",
    "benchmarks_applied": {
      "arr_growth_rate": {
        "target": 50.0,
        "top_quartile": 80.0,
        "median": 50.0,
        "bottom_quartile": 30.0,
        "company_value": 66.7,
        "status": "above_median"
      },
      "gross_margin": {
        "target": 70.0,
        "top_quartile": 80.0,
        "median": 75.0,
        "bottom_quartile": 65.0,
        "company_value": 75.0,
        "status": "at_median"
      },
      "nrr": {
        "target": 100.0,
        "top_quartile": 120.0,
        "median": 110.0,
        "bottom_quartile": 100.0,
        "company_value": 115.0,
        "status": "above_median"
      },
      "ltv_cac_ratio": {
        "target": 3.0,
        "top_quartile": 4.0,
        "median": 3.0,
        "bottom_quartile": 2.0,
        "company_value": 3.0,
        "status": "at_median"
      },
      "cac_payback_months": {
        "target": 12,
        "top_quartile": 9,
        "median": 12,
        "bottom_quartile": 18,
        "company_value": 13.3,
        "status": "acceptable"
      }
    }
  },
  "recommendations": {
    "priority_1_critical": [
      {
        "category": "runway",
        "issue": "12-month runway requires fundraising planning",
        "recommendation": "Begin fundraising process in next 6 months to maintain 12+ month cushion",
        "impact": "Prevents emergency fundraising, maintains negotiating leverage",
        "timeframe": "Q2 2026"
      }
    ],
    "priority_2_high": [
      {
        "category": "efficiency",
        "issue": "Revenue per employee below benchmark ($67K vs $100K+ target)",
        "recommendation": "Improve productivity through automation, tooling, and process optimization before adding headcount",
        "impact": "Increase revenue per employee 50% to $100K+ within 12 months",
        "timeframe": "Ongoing through 2026"
      },
      {
        "category": "retention",
        "issue": "Monthly churn at 3% - opportunity to reduce to 2%",
        "recommendation": "Invest in customer success, onboarding improvements, and proactive churn prevention",
        "impact": "Reducing churn from 3% to 2% increases LTV from $15K to $22.5K (+50%)",
        "timeframe": "Q2-Q3 2026"
      },
      {
        "category": "unit_economics",
        "issue": "CAC payback period 1.3 months above target",
        "recommendation": "Optimize sales & marketing efficiency: improve conversion rates, reduce sales cycle, increase ARPC",
        "impact": "Reduce payback to 12 months or below, improving cash flow",
        "timeframe": "Q2-Q4 2026"
      }
    ],
    "priority_3_medium": [
      {
        "category": "growth",
        "issue": "Maintain high growth rate while improving efficiency",
        "recommendation": "Balance growth investments with path to profitability. Target 50%+ growth with improving EBITDA margin.",
        "impact": "Sustain Rule of 40 excellence as company scales",
        "timeframe": "2026-2027"
      }
    ],
    "strategic_initiatives": [
      "Fundraising: Initiate Series B/C process in Q2 2026 to extend runway to 24+ months",
      "Efficiency: Implement productivity initiatives to reach $100K+ revenue per employee",
      "Retention: Launch customer success program to reduce churn from 3% to 2%",
      "Unit Economics: Optimize CAC payback to 12 months through sales efficiency improvements",
      "Profitability Path: Model path to 20%+ EBITDA margin within 18-24 months while maintaining 40%+ growth"
    ]
  },
  "metadata": {
    "report_date": "2026-01-23T10:00:00Z",
    "period_covered": "2025-01-01 to 2025-12-31",
    "data_confidence": "high",
    "previous_assessment_date": "2025-10-15T10:00:00Z",
    "assessment_frequency": "quarterly",
    "next_assessment_due": "2026-04-23T10:00:00Z"
  }
}
```

### File 2: `.product-finance/health-report.md`

Executive report:

```markdown
# Financial Health Check Report

**Company:** Example SaaS Co
**Assessment Date:** January 23, 2026
**Company Stage:** Growth Stage ($1M-$10M ARR)
**Purpose:** Board Preparation

**Overall Health Score: 82/100 - STRONG**

---

## Executive Summary

Example SaaS Co demonstrates **strong financial health** with excellent growth, healthy unit economics, and capital-efficient scaling. The company is in the top quartile for Rule of 40 performance and demonstrates outstanding sales efficiency.

**Key Highlights:**
- Rule of 40 score of **76.7** (well above 40 threshold)
- ARR growth of **67%** year-over-year
- Unit economics at target (LTV:CAC = **3.0x**)
- Exceptional sales efficiency (Magic Number = **3.33**)
- Strong retention (NRR = **115%**, GRR = **90%**)
- Capital efficient growth (Burn Multiple = **0.75**)

**Key Concerns:**
- Runway of 12 months requires fundraising planning
- Revenue per employee below benchmark
- CAC payback period slightly above target
- Opportunity to reduce churn and improve LTV

---

## 1. Growth Metrics

### Annual Recurring Revenue (ARR)

| Metric | Value | Status |
|--------|-------|--------|
| Current ARR | $5,000,000 | ✓ Strong |
| Prior Year ARR | $3,000,000 | - |
| YoY Growth Rate | 66.7% | ✓ Excellent |
| Prior Quarter ARR | $4,500,000 | - |
| QoQ Growth Rate | 11.1% | ✓ Strong |

**Assessment:** Growth rate of 67% is **above median** for growth-stage companies (benchmark: 50% median, 80% top quartile). Company is efficiently scaling.

### ARR Composition

| Component | Value | % of ARR |
|-----------|-------|----------|
| New ARR | $1,500,000 | 30% |
| Expansion ARR | $700,000 | 14% |
| Retained ARR | $2,800,000 | 56% |
| Churned ARR | ($200,000) | -4% |

**Insights:**
- Balanced growth: 30% from new customers, 14% from expansion
- Low churn (4%) indicates strong product-market fit
- Expansion revenue driving net retention above 100%

---

## 2. Rule of 40 Assessment

### Rule of 40 Score: 76.7 ✓ EXCELLENT

```
Rule of 40 = Growth Rate % + EBITDA Margin %
Rule of 40 = 66.7% + 10.0% = 76.7

Status: EXCELLENT (≥ 40 = healthy, ≥ 60 = exceptional)
Compliance: ✓ COMPLIANT (well above 40 threshold)
```

**Weighted Rule of 40:** 95.4
Formula: (1.33 × 66.7) + (0.67 × 10.0) = 95.4

### Benchmark Comparison

| Percentile | Score | Company Status |
|------------|-------|----------------|
| Top Quartile | 70+ | ✓ Top Quartile |
| Median | 45 | Well Above |
| Bottom Quartile | 20 | Well Above |

**Interpretation:** Exceptional Rule of 40 performance driven by high growth rate (67%) with emerging profitability (10% EBITDA margin). Company is efficiently balancing growth and profitability.

### Rule of 40 Trajectory

The company's strong Rule of 40 score is **growth-led**. As growth naturally moderates with scale, focus should shift to improving EBITDA margin to maintain Rule of 40 compliance.

**Target Path:**
- 2026: Maintain 50%+ growth, improve EBITDA margin to 15%+ (Rule of 40 = 65+)
- 2027: 40% growth, 20% EBITDA margin (Rule of 40 = 60)
- 2028: 30% growth, 25% EBITDA margin (Rule of 40 = 55)

---

## 3. Profitability Metrics

### Margins Analysis

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Gross Margin | 75.0% | 70%+ | ✓ Healthy |
| EBITDA Margin | 10.0% | Variable | Emerging |
| Operating Margin | -20.0% | Variable | Investing |

**Gross Margin:** 75% is **at benchmark** for SaaS companies. Strong gross margins provide operating leverage for future profitability.

**EBITDA Margin:** 10% positive EBITDA indicates emerging profitability while maintaining high growth. This is a healthy balance for growth-stage companies.

**Cost Structure:**
- Annual COGS: $1,250,000 (25% of revenue)
- Annual OpEx: $4,000,000 (80% of revenue)
- S&M: $2,000,000 (40% of revenue) - efficient for 67% growth
- R&D + G&A: $2,000,000 (40% of revenue)

---

## 4. Unit Economics

### Customer Acquisition Cost (CAC): $5,000

| Metric | Value |
|--------|-------|
| Annual S&M Spend | $2,000,000 |
| New Customers (12mo) | 400 |
| CAC per Customer | $5,000 |

**Status:** Reasonable CAC for growth-stage SaaS. At median benchmark for company stage.

### Lifetime Value (LTV): $15,000

| Metric | Value |
|--------|-------|
| Annual ARPC | $6,000 |
| Gross Margin % | 75% |
| Annual Churn Rate | 30.6% |
| Monthly Churn Rate | 3.0% |
| LTV Calculation | $6,000 × 75% / 30.6% = $15,000 |

**Status:** Healthy LTV driven by reasonable ARPC and gross margin. Churn rate at 3% monthly (30.6% annually) presents opportunity for improvement.

### LTV:CAC Ratio: 3.0x ✓ MEETS TARGET

```
LTV:CAC Ratio = $15,000 / $5,000 = 3.0x

Target: ≥ 3.0x
Status: ✓ MEETS TARGET (at benchmark)
```

**Interpretation:** Healthy unit economics. Each customer generates 3x their acquisition cost over their lifetime. This ratio is at the target threshold and industry median.

**Improvement Opportunity:** Reducing churn from 3% to 2% monthly would increase LTV to $22,500, improving LTV:CAC to 4.5x (excellent).

### CAC Payback Period: 13.3 months

```
CAC Payback = CAC / (Monthly ARPC × Gross Margin %)
CAC Payback = $5,000 / ($500 × 75%) = 13.3 months

Target: ≤ 12 months
Status: SLIGHTLY ABOVE TARGET (+1.3 months)
```

**Assessment:** Payback period is 1.3 months above the 12-month target, indicating room for efficiency improvement. This is still within acceptable range (< 18 months) but should be optimized.

**Improvement Paths:**
- Increase ARPC (raise prices, upsell features)
- Reduce CAC (improve conversion rates, lower cost channels)
- Accelerate time-to-value (faster onboarding, quicker expansion)

### Magic Number: 3.33 ✓ EXCELLENT

```
Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend
Magic Number = ($500,000 × 4) / $600,000 = 3.33

Interpretation:
< 0.5 = Poor
0.5 - 0.75 = Acceptable
0.75 - 1.0 = Good
> 1.0 = Excellent

Status: ✓ EXCELLENT (top decile)
```

**Assessment:** Outstanding sales and marketing efficiency. Generating $3.33 in ARR per $1 spent on S&M. This is top decile performance and indicates highly efficient go-to-market motion.

**Strategic Insight:** With Magic Number > 1.0, the company should **invest aggressively** in sales & marketing to maximize growth while efficiency remains high.

---

## 5. Retention & Expansion Metrics

### Net Revenue Retention (NRR): 115% ✓ STRONG

```
NRR = (Current Cohort ARR / Starting Cohort ARR) × 100
NRR = ($2,300,000 / $2,000,000) × 100 = 115%

Target: ≥ 100% (ideal: ≥ 120%)
Status: ✓ STRONG (above median)
```

**Assessment:** Excellent net retention. The cohort from 12 months ago has expanded 15% through upsells and expansions, more than offsetting churn. NRR of 115% is above median (110%) for growth-stage companies.

**Composition:**
- Starting Cohort ARR: $2,000,000
- Churned ARR: ($200,000) - 10% revenue churn
- Retained ARR: $1,800,000
- Expansion ARR: $500,000 - 25% expansion rate
- Current Cohort ARR: $2,300,000

### Gross Revenue Retention (GRR): 90% ✓ GOOD

```
GRR = (Retained ARR / Starting Cohort ARR) × 100
GRR = ($1,800,000 / $2,000,000) × 100 = 90%

Target: ≥ 85% (ideal: ≥ 90%)
Status: ✓ GOOD (above median)
```

**Assessment:** Good gross retention at 90%, meeting the ideal target. Only 10% revenue churn indicates strong product-market fit and customer satisfaction.

**Benchmark Comparison:** Above median (87%) for growth-stage companies. Top quartile is 93%.

### Logo Retention: 90% ✓ GOOD

| Metric | Value |
|--------|-------|
| Starting Customers (12mo ago) | 500 |
| Surviving Customers | 450 |
| Churned Customers | 50 |
| Logo Retention Rate | 90% |
| Annual Logo Churn Rate | 10% |

**Assessment:** Good logo retention at 90%. Annual logo churn of 10% is acceptable for growth-stage SaaS.

### Customer Growth: +30%

| Metric | Value |
|--------|-------|
| Starting Customers | 500 |
| Current Customers | 650 |
| Net New Customers | 150 |
| Growth Rate | 30% |

**Assessment:** Strong customer growth of 30% year-over-year, exceeding revenue growth of 67%. This indicates new customers are coming in at lower ARPC than existing customers (potential land-and-expand motion).

---

## 6. Efficiency Metrics

### Burn Rate & Runway

| Metric | Value | Status |
|--------|-------|--------|
| Monthly Burn Rate | $250,000 | Burning |
| Annual Burn | $3,000,000 | - |
| Cash Balance | $3,000,000 | - |
| Runway | 12 months | ADEQUATE |

**Assessment:** Runway of 12 months is **adequate** but requires close monitoring. Company should initiate fundraising process within the next 6-9 months to maintain comfortable cushion.

**Runway Status:**
- ✗ < 6 months = CRITICAL
- ⚠ 6-12 months = WARNING
- ✓ 12-18 months = ADEQUATE (current status)
- ✓ > 18 months = HEALTHY

**Recommendation:** Begin fundraising process in Q2 2026 to extend runway to 24+ months and maintain negotiating leverage.

### Revenue Per Employee: $66,667

```
Revenue Per Employee = ARR / Headcount
Revenue Per Employee = $5,000,000 / 75 = $66,667

Benchmark (SaaS):
$100K+ = Efficient
$150K+ = Highly efficient
$200K+ = Best-in-class

Status: DEVELOPING (below benchmark)
```

**Assessment:** Revenue per employee at $67K is **below benchmark** for SaaS companies ($100K+ target). This indicates opportunity for productivity improvements before scaling headcount.

**Improvement Path:** Focus on automation, tooling, process optimization, and leveraging AI to increase output per employee. Target: $100K+ within 12 months (50% improvement).

### Burn Multiple: 0.75 ✓ EFFICIENT

```
Burn Multiple = Net Burn / Net New ARR
Burn Multiple = $1,500,000 / $2,000,000 = 0.75

Interpretation:
< 1.0 = Efficient
1.0 - 1.5 = Acceptable
1.5 - 2.0 = Inefficient
> 2.0 = Very inefficient

Status: ✓ EFFICIENT (above median)
```

**Assessment:** Excellent capital efficiency. Burning $0.75 to generate $1 in new ARR. This is above median for growth-stage companies and indicates efficient growth.

**Strategic Insight:** With burn multiple < 1.0, the company is efficiently converting capital into growth. This positions the company well for fundraising and validates the growth investment strategy.

---

## 7. Benchmark Comparison

### Stage-Appropriate Benchmarks (Growth Stage: $1M-$10M ARR)

| Metric | Target | Top 25% | Median | Bottom 25% | Company | Status |
|--------|--------|---------|--------|------------|---------|--------|
| ARR Growth Rate | 50% | 80% | 50% | 30% | 66.7% | ✓ Above Median |
| Gross Margin | 70% | 80% | 75% | 65% | 75% | ✓ At Median |
| NRR | 100% | 120% | 110% | 100% | 115% | ✓ Above Median |
| LTV:CAC Ratio | 3.0 | 4.0 | 3.0 | 2.0 | 3.0 | ✓ At Median |
| CAC Payback (mo) | 12 | 9 | 12 | 18 | 13.3 | ⚠ Acceptable |
| Magic Number | 0.75 | 1.0+ | 0.75 | 0.5 | 3.33 | ✓ Top Decile |
| Rule of 40 | 40 | 70+ | 45 | 20 | 76.7 | ✓ Top Quartile |

### Competitive Position

**Strengths (Above Benchmark):**
- Rule of 40 score: Top quartile
- Magic Number: Top decile (exceptional sales efficiency)
- ARR Growth Rate: Above median
- NRR: Above median
- Burn Multiple: Above median (capital efficient)

**At Benchmark:**
- Gross Margin: At median
- LTV:CAC Ratio: At target

**Below Benchmark:**
- Revenue per Employee: Below target ($67K vs $100K+)
- CAC Payback Period: Slightly above target (13.3 vs 12 months)

---

## 8. Overall Assessment

### Health Score: 82/100 - STRONG

**Score Breakdown:**
- Growth Metrics: 18/20 (Strong growth, excellent composition)
- Profitability: 16/20 (Emerging profitability, Rule of 40 excellence)
- Unit Economics: 15/20 (At target, room for optimization)
- Retention: 18/20 (Strong NRR and GRR)
- Efficiency: 15/20 (Capital efficient, but revenue per employee below target)

### Financial Health Status: STRONG ✓

The company demonstrates **strong overall financial health** with particular strengths in growth efficiency, retention, and Rule of 40 performance. Key areas for improvement include revenue per employee, CAC payback optimization, and runway extension through fundraising.

### Key Strengths

1. **Exceptional Rule of 40 Performance (76.7)**
   Top quartile score driven by 67% growth with 10% EBITDA margin. Demonstrates efficient scaling.

2. **Outstanding Sales Efficiency (Magic Number = 3.33)**
   Top decile performance. Generating $3.33 in ARR per $1 spent on S&M. Should invest aggressively while efficiency remains high.

3. **Healthy Unit Economics (LTV:CAC = 3.0x)**
   At target threshold. Each customer generates 3x their acquisition cost.

4. **Strong Retention (NRR = 115%, GRR = 90%)**
   Above median net retention driven by expansion revenue. Low churn indicates product-market fit.

5. **Capital Efficient Growth (Burn Multiple = 0.75)**
   Burning $0.75 to generate $1 in ARR. Efficient conversion of capital to growth.

### Key Weaknesses

1. **Revenue Per Employee Below Benchmark ($67K vs $100K+ target)**
   Indicates need for productivity improvements before scaling headcount further. Focus on automation and tooling.

2. **CAC Payback Period Above Target (13.3 vs 12 months)**
   Room for efficiency improvement. Optimize conversion rates, sales cycle, or increase ARPC.

3. **Runway Requires Monitoring (12 months)**
   Adequate but not comfortable. Should initiate fundraising in next 6-9 months.

4. **Monthly Churn at 3% - Opportunity to Improve**
   Reducing churn to 2% would increase LTV from $15K to $22.5K (+50%), dramatically improving unit economics.

### Key Risks

1. **Fundraising Timing Risk**
   With 12-month runway, company must initiate fundraising process within 6-9 months to avoid emergency situation and maintain negotiating leverage.

2. **Productivity Risk**
   Revenue per employee below benchmark could limit scalability. Must improve productivity before aggressive hiring.

3. **Gross Margin Compression Risk**
   At 75%, gross margin is healthy but could face compression with scale (infrastructure costs, support costs). Monitor closely.

4. **Churn Sensitivity**
   At 3% monthly churn, small improvements have large LTV impact. Conversely, churn deterioration would significantly impact unit economics.

---

## 9. Strategic Recommendations

### Priority 1: CRITICAL (Immediate Action Required)

#### 1.1 Fundraising Planning (Q2 2026)
**Issue:** 12-month runway requires proactive fundraising planning

**Recommendation:**
- Initiate Series B/C fundraising process in Q2 2026 (within 6 months)
- Target: Extend runway to 24+ months post-funding
- Use strong metrics (Rule of 40 = 76.7, Magic Number = 3.33) to secure favorable terms

**Impact:** Prevents emergency fundraising, maintains negotiating leverage, provides capital for aggressive growth

**Timeline:** Begin conversations Q2 2026, close by Q3 2026

**Success Metrics:**
- Fundraising initiated by April 2026
- Term sheet secured by June 2026
- Funding closed by August 2026
- Post-funding runway > 24 months

---

### Priority 2: HIGH (Address within 6-12 months)

#### 2.1 Improve Revenue Per Employee
**Issue:** Revenue per employee at $67K is below $100K+ benchmark

**Recommendation:**
- Implement productivity initiatives: automation, AI tooling, process optimization
- Pause non-critical hiring until productivity improves
- Leverage AI for customer support, sales operations, development acceleration
- Focus on revenue acceleration before headcount acceleration

**Impact:** Increase revenue per employee from $67K to $100K+ within 12 months (+50% improvement)

**Timeline:** Q2-Q4 2026

**Success Metrics:**
- Q2 2026: Productivity initiatives identified and roadmapped
- Q3 2026: $80K revenue per employee
- Q4 2026: $90K revenue per employee
- Q2 2027: $100K+ revenue per employee (target achieved)

#### 2.2 Reduce Churn from 3% to 2% Monthly
**Issue:** Monthly churn at 3% represents significant LTV opportunity

**Recommendation:**
- Launch proactive customer success program
- Improve onboarding and time-to-value
- Implement churn prediction and intervention
- Invest in product improvements addressing top churn reasons
- Create quarterly business reviews (QBRs) for at-risk customers

**Impact:**
- Reduce monthly churn from 3% to 2%
- Increase LTV from $15K to $22.5K (+50%)
- Improve LTV:CAC from 3.0x to 4.5x (excellent)
- Increase NRR from 115% to 120%+ (top quartile)

**Timeline:** Q2-Q3 2026

**Success Metrics:**
- Q2 2026: Churn reduced to 2.5%
- Q3 2026: Churn reduced to 2.0%
- Q4 2026: Sustained at 2.0% or below

#### 2.3 Optimize CAC Payback Period
**Issue:** CAC payback at 13.3 months, target is ≤ 12 months

**Recommendation:**
Three parallel initiatives to reduce payback period:

**Option A: Increase ARPC**
- Implement value-based pricing review
- Launch premium tier or add-ons
- Target: Increase ARPC from $500/mo to $550/mo (+10%)
- Impact: Reduce payback to 12.1 months

**Option B: Reduce CAC**
- Optimize conversion rates across funnel
- Shift mix to lower-cost channels (self-service, inbound)
- Improve sales productivity and close rates
- Target: Reduce CAC from $5,000 to $4,500 (-10%)
- Impact: Reduce payback to 12.0 months

**Option C: Accelerate Time-to-Value**
- Improve onboarding to faster expansion/upsell
- Reduce time from signup to upgrade
- Target: Accelerate first expansion by 3 months
- Impact: Improve effective payback period

**Timeline:** Q2-Q4 2026

**Success Metrics:**
- Q4 2026: CAC payback reduced to 12 months or below
- Combination of ARPC increase, CAC reduction, and faster expansion

---

### Priority 3: MEDIUM (Address within 12-24 months)

#### 3.1 Sustain Rule of 40 Excellence as Company Scales
**Issue:** Maintain high growth while improving profitability margins

**Recommendation:**
- Model path to Rule of 40 sustainability as growth moderates
- Target: 50%+ growth with 15%+ EBITDA margin in 2026 (Rule of 40 = 65+)
- Target: 40% growth with 20% EBITDA margin in 2027 (Rule of 40 = 60)
- Balance growth investments with margin expansion

**Impact:** Sustain top-quartile Rule of 40 performance through scale stages

**Timeline:** 2026-2027

#### 3.2 Gross Margin Protection
**Issue:** Monitor gross margin for compression risk as company scales

**Recommendation:**
- Track gross margin trends monthly
- Optimize infrastructure costs (cloud spend, AI API costs)
- Implement usage-based pricing for high-cost features
- Monitor COGS per customer as customer mix evolves

**Target:** Maintain 75%+ gross margin through $10M ARR milestone

**Timeline:** Ongoing monitoring

---

### Strategic Initiatives Summary

| Priority | Initiative | Impact | Timeline |
|----------|-----------|--------|----------|
| 1 - Critical | Fundraising (Series B/C) | Extend runway to 24+ months | Q2-Q3 2026 |
| 2 - High | Revenue per employee to $100K+ | Improve efficiency 50% | Q2-Q4 2026 |
| 2 - High | Reduce churn from 3% to 2% | Increase LTV 50% to $22.5K | Q2-Q3 2026 |
| 2 - High | CAC payback to ≤12 months | Improve cash flow | Q2-Q4 2026 |
| 3 - Medium | Sustain Rule of 40 excellence | Top-quartile performance | 2026-2027 |
| 3 - Medium | Gross margin protection | Maintain 75%+ margins | Ongoing |

---

## 10. Next Steps

### Immediate Actions (Next 30 Days)

1. **Board Presentation Prep**
   - Use this report as foundation for the board meeting
   - Highlight Rule of 40 excellence, Magic Number performance
   - Address runway and fundraising timeline proactively

2. **Fundraising Kickoff**
   - Engage investment bank or advisors
   - Update the investor update with strong metrics
   - Develop investor target list

3. **Productivity Initiative Launch**
   - Form cross-functional productivity task force
   - Identify top 5 automation opportunities
   - Begin AI tooling evaluation and pilots

4. **Churn Reduction Program**
   - Analyze top churn reasons from exit interviews
   - Identify at-risk customer cohorts
   - Design proactive intervention playbook

### Quarterly Review Cadence

- **Monthly:** Track burn rate, runway, key efficiency metrics
- **Quarterly:** Full health check assessment, board reporting
- **Next Assessment Due:** April 23, 2026

### Success Criteria (12 Months)

By January 2027, the company should achieve:
- ✓ Fundraising completed, runway extended to 24+ months
- ✓ Revenue per employee improved to $100K+
- ✓ Monthly churn reduced to 2% or below
- ✓ CAC payback reduced to ≤12 months
- ✓ Rule of 40 score maintained at 60+
- ✓ LTV:CAC ratio improved to 4.0x+

---

## Appendix: Calculation Details

### Rule of 40 Calculation
```
Rule of 40 = ARR Growth Rate % + EBITDA Margin %

Growth Rate = (Current ARR - Prior Year ARR) / Prior Year ARR × 100
Growth Rate = ($5M - $3M) / $3M × 100 = 66.7%

EBITDA Margin = EBITDA / ARR × 100
EBITDA Margin = $500K / $5M × 100 = 10.0%

Rule of 40 = 66.7% + 10.0% = 76.7 ✓
```

### LTV Calculation
```
LTV = Annual ARPC × Gross Margin % / Annual Churn Rate

Monthly ARPC = $500
Annual ARPC = $500 × 12 = $6,000
Gross Margin % = 75%
Monthly Churn = 3.0%
Annual Churn = 1 - (1 - 0.03)^12 = 30.6%

LTV = $6,000 × 75% / 30.6% = $14,706 ≈ $15,000
```

### CAC Payback Period
```
CAC Payback = CAC / (Monthly ARPC × Gross Margin %)

CAC = $5,000
Monthly ARPC = $500
Gross Margin % = 75%

CAC Payback = $5,000 / ($500 × 75%)
CAC Payback = $5,000 / $375 = 13.3 months
```

### Magic Number
```
Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend

Quarterly Net New ARR = $500,000
Annualized = $500,000 × 4 = $2,000,000
Prior Quarter S&M = $600,000

Magic Number = $2,000,000 / $600,000 = 3.33
```

### NRR and GRR Calculations
```
Starting Cohort ARR (12 months ago) = $2,000,000
Churned ARR = $200,000
Expansion ARR = $500,000
Current Cohort ARR = $2,300,000

GRR = (Starting ARR - Churned ARR) / Starting ARR × 100
GRR = ($2M - $200K) / $2M × 100 = 90%

NRR = Current Cohort ARR / Starting ARR × 100
NRR = $2.3M / $2M × 100 = 115%
```

### Burn Multiple
```
Burn Multiple = Net Burn / Net New ARR

Net Burn = Absolute value of negative EBITDA
Net Burn = $1,500,000 (annual burn)

Net New ARR = Current ARR - Prior Year ARR
Net New ARR = $5M - $3M = $2,000,000

Burn Multiple = $1.5M / $2M = 0.75
```

---

*Financial Health Check Report - Product Finance Plugin*
*Assessment Date: January 23, 2026 | Next Review: April 23, 2026*
*Confidence Level: High | Data Quality: Strong*
```

### Console Output

**Summary displayed to user:**

```
Financial Health Check Complete!
================================

Company: Example SaaS Co
Stage: Growth Stage ($1M-$10M ARR)
Assessment Date: January 23, 2026

OVERALL HEALTH: STRONG ✓
Health Score: 82/100

Key Highlights
--------------
✓ Rule of 40: 76.7 (EXCELLENT - top quartile)
✓ ARR Growth: 66.7% year-over-year (above median)
✓ Magic Number: 3.33 (EXCELLENT - top decile sales efficiency)
✓ NRR: 115% (strong retention and expansion)
✓ LTV:CAC Ratio: 3.0x (meets target)
✓ Burn Multiple: 0.75 (capital efficient growth)

Areas for Improvement
---------------------
⚠ CAC Payback: 13.3 months (target: ≤12 months)
⚠ Revenue per Employee: $67K (target: $100K+)
⚠ Runway: 12 months (adequate but requires fundraising planning)
⚠ Monthly Churn: 3% (opportunity to reduce to 2%)

Board-Level KPIs Summary
------------------------
Growth:
  Current ARR: $5,000,000
  ARR Growth Rate: 66.7% YoY
  New ARR: $1,500,000 (30%)
  Expansion ARR: $700,000 (14%)

Profitability:
  Gross Margin: 75%
  EBITDA Margin: 10%
  Rule of 40 Score: 76.7 ✓

Unit Economics:
  CAC: $5,000
  LTV: $15,000
  LTV:CAC Ratio: 3.0x ✓
  CAC Payback: 13.3 months
  Magic Number: 3.33 ✓

Retention:
  NRR: 115% ✓
  GRR: 90% ✓
  Logo Retention: 90%
  Monthly Churn: 3%

Efficiency:
  Burn Rate: $250K/month
  Runway: 12 months
  Revenue per Employee: $67K
  Burn Multiple: 0.75 ✓

Priority Recommendations
------------------------
1. CRITICAL: Initiate fundraising in Q2 2026 (12-month runway)
2. HIGH: Improve revenue per employee to $100K+ through productivity initiatives
3. HIGH: Reduce monthly churn from 3% to 2% (increases LTV 50%)
4. HIGH: Optimize CAC payback to ≤12 months

Strategic Initiatives
---------------------
✓ Fundraising: Begin Series B/C process Q2 2026
✓ Efficiency: Launch productivity program targeting $100K+ per employee
✓ Retention: Customer success program to reduce churn to 2%
✓ Unit Economics: Optimize CAC payback through ARPC increase and sales efficiency

Files Generated
---------------
✓ .product-finance/health-check.json (structured data)
✓ .product-finance/health-report.md (executive report)

Next Steps
----------
1. Use health-report.md for board presentation
2. Initiate fundraising conversations (Q2 2026 target)
3. Launch productivity and churn reduction initiatives
4. Schedule next health check: April 23, 2026 (quarterly cadence)

Next Commands
-------------
- Run `/product-finance:feature-roi` to analyze specific investment opportunities
- Run `/product-finance:discover` for market opportunity assessment
- After improvements: Re-run health-check to track progress

Benchmark Performance: Top Quartile (Rule of 40, Magic Number)
Capital Efficiency: Excellent (Burn Multiple 0.75)
Overall Trajectory: Strong Growth, Path to Profitability
```

## Implementation Notes

### For Claude Code Agent

**Interactive Data Collection:**
- Use progressive disclosure: collect foundational metrics first (ARR, growth, EBITDA)
- Build upon existing data: calculate derived metrics automatically
- Validate consistency: cross-check inputs (e.g., ARR composition should sum to current ARR)
- Pre-populate from `.product-finance/assumptions.json` when available
- Allow "approximate" values with confidence indicators

**Calculation Logic:**
1. **Rule of 40:** Growth Rate % + EBITDA Margin %
2. **LTV:** Annual ARPC × Gross Margin % / Annual Churn Rate
3. **CAC:** Total S&M Spend / New Customers
4. **LTV:CAC Ratio:** LTV / CAC (target: ≥ 3.0)
5. **CAC Payback:** CAC / (Monthly ARPC × Gross Margin %)
6. **Magic Number:** (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend
7. **NRR:** (Current Cohort ARR / Starting Cohort ARR) × 100
8. **GRR:** ((Starting ARR - Churned ARR) / Starting ARR) × 100
9. **Burn Multiple:** Net Burn / Net New ARR
10. **Revenue per Employee:** ARR / Headcount

**Assessment Logic:**

**Health Score Calculation (0-100):**
- Growth Metrics: 20 points
  - ARR growth rate vs. stage benchmark
  - ARR composition quality
- Profitability: 20 points
  - Rule of 40 score
  - Gross margin health
- Unit Economics: 20 points
  - LTV:CAC ratio vs. target
  - CAC payback vs. target
  - Magic Number assessment
- Retention: 20 points
  - NRR vs. target
  - GRR vs. target
  - Logo retention
- Efficiency: 20 points
  - Burn multiple
  - Revenue per employee vs. benchmark
  - Runway adequacy

**Status Determination:**
- 90-100: EXCELLENT
- 75-89: STRONG
- 60-74: GOOD
- 40-59: NEEDS IMPROVEMENT
- 0-39: CONCERNING

**Benchmark Comparison:**
Stage-based benchmarks:
- Pre-revenue: Minimal metrics, focus on burn and runway
- Early-stage (<$1M ARR): Growth focus, unit economics emerging
- Growth-stage ($1M-$10M): Balanced growth and efficiency
- Scale-stage ($10M-$50M): Efficiency optimization, path to profitability
- Mature ($50M+): Profitability focus, Rule of 40 maintenance

**Recommendation Logic:**
1. Identify metrics below target or benchmark
2. Prioritize by impact and urgency
3. Provide specific, actionable recommendations
4. Include success metrics and timelines
5. Consider stage-appropriate expectations

**File Management:**
- Save structured data: `.product-finance/health-check.json`
- Save executive report: `.product-finance/health-report.md`
- Check for historical data: load previous health-check.json if exists
- Enable trend analysis: compare current to previous assessments
- Timestamp and version: track assessment date and frequency

**Trend Analysis (if historical data exists):**
- Load previous health-check.json files
- Calculate metric changes (improving, stable, declining)
- Show trajectory arrows in report (↑ improving, → stable, ↓ declining)
- Highlight significant changes (>10% swing)

**Integration with assumptions.json:**
- Pre-populate inputs from assumptions: pricing, costs, churn, growth rates
- Update assumptions.json with new data points collected during health check
- Maintain single source of truth for financial assumptions

**Validation Rules:**
- ARR must be positive
- Growth rate can be negative (declining businesses) but flag as concerning
- EBITDA can be negative (burning) - common for growth-stage
- Gross margin should be 0-100%, typically 60-90% for SaaS
- Churn rate should be 0-100%
- LTV:CAC ratio should be positive (flag if <1.0 as concerning)
- Warn if metrics seem unrealistic (e.g., NRR >200%, churn >20% monthly)

## Success Criteria

1. **Comprehensive assessment:** All board-level KPIs calculated accurately
2. **Rule of 40 clarity:** Clear compliance status and improvement path
3. **Unit economics transparency:** LTV:CAC, payback, Magic Number all evaluated
4. **Retention insights:** NRR, GRR, churn analysis with improvement opportunities
5. **Efficiency metrics:** Burn, runway, productivity assessed
6. **Actionable recommendations:** Prioritized, specific, measurable, time-bound
7. **Benchmark context:** Compare to stage-appropriate industry standards
8. **CFO-ready output:** Professional report suitable for board presentation
9. **Trend awareness:** Show metric progression if historical data available

## Agent Dispatch

Dispatch the `product-finance:financial-analyst` agent (Sonnet) with the `Agent` tool.

**Process:**
1. Agent loads assumptions and historical data from `.product-finance/`
2. Agent collects current metrics (ARR, EBITDA, churn, CAC, LTV)
3. Agent uses skills: rule-of-40, unit-economics, retention-analysis, benchmark-comparison
4. Agent calculates health score and identifies strengths/weaknesses
5. Agent generates prioritized recommendations and board-ready report

**Skills Used:**
- `rule-of-40` - Calculate Rule of 40 score and compliance status
- `unit-economics` - Evaluate CAC, LTV, LTV:CAC ratio, payback period, Magic Number
- `retention-analysis` - Assess NRR, GRR, logo retention, churn trends
- `efficiency-metrics` - Analyze burn rate, runway, revenue per employee, burn multiple
- `benchmark-comparison` - Compare metrics to stage-appropriate industry benchmarks
- `strategic-recommendations` - Generate prioritized action items with impact estimates

**Output:**
- `.product-finance/health-check.json` - Structured health assessment data
- `.product-finance/health-report.md` - Board-ready executive report
- Console summary with health score, key metrics, and top priorities

**User Interaction:** Medium (provides current metrics, confirms data, reviews recommendations)

---

## References

- **Framework:** `BRAINSTORMING.md` - Core financial metrics and Rule of 40 methodology
- **Assumptions Schema:** `templates/assumptions.json` - Financial assumptions structure
- **Integration:** Other product-finance commands for deeper analysis
- **Benchmarks:** Industry-standard SaaS metrics from SaaS Capital, Tomasz Tunguz, David Skok

---

**Financial Intelligence as Code** - Transform raw metrics into strategic insights, board-ready reporting, and actionable recommendations.
