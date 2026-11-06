---
description: Financial modeling for consulting and professional services businesses — utilization, capacity, pipeline math, break-even, hiring triggers, and scenario analysis
---

# Services Model Command

## Purpose

The services-model command provides comprehensive financial modeling for consulting and professional services businesses. Unlike SaaS businesses that rely on MRR and subscription metrics, services firms are capacity-constrained and project-based. This command models the core levers that drive services profitability: utilization, billable capacity, pipeline conversion, break-even thresholds, and capacity-driven hiring decisions.

This command enables services firm founders, practice leaders, and fractional CFOs to build defensible financial models, identify revenue gaps, plan hiring, and present scenarios to investors or boards.

## When to Use

- **Revenue Planning:** Modeling annual revenue capacity based on team size and utilization
- **Hiring Decisions:** Determining when to hire the next billable person based on capacity utilization
- **Pipeline Health:** Validating whether outreach volume and conversion rates support revenue targets
- **Break-Even Analysis:** Understanding how many deals per month are needed to cover fixed costs
- **Scenario Planning:** Modeling conservative, base, and stretch outcomes for board or investor discussions
- **Pricing Strategy:** Testing how billing rate changes affect revenue ceiling and margins
- **Growth Planning:** Identifying whether growth is constrained by capacity, pipeline, or pricing
- **Fundraising:** Demonstrating services unit economics and growth trajectory to investors

## What It Does

1. **Calculates Utilization Rate:**
   - Utilization = Billable Hours / Total Available Hours
   - Benchmarked against 65-75% healthy target range
   - Flags under-utilization (pipeline problem) and over-utilization (burnout risk)

2. **Computes Billable Capacity:**
   - Billable Capacity = Team Size x Hours/Person/Year x Utilization Rate
   - Determines total billable hours available for revenue generation
   - Basis for revenue capacity ceiling calculation

3. **Determines Revenue Capacity Ceiling:**
   - Revenue Ceiling = Billable Capacity x Average Billing Rate
   - Maximum possible revenue with current team at target utilization
   - Shows headroom between projected revenue and ceiling

4. **Models Project-Based Revenue:**
   - Projected Revenue = Number of Deals x Average Deal Size
   - Compares against capacity ceiling to identify constraints
   - Not MRR — revenue recognized on project delivery milestones

5. **Builds Pipeline Math:**
   - Full funnel: Outreach -> Meetings -> Proposals -> Closes
   - Conversion rates at each stage with benchmark comparisons
   - Calculates required outreach volume to hit deal targets
   - Identifies funnel bottlenecks

6. **Runs Break-Even Analysis:**
   - Break-Even Revenue = Fixed Costs / Gross Margin %
   - Determines number of deals per month needed to cover costs
   - Estimates time to break-even based on pipeline velocity

7. **Sets Capacity-Driven Hiring Triggers:**
   - Revenue per billable person calculation
   - 85% capacity threshold as hiring trigger
   - Accounts for 2-3 month ramp time for new hires
   - Estimates months until next hire is needed

8. **Generates Scenario Models:**
   - Conservative: 80% deal count, 90% deal size
   - Base: Target assumptions
   - Stretch: 120% deal count, 110% deal size
   - Gross margin impact for each scenario

9. **Saves Results:**
   - Structured data: `.product-finance/services-model.json`
   - Executive dashboard: `.product-finance/services-model-dashboard.md`
   - Historical tracking for trend analysis

## Command Behavior

### Two Analysis Modes

**Mode 1: Current State Analysis**
- Model current services economics based on actual team size and pipeline data
- Use trailing period actuals for utilization and conversion rates
- Ideal for ongoing monitoring and optimization

**Mode 2: Growth Planning Analysis**
- Model future scenarios with different team sizes, billing rates, or pipeline assumptions
- Test hiring plans, pricing changes, or new service line economics
- Support fundraising and strategic planning

The command defaults to current state analysis. Growth planning mode available via prompt.

## Data Collection Flow

### Phase 1: Team and Capacity

**Introduction:**
```
Services Financial Model — Team & Capacity
============================================
Services businesses are capacity-constrained. Your revenue ceiling
is determined by team size, utilization rate, and billing rate.

Let's start with your team structure and utilization targets.
```

**Question:** "How many billable team members do you have?"
- **Type:** integer
- **Guidance:** "Count only team members who bill client hours (exclude admin, sales, ops)"
- **Example:** "8 billable consultants"
- **Help:** "Include full-time and fractional billable resources converted to FTE"

**Question:** "What are the total working hours per person per year?"
- **Type:** integer
- **Default:** 2,080
- **Guidance:** "Standard is 2,080 (40 hrs/week x 52 weeks). Adjust for PTO, holidays, etc."
- **Example:** "2,080 (standard) or 1,880 (after PTO/holidays)"

**Question:** "What is your target utilization rate?"
- **Type:** number (0-100 percent)
- **Guidance:** "Billable hours as a percentage of total available hours. Healthy range is 65-75%."
- **Example:** "70%"
- **Validation:** Warn if >85% (burnout risk) or <50% (significant underutilization)
- **Help:** "65-75% is the healthy target. Below 65% suggests pipeline issues. Above 80% risks quality and burnout."

**Question:** "What is your average billing rate per hour?"
- **Type:** number
- **Guidance:** "Blended average across all billable team members and service types"
- **Example:** "$175/hour"
- **Help:** "If rates vary widely (e.g., $125-$250), use the weighted average based on hours billed"

**Auto-calculate:**
- Billable Capacity = Team Size x Hours/Person x Utilization Rate
- Revenue Capacity Ceiling = Billable Capacity x Average Billing Rate
- Display: "Your team of {N} at {X}% utilization can generate up to ${ceiling} annually."

