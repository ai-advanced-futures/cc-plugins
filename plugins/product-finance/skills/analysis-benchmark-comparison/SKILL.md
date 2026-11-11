---
name: analysis-benchmark-comparison
description: Compare financial metrics against industry benchmarks and stage-appropriate targets
---

# Benchmark Comparison Skill

## Purpose

Compare financial metrics against industry benchmarks because context transforms raw numbers into actionable insights and helps set realistic targets.

## When to Use

- Evaluating company performance in context
- Setting financial targets and OKRs
- Preparing investor presentations
- Identifying improvement priorities
- Benchmarking against competitors

## What This Skill Provides

Comprehensive benchmark comparison including:
- Metric-by-metric benchmark comparison
- Stage-appropriate target setting
- Quartile ranking against peers
- Gap analysis to best-in-class
- Improvement prioritization

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| company_stage | enum | Yes | early, growth, scale, mature |
<!-- See docs/METHODOLOGY.md — Company Stage Definitions for ARR-to-stage mapping -->
| arr | float | Yes | Annual Recurring Revenue |
| revenue_growth_rate | float | Yes | YoY revenue growth percentage |
| gross_margin | float | Yes | Gross margin percentage |
| ebitda_margin | float | No | EBITDA margin percentage |
| nrr | float | No | Net Revenue Retention percentage |
| grr | float | No | Gross Revenue Retention percentage |
| cac_payback | float | No | CAC payback in months |
| ltv_cac_ratio | float | No | LTV:CAC ratio |
| magic_number | float | No | Sales efficiency metric |
| rule_of_40 | float | No | Growth + EBITDA margin |
| target_status | string | No | met, split, short or not_graded, from the Rule of 40 report |

## Benchmark Database

### By Company Stage

**Early Stage ($0-$1M ARR)**
| Metric | Bottom Quartile | Median | Top Quartile |
|--------|-----------------|--------|--------------|
| Growth Rate | < 100% | 150-200% | > 300% |
| Gross Margin | < 60% | 70-75% | > 80% |
| Monthly Churn | > 5% | 3-4% | < 2% |
| CAC Payback | > 24 months | 12-18 months | < 12 months |

**Growth Stage ($1M-$10M ARR)**
| Metric | Bottom Quartile | Median | Top Quartile |
|--------|-----------------|--------|--------------|
| Growth Rate | < 50% | 80-100% | > 150% |
| Gross Margin | < 65% | 72-78% | > 80% |
| NRR | < 100% | 105-110% | > 120% |
| CAC Payback | > 18 months | 10-14 months | < 9 months |

**Scale Stage ($10M-$100M ARR)**
| Metric | Bottom Quartile | Median | Top Quartile |
|--------|-----------------|--------|--------------|
| Growth Rate | < 30% | 40-60% | > 80% |
| Gross Margin | < 70% | 75-80% | > 82% |
| NRR | < 105% | 110-120% | > 130% |
| GRR | < 85% | 88-92% | > 95% |
| CAC Payback | > 15 months | 9-12 months | < 8 months |
| LTV:CAC | < 3:1 | 3.5:1 – 5:1 | > 5:1 (Excellent) |
| Magic Number | < 0.6 | 0.8-1.0 | > 1.2 |

**Mature Stage ($100M+ ARR)**
| Metric | Bottom Quartile | Median | Top Quartile |
|--------|-----------------|--------|--------------|
| Growth Rate | < 15% | 20-30% | > 40% |
| Gross Margin | < 72% | 78-82% | > 85% |
| EBITDA Margin | < 5% | 15-20% | > 25% |
| NRR | < 110% | 115-125% | > 130% |
| GRR | < 90% | 92-95% | > 97% |

## Benchmark Sources

### Public Company Data
- Bessemer Cloud Index
- OpenView SaaS Benchmarks
- KeyBanc SaaS Survey
- KBCM Technology Survey

### Private Company Data
- SaaS Capital benchmarks
- a16z marketplace data
- Craft Ventures SaaS metrics
- ChartMogul Subscription Benchmarks

## Output Format

