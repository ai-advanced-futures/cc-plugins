# AI Feature ROI Workflow

This document outlines the step-by-step process for evaluating the ROI of adding AI-powered features to your SaaS product.

## Prerequisites

1. Claude Code CLI with Product Finance plugin installed
2. AI feature specification completed
3. Cost estimates from engineering team
4. Market research on AI feature pricing

## Workflow Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Feature Spec  │────▶│  AI Economics   │────▶│   Feature ROI   │
│    (inputs)     │     │   Analysis      │     │   Decision      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Step 1: Define Feature Specification

Create a comprehensive feature specification that includes:

### 1.1 Feature Capabilities

```json
{
  "capabilities": [
    {
      "name": "Natural Language Queries",
      "ai_usage": {
        "model": "gpt-4",
        "queries_per_user_per_month": 50
      }
    }
  ]
}
```

### 1.2 Build Cost Estimate

```json
{
  "build_estimate": {
    "total_story_points": 320,
    "cost_per_story_point": 450,
    "total_build_cost": 144000
  }
}
```

### 1.3 Ongoing Cost Projections

```json
{
  "ongoing_costs": {
    "monthly": {
      "ai_api_costs": 8000,
      "infrastructure": 7500,
      "maintenance": 2500,
      "total": 18000
    }
  }
}
```

## Step 2: Run AI Economics Analysis

The AI Economics command analyzes the cost and value of AI capabilities.

```bash
/product-finance:ai-economics
```

### Expected Questions

**Analysis Context:**
```
Q: What are you analyzing?
A: new_feature

Q: What time period for this analysis?
A: 12_months
```

**AI Cost Data:**
```
Q: What is your total AI API/LLM cost for the period?
A: $96,000 (projected annual)

Q: How many AI interactions/API calls during this period?
A: 360,000 (30,000/month)

Q: How many active users during this period?
A: 300 users

Q: Do you have a breakdown by provider/model?
A: Yes
  - OpenAI GPT-4: $72,000
  - Anthropic Claude: $24,000
```

**Infrastructure Costs:**
```
Q: Do you have AI infrastructure costs beyond API calls?
A: Yes
  - Vector database: $30,000/year
  - Caching: $12,000/year
  - Compute: $36,000/year
  - Monitoring: $12,000/year
```

**AI Value Data:**
```
Q: What revenue is enabled by AI features?
A: $2,520,000 (AI tier revenue)

Q: Do you charge a premium for AI capabilities?
A: Yes, 50% premium

Q: Does AI save time for your users or team?
A: Yes, 840 hours/year saved
```

### Expected Output

```
AI Economics Analysis Complete!
================================

AI ROI: 385% (3.85x return)
Net Annual Value: $978,000
AI Cost as % of Revenue: 4.2%
Overall Health: EXCELLENT

Files Generated:
  - .product-finance/ai-economics.json
  - .product-finance/reports/ai-economics-report-2026-01-23.md
```

## Step 3: Run Feature ROI Analysis

The Feature ROI command calculates comprehensive investment returns.

```bash
/product-finance:feature-roi "AI Analytics Assistant"
```

### Expected Questions

**Feature Context:**
```
Q: What is the strategic purpose of this feature?
A: expansion

Q: What is the urgency for this feature?
A: high
```

**Build Cost:**
```
Q: How do you want to estimate build effort?
A: story_points

Q: How many story points to build this feature?
A: 320

Q: What is your cost per story point?
A: $450
```

**Ongoing Costs:**
```
Q: Will this feature have ongoing operational costs?
A: Yes
  - Infrastructure: $7,500/month
  - AI API costs: $8,000/month
  - Maintenance: $2,500/month
```

**Revenue Impact:**
```
Q: Will this feature drive new customer revenue?
A: Yes, 10 new customers/month @ $6,000/month

Q: Will this feature drive expansion revenue?
A: Yes, 12 customers upgrading @ $2,000/month increase

Q: Will this feature improve customer retention?
A: Yes, 0.5% churn reduction

Q: Will this feature enable premium pricing?
A: Yes, 50% premium on AI tier
```

**Financial Assumptions:**
```
Q: What discount rate for NPV calculation?
A: 15%

Q: What time horizon for ROI analysis?
A: 36 months

Q: What is your target payback period?
A: 12 months
```

### Expected Output

```
Feature ROI Analysis Complete!
==============================

Feature: AI Analytics Assistant
RECOMMENDATION: BUILD

Key Metrics:
  ROI: 325% (3.25x return)
  Payback Period: 4.2 months (EXCELLENT)
  NPV: $2,150,000 at 15% discount rate
  Total Investment: $609,600 (build + 3-year ongoing)
  3-Year Net Value: $2,580,000

Files Generated:
  - .product-finance/feature-roi-ai-analytics-assistant.json
  - .product-finance/reports/feature-roi-ai-analytics-assistant-2026-01-23.md
```