### Phase 2: Project Revenue

**Introduction:**
```
Project-Based Revenue Modeling
===============================
Services revenue is project-based, not recurring.
Let's model your expected deal flow and revenue.
```

**Question:** "What is your average deal size (project value)?"
- **Type:** number
- **Guidance:** "Average total contract value per client engagement"
- **Example:** "$75,000 per project"
- **Help:** "If deal sizes vary, use the weighted average. For retainers, use annual contract value."

**Question:** "How many deals do you expect to close this year?"
- **Type:** integer
- **Guidance:** "Total new client engagements expected for the analysis period"
- **Example:** "20 deals"

**Auto-calculate:**
- Projected Revenue = Deals x Average Deal Size
- Capacity Utilization % = Projected Revenue / Revenue Ceiling x 100
- Display: "Projected revenue of ${projected} uses {X}% of your ${ceiling} capacity."
- Flag if >85%: "Approaching capacity ceiling. Consider hiring plan."
- Flag if <50%: "Significant capacity surplus. Focus on pipeline development."

### Phase 3: Pipeline Math

**Introduction:**
```
Pipeline Conversion Analysis
==============================
Working backward from your revenue target to determine
the outreach volume and conversion rates needed.
```

**Question:** "How many outreach activities (emails, calls, intros) do you make per month?"
- **Type:** integer
- **Guidance:** "Total monthly outbound touches to prospective clients"
- **Example:** "400 per month"

**Question:** "What percentage of outreach converts to a meeting/discovery call?"
- **Type:** number (0-100)
- **Guidance:** "Benchmark: 2-5% for cold outreach, 10-20% for warm/referral"
- **Example:** "3%"

**Question:** "What percentage of meetings result in a proposal?"
- **Type:** number (0-100)
- **Guidance:** "Benchmark: 30-50% for qualified meetings"
- **Example:** "40%"

**Question:** "What percentage of proposals convert to a closed deal?"
- **Type:** number (0-100)
- **Guidance:** "Benchmark: 25-40% for well-qualified proposals"
- **Example:** "30%"

**Auto-calculate:**
- Monthly funnel: Outreach -> Meetings -> Proposals -> Closes
- Monthly pipeline revenue = Closes x Average Deal Size
- Annual pipeline revenue = Monthly x 12
- Compare pipeline revenue to projected revenue target
- Display funnel waterfall and gap analysis

### Phase 4: Cost Structure and Break-Even

**Introduction:**
```
Break-Even Analysis
====================
Understanding your fixed cost structure and the revenue
needed to cover costs before generating profit.
```

**Question:** "What are your total monthly fixed costs?"
- **Type:** number
- **Guidance:** "All fixed monthly expenses: salaries (including non-billable staff), rent, tools, insurance, etc."
- **Example:** "$120,000/month"
- **Help:** "Include: all salaries and benefits, office/co-working, software tools, insurance, accounting, legal retainers"

**Question:** "What is your gross margin percentage per deal?"
- **Type:** number (0-100)
- **Guidance:** "Revenue minus direct project costs (subcontractors, travel, materials) as a percentage of revenue"
- **Example:** "55%"
- **Help:** "Gross margin = (Deal Revenue - Direct Costs) / Deal Revenue. Exclude overhead — that's captured in fixed costs."

**Auto-calculate:**
- Monthly Break-Even Revenue = Fixed Costs / (Gross Margin % / 100)
- Annual Break-Even Revenue = Monthly x 12
- Break-Even Deals per Month = Monthly Break-Even Revenue / Average Deal Size
- Months to Break-Even based on pipeline velocity
- Display: "You need ${break_even}/month ({N} deals) to cover fixed costs."

### Phase 5: Capacity Planning

**Auto-calculate from prior inputs:**
- Revenue per Billable Person = (Hours/Person x Utilization Rate) x Billing Rate
- Hire-Next Trigger = Revenue Ceiling x 85%
- Months until trigger based on projected revenue growth
- Cost of next hire (prompt for loaded cost if not already captured)
- Display: "Begin hiring when revenue approaches ${trigger}. At current trajectory, that's approximately {N} months."

### Phase 6: Scenario Modeling

**Introduction:**
```
Scenario Analysis
==================
Three scenarios to bracket your financial outcomes.
```

**Auto-calculate from prior inputs:**

| Scenario | Deal Count | Deal Size | Revenue | Gross Margin |
|----------|-----------|-----------|---------|-------------|
| Conservative | 80% of base | 90% of base | calculated | calculated |
| Base | target | target | calculated | calculated |
| Stretch | 120% of base | 110% of base | calculated | calculated |

**Question:** "Would you like to customize the scenario assumptions?" (yes/no)

**If yes:**
- Allow override of deal count and deal size multipliers for each scenario
- Allow override of utilization rate for each scenario
- Recalculate all downstream metrics

**Auto-calculate for each scenario:**
- Revenue, gross margin, profit/loss
- Capacity utilization percentage
- Months to break-even
- Hiring trigger timing

### Phase 7: Results and Recommendations

**Generate comprehensive output:**
1. Executive summary with overall health status
2. Utilization and capacity metrics with benchmarks
3. Revenue projection vs. capacity ceiling
4. Pipeline waterfall with conversion analysis
5. Break-even analysis with timeline
6. Capacity planning with hiring triggers
7. Three-scenario comparison table
8. Prioritized recommendations

**Save artifacts:**
- `.product-finance/services-model.json` — structured calculation results
- `.product-finance/services-model-dashboard.md` — formatted executive dashboard

## Integration with Other Commands

- **health-check:** Services model feeds into overall financial health assessment
- **setup:** Initial assumptions can seed services model defaults
- **feature-roi:** Can model ROI of investing in new service lines or capabilities
