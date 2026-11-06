---
name: quick-validate
description: Skip to opportunity analysis when you already have survey data, a job statement and a needs list. Use when the person has survey ratings and wants scores, value, segments and a price check in one pass, with no agents.
allowed-tools: AskUserQuestion, Read, Write, Glob
---

# /jtbd-market-discovery:quick-validate

You run all steps in the main conversation and dispatch no agent.

## Purpose

Accelerate to opportunity analysis when you already have survey data because jumping directly to scoring and validation saves time for experienced JTBD practitioners.

## Prerequisites

**Required:**
- Survey data (CSV format with importance/satisfaction ratings)
- Job statement already identified
- Customer needs list already generated

**Use this command when:**
- You've already conducted JTBD job decomposition
- You have survey responses with importance/satisfaction data
- You want to skip to Phases 6-10 (Opportunity Scoring → Output)

## Process

### Step 1: Validate Prerequisites

Ask the person with the `AskUserQuestion` tool to confirm they have all of the items below. If they do not, say that `/jtbd-market-discovery:discover` fits them better, because it covers the steps that they lack, and stop.

```
I'll help you validate your opportunity using existing survey data.

This command skips Phases 1-5 and jumps directly to:
- Phase 6: Opportunity Scoring (ODI algorithm)
- Phase 7: EVC Calculation
- Phase 8: Segmentation
- Phase 9: WTP Validation
- Phase 10: Output Generation

To proceed, I need:
1. Your job statement (e.g., "Get to destinations on time")
2. Survey data (CSV with importance/satisfaction columns)
3. Context about your target market

Do you have all of these?
```

### Step 2: Collect Job Context

Ask for essential context with the `AskUserQuestion` tool, one question for each call:

**Questions:**
- What is the job statement you're analyzing?
- How many survey respondents do you have?
- What is the target market segment? (B2B/B2C, role, industry)
- What is the estimated market size? (total addressable users)

**Validation:**
- Job statement should be clear and solution-agnostic
- Survey should have n > 30 for statistical validity
- Market context helps with WTP validation

### Step 3: Import Survey Data

Ask the person for the path of the survey file, or for the data pasted as text, in this format:

```
Please paste your survey data as CSV with this format:

need_id,need_description,importance,satisfaction
N001,Minimize time to estimate departure time,9.2,3.1
N002,Reduce likelihood of arriving late,9.5,2.8
...

Expected columns:
- need_id: Unique identifier (e.g., N001, N002)
- need_description: Full need statement
- importance: Average importance rating (1-10 scale)
- satisfaction: Average satisfaction rating (1-10 scale)

If you have individual respondent data (not averages), paste that format:
respondent_id,need_id,importance,satisfaction
R001,N001,9,3
R001,N002,10,2
...
```

**Parse and validate:**
- Check column structure
- Validate data ranges (1-10 scale)
- Calculate averages if individual respondent data
- Count unique needs and respondents

### Step 4: Execute Phase 6 - Opportunity Scoring

Calculate ODI scores for all needs:

**ODI Formula:** `Opportunity = Importance + max(Importance - Satisfaction, 0)`

**For each need:**
1. Apply formula
2. Classify opportunity level:
   - Severely Underserved: >= 15
   - Underserved: 12-15
   - Appropriately Served: 10-12
   - Overserved: < 10

**Output:**
```
Opportunity Analysis Results:

Top 10 Opportunities:
1. O001: Minimize time to estimate departure time (ODI: 15.3)
   Importance: 9.2 | Satisfaction: 3.1 | Gap: 6.1

2. O002: Reduce likelihood of arriving late (ODI: 16.7)
   Importance: 9.5 | Satisfaction: 2.8 | Gap: 6.7

...

Severely Underserved: 12 needs (top priorities)
Underserved: 18 needs (secondary priorities)
Appropriately Served: 25 needs (maintain current performance)
Overserved: 15 needs (don't over-invest)
```

### Step 5: Execute Phase 7 - EVC Calculation (Quick)

For top 3 opportunities, calculate quick EVC:

**Ask with the `AskUserQuestion` tool:**
- What is the typical time savings your solution creates? (hours/month)
- What is the hourly rate of target users? ($)
- How many errors/failures does your solution prevent? (per month)
- What is the cost per error/failure? ($)

**Calculate baseline EVC:**
```
Baseline EVC (top opportunity):
- Time savings: 2 hrs/month × $25/hr = $50
- Error reduction: 6 failures × $50 = $300
Total: $350/month

With 20% moderate differentiation premium: $420/month
```

**Skip detailed 4-component if user wants speed:**
- Focus on time savings + error reduction only
- Use conservative estimates
- Flag as "quick estimate" vs "detailed calculation"

### Step 6: Execute Phase 8 - Segmentation (Quick)

Use importance patterns to identify 3 segments:

**Approach:**
- Cluster customers by importance profile (which needs rated highest)
- Characterize each cluster
- Estimate size and WTP

**Quick segmentation output:**
```
3 Customer Segments Identified:

1. High-Value Segment (35% of market)
   - High importance on top 10 needs
   - Low current satisfaction
   - Estimated WTP: $40-60/month
   - Profile: [Brief description]

2. Mid-Value Segment (40% of market)
   - Medium importance across needs
   - Medium satisfaction
   - Estimated WTP: $20-30/month
   - Profile: [Brief description]

3. Low-Value Segment (25% of market)
   - Lower importance, higher satisfaction
   - Estimated WTP: $10-15/month
   - Profile: [Brief description]
```

### Step 7: Execute Phase 9 - WTP Validation

Apply 6-layer validation framework to segment WTP estimates:

**Layer 1: Statistical Check**
- If survey has WTP data, check for outliers
- Validate consistency across responses

**Layer 2: Competitive Benchmark**
- Ask with the `AskUserQuestion` tool: "What direct competitors exist?"
- Ask with the `AskUserQuestion` tool: "Are there free alternatives?"
- Compare WTP to competitor pricing

**Layer 3: Value Economics**
- WTP should be 10-40% of EVC
- If WTP > 40% EVC: Flag as unrealistic
- If WTP < 10% EVC: Leaving value on table

**Layer 4: Segment Benchmark**
- B2B: $20-200/user/month typical
- B2C: $5-50/month typical
- If B2C > $50/month: Challenge pricing

**Critical validation output:**
```
WTP Validation Results:

High-Value Segment: $40-60/month
✓ PASS: Statistical check (n=30, consistent)
⚠ CHALLENGED: Competitive benchmark (free alternatives exist)
✓ PASS: Value economics (14% of EVC)
⚠ CHALLENGED: B2C benchmark (high for consumer)

Overall: CHALLENGED
Recommendation: Consider B2B pivot or freemium model
```

### Step 8: Generate Quick Output

Create condensed JSON output:

```json
{
  "analysis_metadata": {
    "date": "2026-01-23",
    "job_statement": "...",
    "respondents": 87,
    "analysis_type": "quick_validate"
  },
  "top_opportunities": [
    {
      "opportunity_id": "O001",
      "need": "Minimize time to estimate departure time",
      "importance": 9.2,
      "satisfaction": 3.1,
      "odi_score": 15.3,
      "recommended_segment": "High-Value"
    }
  ],
  "segments": [
    {
      "segment_id": "S001",
      "name": "High-Value",
      "size_percent": 35,
      "wtp_validated": 50,
      "validation_status": "CHALLENGED"
    }
  ],
  "quick_evc": {
    "baseline": 350,
    "premium": 420
  },
  "recommendations": [
    "Consider B2B pivot due to free alternatives",
    "Focus on High-Value segment (35% of market)",
    "Target pricing: $40-50/month"
  ]
}
```

### Step 9: Next Steps

Offer integration options:

```
Quick Validation Complete!

Key Findings:
- Top Opportunity: [need] (ODI: 15.3)
- Target Segment: High-Value (35% market, ~2100 companies)
- Validated WTP: $40-50/month (CHALLENGED - consider B2B)
- Quick EVC: $420/month per user

Would you like to:
1. Run full /jtbd-market-discovery:discover for detailed analysis?
2. Turn the top opportunity into product requirements? (/product:explore)
3. Validate pricing more rigorously? (/jtbd-market-discovery:wtp-check)
4. Export results to JSON/CSV?
```

## Important Notes

**When to Use Quick Validate:**
- ✅ You have clean survey data with importance/satisfaction ratings
- ✅ You want to skip educational Socratic dialogue
- ✅ You're experienced with JTBD methodology
- ✅ You need fast insights for decision-making

**When to use something else:**
- ❌ You're new to JTBD (use /jtbd-market-discovery:discover for education)
- ❌ You have no survey data yet
- ❌ You need help decomposing the job into steps
- ❌ You want to learn JTBD methodology

**Speed vs Depth Tradeoff:**
- Quick Validate: 15-30 minutes
- Full Discover: 45-90 minutes
- Quick is 80% accuracy with conservative assumptions
- Full is 95% accuracy with detailed analysis

**Conservative Bias:**
- Quick validate uses conservative estimates
- Flags uncertainties clearly
- Recommends full analysis if high-stakes decision

## Examples

**Good use case:**
```
User: "I surveyed 87 customers about navigation app. Have importance/satisfaction
data for 40 needs. Want to quickly identify top opportunities."

Result: Perfect for /jtbd-market-discovery:quick-validate
```

**Bad use case:**
```
User: "I want to discover market opportunities for a new product idea."

Result: Use /jtbd-market-discovery:discover instead (no data yet, needs education)
```