```json
{
  "benchmark_comparison": {
    "company_stage": "growth",
    "arr": 5000000,
    "metrics": [
      {
        "metric": "Revenue Growth",
        "value": 85,
        "unit": "%",
        "benchmark_median": 90,
        "benchmark_top_quartile": 150,
        "percentile": 45,
        "status": "below_median",
        "gap_to_median": -5,
        "gap_to_top_quartile": -65
      },
      {
        "metric": "NRR",
        "value": 118,
        "unit": "%",
        "benchmark_median": 108,
        "benchmark_top_quartile": 120,
        "percentile": 72,
        "status": "above_median",
        "gap_to_median": 10,
        "gap_to_top_quartile": -2
      }
    ],
    "overall_percentile": 58,
    "strengths": ["NRR", "Gross Margin"],
    "improvement_areas": ["Revenue Growth", "CAC Payback"],
    "priority_focus": "Improve CAC efficiency to enable growth acceleration"
  }
}
```

## Process

1. **Determine Company Stage:**
   - Based on ARR and business maturity
   - Select the benchmark set of the company's stage and sector

2. **Collect Current Metrics:**
   - Gather all available financial metrics
   - Ensure consistent calculation methodology

3. **Compare to Benchmarks:**
   - Calculate percentile for each metric in the stage tables above
   - Identify above/below median
   - Calculate gaps to targets

4. **Prioritize Improvements:**
   - Identify biggest gaps
   - Weight by business impact
   - Consider dependencies

5. **Set Targets (stage-table metrics only):**
   - Near-term: reach median if below
   - Medium-term: reach top quartile
   - Long-term: best-in-class

## Percentile Calculation

```
Percentile = (Value - Bottom Quartile) / (Top Quartile - Bottom Quartile) × 75 + 25
```

Capped at 0-100.

## Metric Weighting

Not all metrics are equally important. Weighted scoring:

| Metric | Weight | Rationale |
|--------|--------|-----------|
| Rule of 40 | 20% | From target_status: met 100, split 50, short 0 |
| NRR | 18% | Revenue quality |
| Growth Rate | 15% | Scale potential |
| CAC Payback | 15% | Efficiency |
| Gross Margin | 12% | Unit economics |
| GRR | 10% | Retention foundation |
| LTV:CAC | 10% | Acquisition efficiency |

When `target_status` is missing or `not_graded`, the Rule of 40 leaves the weighting and the other weights are scaled so they sum to 100%.

## Stage-Appropriate Targets

### Early Stage Priorities
1. **Growth Rate** - Prove product-market fit
2. **Gross Margin** - Validate business model
3. **Monthly Churn** - Early retention signals

### Growth Stage Priorities
1. **NRR** - Expansion capability
2. **CAC Payback** - Efficient growth
3. **Rule of 40** - Balance growth/efficiency

### Scale Stage Priorities
1. **Rule of 40** - Growth and margin together
2. **GRR** - Revenue durability
3. **Magic Number** - Sales efficiency

### Mature Stage Priorities
1. **EBITDA Margin** - Profitability
2. **Rule of 40** - Sustained health
3. **FCF Margin** - Cash generation

## Gap Analysis

### Critical Gaps (Fix First)
- NRR < 100%
- LTV:CAC < 1:1 (Critical by the thresholds of the plugin scripts; 1:1–3:1 is Warning)
- CAC Payback > 24 months

### Improvement Opportunities
- Rule of 40 target_status short
- Gap > 15 points from median
- Metric declining quarter-over-quarter
- Below bottom quartile

### Optimization Opportunities
- Above median but below top quartile
- Competing priority trade-offs

## Best-in-Class Examples

### Growth Rate Leaders
- Company: Slack (IPO year)
- Growth: 82% at $400M ARR
- How: Viral product-led growth, enterprise expansion

### NRR Leaders
- Company: Snowflake
- NRR: 169% (peak)
- How: Consumption model, expansion-first design

### Efficiency Leaders
- Company: Atlassian
- CAC Payback: < 12 months
- How: Self-serve, minimal sales team

## Benchmark Caveats

1. **Industry Variation:** DevTools vs. MarTech vs. FinTech have different profiles
2. **Business Model:** Usage-based vs. seat-based affects benchmarks
3. **Geography:** US vs. Europe vs. Asia have different expectations
4. **Market Conditions:** 2021 vs. 2023 benchmarks differ significantly
5. **Sample Bias:** Public companies skew higher than all SaaS

## Recommendation Framework

Based on gap analysis, generate recommendations:

| Gap Size | Gap Direction | Recommendation |
|----------|---------------|----------------|
| Large (>20pts) | Below median | Critical priority - dedicate resources |
| Moderate (10-20pts) | Below median | High priority - improvement plan |
| Small (<10pts) | Below median | Monitor and improve |
| Above median | At median | Good - maintain |
| Top quartile | At/above | Excellent - protect and learn from |
