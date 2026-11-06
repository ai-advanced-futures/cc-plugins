# SaaS Product Analysis Workflow

This document outlines the step-by-step command sequence for performing a comprehensive financial analysis of a B2B SaaS company.

## Prerequisites

1. Claude Code CLI installed and configured
2. Product Finance plugin installed
3. Access to financial data (Stripe, CRM, accounting system)

## Workflow Steps

### Step 1: Initialize Plugin Configuration

First, set up the plugin with your company's assumptions and baseline data.

```bash
# Interactive setup (recommended for first time)
/product-finance:setup
```

Or copy the pre-configured assumptions:

```bash
# Create the .product-finance directory
mkdir -p .product-finance

# Copy the example assumptions
cp examples/saas-product-analysis/inputs/assumptions.json .product-finance/assumptions.json
```

**Expected Output:**
```
Product Finance Setup Complete!
================================

Configuration saved to:
  - .product-finance/assumptions.json

Company Profile:
  - Name: DataSync Pro
  - Stage: Series A
  - Business Model: B2B SaaS

Ready to run:
  - /product-finance:health-check
  - /product-finance:unit-economics
```

### Step 2: Run Financial Health Check

Assess overall financial health with board-level KPIs.

```bash
/product-finance:health-check
```

**Input Data Required:**
- Current MRR/ARR
- Customer count
- Churn rate
- Growth rate
- Gross margin

**Expected Output:**
```
Financial Health Assessment Complete!
=====================================

Overall Health: GOOD

Key Metrics:
  - MRR: $250,000 (GOOD)
  - ARR: $3,000,000 (GOOD)
  - MRR Growth: 8.7% MoM (EXCELLENT)
  - Net Revenue Retention: 115% (EXCELLENT)
  - Gross Margin: 78% (GOOD)
  - Monthly Churn: 1.2% (GOOD)
  - Rule of 40: 82 (EXCELLENT)

Files Generated:
  - .product-finance/health-report.json
  - .product-finance/reports/health-report-2026-01-23.md
```

### Step 3: Run Unit Economics Analysis

Calculate CAC, LTV, and profitability metrics.

```bash
/product-finance:unit-economics
```

**Input Data Required:**
- Sales and marketing spend
- New customers acquired
- Customer lifetime assumptions
- Gross margin

**Expected Output:**
```
Unit Economics Analysis Complete!
=================================

Summary:
  - CAC: $45,000 (GOOD)
  - LTV: $375,000 (EXCELLENT)
  - LTV:CAC Ratio: 8.33x (EXCELLENT)
  - CAC Payback: 9 months (EXCELLENT)
  - Gross Margin per Customer: $3,900/month (GOOD)

Profitability Analysis:
  - Customer Profitable After: 12 months
  - Fully-Loaded Payback: 15 months
  - Unit Margin: 72%

Files Generated:
  - .product-finance/unit-economics.json
  - .product-finance/reports/unit-economics-report-2026-01-23.md
```

### Step 4: Review and Interpret Results

#### Health Report Analysis

Open `.product-finance/reports/health-report-2026-01-23.md` and review:

1. **Executive Summary** - Overall health score and key concerns
2. **Growth Metrics** - MRR/ARR trends and growth rate
3. **Retention Metrics** - Churn and NRR analysis
4. **Efficiency Metrics** - Rule of 40 and burn multiple
5. **Recommendations** - Prioritized action items

#### Unit Economics Analysis

Open `.product-finance/reports/unit-economics-report-2026-01-23.md` and review:

1. **CAC Analysis** - Acquisition costs by channel
2. **LTV Analysis** - Customer lifetime value breakdown
3. **Efficiency Ratios** - LTV:CAC, payback period
4. **Cohort Analysis** - Performance by customer cohort
5. **Optimization Opportunities** - Cost reduction and revenue improvement

## Complete Command Sequence

```bash
# 1. Setup (one-time)
/product-finance:setup

# 2. Health Check
/product-finance:health-check

# 3. Unit Economics
/product-finance:unit-economics

# 4. Optional: AI Economics (if applicable)
/product-finance:ai-economics

# 5. Optional: Feature ROI analysis
/product-finance:feature-roi "Advanced Analytics Dashboard"
```

## Interpreting Results

### Health Scores

| Score | Meaning | Action |
|-------|---------|--------|
| EXCELLENT | Top quartile performance | Maintain and optimize |
| GOOD | Healthy performance | Continue current strategy |
| WARNING | Below benchmark | Investigate and improve |
| CRITICAL | Urgent attention needed | Immediate action required |

### Key Thresholds

| Metric | Critical | Warning | Good | Excellent |
|--------|----------|---------|------|-----------|
| Monthly Churn | >5% | 2-5% | 1-2% | <1% |
| NRR | <90% | 90-100% | 100-115% | >115% |
| Gross Margin | <60% | 60-70% | 70-80% | >80% |
| LTV:CAC | <2x | 2-3x | 3-5x | >5x |
| Rule of 40 | <20 | 20-30 | 30-50 | >50 |

## Troubleshooting

### Missing Data

If the analysis shows "insufficient data":

1. Check `.product-finance/assumptions.json` for completeness
2. Verify all required fields are populated
3. Run `/product-finance:setup` to fill in missing values

### Inconsistent Metrics

If metrics don't match your internal reports:

1. Verify data sources are aligned
2. Check calculation methodology in `docs/METHODOLOGY.md`
3. Ensure period dates are correct

### Permission Issues

If file creation fails:

1. Ensure write permissions on current directory
2. Check that `.product-finance/` directory exists
3. Verify disk space availability

## Next Steps

After completing the basic analysis:

1. **Set up instrumentation** - `/product-finance:instrumentation` to track metrics automatically
2. **Analyze specific features** - `/product-finance:feature-roi` for investment decisions
3. **Track AI economics** - `/product-finance:ai-economics` if using AI features
4. **Create monitoring dashboard** - Use output data to build real-time dashboards

## Related Documentation

- [Health Check Command](../../commands/health-check.md)
- [Unit Economics Command](../../commands/unit-economics.md)
- [Methodology](../../docs/METHODOLOGY.md)
- [KPI Definitions](../../docs/KPI_DEFINITIONS.md)
