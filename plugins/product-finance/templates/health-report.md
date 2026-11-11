# Financial Health Report

**Company:** {{COMPANY_NAME}}
**Assessment Date:** {{ASSESSMENT_DATE}}
**Company Stage:** {{COMPANY_STAGE}}
**Report Period:** {{REPORT_PERIOD}}
**Assessment Purpose:** {{ASSESSMENT_PURPOSE}}

---

## Executive Summary

### Overall Health Score: {{HEALTH_SCORE}}/100 - {{HEALTH_STATUS}}

{{EXECUTIVE_SUMMARY}}

### Key Highlights

{{#HIGHLIGHTS}}
- {{HIGHLIGHT_TEXT}}
{{/HIGHLIGHTS}}

### Critical Alerts

{{#CRITICAL_ALERTS}}
- **{{ALERT_CATEGORY}}:** {{ALERT_MESSAGE}}
{{/CRITICAL_ALERTS}}

{{#NO_CRITICAL_ALERTS}}
No critical alerts at this time.
{{/NO_CRITICAL_ALERTS}}

---

## 1. Rule of 40 Assessment

<!-- the markdown of rule_of_40.py from ## Key Metrics on, headings demoted -->
{{RULE_OF_40_SECTION}}

---

## 2. Growth Metrics

### Annual Recurring Revenue (ARR)

| Metric | Value | Status |
|--------|-------|--------|
| Current ARR | {{ARR_CURRENT}} | {{ARR_STATUS}} |
| Prior Year ARR | {{ARR_PRIOR_YEAR}} | - |
| YoY Growth Rate | {{ARR_GROWTH_RATE}}% | {{GROWTH_STATUS}} |
| Prior Quarter ARR | {{ARR_PRIOR_QUARTER}} | - |
| QoQ Growth Rate | {{ARR_QOQ_GROWTH}}% | {{QOQ_STATUS}} |

### Monthly Recurring Revenue (MRR)

| Metric | Value |
|--------|-------|
| Current MRR | {{MRR_CURRENT}} |
| MoM Growth Rate | {{MRR_GROWTH_RATE}}% |

### Net New ARR Breakdown

| Component | Amount | % of Total |
|-----------|--------|------------|
| New ARR (New Customers) | {{NEW_ARR}} | {{NEW_ARR_PCT}}% |
| Expansion ARR | {{EXPANSION_ARR}} | {{EXPANSION_ARR_PCT}}% |
| Churned ARR | ({{CHURNED_ARR}}) | -{{CHURNED_ARR_PCT}}% |
| **Net New ARR** | **{{NET_NEW_ARR}}** | **100%** |

### ARR Composition

```
ARR Composition Analysis
========================

Total ARR: {{ARR_CURRENT}}

By Source:
  [{{NEW_ARR_BAR}}] New Customers: {{NEW_ARR_PCT}}%
  [{{EXPANSION_ARR_BAR}}] Expansion: {{EXPANSION_ARR_PCT}}%
  [{{RETAINED_ARR_BAR}}] Retained: {{RETAINED_ARR_PCT}}%
  [{{CHURNED_ARR_BAR}}] Churned: -{{CHURNED_ARR_PCT}}%
```

### Growth Trajectory

**Current Trajectory:** {{GROWTH_TRAJECTORY}}

**Assessment:** {{GROWTH_ASSESSMENT}}

---

## 3. Unit Economics

### Customer Acquisition Cost (CAC)

| Metric | Value | Status |
|--------|-------|--------|
| Blended CAC | {{CAC}} | {{CAC_STATUS}} |
| Annual S&M Spend | {{SM_SPEND_ANNUAL}} | - |
| New Customers (12mo) | {{NEW_CUSTOMERS}} | - |

**Calculation:**
```
CAC = Total S&M Spend / New Customers Acquired
CAC = {{SM_SPEND_ANNUAL}} / {{NEW_CUSTOMERS}} = {{CAC}}
```

### Lifetime Value (LTV)

| Metric | Value | Status |
|--------|-------|--------|
| LTV | {{LTV}} | {{LTV_STATUS}} |
| Average Revenue Per Customer (ARPC) | {{ARPC}} | - |
| Gross Margin | {{GROSS_MARGIN}}% | {{GROSS_MARGIN_STATUS}} |
| Monthly Churn Rate | {{MONTHLY_CHURN_RATE}}% | {{CHURN_STATUS}} |
| Average Customer Lifetime | {{CUSTOMER_LIFETIME}} months | - |

**Calculation:**
```
LTV = (ARPC x Gross Margin %) / Monthly Churn Rate
LTV = ({{ARPC}} x {{GROSS_MARGIN}}%) / {{MONTHLY_CHURN_RATE}}%
LTV = {{LTV}}
```

### LTV:CAC Ratio {{LTV_CAC_INDICATOR}}

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| LTV:CAC Ratio | {{LTV_CAC_RATIO}}x | >= 3.0x | {{LTV_CAC_STATUS}} |

**Interpretation:** {{LTV_CAC_INTERPRETATION}}

**Benchmark Analysis:**

| Range | Status | Your Position |
|-------|--------|---------------|
| > 5:1 | Excellent | {{EXCELLENT_STATUS}} |
| 3-5:1 | Good | {{GOOD_STATUS}} |
| 1-3:1 | Acceptable | {{ACCEPTABLE_STATUS}} |
| < 1:1 | Unhealthy | {{UNHEALTHY_STATUS}} |

### CAC Payback Period {{PAYBACK_INDICATOR}}

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| CAC Payback | {{CAC_PAYBACK_MONTHS}} months | <= 12 months | {{PAYBACK_STATUS}} |

**Calculation:**
```
CAC Payback = CAC / (Monthly ARPC x Gross Margin %)
CAC Payback = {{CAC}} / ({{ARPC_MONTHLY}} x {{GROSS_MARGIN}}%)
CAC Payback = {{CAC_PAYBACK_MONTHS}} months
```

**Assessment:** {{PAYBACK_ASSESSMENT}}

**Benchmark Analysis:**

| Range | Status | Your Position |
|-------|--------|---------------|
| < 6 months | Excellent | {{PAYBACK_EXCELLENT}} |
| 6-12 months | Good | {{PAYBACK_GOOD}} |
| 12-18 months | Acceptable | {{PAYBACK_ACCEPTABLE}} |
| > 18 months | Poor | {{PAYBACK_POOR}} |

### Magic Number (Sales Efficiency) {{MAGIC_NUMBER_INDICATOR}}

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Magic Number | {{MAGIC_NUMBER}} | >= 0.75 | {{MAGIC_NUMBER_STATUS}} |
| Quarterly Net New ARR | {{QUARTERLY_NET_NEW_ARR}} | - | - |
| Prior Quarter S&M Spend | {{PRIOR_QUARTER_SM_SPEND}} | - | - |

**Calculation:**
```
Magic Number = (Quarterly Net New ARR x 4) / Prior Quarter S&M Spend
Magic Number = ({{QUARTERLY_NET_NEW_ARR}} x 4) / {{PRIOR_QUARTER_SM_SPEND}}
Magic Number = {{MAGIC_NUMBER}}
```

**Interpretation:** {{MAGIC_NUMBER_INTERPRETATION}}

**Benchmark Analysis:**

| Range | Status | Recommendation |
|-------|--------|----------------|
| 1.0 or more | Excellent | Invest aggressively in S&M |
| 0.75 up to 1.0 | Good | Scale S&M investment |
| 0.5 up to 0.75 | Acceptable | Optimize before scaling |
| under 0.5 | Poor | Pause growth, fix efficiency |

---

## 4. Retention Metrics

### Net Revenue Retention (NRR) {{NRR_INDICATOR}}

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| NRR | {{NRR}}% | >= 100% | {{NRR_STATUS}} |
| Starting Cohort ARR | {{COHORT_STARTING_ARR}} | - | - |
| Current Cohort ARR | {{COHORT_CURRENT_ARR}} | - | - |

**Calculation:**
```
NRR = (Current Cohort ARR / Starting Cohort ARR) x 100
NRR = ({{COHORT_CURRENT_ARR}} / {{COHORT_STARTING_ARR}}) x 100
NRR = {{NRR}}%
```

**Interpretation:** {{NRR_INTERPRETATION}}

**Benchmark Comparison:**

| Range | Status | Your Position |
|-------|--------|---------------|
| >= 130% | World-Class | {{NRR_WORLD_CLASS}} |
| 120-130% | Excellent | {{NRR_EXCELLENT}} |
| 100-120% | Good | {{NRR_GOOD}} |
| < 100% | Contraction | {{NRR_CONTRACTION}} |

### Gross Revenue Retention (GRR) {{GRR_INDICATOR}}

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| GRR | {{GRR}}% | >= 85% | {{GRR_STATUS}} |
| Retained ARR (excl. expansion) | {{RETAINED_ARR}} | - | - |
| Churned ARR | {{CHURNED_ARR_COHORT}} | - | - |

**Calculation:**
```
GRR = ((Starting ARR - Churned ARR) / Starting ARR) x 100
GRR = (({{COHORT_STARTING_ARR}} - {{CHURNED_ARR_COHORT}}) / {{COHORT_STARTING_ARR}}) x 100
GRR = {{GRR}}%
```

**Interpretation:** {{GRR_INTERPRETATION}}

### Churn Analysis

| Metric | Monthly | Annual |
|--------|---------|--------|
| Revenue Churn Rate | {{MONTHLY_REVENUE_CHURN}}% | {{ANNUAL_REVENUE_CHURN}}% |
| Logo Churn Rate | {{MONTHLY_LOGO_CHURN}}% | {{ANNUAL_LOGO_CHURN}}% |

**Churn Breakdown:**

| Churn Reason | % of Churned Revenue | Trend |
|--------------|---------------------|-------|
{{#CHURN_REASONS}}
| {{REASON}} | {{PERCENTAGE}}% | {{TREND}} |
{{/CHURN_REASONS}}

### Expansion Revenue

| Metric | Value | % of ARR |
|--------|-------|----------|
| Expansion ARR | {{EXPANSION_ARR}} | {{EXPANSION_PCT}}% |
| Upsell Revenue | {{UPSELL_REVENUE}} | {{UPSELL_PCT}}% |
| Cross-sell Revenue | {{CROSS_SELL_REVENUE}} | {{CROSS_SELL_PCT}}% |
| Price Increase Revenue | {{PRICE_INCREASE_REVENUE}} | {{PRICE_INCREASE_PCT}}% |

**Expansion Rate:** {{EXPANSION_RATE}}% of existing customers expanded in last 12 months

### Customer Count Analysis

| Metric | Value | Change |
|--------|-------|--------|
| Starting Customers (12mo ago) | {{STARTING_CUSTOMERS}} | - |
| New Customers | +{{NEW_CUSTOMERS_12MO}} | +{{NEW_CUSTOMERS_PCT}}% |
| Churned Customers | -{{CHURNED_CUSTOMERS}} | -{{CHURNED_CUSTOMERS_PCT}}% |
| Current Customers | {{CURRENT_CUSTOMERS}} | Net +{{NET_CUSTOMER_CHANGE}}% |
| Logo Retention Rate | {{LOGO_RETENTION}}% | {{LOGO_RETENTION_STATUS}} |

---

## 5. Profitability & Efficiency

### Gross Margin

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Gross Margin | {{GROSS_MARGIN}}% | >= 70% | {{GROSS_MARGIN_STATUS}} |
| Annual Revenue | {{ANNUAL_REVENUE}} | - | - |
| Annual COGS | {{ANNUAL_COGS}} | - | - |

**COGS Breakdown:**

| Category | Amount | % of COGS |
|----------|--------|-----------|
| Infrastructure/Hosting | {{COGS_INFRASTRUCTURE}} | {{COGS_INFRA_PCT}}% |
| Support | {{COGS_SUPPORT}} | {{COGS_SUPPORT_PCT}}% |
| Third-party Services | {{COGS_THIRD_PARTY}} | {{COGS_THIRD_PARTY_PCT}}% |
{{#HAS_AI_COSTS}}
| AI/ML Services | {{COGS_AI}} | {{COGS_AI_PCT}}% |
{{/HAS_AI_COSTS}}
| Other | {{COGS_OTHER}} | {{COGS_OTHER_PCT}}% |

### EBITDA

| Metric | Value | Status |
|--------|-------|--------|
| EBITDA | {{EBITDA}} | {{EBITDA_STATUS}} |
| EBITDA Margin | {{EBITDA_MARGIN}}% | {{EBITDA_MARGIN_STATUS}} |

### Operating Expenses

| Category | Amount | % of Revenue |
|----------|--------|--------------|
| Sales & Marketing | {{OPEX_SM}} | {{OPEX_SM_PCT}}% |
| Research & Development | {{OPEX_RD}} | {{OPEX_RD_PCT}}% |
| General & Administrative | {{OPEX_GA}} | {{OPEX_GA_PCT}}% |
| **Total OpEx** | **{{TOTAL_OPEX}}** | **{{TOTAL_OPEX_PCT}}%** |

### Burn Rate & Runway

| Metric | Value | Status |
|--------|-------|--------|
| Monthly Burn Rate | {{MONTHLY_BURN}} | {{BURN_STATUS}} |
| Cash Balance | {{CASH_BALANCE}} | - |
| Runway | {{RUNWAY_MONTHS}} months | {{RUNWAY_STATUS}} |

**Runway Assessment:**

```
Runway Status: {{RUNWAY_STATUS}}
===============

  < 6 months   = CRITICAL   [{{RUNWAY_CRITICAL}}]
  6-12 months  = WARNING    [{{RUNWAY_WARNING}}]
  12-18 months = ADEQUATE   [{{RUNWAY_ADEQUATE}}]
  > 18 months  = HEALTHY    [{{RUNWAY_HEALTHY}}]

Your Runway: {{RUNWAY_MONTHS}} months
```

**Recommendation:** {{RUNWAY_RECOMMENDATION}}

### Efficiency Ratios

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Revenue per Employee | {{REVENUE_PER_EMPLOYEE}} | >= $100K | {{RPE_STATUS}} |
| Burn Multiple | {{BURN_MULTIPLE}} | < 1.5 | {{BURN_MULTIPLE_STATUS}} |
| Sales Efficiency | {{SALES_EFFICIENCY}}% | >= 100% | {{SALES_EFFICIENCY_STATUS}} |

**Burn Multiple Calculation:**
```
Burn Multiple = Net Burn / Net New ARR
Burn Multiple = {{NET_BURN}} / {{NET_NEW_ARR}}
Burn Multiple = {{BURN_MULTIPLE}}

Interpretation:
< 1.0  = Efficient (burning < $1 to generate $1 ARR)
1.0-1.5 = Acceptable
1.5-2.0 = Inefficient
> 2.0  = Very inefficient
```

---

{{#HAS_AI_ECONOMICS}}
## 6. AI Economics

### AI Cost Summary

| Metric | Value | % of COGS |
|--------|-------|-----------|
| Total AI Costs | {{AI_COSTS_TOTAL}} | {{AI_COSTS_PCT}}% |
| AI Cost per User | {{AI_COST_PER_USER}} | - |
| AI Cost per Request | {{AI_COST_PER_REQUEST}} | - |

### AI Cost Breakdown

| Provider/Category | Monthly Cost | % of AI Costs |
|-------------------|--------------|---------------|
{{#AI_COST_BREAKDOWN}}
| {{PROVIDER}} | {{COST}} | {{PERCENTAGE}}% |
{{/AI_COST_BREAKDOWN}}

### AI ROI Analysis

| Metric | Value | Status |
|--------|-------|--------|
| AI-Attributed Revenue | {{AI_ATTRIBUTED_REVENUE}} | {{AI_REVENUE_STATUS}} |
| AI Cost : Revenue Ratio | {{AI_COST_REVENUE_RATIO}} | {{AI_RATIO_STATUS}} |
| AI ROI | {{AI_ROI}}% | {{AI_ROI_STATUS}} |

**Calculation:**
```
AI ROI = ((AI-Attributed Revenue - AI Costs) / AI Costs) x 100
AI ROI = (({{AI_ATTRIBUTED_REVENUE}} - {{AI_COSTS_TOTAL}}) / {{AI_COSTS_TOTAL}}) x 100
AI ROI = {{AI_ROI}}%
```

### AI Cost Trends

| Period | AI Costs | % of Revenue | Cost per User |
|--------|----------|--------------|---------------|
{{#AI_COST_TRENDS}}
| {{PERIOD}} | {{COST}} | {{PCT_REVENUE}}% | {{COST_PER_USER}} |
{{/AI_COST_TRENDS}}

### AI Cost Optimization Opportunities

{{#AI_OPTIMIZATION_OPPORTUNITIES}}
**{{OPPORTUNITY_NUMBER}}. {{OPPORTUNITY_TITLE}}**
- **Current State:** {{CURRENT_STATE}}
- **Recommendation:** {{RECOMMENDATION}}
- **Potential Savings:** {{POTENTIAL_SAVINGS}}
- **Implementation Effort:** {{EFFORT}}

{{/AI_OPTIMIZATION_OPPORTUNITIES}}

### AI Economics Health Indicators

| Indicator | Value | Target | Status |
|-----------|-------|--------|--------|
| AI Costs as % of COGS | {{AI_PCT_COGS}}% | < 30% | {{AI_COGS_STATUS}} |
| AI Costs as % of Revenue | {{AI_PCT_REVENUE}}% | < 10% | {{AI_REVENUE_STATUS}} |
| AI Gross Margin Impact | {{AI_MARGIN_IMPACT}}% | < 5% impact | {{AI_MARGIN_STATUS}} |
| AI Cost Growth Rate | {{AI_COST_GROWTH}}% | < Revenue Growth | {{AI_GROWTH_STATUS}} |

{{/HAS_AI_ECONOMICS}}

---

## {{AI_SECTION_NUMBER}}. Benchmark Comparison

### Stage-Appropriate Benchmarks ({{COMPANY_STAGE}})

| Metric | Your Value | Target | Top 25% | Median | Bottom 25% | Status |
|--------|------------|--------|---------|--------|------------|--------|
| ARR Growth Rate | {{ARR_GROWTH_RATE}}% | {{GROWTH_TARGET}}% | {{GROWTH_TOP_25}}% | {{GROWTH_MEDIAN}}% | {{GROWTH_BOTTOM_25}}% | {{GROWTH_BENCHMARK_STATUS}} |
| Gross Margin | {{GROSS_MARGIN}}% | {{GM_TARGET}}% | {{GM_TOP_25}}% | {{GM_MEDIAN}}% | {{GM_BOTTOM_25}}% | {{GM_BENCHMARK_STATUS}} |
| NRR | {{NRR}}% | {{NRR_TARGET}}% | {{NRR_TOP_25}}% | {{NRR_MEDIAN}}% | {{NRR_BOTTOM_25}}% | {{NRR_BENCHMARK_STATUS}} |
| LTV:CAC Ratio | {{LTV_CAC_RATIO}}x | {{LTV_CAC_TARGET}}x | {{LTV_CAC_TOP_25}}x | {{LTV_CAC_MEDIAN}}x | {{LTV_CAC_BOTTOM_25}}x | {{LTV_CAC_BENCHMARK_STATUS}} |
| CAC Payback | {{CAC_PAYBACK_MONTHS}}mo | {{PAYBACK_TARGET}}mo | {{PAYBACK_TOP_25}}mo | {{PAYBACK_MEDIAN}}mo | {{PAYBACK_BOTTOM_25}}mo | {{PAYBACK_BENCHMARK_STATUS}} |
| Magic Number | {{MAGIC_NUMBER}} | {{MAGIC_TARGET}} | {{MAGIC_TOP_25}} | {{MAGIC_MEDIAN}} | {{MAGIC_BOTTOM_25}} | {{MAGIC_BENCHMARK_STATUS}} |

### Competitive Position Summary

**Strengths (Above Benchmark):**
{{#BENCHMARK_STRENGTHS}}
- {{STRENGTH}}
{{/BENCHMARK_STRENGTHS}}

**At Benchmark:**
{{#BENCHMARK_AT_TARGET}}
- {{METRIC}}
{{/BENCHMARK_AT_TARGET}}

**Below Benchmark:**
{{#BENCHMARK_WEAKNESSES}}
- {{WEAKNESS}}
{{/BENCHMARK_WEAKNESSES}}

---

## {{RECOMMENDATIONS_SECTION_NUMBER}}. Recommendations

### Priority 1: Critical (Immediate Action Required)

{{#PRIORITY_1_RECOMMENDATIONS}}
#### {{REC_NUMBER}}. {{REC_TITLE}}

**Issue:** {{ISSUE}}

**Recommendation:** {{RECOMMENDATION}}

**Impact:** {{IMPACT}}

**Timeline:** {{TIMELINE}}

**Success Metrics:**
{{#SUCCESS_METRICS}}
- {{METRIC}}
{{/SUCCESS_METRICS}}

{{/PRIORITY_1_RECOMMENDATIONS}}

{{#NO_CRITICAL_RECOMMENDATIONS}}
No critical recommendations at this time. Continue monitoring key metrics.
{{/NO_CRITICAL_RECOMMENDATIONS}}

---

### Priority 2: High (Address within 3-6 months)

{{#PRIORITY_2_RECOMMENDATIONS}}
#### {{REC_NUMBER}}. {{REC_TITLE}}

**Issue:** {{ISSUE}}

**Recommendation:** {{RECOMMENDATION}}

**Impact:** {{IMPACT}}

**Timeline:** {{TIMELINE}}

**Action Items:**
{{#ACTION_ITEMS}}
- {{ACTION}}
{{/ACTION_ITEMS}}

{{/PRIORITY_2_RECOMMENDATIONS}}

---

### Priority 3: Medium (Address within 6-12 months)

{{#PRIORITY_3_RECOMMENDATIONS}}
#### {{REC_NUMBER}}. {{REC_TITLE}}

**Issue:** {{ISSUE}}

**Recommendation:** {{RECOMMENDATION}}

**Impact:** {{IMPACT}}

**Timeline:** {{TIMELINE}}

{{/PRIORITY_3_RECOMMENDATIONS}}

---

### Quick Wins (Implement in < 30 days)

| Initiative | Effort | Impact | Owner |
|------------|--------|--------|-------|
{{#QUICK_WINS}}
| {{INITIATIVE}} | {{EFFORT}} | {{IMPACT}} | {{OWNER}} |
{{/QUICK_WINS}}

### Strategic Initiatives (6-12+ months)

| Initiative | Investment | Expected ROI | Timeline |
|------------|------------|--------------|----------|
{{#STRATEGIC_INITIATIVES}}
| {{INITIATIVE}} | {{INVESTMENT}} | {{ROI}} | {{TIMELINE}} |
{{/STRATEGIC_INITIATIVES}}

---

## Summary & Next Steps

### Overall Assessment

**Health Score:** {{HEALTH_SCORE}}/100 - **{{HEALTH_STATUS}}**

**Score Breakdown:**

| Category | Score | Weight | Weighted Score |
|----------|-------|--------|----------------|
| Growth Metrics | {{GROWTH_SCORE}}/20 | 20% | {{GROWTH_WEIGHTED}} |
| Profitability | {{PROFITABILITY_SCORE}}/20 | 20% | {{PROFITABILITY_WEIGHTED}} |
| Unit Economics | {{UNIT_ECON_SCORE}}/20 | 20% | {{UNIT_ECON_WEIGHTED}} |
| Retention | {{RETENTION_SCORE}}/20 | 20% | {{RETENTION_WEIGHTED}} |
| Efficiency | {{EFFICIENCY_SCORE}}/20 | 20% | {{EFFICIENCY_WEIGHTED}} |
| **Total** | **{{HEALTH_SCORE}}/100** | **100%** | **{{HEALTH_SCORE}}** |

### Key Strengths

{{#KEY_STRENGTHS}}
1. **{{STRENGTH_TITLE}}**
   {{STRENGTH_DESCRIPTION}}

{{/KEY_STRENGTHS}}

### Key Weaknesses

{{#KEY_WEAKNESSES}}
1. **{{WEAKNESS_TITLE}}**
   {{WEAKNESS_DESCRIPTION}}

{{/KEY_WEAKNESSES}}

### Key Risks

{{#KEY_RISKS}}
1. **{{RISK_TITLE}}**
   {{RISK_DESCRIPTION}}

{{/KEY_RISKS}}

### Immediate Actions (Next 30 Days)

{{#IMMEDIATE_ACTIONS}}
{{ACTION_NUMBER}}. {{ACTION_DESCRIPTION}}
{{/IMMEDIATE_ACTIONS}}

### Review Cadence

| Review Type | Frequency | Next Due |
|-------------|-----------|----------|
| Full Health Check | {{HEALTH_CHECK_FREQUENCY}} | {{NEXT_HEALTH_CHECK}} |
| Key Metrics Review | Monthly | {{NEXT_MONTHLY_REVIEW}} |
| Board Reporting | {{BOARD_FREQUENCY}} | {{NEXT_BOARD_MEETING}} |

### Success Criteria (12 Months)

By {{TWELVE_MONTH_DATE}}, the company should achieve:

{{#SUCCESS_CRITERIA_12MO}}
- {{CRITERIA_STATUS}} {{CRITERIA_DESCRIPTION}}
{{/SUCCESS_CRITERIA_12MO}}

---

## Appendix: Calculation Details

### Rule of 40 Calculation
See the Rule of 40 section.

### LTV Calculation
```
LTV = Annual ARPC x Gross Margin % / Annual Churn Rate

Monthly ARPC = {{ARPC_MONTHLY}}
Annual ARPC = {{ARPC_MONTHLY}} x 12 = {{ARPC_ANNUAL}}
Gross Margin % = {{GROSS_MARGIN}}%
Monthly Churn = {{MONTHLY_CHURN_RATE}}%
Annual Churn = 1 - (1 - {{MONTHLY_CHURN_DECIMAL}})^12 = {{ANNUAL_CHURN_RATE}}%

LTV = {{ARPC_ANNUAL}} x {{GROSS_MARGIN}}% / {{ANNUAL_CHURN_RATE}}% = {{LTV}}
```

### CAC Payback Period
```
CAC Payback = CAC / (Monthly ARPC x Gross Margin %)

CAC = {{CAC}}
Monthly ARPC = {{ARPC_MONTHLY}}
Gross Margin % = {{GROSS_MARGIN}}%

CAC Payback = {{CAC}} / ({{ARPC_MONTHLY}} x {{GROSS_MARGIN_DECIMAL}})
CAC Payback = {{CAC}} / {{MONTHLY_GROSS_PROFIT}}
CAC Payback = {{CAC_PAYBACK_MONTHS}} months
```

### Magic Number
```
Magic Number = (Quarterly Net New ARR x 4) / Prior Quarter S&M Spend

Quarterly Net New ARR = {{QUARTERLY_NET_NEW_ARR}}
Annualized = {{QUARTERLY_NET_NEW_ARR}} x 4 = {{ANNUALIZED_NET_NEW_ARR}}
Prior Quarter S&M = {{PRIOR_QUARTER_SM_SPEND}}

Magic Number = {{ANNUALIZED_NET_NEW_ARR}} / {{PRIOR_QUARTER_SM_SPEND}} = {{MAGIC_NUMBER}}
```

### NRR and GRR Calculations
```
Starting Cohort ARR (12 months ago) = {{COHORT_STARTING_ARR}}
Churned ARR = {{CHURNED_ARR_COHORT}}
Expansion ARR = {{EXPANSION_ARR_COHORT}}
Current Cohort ARR = {{COHORT_CURRENT_ARR}}

GRR = (Starting ARR - Churned ARR) / Starting ARR x 100
GRR = ({{COHORT_STARTING_ARR}} - {{CHURNED_ARR_COHORT}}) / {{COHORT_STARTING_ARR}} x 100
GRR = {{GRR}}%

NRR = Current Cohort ARR / Starting ARR x 100
NRR = {{COHORT_CURRENT_ARR}} / {{COHORT_STARTING_ARR}} x 100
NRR = {{NRR}}%
```

### Burn Multiple
```
Burn Multiple = Net Burn / Net New ARR

Net Burn = Absolute value of negative EBITDA
Net Burn = {{NET_BURN}}

Net New ARR = Current ARR - Prior Year ARR
Net New ARR = {{ARR_CURRENT}} - {{ARR_PRIOR_YEAR}}
Net New ARR = {{NET_NEW_ARR}}

Burn Multiple = {{NET_BURN}} / {{NET_NEW_ARR}} = {{BURN_MULTIPLE}}
```

---

## Glossary

| Term | Definition |
|------|------------|
| ARR | Annual Recurring Revenue - total annualized value of recurring revenue |
| MRR | Monthly Recurring Revenue - total monthly recurring revenue |
| CAC | Customer Acquisition Cost - cost to acquire one new customer |
| LTV | Lifetime Value - total gross profit from a customer over their lifetime |
| NRR | Net Revenue Retention - revenue retention including expansion |
| GRR | Gross Revenue Retention - revenue retention excluding expansion |
| EBITDA | Earnings Before Interest, Taxes, Depreciation, and Amortization |
| Rule of 40 | Growth Rate % + EBITDA Margin %, against a target of 40, 50 or 60 (default 40) |
| Magic Number | Sales efficiency ratio (Net New ARR / S&M Spend) |
| Burn Multiple | Capital efficiency (Net Burn / Net New ARR) |
| ARPC | Average Revenue Per Customer |
| COGS | Cost of Goods Sold |

---

*Financial Health Report - Product Finance Plugin*
*Report Generated: {{REPORT_GENERATED_DATE}}*
*Assessment Date: {{ASSESSMENT_DATE}} | Next Review: {{NEXT_REVIEW_DATE}}*
*Confidence Level: {{CONFIDENCE_LEVEL}} | Data Quality: {{DATA_QUALITY}}*