## Step 4: Review and Present Results

### 4.1 Generate CFO-Ready Report

The generated markdown report includes:

1. **Executive Summary** - Key metrics and recommendation
2. **Build Cost Analysis** - Detailed cost breakdown
3. **Revenue Impact Projection** - Value attribution by source
4. **Financial Analysis** - ROI, NPV, payback calculations
5. **Risk Analysis** - Key risks and mitigations
6. **Recommendation** - BUILD/DEFER/DON'T BUILD with rationale

### 4.2 Compare Alternatives

Run the analysis with different assumptions:

```bash
# Conservative scenario
/product-finance:feature-roi "AI Analytics Assistant" --scenario=conservative

# Aggressive scenario
/product-finance:feature-roi "AI Analytics Assistant" --scenario=aggressive
```

## Step 5: Track Post-Launch Performance

After feature launch, track actual vs. projected metrics:

### 5.1 Set Up Instrumentation

```bash
/product-finance:instrumentation
```

Track:
- AI queries per user
- AI costs per query
- AI tier adoption rate
- Churn rate by tier
- Expansion revenue

### 5.2 Monthly Review

```bash
# Run monthly to compare actuals vs. projections
/product-finance:ai-economics --mode=existing_product
```

## Decision Framework

### BUILD Criteria

Feature should be built if:
- [ ] ROI > 100% (minimum threshold)
- [ ] Payback < 12 months (target)
- [ ] NPV > 0 (value creation)
- [ ] Strategic alignment confirmed
- [ ] Resources available

### DEFER Criteria

Feature should be deferred if:
- [ ] ROI 50-100% (marginal)
- [ ] Payback 12-18 months (acceptable but not urgent)
- [ ] Higher priority features exist
- [ ] Resource constraints

### DON'T BUILD Criteria

Feature should not be built if:
- [ ] ROI < 50%
- [ ] Payback > 18 months
- [ ] NPV < 0
- [ ] High execution risk
- [ ] Strategic misalignment

## Sensitivity Analysis

### Key Variables to Test

1. **AI Adoption Rate**
   - Base: 50% of customers
   - Conservative: 30%
   - Aggressive: 70%

2. **AI Cost per Query**
   - Base: $0.08
   - Conservative: $0.12
   - Aggressive: $0.05

3. **Premium Pricing Acceptance**
   - Base: 50% premium
   - Conservative: 30% premium
   - Aggressive: 70% premium

4. **Churn Reduction**
   - Base: 0.5%
   - Conservative: 0.2%
   - Aggressive: 0.8%

### Running Sensitivity

```bash
# Model scenarios
/product-finance:feature-roi "AI Analytics Assistant" --sensitivity

# Output shows:
# - Base case ROI: 325%
# - Conservative ROI: 180%
# - Aggressive ROI: 485%
# - Break-even adoption rate: 22%
```

## Common Pitfalls

### 1. Underestimating AI Costs

**Problem:** API costs grow faster than expected with usage

**Solution:**
- Implement aggressive caching (30%+ cache hit rate)
- Use model routing for cost efficiency
- Set per-user rate limits
- Monitor and alert on cost thresholds

### 2. Overestimating Adoption

**Problem:** Fewer customers adopt AI tier than projected

**Solution:**
- Use conservative adoption rates (50% of optimistic)
- Run beta program before full launch
- Track leading indicators (demo requests, trial usage)
- Build adoption campaigns

### 3. Ignoring Ongoing Costs

**Problem:** Focus on build cost, neglect ongoing expenses

**Solution:**
- Always include 3-year TCO in analysis
- Account for maintenance (15-20% of build cost)
- Factor in infrastructure scaling costs
- Include customer support overhead

### 4. Missing Value Sources

**Problem:** Only count direct revenue, miss indirect value

**Solution:**
- Include retention value (reduced churn)
- Count productivity savings (CS team time)
- Measure expansion revenue (upsells)
- Track competitive advantage

## Templates

### Feature Spec Template

See `inputs/feature-spec.json` for a complete template.

### Assumptions Template

See `inputs/assumptions.json` for a complete template.

### Output Examples

See `outputs/` directory for example outputs.

## Related Documentation

- [AI Economics Command](../../commands/ai-economics.md)
- [Feature ROI Command](../../commands/feature-roi.md)
- [Methodology](../../docs/METHODOLOGY.md)
- [KPI Definitions](../../docs/KPI_DEFINITIONS.md)
