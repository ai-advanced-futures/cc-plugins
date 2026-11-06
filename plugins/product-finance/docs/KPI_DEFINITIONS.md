# KPI Definitions Reference

> A comprehensive guide to Key Performance Indicators for AI-powered product finance analysis

**Version:** 1.0.0
**Author:** Product Finance Plugin
**Last Updated:** January 2026

---

## Table of Contents

1. [Growth Metrics](#growth-metrics)
   - [ARR (Annual Recurring Revenue)](#arr-annual-recurring-revenue)
   - [MRR (Monthly Recurring Revenue)](#mrr-monthly-recurring-revenue)
   - [Revenue Growth Rate](#revenue-growth-rate)
   - [Net New ARR](#net-new-arr)
2. [Profitability Metrics](#profitability-metrics)
   - [EBITDA Margin](#ebitda-margin)
   - [Gross Margin](#gross-margin)
   - [Rule of 40](#rule-of-40)
   - [Contribution Margin](#contribution-margin)
3. [Unit Economics Metrics](#unit-economics-metrics)
   - [CAC (Customer Acquisition Cost)](#cac-customer-acquisition-cost)
   - [LTV (Lifetime Value)](#ltv-lifetime-value)
   - [LTV:CAC Ratio](#ltvcac-ratio)
   - [CAC Payback Period](#cac-payback-period)
   - [Magic Number](#magic-number)
4. [Retention Metrics](#retention-metrics)
   - [NRR (Net Revenue Retention)](#nrr-net-revenue-retention)
   - [GRR (Gross Revenue Retention)](#grr-gross-revenue-retention)
   - [Logo Retention](#logo-retention)
   - [Churn Rate](#churn-rate)
   - [Expansion Revenue](#expansion-revenue)
5. [AI-Specific Metrics](#ai-specific-metrics)
   - [AI Cost per Interaction](#ai-cost-per-interaction)
   - [AI Cost Percentage](#ai-cost-percentage)
   - [AI ROI](#ai-roi)
   - [AI-Enabled Revenue](#ai-enabled-revenue)

---

## Growth Metrics

### ARR (Annual Recurring Revenue)

#### Definition
Annual Recurring Revenue (ARR) measures the annualized value of recurring revenue from subscriptions and contracts. It is the most important top-line metric for SaaS businesses.

#### Calculation Formula

```
ARR = MRR × 12
```

Or calculated directly:

```
ARR = (Active Subscriptions₁ × Annual Price₁) + (Active Subscriptions₂ × Annual Price₂) + ...
```

**Components:**
- **New ARR**: ARR from new customers
- **Expansion ARR**: ARR from upsells, cross-sells, and price increases
- **Contraction ARR**: ARR lost from downgrades
- **Churned ARR**: ARR lost from customer cancellations

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `subscription_id` | string | Billing system | Unique identifier for each subscription |
| `customer_id` | string | CRM/Billing | Customer identifier |
| `plan_price_annual` | number | Billing system | Annual subscription price |
| `subscription_status` | string | Billing system | Active, cancelled, paused |
| `subscription_start_date` | date | Billing system | When subscription began |
| `subscription_end_date` | date | Billing system | When subscription ended (if applicable) |

#### Instrumentation Guide

**Events to Track:**

```python
# Event: subscription_created
{
    "event_name": "subscription_created",
    "customer_id": "cust_12345",
    "subscription_id": "sub_67890",
    "plan": "professional",
    "mrr": 199.00,
    "arr": 2388.00,
    "start_date": "2026-01-15",
    "source": "organic",
    "timestamp": "2026-01-15T10:30:00Z"
}

# Event: subscription_upgraded
{
    "event_name": "subscription_upgraded",
    "customer_id": "cust_12345",
    "subscription_id": "sub_67890",
    "previous_plan": "starter",
    "new_plan": "professional",
    "previous_mrr": 49.00,
    "new_mrr": 199.00,
    "expansion_arr": 1800.00,
    "timestamp": "2026-02-01T14:00:00Z"
}
```

**Implementation Location:**
- Subscription creation endpoints
- Plan upgrade/downgrade handlers
- Billing system webhooks (Stripe, Chargebee, etc.)

#### Reporting Cadence

| Cadence | Report Type | Audience |
|---------|-------------|----------|
| Daily | ARR snapshot | Revenue operations |
| Weekly | ARR trend | Leadership team |
| Monthly | ARR analysis with components | Board, investors |
| Quarterly | ARR deep-dive with cohorts | Board package |

#### Benchmark Ranges

| Growth Stage | Good | Excellent | Top Decile |
|--------------|------|-----------|------------|
| Early (<$1M ARR) | 3x YoY | 5x YoY | 10x+ YoY |
| Growth ($1-10M) | 100% YoY | 150% YoY | 200%+ YoY |
| Scale ($10-100M) | 50% YoY | 75% YoY | 100%+ YoY |
| Enterprise ($100M+) | 25% YoY | 40% YoY | 60%+ YoY |

---

### MRR (Monthly Recurring Revenue)

#### Definition
Monthly Recurring Revenue (MRR) measures the normalized monthly value of recurring revenue. It provides a more granular view than ARR and is useful for tracking month-over-month changes.

#### Calculation Formula

```
MRR = Sum of all active monthly subscription values
```

**MRR Movements:**
```
Net New MRR = New MRR + Expansion MRR - Contraction MRR - Churned MRR
```

Where:
- **New MRR**: MRR from brand new customers
- **Expansion MRR**: MRR increase from existing customers (upsells, cross-sells)
- **Contraction MRR**: MRR decrease from existing customers (downgrades)
- **Churned MRR**: MRR lost from cancelled customers

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `subscription_id` | string | Billing | Unique subscription identifier |
| `monthly_price` | number | Billing | Monthly subscription value |
| `billing_period` | string | Billing | Monthly, annual, etc. |
| `normalized_mrr` | number | Calculated | Annual contracts normalized to monthly |

**For Annual Contracts:**
```
Normalized MRR = Annual Contract Value / 12
```

#### Instrumentation Guide

**Database Schema:**
```sql
-- MRR tracking table
CREATE TABLE mrr_snapshots (
    id BIGSERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255) NOT NULL,
    mrr DECIMAL(10, 2) NOT NULL,
    mrr_type VARCHAR(50), -- 'new', 'expansion', 'contraction', 'churn'
    plan VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(snapshot_date, subscription_id)
);

-- Create daily MRR snapshots
CREATE INDEX idx_mrr_date ON mrr_snapshots(snapshot_date);
```

**Events to Track:**
```python
# Track MRR changes
def track_mrr_change(customer_id, subscription_id, old_mrr, new_mrr, change_type):
    track_event("mrr_changed", {
        "customer_id": customer_id,
        "subscription_id": subscription_id,
        "old_mrr": old_mrr,
        "new_mrr": new_mrr,
        "mrr_delta": new_mrr - old_mrr,
        "change_type": change_type,  # 'new', 'expansion', 'contraction', 'churn'
        "timestamp": datetime.utcnow().isoformat()
    })
```

#### Reporting Cadence

| Cadence | Report Type | Key Components |
|---------|-------------|----------------|
| Daily | MRR snapshot | Total MRR, net change |
| Weekly | MRR waterfall | New, expansion, contraction, churn |
| Monthly | MRR analysis | Cohort breakdown, plan mix |

#### Benchmark Ranges

| Metric | Warning | Good | Excellent |
|--------|---------|------|-----------|
| MRR Growth (early) | <5% MoM | 10-20% MoM | >20% MoM |
| MRR Growth (growth) | <3% MoM | 5-10% MoM | >10% MoM |
| MRR Growth (scale) | <2% MoM | 3-5% MoM | >5% MoM |

---

### Revenue Growth Rate

#### Definition
Revenue Growth Rate measures the percentage change in revenue over a specific time period. It is typically calculated as year-over-year (YoY), quarter-over-quarter (QoQ), or month-over-month (MoM) growth.

#### Calculation Formula

**Year-over-Year Growth:**
```
YoY Growth Rate = ((Current Year ARR - Prior Year ARR) / Prior Year ARR) × 100
```

**Quarter-over-Quarter Growth (Annualized):**
```
QoQ Growth Rate = ((Current Quarter ARR / Prior Quarter ARR)^4 - 1) × 100
```

**Month-over-Month Growth:**
```
MoM Growth Rate = ((Current MRR - Prior MRR) / Prior MRR) × 100
```

**CAGR (Compound Annual Growth Rate):**
```
CAGR = ((Ending Value / Beginning Value)^(1/n) - 1) × 100
```
Where n = number of years

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `revenue_current_period` | number | Financial system | Revenue in current period |
| `revenue_prior_period` | number | Financial system | Revenue in comparison period |
| `period_type` | string | Configuration | month, quarter, year |

#### Instrumentation Guide

**Python Implementation (from `scripts/utils/calculators.py`):**
```python
def calculate_growth_rate(
    initial_value: float,
    final_value: float,
    periods: int = 1,
    decimal_places: int = 2,
) -> float:
    """Calculate growth rate between two values over periods.

    For single period: ((final - initial) / initial) × 100
    For multiple periods: CAGR formula
    """
    if initial_value <= 0:
        raise ValueError("Initial value must be positive")

    if periods == 1:
        return round(((final_value - initial_value) / initial_value) * 100, decimal_places)
    else:
        # CAGR calculation
        cagr = (pow(final_value / initial_value, 1 / periods) - 1) * 100
        return round(cagr, decimal_places)
```

#### Reporting Cadence

| Cadence | Growth Type | Use Case |
|---------|-------------|----------|
| Monthly | MoM | Operational tracking |
| Quarterly | QoQ, YoY | Board reporting |
| Annual | YoY, CAGR | Investor updates |

#### Benchmark Ranges

| ARR Range | T2D3 Target | Good | Excellent |
|-----------|-------------|------|-----------|
| $1M-$2M | Triple (200%) | 100% | 150%+ |
| $2M-$6M | Triple (200%) | 80% | 120%+ |
| $6M-$18M | Double (100%) | 60% | 80%+ |
| $18M-$36M | Double (100%) | 40% | 60%+ |
| $36M+ | 50%+ | 30% | 50%+ |

*T2D3: Triple-Triple-Double-Double-Double growth pattern for elite SaaS companies*

---

### Net New ARR

#### Definition
Net New ARR measures the total change in ARR over a period, accounting for all sources of growth and loss. It is the primary metric for understanding overall business momentum.

#### Calculation Formula

```
Net New ARR = New ARR + Expansion ARR - Contraction ARR - Churned ARR
```

**Components:**
- **New ARR**: First-time subscription revenue from new customers
- **Expansion ARR**: Additional revenue from existing customers (upsells, cross-sells, seat expansion)
- **Contraction ARR**: Revenue lost from downgrades (but customer retained)
- **Churned ARR**: Revenue lost from cancelled customers

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `new_customers` | count | CRM | New customers acquired |
| `new_customer_arr` | number | Billing | ARR from new customers |
| `expansion_events` | array | Billing | Upgrade transactions |
| `expansion_arr` | number | Billing | ARR from expansions |
| `contraction_events` | array | Billing | Downgrade transactions |
| `contraction_arr` | number | Billing | ARR lost to downgrades |
| `churned_customers` | count | CRM | Customers who cancelled |
| `churned_arr` | number | Billing | ARR lost to churn |

#### Instrumentation Guide

**ARR Waterfall Tracking:**
```python
# Daily ARR movement tracking
def track_arr_movement(period_date):
    movements = {
        "period_date": period_date.isoformat(),
        "opening_arr": get_arr_at_date(period_date - timedelta(days=1)),
        "new_arr": sum_new_subscriptions(period_date),
        "expansion_arr": sum_expansions(period_date),
        "contraction_arr": sum_contractions(period_date),
        "churned_arr": sum_churned(period_date),
    }
    movements["closing_arr"] = (
        movements["opening_arr"]
        + movements["new_arr"]
        + movements["expansion_arr"]
        - movements["contraction_arr"]
        - movements["churned_arr"]
    )
    movements["net_new_arr"] = movements["closing_arr"] - movements["opening_arr"]

    track_event("arr_movement", movements)
    return movements
```

#### Reporting Cadence

| Cadence | Report Type | Visualizations |
|---------|-------------|----------------|
| Weekly | Net New ARR trend | Line chart |
| Monthly | ARR waterfall | Waterfall chart |
| Quarterly | Component analysis | Stacked bar, cohort |

#### Benchmark Ranges

| ARR Range | Warning | Good | Excellent |
|-----------|---------|------|-----------|
| <$1M | <$50K/quarter | $100K+/quarter | $250K+/quarter |
| $1M-$10M | <10% of ARR | 15-25% of ARR | 30%+ of ARR |
| $10M-$100M | <8% of ARR | 10-15% of ARR | 20%+ of ARR |

---

## Profitability Metrics

### EBITDA Margin

#### Definition
EBITDA Margin measures operating profitability as a percentage of revenue, excluding interest, taxes, depreciation, and amortization. It is a key measure of operating efficiency for SaaS companies.

#### Calculation Formula

```
EBITDA = Revenue - Operating Expenses (excluding D&A, Interest, Taxes)
EBITDA Margin = (EBITDA / Revenue) × 100
```

**SaaS EBITDA Components:**
```
EBITDA = Revenue - COGS - Sales & Marketing - R&D - G&A
```

Where:
- **COGS**: Hosting, support, customer success (costs to serve)
- **S&M**: Sales, marketing, lead generation
- **R&D**: Engineering, product development
- **G&A**: Finance, HR, legal, facilities

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `total_revenue` | number | Financial system | Total revenue for period |
| `cogs` | number | Financial system | Cost of goods sold |
| `sales_marketing` | number | Financial system | S&M expenses |
| `research_development` | number | Financial system | R&D expenses |
| `general_admin` | number | Financial system | G&A expenses |

#### Instrumentation Guide

**Financial Data Tracking:**
```python
# Monthly P&L tracking
def track_monthly_financials(month_end_date):
    financials = {
        "period_end": month_end_date.isoformat(),
        "revenue": get_total_revenue(month_end_date),
        "cogs": get_cogs(month_end_date),
        "gross_profit": None,  # Calculated
        "sales_marketing": get_sm_expense(month_end_date),
        "research_development": get_rd_expense(month_end_date),
        "general_admin": get_ga_expense(month_end_date),
        "ebitda": None,  # Calculated
        "ebitda_margin": None  # Calculated
    }

    financials["gross_profit"] = financials["revenue"] - financials["cogs"]
    financials["ebitda"] = (
        financials["revenue"]
        - financials["cogs"]
        - financials["sales_marketing"]
        - financials["research_development"]
        - financials["general_admin"]
    )
    financials["ebitda_margin"] = (financials["ebitda"] / financials["revenue"]) * 100

    track_event("monthly_financials", financials)
```

#### Reporting Cadence

| Cadence | Report Type | Audience |
|---------|-------------|----------|
| Monthly | P&L with EBITDA | Finance team |
| Quarterly | EBITDA trend analysis | Board |
| Annual | Full-year EBITDA report | Investors |

#### Benchmark Ranges

| Company Stage | Target EBITDA Margin |
|---------------|----------------------|
| Early (growth-first) | -50% to -20% acceptable |
| Growth (100%+ growth) | -20% to 0% acceptable |
| Scale (50-100% growth) | 0% to 15% target |
| Mature (<50% growth) | 15% to 30%+ target |
| Public SaaS median | 10-15% |
| Top quartile public | 25%+ |

---

### Gross Margin

#### Definition
Gross Margin measures the percentage of revenue retained after subtracting the direct costs of delivering the product/service (Cost of Goods Sold). For SaaS, this includes hosting, infrastructure, and customer support costs.

#### Calculation Formula

```
Gross Profit = Revenue - COGS
Gross Margin = (Gross Profit / Revenue) × 100
```

**SaaS COGS Components:**
- Cloud infrastructure (AWS, GCP, Azure)
- Third-party API costs
- Customer support costs
- Professional services costs
- AI/ML inference costs

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `total_revenue` | number | Financial system | Total revenue |
| `infrastructure_cost` | number | Cloud billing | AWS, GCP, Azure costs |
| `api_costs` | number | Vendor invoices | Third-party API costs |
| `support_cost` | number | HR/Finance | Support team cost allocation |
| `ai_inference_cost` | number | AI provider billing | LLM/AI API costs |

#### Instrumentation Guide

**Python Implementation (from `scripts/utils/calculators.py`):**
```python
def calculate_gross_margin(
    revenue: float,
    cogs: float,
    decimal_places: int = 2,
) -> float:
    """Calculate gross margin percentage.

    Formula: ((revenue - COGS) / revenue) × 100
    """
    if revenue == 0:
        raise ValueError("Cannot calculate margin with zero revenue")

    margin = ((revenue - cogs) / revenue) * 100
    return round(margin, decimal_places)
```

**Cost Allocation Tracking:**
```python
def track_cogs_allocation():
    cogs = {
        "period": current_month.isoformat(),
        "infrastructure": {
            "aws": get_aws_cost(),
            "gcp": get_gcp_cost(),
            "cdn": get_cdn_cost()
        },
        "third_party_apis": {
            "ai_providers": get_ai_api_cost(),
            "email": get_email_cost(),
            "analytics": get_analytics_cost()
        },
        "support": {
            "team_cost": get_support_team_cost(),
            "tools": get_support_tools_cost()
        }
    }
    cogs["total"] = sum_all_costs(cogs)
    track_event("cogs_allocation", cogs)
```

#### Reporting Cadence

| Cadence | Report Type | Detail Level |
|---------|-------------|--------------|
| Monthly | Gross margin trend | Summary |
| Quarterly | COGS breakdown | Component-level |
| Annual | Gross margin analysis | Deep-dive with YoY |

#### Benchmark Ranges

| Business Type | Target Gross Margin |
|---------------|---------------------|
| Pure SaaS (no services) | 75-85% |
| SaaS with services | 65-75% |
| AI-heavy SaaS | 60-75% |
| Marketplace/platform | 50-70% |
| **Warning threshold** | <70% for pure SaaS |
| **Top quartile** | >80% |

---

### Rule of 40

#### Definition
The Rule of 40 is a benchmark that combines growth rate and profitability margin. A company is considered healthy if the sum of its revenue growth rate and profit margin equals or exceeds 40%.

#### Calculation Formula

**Classic Rule of 40:**
```
Rule of 40 Score = Revenue Growth Rate (%) + EBITDA Margin (%)
```

**Weighted Rule of 40 (growth weighted 2x):**
```
Weighted Rule of 40 = (1.33 × Revenue Growth Rate) + (0.67 × EBITDA Margin)
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `revenue_growth_rate` | number | Calculated | YoY revenue growth % |
| `ebitda_margin` | number | Financial system | EBITDA margin % |
| `company_stage` | string | Configuration | early, growth, scale, mature |

#### Instrumentation Guide

**Python Implementation (from `scripts/rule_of_40.py`):**
```python
def calculate_rule_of_40(data: RuleOf40Input) -> RuleOf40Result:
    """Calculate Rule of 40 and weighted Rule of 40.

    Classic Rule of 40 Formula:
        Rule of 40 = Revenue Growth Rate (%) + EBITDA Margin (%)

    Weighted Rule of 40 Formula:
        Weighted Rule of 40 = 1.33 × Growth Rate + 0.67 × EBITDA Margin
    """
    # Calculate classic Rule of 40
    rule_of_40_score = data.revenue_growth_rate + data.ebitda_margin

    # Calculate weighted Rule of 40
    weighted_rule_of_40 = (1.33 * data.revenue_growth_rate) + (0.67 * data.ebitda_margin)

    return RuleOf40Result(
        rule_of_40_score=rule_of_40_score,
        weighted_rule_of_40=weighted_rule_of_40,
        revenue_growth_rate=data.revenue_growth_rate,
        ebitda_margin=data.ebitda_margin,
        health_status=assess_health(rule_of_40_score, data.company_stage),
        # ... additional analysis
    )
```

#### Reporting Cadence

| Cadence | Report Type | Key Elements |
|---------|-------------|--------------|
| Monthly | Rule of 40 tracking | Score, trend |
| Quarterly | Board Rule of 40 | Score, peer comparison |
| Annual | Strategic Rule of 40 | Historical trend, outlook |

#### Benchmark Ranges

| Score Range | Health Status | Interpretation |
|-------------|---------------|----------------|
| >= 40 | **Excellent** | IPO-ready, top quartile |
| 30-40 | **Good** | Solid performance |
| 20-30 | **Warning** | Needs improvement |
| < 20 | **Critical** | Urgent action required |

**Stage-Adjusted Benchmarks:**
| Stage | Excellent | Good | Warning | Critical |
|-------|-----------|------|---------|----------|
| Early | >= 30 | 20-30 | 10-20 | < 10 |
| Growth | >= 40 | 30-40 | 20-30 | < 20 |
| Scale | >= 50 | 40-50 | 30-40 | < 30 |
| Mature | >= 50 | 40-50 | 30-40 | < 30 |

---

### Contribution Margin

#### Definition
Contribution Margin measures the profitability of individual products, features, or customer segments after subtracting variable costs. It helps identify which areas of the business generate the most profit.

#### Calculation Formula

```
Contribution Margin = (Revenue - Variable Costs) / Revenue × 100
```

**Per-Unit Contribution Margin:**
```
Per-Unit CM = Price per Unit - Variable Cost per Unit
```

**For SaaS features/products:**
```
Feature CM = Feature Revenue - (AI Costs + Infrastructure Costs + Support Costs attributable to feature)
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `feature_revenue` | number | Billing | Revenue attributable to feature |
| `feature_variable_costs` | number | Cost allocation | Variable costs for feature |
| `ai_cost_per_feature` | number | AI tracking | AI costs for specific feature |
| `support_cost_per_feature` | number | Support system | Support costs per feature |

#### Instrumentation Guide

**Feature-Level Cost Tracking:**
```python
def calculate_feature_contribution_margin(feature_id, period):
    # Get feature revenue
    revenue = get_feature_revenue(feature_id, period)

    # Allocate variable costs
    variable_costs = {
        "ai_costs": get_ai_costs_for_feature(feature_id, period),
        "infrastructure": get_infra_costs_for_feature(feature_id, period),
        "support_allocation": allocate_support_costs(feature_id, period)
    }

    total_variable_costs = sum(variable_costs.values())
    contribution_margin = ((revenue - total_variable_costs) / revenue) * 100

    return {
        "feature_id": feature_id,
        "revenue": revenue,
        "variable_costs": total_variable_costs,
        "contribution_margin": contribution_margin,
        "cost_breakdown": variable_costs
    }
```

#### Reporting Cadence

| Cadence | Report Type | Granularity |
|---------|-------------|-------------|
| Monthly | Feature CM analysis | Feature-level |
| Quarterly | Product line CM | Product/segment |
| Annual | Strategic CM review | Business unit |

#### Benchmark Ranges

| Business Area | Target CM | Warning Threshold |
|---------------|-----------|-------------------|
| Core SaaS features | 70-85% | < 60% |
| AI-powered features | 50-70% | < 40% |
| Professional services | 30-50% | < 20% |
| Support/Success | 40-60% | < 30% |

---

## Unit Economics Metrics

### CAC (Customer Acquisition Cost)

#### Definition
Customer Acquisition Cost (CAC) measures the total cost to acquire a new customer, including all sales and marketing expenses. It is a fundamental unit economics metric.

#### Calculation Formula

```
CAC = (Total Sales Costs + Total Marketing Costs) / Number of New Customers
```

**Fully-Loaded CAC:**
```
Fully-Loaded CAC = (Sales + Marketing + Sales Engineering + Implementation) / New Customers
```

**Blended vs. Paid CAC:**
- **Blended CAC**: All acquisition costs / All new customers
- **Paid CAC**: Paid channel costs / Paid-acquired customers
- **Organic CAC**: Organic costs / Organic-acquired customers

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `sales_costs` | number | Financial system | Sales team fully-loaded costs |
| `marketing_costs` | number | Financial system | All marketing spend |
| `new_customers` | integer | CRM | New customers acquired |
| `period_months` | integer | Configuration | Analysis period |
| `acquisition_channel` | string | CRM | Channel attribution |

#### Instrumentation Guide

**Python Implementation (from `scripts/unit_economics.py`):**
```python
def calculate_cac(data: CACInput) -> CACResult:
    """Calculate Customer Acquisition Cost (CAC).

    Formula: CAC = (Sales Costs + Marketing Costs) / New Customers
    """
    total_costs = data.sales_costs + data.marketing_costs
    cac = total_costs / data.new_customers

    # Health assessment
    if cac < 100:
        health = MetricHealth.EXCELLENT
    elif cac < 500:
        health = MetricHealth.GOOD
    elif cac < 2000:
        health = MetricHealth.WARNING
    else:
        health = MetricHealth.CRITICAL

    return CACResult(
        cac=cac,
        total_acquisition_costs=total_costs,
        new_customers=data.new_customers,
        health_status=health
    )
```

**Tracking Implementation:**
```python
# Track customer acquisition
def track_customer_acquisition(customer_id, acquisition_data):
    track_event("customer_acquired", {
        "customer_id": customer_id,
        "acquisition_date": datetime.utcnow().isoformat(),
        "channel": acquisition_data.get("channel"),
        "campaign_id": acquisition_data.get("campaign_id"),
        "attributed_cost": acquisition_data.get("attributed_cost"),
        "first_touch": acquisition_data.get("first_touch"),
        "last_touch": acquisition_data.get("last_touch")
    })
```

#### Reporting Cadence

| Cadence | Report Type | Segmentation |
|---------|-------------|--------------|
| Monthly | CAC trend | By channel |
| Quarterly | CAC analysis | By segment, channel, cohort |
| Annual | CAC deep-dive | Strategic planning |

#### Benchmark Ranges

| Segment | Good CAC | Excellent CAC | Warning |
|---------|----------|---------------|---------|
| SMB B2C | $50-$200 | < $50 | > $500 |
| SMB B2B | $200-$1,000 | < $200 | > $2,000 |
| Mid-Market | $1,000-$5,000 | < $1,000 | > $10,000 |
| Enterprise | $5,000-$50,000 | < $5,000 | > $100,000 |

---

### LTV (Lifetime Value)

#### Definition
Lifetime Value (LTV) measures the total revenue a business can expect from a single customer account over the entire duration of their relationship. It is critical for understanding the long-term value of customer acquisition.

#### Calculation Formula

**Simple LTV:**
```
LTV = ARPU × Gross Margin % / Monthly Churn Rate
```

**Alternative LTV Formula:**
```
LTV = ARPU × Average Customer Lifetime (months) × Gross Margin %
```

Where:
```
Average Customer Lifetime = 1 / Monthly Churn Rate
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `arpu` | number | Billing | Average Revenue Per User (monthly) |
| `gross_margin_percent` | number | Financial system | Gross margin % |
| `churn_rate_percent` | number | Retention analysis | Monthly churn rate % |
| `average_lifetime_months` | number | Cohort analysis | Average customer lifetime |

#### Instrumentation Guide

**Python Implementation (from `scripts/unit_economics.py`):**
```python
def calculate_ltv(data: LTVInput) -> LTVResult:
    """Calculate Customer Lifetime Value (LTV).

    Formula: LTV = ARPU × (Gross Margin % / 100) / (Churn Rate % / 100)
    """
    gross_margin_decimal = data.gross_margin_percent / 100
    churn_rate_decimal = data.churn_rate_percent / 100

    ltv = data.arpu * gross_margin_decimal / churn_rate_decimal
    average_lifespan = 1 / churn_rate_decimal  # months

    # Health assessment
    if ltv < 500:
        health = MetricHealth.WARNING
    elif ltv < 2000:
        health = MetricHealth.GOOD
    elif ltv < 10000:
        health = MetricHealth.GOOD
    else:
        health = MetricHealth.EXCELLENT

    return LTVResult(
        ltv=ltv,
        arpu=data.arpu,
        average_customer_lifespan_months=average_lifespan,
        health_status=health
    )
```

**Cohort-Based LTV Tracking:**
```python
def track_cohort_ltv(cohort_month):
    """Track LTV by acquisition cohort."""
    cohort_customers = get_cohort_customers(cohort_month)

    for customer in cohort_customers:
        track_event("cohort_ltv_update", {
            "customer_id": customer.id,
            "cohort_month": cohort_month.isoformat(),
            "total_revenue_to_date": customer.total_revenue,
            "months_active": customer.months_since_acquisition,
            "predicted_ltv": calculate_predicted_ltv(customer),
            "is_churned": customer.is_churned
        })
```

#### Reporting Cadence

| Cadence | Report Type | Analysis Type |
|---------|-------------|---------------|
| Monthly | LTV trend | Overall, by segment |
| Quarterly | Cohort LTV analysis | By acquisition cohort |
| Annual | LTV deep-dive | Strategic, predictive |

#### Benchmark Ranges

| Segment | Good LTV | Excellent LTV | Warning |
|---------|----------|---------------|---------|
| SMB B2C | $200-$1,000 | > $1,000 | < $200 |
| SMB B2B | $2,000-$10,000 | > $10,000 | < $2,000 |
| Mid-Market | $10,000-$50,000 | > $50,000 | < $10,000 |
| Enterprise | $50,000-$500,000+ | > $500,000 | < $50,000 |

---

### LTV:CAC Ratio

#### Definition
The LTV:CAC Ratio compares the lifetime value of a customer to the cost of acquiring them. It is the most important unit economics metric for determining whether a business has sustainable economics.

#### Calculation Formula

```
LTV:CAC Ratio = LTV / CAC
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `ltv` | number | Calculated | Customer Lifetime Value |
| `cac` | number | Calculated | Customer Acquisition Cost |

#### Instrumentation Guide

**Python Implementation (from `scripts/unit_economics.py`):**
```python
def calculate_ltv_cac_ratio(ltv: float, cac: float) -> LTVCACRatioResult:
    """Calculate LTV:CAC Ratio.

    Formula: LTV:CAC Ratio = LTV / CAC
    """
    if cac <= 0:
        raise ValueError("CAC must be positive")

    ratio = ltv / cac

    # Health assessment based on industry benchmarks
    if ratio < 1:
        health = MetricHealth.CRITICAL
        notes = "Critical: LTV < CAC. Losing money on each customer."
    elif ratio < 3:
        health = MetricHealth.WARNING
        notes = "Warning: LTV:CAC < 3:1. Marginally viable."
    elif ratio <= 5:
        health = MetricHealth.GOOD
        notes = "Good: LTV:CAC 3:1 to 5:1. Healthy unit economics."
    elif ratio <= 8:
        health = MetricHealth.EXCELLENT
        notes = "Excellent: LTV:CAC 5:1 to 8:1. Very efficient."
    else:
        health = MetricHealth.WARNING
        notes = "Very high ratio (>8:1). May indicate under-investment in growth."

    return LTVCACRatioResult(
        ratio=ratio,
        ltv=ltv,
        cac=cac,
        health_status=health,
        benchmark_notes=notes
    )
```

#### Reporting Cadence

| Cadence | Report Type | Segments |
|---------|-------------|----------|
| Monthly | LTV:CAC tracking | Overall |
| Quarterly | Segmented analysis | By channel, segment, cohort |
| Annual | Strategic review | Trend analysis |

#### Benchmark Ranges

| Ratio | Health Status | Interpretation |
|-------|---------------|----------------|
| < 1:1 | **Critical** | Losing money on each customer |
| 1:1 - 3:1 | **Warning** | Marginally viable, needs improvement |
| 3:1 - 5:1 | **Good** | Healthy unit economics (target range) |
| 5:1 - 8:1 | **Excellent** | Very efficient, strong growth potential |
| > 8:1 | **Warning** | May be under-investing in growth |

---

### CAC Payback Period

#### Definition
CAC Payback Period measures the number of months required to recover the cost of acquiring a customer through their gross profit contribution. It indicates how quickly a company can reinvest in growth.

#### Calculation Formula

```
CAC Payback Period (months) = CAC / (ARPU × Gross Margin %)
```

Or equivalently:
```
CAC Payback Period = CAC / Monthly Gross Profit per Customer
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `cac` | number | Calculated | Customer Acquisition Cost |
| `arpu` | number | Billing | Average Revenue Per User (monthly) |
| `gross_margin_percent` | number | Financial system | Gross margin % |

#### Instrumentation Guide

**Python Implementation (from `scripts/unit_economics.py`):**
```python
def calculate_cac_payback(data: CACPaybackInput) -> CACPaybackResult:
    """Calculate CAC Payback Period.

    Formula: CAC Payback Period = CAC / (ARPU × Gross Margin %)
    """
    gross_margin_decimal = data.gross_margin_percent / 100
    monthly_gross_profit = data.arpu * gross_margin_decimal

    payback_months = data.cac / monthly_gross_profit

    # Health assessment
    if payback_months < 6:
        health = MetricHealth.EXCELLENT
        notes = "Excellent: Payback < 6 months. Enables rapid scaling."
    elif payback_months <= 12:
        health = MetricHealth.GOOD
        notes = "Good: Payback 6-12 months. Acceptable for most SaaS."
    elif payback_months <= 18:
        health = MetricHealth.WARNING
        notes = "Warning: Payback 12-18 months. Long payback limits growth."
    else:
        health = MetricHealth.CRITICAL
        notes = "Critical: Payback > 18 months. Too long to scale profitably."

    return CACPaybackResult(
        payback_months=payback_months,
        cac=data.cac,
        monthly_gross_profit=monthly_gross_profit,
        health_status=health
    )
```

#### Reporting Cadence

| Cadence | Report Type | Segmentation |
|---------|-------------|--------------|
| Monthly | Payback tracking | Overall |
| Quarterly | Segmented payback | By channel, segment |
| Annual | Strategic analysis | Trend, improvement initiatives |

#### Benchmark Ranges

| Payback Period | Health Status | Interpretation |
|----------------|---------------|----------------|
| < 6 months | **Excellent** | Very efficient, enables rapid scaling |
| 6-12 months | **Good** | Acceptable for most SaaS businesses |
| 12-18 months | **Warning** | Long payback limits growth velocity |
| > 18 months | **Critical** | Too long to scale profitably |

---

### Magic Number

#### Definition
The Magic Number measures sales efficiency by comparing the net new ARR generated to the sales and marketing investment made. It indicates how efficiently the go-to-market machine converts investment into growth.

#### Calculation Formula

```
Magic Number = Net New ARR / Prior Period Sales & Marketing Spend
```

**Annualized Magic Number (for quarterly data) — the form product-finance computes:**
```
Annualized Magic Number = (Quarterly Net New ARR × 4) / Prior-Quarter S&M Spend
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `quarterly_net_new_arr` | number | Revenue data | Net new ARR added in the most recent quarter |
| `prior_quarter_sm_spend` | number | Financial system | Sales & Marketing spend in the PRIOR quarter |

#### Instrumentation Guide

**Python Implementation (from `scripts/unit_economics.py`):**
```python
def calculate_magic_number(data: MagicNumberInput) -> MagicNumberResult:
    """Calculate Magic Number (Sales Efficiency).

    Formula: (Quarterly Net New ARR × 4) / Prior-Quarter S&M Spend

    Delegates to the canonical scripts.utils.magic_number.calculate_magic_number
    helper (single source of truth) and adapts its MagicNumberOutcome.
    """
    outcome = _canonical_magic_number(
        data.quarterly_net_new_arr,
        data.prior_quarter_sm_spend,
    )
    return MagicNumberResult(
        magic_number=outcome.magic_number,
        quarterly_net_new_arr=data.quarterly_net_new_arr,
        prior_quarter_sm_spend=data.prior_quarter_sm_spend,
        efficiency_interpretation=f"Magic Number: {outcome.magic_number:.2f}",
        health_status=outcome.health,
        benchmark_notes=outcome.interpretation,
    )
```

#### Reporting Cadence

| Cadence | Report Type | Context |
|---------|-------------|---------|
| Quarterly | Magic Number report | With S&M spend breakdown |
| Annual | Magic Number trend | Year-over-year comparison |

#### Benchmark Ranges

| Magic Number | Health Status | Interpretation |
|--------------|---------------|----------------|
| < 0 | **Critical** | ARR declining, urgent intervention needed |
| 0-0.5 | **Critical** | Very inefficient, losing money on growth |
| 0.5-0.75 | **Warning** | Below average efficiency |
| 0.75-1.0 | **Good** | Average efficiency, sustainable growth |
| > 1.0 | **Excellent** | Highly efficient, strong growth engine |

---

## Retention Metrics

### NRR (Net Revenue Retention)

#### Definition
Net Revenue Retention (NRR) measures the percentage of recurring revenue retained from existing customers over a period, including the effects of expansion, contraction, and churn. It is the single best indicator of product-market fit and customer value.

#### Calculation Formula

```
NRR = ((Starting ARR + Expansion - Contraction - Churn) / Starting ARR) × 100
```

Or:
```
NRR = (Ending ARR from Existing Customers / Starting ARR) × 100
```

**Components:**
- **Starting ARR**: ARR at the beginning of the period
- **Expansion ARR**: Upsells, cross-sells, seat expansion
- **Contraction ARR**: Downgrades (customer retained but paying less)
- **Churned ARR**: Revenue from cancelled customers

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `starting_arr` | number | Revenue data | ARR at period start |
| `expansion_arr` | number | Billing | ARR from expansions |
| `contraction_arr` | number | Billing | ARR from contractions |
| `churned_arr` | number | Billing | ARR from churns |

#### Instrumentation Guide

**Python Implementation (from `scripts/utils/calculators.py`):**
```python
def calculate_net_revenue_retention(
    starting_arr: float,
    expansion_arr: float,
    contraction_arr: float,
    churned_arr: float,
    decimal_places: int = 2,
) -> float:
    """Calculate Net Revenue Retention (NRR) percentage.

    Formula: ((Starting ARR + Expansion - Contraction - Churn) / Starting ARR) × 100
    """
    if starting_arr <= 0:
        raise ValueError("Starting ARR must be positive")

    ending_arr = starting_arr + expansion_arr - contraction_arr - churned_arr
    nrr = (ending_arr / starting_arr) * 100
    return round(nrr, decimal_places)
```

**Cohort NRR Tracking:**
```python
def track_cohort_nrr(cohort_month):
    """Track NRR by customer cohort."""
    cohort = get_cohort(cohort_month)

    track_event("cohort_nrr_update", {
        "cohort_month": cohort_month.isoformat(),
        "starting_arr": cohort.starting_arr,
        "current_arr": cohort.current_arr,
        "expansion_arr": cohort.expansion_arr,
        "contraction_arr": cohort.contraction_arr,
        "churned_arr": cohort.churned_arr,
        "nrr_percent": (cohort.current_arr / cohort.starting_arr) * 100,
        "months_since_acquisition": cohort.months_active
    })
```

#### Reporting Cadence

| Cadence | Report Type | Segmentation |
|---------|-------------|--------------|
| Monthly | NRR tracking | Overall |
| Quarterly | NRR analysis | By segment, cohort |
| Annual | NRR deep-dive | Strategic planning |

#### Benchmark Ranges

| NRR Range | Health Status | Interpretation |
|-----------|---------------|----------------|
| < 90% | **Critical** | Net revenue declining, urgent action needed |
| 90-100% | **Warning** | Revenue flat, growth must come from new customers |
| 100-110% | **Good** | Healthy expansion offsetting churn |
| 110-130% | **Excellent** | Strong expansion revenue |
| > 130% | **Best-in-class** | Elite NRR (Snowflake, Twilio levels) |

**Segment Benchmarks:**
| Segment | Median NRR | Top Quartile |
|---------|------------|--------------|
| SMB | 90-100% | 105%+ |
| Mid-Market | 100-110% | 115%+ |
| Enterprise | 110-120% | 130%+ |

---

### GRR (Gross Revenue Retention)

#### Definition
Gross Revenue Retention (GRR) measures the percentage of recurring revenue retained from existing customers, excluding expansion. It isolates the effects of churn and contraction.

#### Calculation Formula

```
GRR = ((Starting ARR - Contraction - Churn) / Starting ARR) × 100
```

Or:
```
GRR = NRR - Expansion Rate
```

**Note:** GRR cannot exceed 100% since it excludes expansion.

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `starting_arr` | number | Revenue data | ARR at period start |
| `contraction_arr` | number | Billing | ARR from contractions |
| `churned_arr` | number | Billing | ARR from churns |

#### Instrumentation Guide

```python
def calculate_gross_revenue_retention(
    starting_arr: float,
    contraction_arr: float,
    churned_arr: float,
) -> float:
    """Calculate Gross Revenue Retention (GRR).

    Formula: ((Starting ARR - Contraction - Churn) / Starting ARR) × 100
    GRR is capped at 100% (no expansion included)
    """
    if starting_arr <= 0:
        raise ValueError("Starting ARR must be positive")

    ending_arr = starting_arr - contraction_arr - churned_arr
    grr = (ending_arr / starting_arr) * 100
    return min(100.0, round(grr, 2))  # Cap at 100%
```

#### Reporting Cadence

| Cadence | Report Type | Analysis |
|---------|-------------|----------|
| Monthly | GRR trend | Overall |
| Quarterly | GRR analysis | By segment, reason |
| Annual | GRR deep-dive | Churn root cause |

#### Benchmark Ranges

| GRR Range | Health Status | Interpretation |
|-----------|---------------|----------------|
| < 80% | **Critical** | High churn, product-market fit issues |
| 80-90% | **Warning** | Moderate churn, improvement needed |
| 90-95% | **Good** | Healthy retention |
| 95-100% | **Excellent** | Very low churn |

---

### Logo Retention

#### Definition
Logo Retention (also called Customer Retention Rate) measures the percentage of customers retained over a period, regardless of their revenue contribution. It tracks customer count rather than revenue.

#### Calculation Formula

```
Logo Retention = ((Starting Customers - Churned Customers) / Starting Customers) × 100
```

Or:
```
Logo Retention = (Ending Customers from Starting Cohort / Starting Customers) × 100
```

**Logo Churn Rate (inverse):**
```
Logo Churn Rate = 100% - Logo Retention
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `starting_customers` | integer | CRM | Customers at period start |
| `churned_customers` | integer | CRM | Customers who cancelled |

#### Instrumentation Guide

```python
def calculate_logo_retention(
    starting_customers: int,
    churned_customers: int,
) -> dict:
    """Calculate logo retention metrics."""

    ending_customers = starting_customers - churned_customers
    retention_rate = (ending_customers / starting_customers) * 100
    churn_rate = 100 - retention_rate

    return {
        "starting_customers": starting_customers,
        "churned_customers": churned_customers,
        "ending_customers": ending_customers,
        "logo_retention_rate": round(retention_rate, 2),
        "logo_churn_rate": round(churn_rate, 2)
    }
```

#### Reporting Cadence

| Cadence | Report Type | Segmentation |
|---------|-------------|--------------|
| Monthly | Logo retention tracking | Overall |
| Quarterly | Cohort retention | By cohort, segment |
| Annual | Retention deep-dive | Strategic analysis |

#### Benchmark Ranges

| Retention Rate | Health Status | Interpretation |
|----------------|---------------|----------------|
| < 85% | **Critical** | Very high churn |
| 85-90% | **Warning** | High churn |
| 90-95% | **Good** | Healthy retention |
| > 95% | **Excellent** | Very sticky product |

---

### Churn Rate

#### Definition
Churn Rate measures the percentage of customers or revenue lost over a specific period. It can be calculated as logo churn (customer count) or revenue churn (ARR/MRR lost).

#### Calculation Formula

**Monthly Logo Churn Rate:**
```
Monthly Logo Churn = (Churned Customers / Starting Customers) × 100
```

**Monthly Revenue Churn Rate:**
```
Monthly Revenue Churn = (Churned MRR / Starting MRR) × 100
```

**Annual Churn Rate (from monthly):**
```
Annual Churn = 1 - (1 - Monthly Churn)^12
```

**Gross Churn vs. Net Churn:**
- **Gross Churn**: Total revenue lost (churn + contraction)
- **Net Churn**: Gross churn minus expansion (can be negative if expansion > churn)

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `starting_mrr` | number | Billing | MRR at period start |
| `churned_mrr` | number | Billing | MRR lost to cancellations |
| `starting_customers` | integer | CRM | Customer count at start |
| `churned_customers` | integer | CRM | Customers who cancelled |
| `churn_reasons` | array | CRM/Support | Reasons for cancellation |

#### Instrumentation Guide

**Churn Event Tracking:**
```python
# Event: subscription_cancelled
{
    "event_name": "subscription_cancelled",
    "customer_id": "cust_12345",
    "subscription_id": "sub_67890",
    "churned_mrr": 199.00,
    "churned_arr": 2388.00,
    "cancellation_reason": "switched_competitor",
    "cancellation_category": "voluntary",  # voluntary, involuntary, other
    "subscription_lifetime_days": 365,
    "last_login_days_ago": 45,
    "support_tickets_last_90_days": 3,
    "nps_score": 6,
    "timestamp": "2026-01-15T14:30:00Z"
}
```

**Churn Analysis Query:**
```sql
SELECT
    DATE_TRUNC('month', cancelled_at) as month,
    COUNT(*) as churned_customers,
    SUM(mrr) as churned_mrr,
    cancellation_reason,
    AVG(subscription_lifetime_days) as avg_lifetime
FROM subscriptions
WHERE status = 'cancelled'
GROUP BY 1, 4
ORDER BY 1 DESC;
```

#### Reporting Cadence

| Cadence | Report Type | Analysis |
|---------|-------------|----------|
| Weekly | Churn alerts | Early warning |
| Monthly | Churn analysis | Trend, reasons |
| Quarterly | Churn deep-dive | Cohort, root cause |

#### Benchmark Ranges

**Monthly Churn Rates:**
| Segment | Good | Excellent | Warning |
|---------|------|-----------|---------|
| SMB B2C | 5-8% | < 5% | > 10% |
| SMB B2B | 3-5% | < 3% | > 7% |
| Mid-Market | 1-2% | < 1% | > 3% |
| Enterprise | 0.5-1% | < 0.5% | > 2% |

**Annual Churn Rates (equivalent):**
| Segment | Good | Excellent | Warning |
|---------|------|-----------|---------|
| SMB B2C | 45-65% | < 45% | > 75% |
| SMB B2B | 30-45% | < 30% | > 60% |
| Mid-Market | 10-20% | < 10% | > 30% |
| Enterprise | 5-10% | < 5% | > 20% |

---

### Expansion Revenue

#### Definition
Expansion Revenue measures the additional revenue generated from existing customers through upsells, cross-sells, seat expansion, or usage increases. It is a key component of NRR.

#### Calculation Formula

```
Expansion Rate = (Expansion ARR / Starting ARR) × 100
```

**Expansion ARR Components:**
- **Upsells**: Customers moving to higher-priced plans
- **Cross-sells**: Customers purchasing additional products
- **Seat Expansion**: More users added to existing subscriptions
- **Usage Growth**: Increased usage on consumption-based pricing

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `expansion_arr` | number | Billing | Total expansion revenue |
| `upsell_arr` | number | Billing | Revenue from plan upgrades |
| `cross_sell_arr` | number | Billing | Revenue from new products |
| `seat_expansion_arr` | number | Billing | Revenue from added seats |
| `starting_arr` | number | Billing | Beginning ARR for calculation |

#### Instrumentation Guide

**Expansion Event Tracking:**
```python
# Event: subscription_upgraded
{
    "event_name": "subscription_upgraded",
    "customer_id": "cust_12345",
    "subscription_id": "sub_67890",
    "expansion_type": "upsell",  # upsell, cross_sell, seat_expansion, usage
    "previous_plan": "starter",
    "new_plan": "professional",
    "previous_mrr": 49.00,
    "new_mrr": 199.00,
    "expansion_mrr": 150.00,
    "expansion_arr": 1800.00,
    "trigger": "user_initiated",  # user_initiated, sales_led, auto_upgrade
    "timestamp": "2026-01-20T10:00:00Z"
}
```

#### Reporting Cadence

| Cadence | Report Type | Breakdown |
|---------|-------------|-----------|
| Monthly | Expansion tracking | By type |
| Quarterly | Expansion analysis | By segment, cohort |
| Annual | Expansion strategy | Strategic planning |

#### Benchmark Ranges

| Expansion Rate | Health Status | Interpretation |
|----------------|---------------|----------------|
| < 5% | **Warning** | Low expansion, limited land-and-expand |
| 5-15% | **Good** | Healthy expansion motion |
| 15-30% | **Excellent** | Strong upsell/cross-sell |
| > 30% | **Best-in-class** | Exceptional expansion (usage-based models) |

---

## AI-Specific Metrics

### AI Cost per Interaction

#### Definition
AI Cost per Interaction measures the average cost of a single AI/LLM API call or interaction. It is critical for understanding and optimizing AI unit economics.

#### Calculation Formula

```
AI Cost per Interaction = Total AI API Costs / Total AI Interactions
```

**Detailed Calculation:**
```
AI Cost per Interaction = (Input Token Cost + Output Token Cost + Infrastructure Cost) / Interactions
```

Where:
```
Token Cost = (Input Tokens × Price per 1K Input) + (Output Tokens × Price per 1K Output)
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `total_ai_cost` | number | Provider billing | Total AI API costs |
| `ai_interactions` | integer | Application logs | Number of API calls |
| `input_tokens` | integer | API response | Input token count |
| `output_tokens` | integer | API response | Output token count |
| `model` | string | API request | Model identifier |
| `provider` | string | Configuration | AI provider (Anthropic, OpenAI, etc.) |

#### Instrumentation Guide

**Python Implementation (from `scripts/ai_roi_calculator.py`):**
```python
def calculate_ai_costs(data: AICostInput) -> AICostResult:
    """Calculate AI cost metrics."""

    # Calculate cost per interaction
    cost_per_interaction = data.total_ai_cost / data.ai_interactions

    # Calculate cost per user per month
    cost_per_user_per_month = data.total_ai_cost / data.active_users / data.period_months

    # Calculate AI cost as percentage of revenue
    ai_cost_percentage = (data.total_ai_cost / data.total_revenue) * 100

    return AICostResult(
        cost_per_interaction=cost_per_interaction,
        cost_per_user_per_month=cost_per_user_per_month,
        ai_cost_percentage_of_revenue=ai_cost_percentage,
        total_ai_cost=data.total_ai_cost,
        # ... additional metrics
    )
```

**AI Interaction Event Tracking:**
```python
# Event: ai_request_completed
{
    "event_name": "ai_request_completed",
    "request_id": "req_abc123",
    "user_id": "user_456",
    "customer_id": "cust_789",
    "feature": "code_assistant",
    "model": "claude-sonnet-4-20250514",
    "provider": "anthropic",
    "tokens_input": 1500,
    "tokens_output": 800,
    "tokens_total": 2300,
    "cost_usd": 0.0138,
    "latency_ms": 1250,
    "cache_hit": false,
    "timestamp": "2026-01-23T14:30:00Z"
}
```

**Database Schema:**
```sql
CREATE TABLE ai_usage_events (
    id BIGSERIAL PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    feature VARCHAR(255),
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_cost_analysis ON ai_usage_events(customer_id, created_at, cost_usd);
```

#### Reporting Cadence

| Cadence | Report Type | Breakdown |
|---------|-------------|-----------|
| Daily | Cost monitoring | By model, feature |
| Weekly | Cost trend | By customer segment |
| Monthly | AI cost analysis | Full breakdown, optimization |

#### Benchmark Ranges

| Model Tier | Good | Excellent | Warning |
|------------|------|-----------|---------|
| Large (GPT-4, Claude Opus) | $0.05-$0.15 | < $0.05 | > $0.20 |
| Medium (GPT-3.5, Claude Sonnet) | $0.01-$0.03 | < $0.01 | > $0.05 |
| Small (Haiku, lightweight) | $0.001-$0.005 | < $0.001 | > $0.01 |

---

### AI Cost Percentage

#### Definition
AI Cost Percentage measures AI/LLM costs as a percentage of total revenue. It indicates how much of revenue is consumed by AI infrastructure costs.

#### Calculation Formula

```
AI Cost % = (Total AI Costs / Total Revenue) × 100
```

**For margin analysis:**
```
AI-Adjusted Gross Margin = ((Revenue - COGS - AI Costs) / Revenue) × 100
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `total_ai_costs` | number | Provider billing | All AI-related costs |
| `total_revenue` | number | Financial system | Total revenue |
| `ai_infrastructure_costs` | number | Cloud billing | AI hosting/infrastructure |

#### Instrumentation Guide

```python
def calculate_ai_cost_percentage(ai_costs: float, revenue: float) -> dict:
    """Calculate AI cost as percentage of revenue."""

    ai_cost_percent = (ai_costs / revenue) * 100

    # Health assessment
    if ai_cost_percent < 5:
        health = "excellent"
        notes = "AI costs < 5% of revenue. Very efficient."
    elif ai_cost_percent < 10:
        health = "good"
        notes = "AI costs 5-10% of revenue. Healthy range."
    elif ai_cost_percent < 20:
        health = "warning"
        notes = "AI costs 10-20% of revenue. Monitor closely."
    else:
        health = "critical"
        notes = "AI costs > 20% of revenue. Urgent optimization needed."

    return {
        "ai_cost_percent": round(ai_cost_percent, 2),
        "health_status": health,
        "notes": notes
    }
```

#### Reporting Cadence

| Cadence | Report Type | Context |
|---------|-------------|---------|
| Weekly | AI cost monitoring | Operational |
| Monthly | AI cost analysis | P&L impact |
| Quarterly | AI economics review | Strategic |

#### Benchmark Ranges

| AI Cost % | Health Status | Interpretation |
|-----------|---------------|----------------|
| < 5% | **Excellent** | Very efficient AI implementation |
| 5-10% | **Good** | Healthy range for AI-powered products |
| 10-20% | **Warning** | Monitor closely, optimize where possible |
| > 20% | **Critical** | Urgent optimization or pricing adjustment needed |

---

### AI ROI

#### Definition
AI ROI measures the return on investment for AI capabilities by comparing the value generated by AI to its costs. It justifies AI investments and informs feature prioritization.

#### Calculation Formula

```
AI ROI = ((AI Value - AI Costs) / AI Costs) × 100
```

Or as a ratio:
```
AI ROI Ratio = AI Value / AI Costs
```

**AI Value Components:**
- AI-enabled revenue (premium features)
- Productivity savings (time saved × cost per hour)
- Retention impact (churn reduction value)
- Expansion revenue from AI features
- Time-to-value acceleration

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `total_ai_costs` | number | Provider billing | All AI costs |
| `ai_enabled_revenue` | number | Billing | Revenue from AI features |
| `productivity_savings` | number | Calculated | Value of time saved |
| `retention_value` | number | Calculated | Value of reduced churn |
| `expansion_value` | number | Billing | Expansion from AI adoption |

#### Instrumentation Guide

**Python Implementation (from `scripts/ai_roi_calculator.py`):**
```python
def calculate_ai_roi(data: AIROIInput) -> AIROIResult:
    """Calculate comprehensive AI ROI.

    Formula: AI ROI = (AI Value - AI Costs) / AI Costs × 100
    """
    # Calculate costs and value
    cost_result = calculate_ai_costs(data.cost_data)
    value_result = calculate_ai_value(data.value_data)

    # Annualize for fair comparison
    annualized_value = value_result.total_ai_value * (12 / data.cost_data.period_months)
    annualized_cost = cost_result.annualized_ai_cost

    # Calculate ROI
    net_ai_value = annualized_value - annualized_cost
    ai_roi = (net_ai_value / annualized_cost) * 100
    ai_roi_ratio = annualized_value / annualized_cost

    # Calculate payback period
    if annualized_value > annualized_cost:
        monthly_net = (annualized_value - annualized_cost) / 12
        payback_period = annualized_cost / monthly_net
    else:
        payback_period = None

    return AIROIResult(
        ai_roi=ai_roi,
        ai_roi_ratio=ai_roi_ratio,
        net_ai_value=net_ai_value,
        payback_period=payback_period,
        cost_result=cost_result,
        value_result=value_result
    )
```

#### Reporting Cadence

| Cadence | Report Type | Audience |
|---------|-------------|----------|
| Monthly | AI ROI tracking | Product team |
| Quarterly | AI ROI analysis | CFO, leadership |
| Annual | AI investment review | Board |

#### Benchmark Ranges

| AI ROI | Health Status | Interpretation |
|--------|---------------|----------------|
| < 0% | **Critical** | Losing money on AI. Review strategy. |
| 0-100% | **Warning** | Marginal returns. Optimize or justify. |
| 100-200% | **Good** | Positive ROI. Healthy investment. |
| > 200% | **Excellent** | Strong ROI. Consider expanding. |

---

### AI-Enabled Revenue

#### Definition
AI-Enabled Revenue measures the revenue directly attributable to AI-powered features. It includes premium pricing for AI capabilities, revenue from AI-only products, and the AI contribution to overall product value.

#### Calculation Formula

```
AI-Enabled Revenue = Revenue from AI Features + Premium Pricing Uplift + AI Expansion Revenue
```

**AI Revenue Percentage:**
```
AI Revenue % = (AI-Enabled Revenue / Total Revenue) × 100
```

#### Data Requirements

| Data Point | Type | Source | Description |
|------------|------|--------|-------------|
| `ai_feature_revenue` | number | Billing | Revenue from AI-specific features |
| `premium_pricing_revenue` | number | Billing | Price premium for AI capabilities |
| `non_ai_revenue` | number | Billing | Revenue from non-AI features |
| `ai_expansion_revenue` | number | Billing | Expansion driven by AI adoption |

#### Instrumentation Guide

**Revenue Attribution Tracking:**
```python
# Track AI feature usage for revenue attribution
def track_ai_feature_usage(user_id, feature_id, interaction_data):
    track_event("ai_feature_used", {
        "user_id": user_id,
        "customer_id": get_customer_id(user_id),
        "feature_id": feature_id,
        "feature_name": get_feature_name(feature_id),
        "subscription_plan": get_user_plan(user_id),
        "is_ai_enabled_plan": is_ai_plan(user_id),
        "mrr_contribution": calculate_feature_mrr_contribution(user_id, feature_id),
        "timestamp": datetime.utcnow().isoformat()
    })

# Calculate AI revenue attribution
def calculate_ai_revenue_attribution(period):
    # Direct AI feature revenue
    ai_plans_revenue = sum_revenue_from_ai_plans(period)

    # Premium pricing uplift
    baseline_price = get_non_ai_equivalent_price()
    ai_price = get_ai_enabled_price()
    premium_uplift = (ai_price - baseline_price) * ai_subscriber_count(period)

    # Expansion from AI adoption
    ai_expansion = sum_expansions_to_ai_plans(period)

    return {
        "ai_plans_revenue": ai_plans_revenue,
        "premium_pricing_uplift": premium_uplift,
        "ai_expansion_revenue": ai_expansion,
        "total_ai_enabled_revenue": ai_plans_revenue + premium_uplift + ai_expansion
    }
```

#### Reporting Cadence

| Cadence | Report Type | Breakdown |
|---------|-------------|-----------|
| Monthly | AI revenue tracking | By feature, plan |
| Quarterly | AI revenue analysis | Attribution, trends |
| Annual | AI strategy review | Investment vs. returns |

#### Benchmark Ranges

| AI Revenue % | Interpretation |
|--------------|----------------|
| < 10% | AI as add-on feature |
| 10-30% | Significant AI component |
| 30-50% | AI-first product |
| > 50% | AI-native business |

---

## Appendix A: Formula Quick Reference

| Metric | Formula |
|--------|---------|
| ARR | MRR × 12 |
| Net New ARR | New ARR + Expansion - Contraction - Churn |
| Revenue Growth | ((Current - Prior) / Prior) × 100 |
| Gross Margin | ((Revenue - COGS) / Revenue) × 100 |
| EBITDA Margin | (EBITDA / Revenue) × 100 |
| Rule of 40 | Growth Rate % + EBITDA Margin % |
| CAC | (Sales + Marketing Costs) / New Customers |
| LTV | ARPU × Gross Margin % / Churn Rate |
| LTV:CAC | LTV / CAC |
| CAC Payback | CAC / (ARPU × Gross Margin %) |
| Magic Number | (Quarterly Net New ARR × 4) / Prior-Quarter S&M Spend |
| NRR | ((Start + Expansion - Contraction - Churn) / Start) × 100 |
| GRR | ((Start - Contraction - Churn) / Start) × 100 |
| Logo Retention | ((Start Customers - Churned) / Start) × 100 |
| Churn Rate | (Churned / Starting) × 100 |
| AI Cost per Interaction | Total AI Cost / AI Interactions |
| AI Cost % | (AI Costs / Revenue) × 100 |
| AI ROI | ((AI Value - AI Costs) / AI Costs) × 100 |

---

## Appendix B: Data Sources Matrix

| Data Category | Common Sources | Integration Methods |
|---------------|----------------|---------------------|
| Revenue/Billing | Stripe, Chargebee, Recurly | Webhooks, API |
| CRM | Salesforce, HubSpot | API, CDC |
| Financial | NetSuite, QuickBooks, Xero | API, exports |
| Product Analytics | Amplitude, Mixpanel, Segment | Event streams |
| AI Costs | Anthropic, OpenAI, AWS Bedrock | API, billing export |
| Infrastructure | AWS, GCP, Azure | Cost Explorer APIs |
| Support | Zendesk, Intercom | API |

---

## Appendix C: Reporting Calendar

| Report | Frequency | Timing | Audience |
|--------|-----------|--------|----------|
| Revenue Dashboard | Daily | Real-time | Revenue ops |
| MRR/ARR Report | Weekly | Monday AM | Leadership |
| Unit Economics | Monthly | Month-end +3 | Finance, product |
| Board Package | Quarterly | Quarter-end +15 | Board |
| Investor Update | Quarterly | Quarter-end +30 | Investors |
| Annual Review | Annual | Year-end +45 | All stakeholders |

---

*This document is part of the Product Finance Plugin documentation. For implementation details, refer to the Python scripts in `/scripts/`.*
