# SaaS Product Analysis Example

This example demonstrates a complete product financial analysis workflow for a Series A B2B SaaS company. The company, "DataSync Pro", provides enterprise data integration solutions with approximately $3M ARR and 50 customers.

## Company Profile

**Company:** DataSync Pro
**Stage:** Series A ($8M raised)
**Business Model:** B2B SaaS, subscription-based
**ARR:** $3,000,000
**Customer Count:** 50 enterprise customers
**Average Contract Value (ACV):** $60,000/year
**Team Size:** 25 employees

## Use Case Overview

DataSync Pro's finance team needs to:
1. Assess overall financial health for their upcoming board meeting
2. Calculate unit economics to validate their GTM strategy
3. Identify areas for improvement before the Series B raise

## Files Included

### Inputs

- **`inputs/assumptions.json`** - Financial assumptions including costs, pricing, and benchmark targets
- **`inputs/metrics.json`** - Current operational and financial metrics

### Outputs

- **`outputs/health-report.json`** - Structured health assessment data
- **`outputs/health-report.md`** - Human-readable health report for stakeholders
- **`outputs/unit-economics.json`** - Detailed unit economics analysis

## Running This Example

### Step 1: Initialize with Assumptions

```bash
# Copy assumptions to your project
cp inputs/assumptions.json .product-finance/assumptions.json

# Or run setup to create interactively
/product-finance:setup
```

### Step 2: Run Health Check

```bash
/product-finance:health-check
```

This will generate:
- `.product-finance/health-report.json`
- `.product-finance/reports/health-report-YYYY-MM-DD.md`

### Step 3: Run Unit Economics Analysis

```bash
/product-finance:unit-economics
```

This will generate:
- `.product-finance/unit-economics.json`
- `.product-finance/reports/unit-economics-report-YYYY-MM-DD.md`

## Key Insights from This Example

### Financial Health Summary

| Metric | Value | Status |
|--------|-------|--------|
| ARR | $3,000,000 | GOOD |
| MRR Growth | 8.5% MoM | EXCELLENT |
| Net Revenue Retention | 115% | EXCELLENT |
| Gross Margin | 78% | GOOD |
| Churn Rate | 1.2% monthly | GOOD |
| Rule of 40 | 84.0 | met against 40 (default) |

### Unit Economics Summary

| Metric | Value | Status |
|--------|-------|--------|
| CAC | $45,000 | GOOD |
| LTV | $375,000 | EXCELLENT |
| LTV:CAC Ratio | 8.3x | EXCELLENT |
| CAC Payback | 9 months | EXCELLENT |
| Gross Margin per Customer | $3,900/month | GOOD |

### Key Recommendations

1. **Optimize CAC** - While healthy, CAC of $45K leaves room for channel optimization
2. **Focus on expansion revenue** - 115% NRR is strong; target 120%+ for Series B
3. **Maintain churn discipline** - 1.2% monthly churn is good but target <1% for enterprise

## Customizing This Example

To adapt this example for your company:

1. Update `inputs/assumptions.json` with your costs and targets
2. Update `inputs/metrics.json` with your current metrics
3. Run the workflow commands
4. Compare your outputs to the provided examples

## Related Examples

- [AI Feature ROI](../ai-feature-roi/) - Calculate ROI for AI feature investments
- [Instrumentation Plan](../instrumentation-plan/) - Plan financial tracking implementation

## References

- [Methodology Documentation](../../docs/METHODOLOGY.md)
- [KPI Definitions](../../docs/KPI_DEFINITIONS.md)
- [Health Check Command](../../commands/health-check.md)
- [Unit Economics Command](../../commands/unit-economics.md)
