---
description: Calculate ROI for specific features or initiatives with build cost estimation, revenue impact, payback period, NPV analysis, and Build/Don't Build/Defer recommendation
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*), Edit(/.product-finance/**)
---

# Feature ROI Command

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `uv run python`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because only the plugin's own scripts are tested.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

## Every run

0. **Read the start time and the version** — run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and keep its output as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. Never type a time yourself, because a typed time is a guess and not the time of the run. The result file needs both.
1. Do the work the rest of this file describes.
2. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/roi-calculator.md` with the Read tool and follow its `## Result file` section, in every run.

## Purpose

The feature-roi command provides comprehensive financial analysis for feature investment decisions. It calculates Return on Investment (ROI) by estimating build costs (converting dev effort to fully-loaded costs), projecting revenue impact, calculating payback period, performing NPV (Net Present Value) analysis, and generating a recommendation: `BUILD`, `DON'T BUILD` or `DEFER`.

This command enables data-driven prioritization and helps product teams make defensible investment decisions with CFO-ready justification.

## When to Use

- **Feature prioritization:** Comparing multiple features to determine which to build first
- **Build vs. buy decisions:** Evaluating whether to build in-house or purchase solution
- **Roadmap planning:** Annual or quarterly planning with budget constraints
- **Resource allocation:** Justifying engineering team allocation to stakeholders
- **Investment approval:** Getting CFO/leadership sign-off on major features
- **Post-launch review:** Validating if actual ROI matched projections
- **Defer decisions:** Determining if feature should be postponed

## What It Does

1. **Estimates Build Cost:**
   - Converts development effort (story points, weeks, FTE) to fully-loaded costs
   - Includes engineering, product, design, QA resources
   - Accounts for ongoing maintenance and operational costs
   - Factors in opportunity cost of alternative features

2. **Projects Revenue Impact:**
   - New revenue from feature adoption
   - Expansion revenue from upsell opportunities
   - Retention improvements (reduced churn)
   - Premium pricing capture
   - Time-to-value acceleration

3. **Calculates Payback Period:**
   - Months to break even on investment
   - Cumulative cash flow over time
   - Comparison to company target (typically 12-18 months)

4. **Performs NPV Analysis:**
   - Net Present Value calculation with discount rate
   - Time value of money considerations
   - Multi-year revenue projections
   - Risk-adjusted returns

5. **Generates ROI Recommendation:**
   - **Build:** Strong positive ROI, short payback, strategic alignment
   - **`DON'T BUILD`:** Negative ROI, long payback, resource constraints
   - **Defer:** Positive but marginal ROI, better timing later, higher priorities exist

6. **Saves Results:**
   - Structured data: `.product-finance/feature-roi-{feature-name}.json`
   - Executive report: `.product-finance/reports/feature-roi-{feature-name}-YYYY-MM-DD.md`
   - Historical tracking for post-launch comparison

## Command Behavior

### Two Analysis Modes

**Mode 1: Single Feature Analysis**
- Deep dive on one specific feature
- Comprehensive cost/benefit analysis
- Detailed recommendation with justification

**Mode 2: Multi-Feature Comparison (Optional)**
- Analyze multiple features side-by-side
- Rank by ROI, payback period, NPV
- Resource allocation recommendations

The command defaults to single feature analysis. Multi-feature mode available via flag or prompt.

## Question Flow

### Phase 1: Feature Context

**Question** (AskUserQuestion [q: feature_name]): "What feature are you analyzing?"
- **Type:** text
- **Guidance:** "Brief name or description (e.g., 'AI-powered search', 'Enterprise SSO', 'Mobile app')"
- **Example:** "Advanced analytics dashboard"

**Question** (AskUserQuestion [q: strategic_purpose]): "What is the strategic purpose of this feature?"

**Options:**
- `new_revenue` - Attract new customers or new market segment
- `expansion` - Upsell existing customers to higher tiers
- `retention` - Reduce churn by improving product value
- `efficiency` - Improve internal efficiency or reduce costs
- `competitive` - Match competitor feature (table stakes)
- `strategic` - Long-term strategic positioning
- `hybrid` - Multiple purposes (describe)

**Why we need this:** Purpose determines which value metrics to prioritize and affects recommendation logic.

**Question** (AskUserQuestion [q: urgency]): "What is the urgency for this feature?"

**Options:**
- `critical` - Losing customers without it, competitive threat
- `high` - Strong customer demand, revenue opportunity
- `medium` - Important but not urgent
- `low` - Nice-to-have, can defer
- `exploratory` - Research/experimentation
- **Default:** `medium`, when nobody gives one

**Why we need this:** Urgency affects recommendation, especially for "Defer" scenarios.

### Phase 2: Build Cost Estimation

**Introduction:**
```
Build Cost Estimation
=====================
We'll estimate the fully-loaded cost to build this feature.
Choose your estimation method:
1. Story points (Agile teams)
2. Time-based (weeks/sprints)
3. FTE allocation (person-months)
4. Direct cost (if you already know)
```

**Question** (AskUserQuestion [q: build_method]): "How do you want to estimate build effort?"

**Options:**
- `story_points` - Estimate in story points
- `time_based` - Estimate in weeks or sprints
- `fte_allocation` - Estimate in person-months (FTE)
- `direct_cost` - Provide direct dollar amount
- **Default:** `time_based`, when nobody gives a method

#### 2a. Story Points Method

**If `story_points`:**

**Question** (AskUserQuestion [q: story_points]): "How many story points to build this feature?"
- **Type:** integer (1-1000)
- **Guidance:** "Total estimated story points including all work (frontend, backend, QA, etc.)"
- **Example:** "150 story points"

**Check assumptions.json for cost per story point. If not found:**

**Question** (AskUserQuestion [q: cost_per_story_point]): "What is your cost per story point?"
- **Type:** number
- **Guidance:** "Calculate as: (Total monthly R&D cost) / (Story points completed per month)"
- **Example:** "If R&D costs $100K/month and team completes 200 points/month = $500/point"
- **Help:** "If unknown, we'll estimate from team costs"

**If cost per story point unknown, ask:**

**Question** (AskUserQuestion [q: monthly_rd_cost]): "What is your total monthly R&D cost?"
- **Type:** number
- **Guidance:** "Fully-loaded cost of engineering, product, design team"

**Question** (AskUserQuestion [q: story_points_per_month]): "How many story points does your team complete per month?"
- **Type:** integer
- **Guidance:** "Average velocity across all teams"

**Auto-calculate:** Cost per story point = Monthly R&D Cost / Monthly Story Points

**Final calculation:** Build cost = Story Points × Cost per Story Point

#### 2b. Time-Based Method

**If `time_based`:**

**Question** (AskUserQuestion [q: build_weeks]): "How many weeks to build this feature?"
- **Type:** number (0.5-52)
- **Guidance:** "Estimated calendar time from start to launch"
- **Example:** "8 weeks"
- **Default:** 4 weeks, when nobody gives a number

**Question** (AskUserQuestion [q: engineers]): "How many engineers will work on this?"
- **Type:** number
- **Guidance:** "Average FTE allocation (can be fractional, e.g., 2.5 engineers)"
- **Example:** "3 engineers"
- **Default:** 1 engineer, when nobody gives a number

**Question** (AskUserQuestion [q: engineer_monthly_cost]): "What is the average fully-loaded cost per engineer?"
- **Type:** number
- **Guidance:** "Annual cost / 12 months. Include salary, benefits, overhead (multiply base × 1.7-2.0)"
- **Example:** "Engineer at $150K salary × 1.7 = $255K/year = $21,250/month"
- **Default:** Pull from assumptions.json if available; else $16,667 a month ($200,000 a year)

**Question** (AskUserQuestion [q: non_engineering_resources]): "Any non-engineering resources needed?" (yes/no; default: no)

**If yes:**
- "Product manager time (weeks)?" - number
- "Designer time (weeks)?" - number
- "QA time (weeks)?" - number
- "Cost per week for each role?" - number (for each role)

**Auto-calculate:**
- Engineering cost = (Weeks × Engineers × Monthly Cost) / 4.33 weeks per month
- Total build cost = Engineering + PM + Design + QA

#### 2c. FTE Allocation Method

**If `fte_allocation`:**

**Question** (AskUserQuestion [q: person_months]): "How many person-months to build this feature?"
- **Type:** number
- **Guidance:** "Total effort across all roles (e.g., 1 person for 3 months = 3 person-months, or 3 people for 1 month = 3 person-months)"
- **Example:** "6 person-months"

**Question** (AskUserQuestion [q: cost_per_person_month]): "Average fully-loaded cost per person-month?"
- **Type:** number
- **Guidance:** "Blended rate across engineering, product, design. Typically $18K-$30K/person-month"
- **Example:** "$22,000/person-month"

**Auto-calculate:** Build cost = Person-Months × Cost per Person-Month

#### 2d. Direct Cost Method

**If `direct_cost`:**

**Question** (AskUserQuestion [q: total_build_cost]): "What is the total build cost?"
- **Type:** number
- **Guidance:** "Fully-loaded cost including all resources and overhead"
- **Example:** "$150,000"

**Question** (AskUserQuestion [q: cost_scope]): "Does this include only build cost, or also ongoing costs?"

**Options:**
- `build_only` - Just the initial build
- `includes_ongoing` - Includes ongoing costs

### Phase 3: Ongoing Costs

**Question** (AskUserQuestion [q: has_ongoing_costs]): "Will this feature have ongoing operational costs?" (yes/no)
- **Default (no answer):** maintenance only, at 15% of build cost a year, by month

**If yes:**

**Question** (AskUserQuestion [q: ongoing_monthly_cost]): "Monthly ongoing costs?"

**Categories:**
- Infrastructure/hosting costs (increased compute, storage, etc.): number
- Third-party API costs: number
- Maintenance/support costs (as % of build cost, default 15%): number
- Other recurring costs: number

**Auto-calculate:**
- Total monthly ongoing costs
- Annual ongoing costs
- 3-year total cost of ownership (TCO)

### Phase 4: Revenue Impact Projection

**Introduction:**
```
Revenue Impact Analysis
=======================
Now let's project the revenue impact of this feature.
We'll analyze multiple value dimensions:
- New customer acquisition
- Expansion revenue (upsell/upgrade)
- Retention improvements (reduced churn)
- Premium pricing capture
- Time-to-value acceleration
```

#### 4a. New Revenue (Optional but Recommended)

**Question** (AskUserQuestion [q: drives_new_revenue]): "Will this feature drive new customer revenue?" (yes/no; default: no)

**If yes:**

**Question** (AskUserQuestion [q: new_customers_per_month]): "How many new customers per month will this feature attract?"
- **Type:** number
- **Guidance:** "Conservative estimate of incremental new customers"
- **Example:** "10 new customers/month"

**Question** (AskUserQuestion [q: new_customer_arpc]): "What is the average revenue per customer per month?"
- **Type:** number
- **Guidance:** "Average ARPC (from assumptions.json if available)"
- **Example:** "$500/customer/month"

**Question** (AskUserQuestion [q: ramp_months]): "How long will it take to reach this run rate?"
- **Type:** number (months)
- **Guidance:** "Ramp-up period from launch to steady state"
- **Default:** 3 months

**Auto-calculate:**
- Monthly new revenue (steady state)
- Annual new revenue (with ramp-up). Ramp-up is linear: in month m of the ramp (m = 1 to the ramp months), revenue is the steady-state rate times m divided by the ramp months; after the ramp it is the steady-state rate.
- 3-year cumulative new revenue

#### 4b. Expansion Revenue (Optional but Recommended)

**Question** (AskUserQuestion [q: drives_expansion]): "Will this feature drive expansion revenue from existing customers?" (yes/no; default: no)

**If yes:**

**Question** (AskUserQuestion [q: upgrading_customers]): "How many existing customers will upgrade for this feature?"
- **Type:** number
- **Guidance:** "Customers who will move to higher tier or add-on"
- **Example:** "25 customers over 12 months"

**Question** (AskUserQuestion [q: upgrade_revenue_per_customer]): "What is the average revenue increase per upgraded customer?"
- **Type:** number (monthly)
- **Guidance:** "Additional monthly revenue from upgrade"
- **Example:** "$200/month additional per customer"

**Auto-calculate:**
- Monthly expansion revenue (steady state)
- Annual expansion revenue
- 3-year cumulative expansion revenue

#### 4c. Retention Impact (Optional but Recommended)

**Question** (AskUserQuestion [q: improves_retention]): "Will this feature improve customer retention?" (yes/no; default: no)

**If yes:**

**Question** (AskUserQuestion [q: current_churn_percent]): "What is your current monthly churn rate?"
- **Type:** number (0-100 percent)
- **Guidance:** "Current monthly churn % (from assumptions.json if available)"
- **Example:** "3.5%"

**Question** (AskUserQuestion [q: churn_reduction_points]): "By how many percentage points will this feature reduce churn?"
- **Type:** number (0-100 percent)
- **Guidance:** "Expected churn reduction (be conservative)"
- **Example:** "0.5% reduction (from 3.5% to 3.0%)"

**Question** (AskUserQuestion [q: retained_customers]): "How many customers will benefit from this retention improvement?"
- **Type:** integer
- **Guidance:** "Total customer base or segment affected"
- **Example:** "500 customers"

**Question** (AskUserQuestion [q: retention_arpc]): "What is the average revenue per customer per month?"
- **Type:** number
- **Guidance:** "ARPC for affected segment"

**Auto-calculate:**
- Monthly retention value = (Churn Reduction % / 100) × Customer Count × ARPC
- Annual retention value
- 3-year cumulative retention value

#### 4d. Premium Pricing (Optional)

**Question** (AskUserQuestion [q: enables_premium]): "Will this feature enable premium pricing?" (yes/no; default: no)

**If yes:**

**Question** (AskUserQuestion [q: premium_percent]): "What is the pricing premium percentage?"
- **Type:** number (0-1000)
- **Guidance:** "How much more can you charge for this capability?"
- **Example:** "20% premium (current tier $100/mo → new tier with feature $120/mo)"

**Question** (AskUserQuestion [q: premium_customers]): "How many customers will pay this premium?"
- **Type:** integer
- **Guidance:** "Customers in premium tier or willing to upgrade"

**Question** (AskUserQuestion [q: premium_base_revenue]): "Current monthly revenue from these customers (without premium)?"
- **Type:** number

**Auto-calculate:**
- Baseline revenue without premium
- Premium pricing value = (Current Revenue × Premium %)
- Annual premium value
- 3-year cumulative premium value

#### 4e. Time-to-Value Acceleration (Optional)

> ⚠️ **Phase 2, not yet implemented:** The time-to-value acceleration calculation
> described below is documented for future implementation. Leave it out of
> current feature ROI calculations, because the script does not compute it yet. Omit this dimension from all outputs until
> implemented in the `unit_economics.py` script.

**Question:** "Will this feature accelerate time-to-value for customers?" (yes/no)

**If yes:**

**Question:** "How many days faster will customers achieve value?"
- **Type:** number
- **Guidance:** "Reduction in onboarding, setup, or time-to-first-value"
- **Example:** "20 days faster (from 45 days to 25 days)"

**Question:** "What is the average monthly revenue per customer?"
- **Type:** number

**Question:** "How many customers per month will benefit?"
- **Type:** integer

**Auto-calculate:**
- Months accelerated = Days / 30
- Monthly acceleration value per customer = (Monthly Revenue × Months Accelerated)
- Annual acceleration value = (Monthly acceleration value per customer × New customers per month × 12)
- 3-year acceleration value = (Monthly acceleration value per customer × New customers per month × 36)
- **Note:** This is a one-time benefit per new customer cohort. Each month's new customers receive the acceleration benefit once. Not recurring revenue from the same customers.

### Phase 5: Financial Assumptions

**Question** (AskUserQuestion [q: discount_rate]): "What discount rate should we use for NPV calculation?"
- **Type:** number (0-50 percent)
- **Guidance:** "Weighted Average Cost of Capital (WACC) or company hurdle rate. Typical range: 10-20%"
- **Default:** 15%
- **Why:** "Accounts for time value of money and investment risk"

**Question** (AskUserQuestion [q: analysis_horizon_months]): "What time horizon for ROI analysis?"
- **Type:** number (months)
- **Options:** 12, 24, 36, 48, 60 months
- **Default:** 36 months
- **Guidance:** "Typical feature lifecycle: 3 years (36 months)"

**Question** (AskUserQuestion [q: target_payback_months]): "What is your company's target payback period?"
- **Type:** number (months)
- **Guidance:** "Maximum acceptable months to break even"
- **Default:** 12 months
- **Pull from:** assumptions.json if available

**Question** (AskUserQuestion [q: minimum_roi_percent]): "What is your company's minimum acceptable ROI?"
- **Type:** number (percent)
- **Guidance:** "Minimum ROI threshold for investment approval"
- **Default:** 100% (2x return)

### Phase 6: Calculate and Report

**Processing:**
1. Aggregate all revenue sources
2. Calculate cumulative cash flow by month
3. Determine payback period (when cumulative cash flow turns positive)
4. Calculate NPV using discount rate
5. Calculate ROI percentage
   - When the ROI is above 1000%, list each input of the ROI and ask: **Question** (AskUserQuestion [q: confirm_high_roi]): "The calculated ROI of {roi}% seems very high. Are these inputs correct, and do you want to proceed with them?" (yes/no)
   - **Default:** yes. Keep the figure, list each input in the report, and flag the figure for review.
6. Generate recommendation based on decision logic
7. Create executive report and structured data

## Output

### File 1: `.product-finance/feature-roi-{feature-name}.json`

Structured data following schema:

```json
{
  "feature": {
    "name": "Advanced Analytics Dashboard",
    "description": "Real-time analytics with custom reporting",
    "strategic_purpose": "expansion",
    "urgency": "high",
    "analysis_date": "2026-01-23T10:00:00Z"
  },
  "build_cost": {
    "estimation_method": "story_points",
    "story_points": 150,
    "cost_per_story_point": 500,
    "total_build_cost": 75000,
    "breakdown": {
      "engineering": 60000,
      "product": 8000,
      "design": 5000,
      "qa": 2000
    }
  },
  "ongoing_costs": {
    "monthly": 2000,
    "annual": 24000,
    "breakdown": {
      "infrastructure": 1000,
      "third_party_apis": 500,
      "maintenance": 500
    }
  },
  "revenue_impact": {
    "new_revenue": {
      "monthly_steady_state": 15000,
      "annual_year_1": 135000,
      "annual_year_2": 180000,
      "annual_year_3": 180000,
      "ramp_up_months": 3,
      "three_year_total": 495000
    },
    "expansion_revenue": {
      "monthly_steady_state": 5000,
      "annual_year_1": 45000,
      "annual_year_2": 60000,
      "annual_year_3": 60000,
      "three_year_total": 165000
    },
    "retention_value": {
      "monthly": 1000,
      "annual_year_1": 12000,
      "annual_year_2": 12000,
      "annual_year_3": 12000,
      "three_year_total": 36000,
      "churn_reduction_pct": 0.5
    },
    "premium_pricing": {
      "annual_year_1": 30000,
      "annual_year_2": 40000,
      "annual_year_3": 40000,
      "three_year_total": 110000
    },
    "total_revenue_impact": {
      "annual_year_1": 222000,
      "annual_year_2": 292000,
      "annual_year_3": 292000,
      "three_year_total": 806000
    }
  },
  "financial_analysis": {
    "roi": {
      "percentage": 432.8,
      "ratio": 5.33,
      "description": "For every $1 invested, return $5.33"
    },
    "payback_period": {
      "months": 4.5,
      "status": "excellent",
      "vs_target": -7.5,
      "description": "Breaks even 7.5 months ahead of 12-month target"
    },
    "npv": {
      "value": 486340,
      "discount_rate": 15,
      "description": "Net Present Value of future cash flows",
      "status": "positive"
    },
    "total_investment": {
      "build_cost": 75000,
      "three_year_ongoing": 72000,
      "total": 147000
    },
    "net_value": {
      "three_year": 659000,
      "description": "Total value minus total costs"
    }
  },
  "decision": {
    "recommendation": "BUILD",
    "confidence": "high",
    "reasoning": [
      "Excellent ROI of 433% well above 100% minimum threshold",
      "Payback period of 4.5 months is significantly better than 12-month target",
      "Positive NPV of $486,340 indicates strong value creation",
      "Strategic alignment: expansion revenue supports growth objectives",
      "High urgency: strong customer demand justifies prioritization"
    ],
    "risks": [
      "Revenue projections assume 3-month ramp-up - may take longer",
      "Expansion revenue depends on existing customer adoption",
      "Ongoing infrastructure costs may increase with scale"
    ],
    "next_steps": [
      "Approve budget allocation for Q1 development",
      "Assign engineering team (estimated 150 story points)",
      "Create launch plan with revenue tracking milestones",
      "Set up post-launch ROI tracking against projections"
    ]
  },
  "metadata": {
    "analysis_date": "2026-01-23T10:00:00Z",
    "analysis_time_horizon_months": 36,
    "discount_rate_pct": 15,
    "confidence_level": "medium",
    "assumptions": {
      "new_customers_per_month": 10,
      "arpc": 1500,
      "churn_reduction": 0.5,
      "premium_pricing_pct": 20
    }
  }
}
```

### File 2: `.product-finance/reports/feature-roi-{feature-name}-YYYY-MM-DD.md`

Executive report:

```markdown
# Feature ROI Analysis: Advanced Analytics Dashboard

**Recommendation:** BUILD
**Confidence:** High
**Analysis Date:** January 23, 2026

---

## Executive Summary

**Strategic Purpose:** Expansion Revenue (Upsell existing customers)
**Urgency:** High (Strong customer demand)

**Key Metrics:**
- **ROI:** 433% (5.33x return)
- **Payback Period:** 4.5 months (vs. 12-month target)
- **NPV:** $486,340 (15% discount rate)
- **Total Investment:** $147,000 (build + 3-year ongoing)
- **3-Year Net Value:** $659,000

---

## Build Cost Analysis

**Estimation Method:** Story Points

**Total Build Cost:** $75,000

**Breakdown:**
- Engineering: $60,000 (120 story points @ $500/point)
- Product Management: $8,000
- Design: $5,000
- QA: $2,000

**Ongoing Costs:**
- Monthly: $2,000
- Annual: $24,000
- 3-Year Total: $72,000

**Total Investment (3 Years):** $147,000

---

## Revenue Impact Projection

### Year 1: $222,000
- New Revenue: $135,000 (10 new customers/month, 3-month ramp)
- Expansion Revenue: $45,000 (25 customers upgrade)
- Retention Value: $12,000 (0.5% churn reduction)
- Premium Pricing: $30,000 (20% premium on 500 customers)

### Year 2: $292,000
- New Revenue: $180,000 (full run rate)
- Expansion Revenue: $60,000 (full run rate)
- Retention Value: $12,000
- Premium Pricing: $40,000

### Year 3: $292,000
- New Revenue: $180,000
- Expansion Revenue: $60,000
- Retention Value: $12,000
- Premium Pricing: $40,000

**3-Year Total Revenue Impact:** $806,000

---

## Financial Analysis

### Return on Investment

```
ROI = (Total Value - Total Cost) / Total Cost × 100
ROI = ($806,000 - $147,000) / $147,000 × 100
ROI = 432.8%
```

**Status:** EXCELLENT (>200% threshold)

**Interpretation:** For every $1 invested, this feature returns $5.33 over 3 years.

### Payback Period

**Break-Even:** 4.5 months after launch

**Status:** EXCELLENT (7.5 months ahead of 12-month target)

**Monthly Cash Flow:**
- Month 1-3: Ramp-up, negative cash flow
- Month 4-5: Approaching break-even
- Month 6+: Positive cash flow

**Cumulative Cash Flow:**
- Month 6: +$12,000
- Month 12: +$147,000
- Month 24: +$439,000
- Month 36: +$659,000

### Net Present Value

**NPV (15% discount rate):** $486,340

**Status:** POSITIVE (strong value creation)

**Interpretation:** After accounting for time value of money (15% discount rate), this feature creates $486,340 in present-day value.

**NPV Sensitivity:**
- At 10% discount rate: $521,800
- At 15% discount rate: $486,340
- At 20% discount rate: $453,600

---

## Decision Recommendation

### BUILD ✓

**Confidence Level:** High

### Why Build

1. **Excellent ROI (433%):** Well above minimum 100% threshold, indicating strong value creation
2. **Fast Payback (4.5 months):** Significantly better than 12-month target, reducing investment risk
3. **Positive NPV ($486K):** Creates substantial present value even after time-value discount
4. **Strategic Alignment:** Expansion revenue directly supports growth objectives
5. **High Urgency:** Strong customer demand justifies immediate prioritization
6. **Multiple Revenue Sources:** New, expansion, retention, and premium pricing diversify value capture

### Key Risks & Mitigation

**Risk 1: Revenue Ramp-Up Timing**
- Assumption: 3-month ramp to steady state
- Risk: May take 6+ months if adoption slower than expected
- Mitigation: Aggressive launch marketing, early customer success engagement

**Risk 2: Expansion Revenue Assumption**
- Assumption: 25 customers upgrade in year 1
- Risk: Lower adoption if feature doesn't meet expectations
- Mitigation: Beta testing with target customers, clear value communication

**Risk 3: Infrastructure Cost Scaling**
- Assumption: $1,000/month infrastructure costs
- Risk: Costs may increase 2-3x with high usage
- Mitigation: Design for cost efficiency, monitor usage patterns, optimize queries

**Risk 4: Competitive Response**
- Risk: Competitors may match feature, reducing premium pricing power
- Mitigation: Continuous enhancement, build moat with integrations

### Success Criteria

**Launch (Month 0):**
- Feature deployed to production
- Customer communication sent
- Upgrade path available

**Month 3 (Ramp Complete):**
- 5+ new customers acquired with feature as decision factor
- 10+ existing customers upgraded
- Infrastructure costs within $1,200/month budget

**Month 6 (Break-Even):**
- Cumulative revenue > $75,000 (covers build cost)
- Customer feedback score >4.0/5.0
- Churn reduction measurable (0.3%+ improvement)

**Month 12 (Validation):**
- Annual revenue impact >$150,000 (>67% of projection)
- 15+ expansion customers (60% of target)
- Infrastructure costs <$1,500/month

### Next Steps

**Immediate Actions:**
1. **Budget Approval:** Secure $75K build budget allocation for Q1
2. **Team Allocation:** Assign 3 engineers + PM + designer (150 story points)
3. **Detailed Scoping:** Break down into implementation phases
4. **Customer Beta:** Recruit 5-10 customers for early access program

**Pre-Launch:**
5. **Pricing Strategy:** Finalize premium tier pricing (20% increase)
6. **Marketing Assets:** Create feature landing page, demo videos, case studies
7. **Sales Enablement:** Train AEs on value proposition and ROI story
8. **Success Metrics:** Instrument feature adoption, usage, and revenue tracking

**Post-Launch:**
9. **Monthly ROI Tracking:** Compare actuals vs. projections
10. **Customer Feedback:** Weekly NPS surveys for first 8 weeks
11. **Cost Monitoring:** Track infrastructure and support costs
12. **Iteration Plan:** Q2 enhancements based on feedback

---

## Assumptions & Confidence

**Confidence Level:** Medium

**Key Assumptions:**
- New customers: 10/month driven by feature
- ARPC: $1,500/customer/month
- Churn reduction: 0.5 percentage points
- Premium pricing: 20% increase, 500 customers
- Ramp-up: 3 months to steady state
- Ongoing costs: $2,000/month stable
- Discount rate: 15% (company WACC)

**High Confidence:**
- Build cost estimate (story point method with historical data)
- Ongoing infrastructure costs (validated with DevOps)
- Current churn rate and customer base

**Medium Confidence:**
- New customer acquisition rate (depends on market conditions)
- Expansion revenue conversion (25 customers upgrade)
- Churn reduction magnitude (0.5% may be optimistic)

**Lower Confidence:**
- Premium pricing adoption (customer willingness to pay)
- Time-to-full-ramp (3 months is aggressive)

**Sensitivity Analysis Recommended:**
- Model with 50% of projected new customers (5/month)
- Model with 6-month ramp instead of 3-month
- Model with 30% lower expansion revenue

---

## Comparison to Alternatives

**Alternative 1: Don't Build (Do Nothing)**
- Cost: $0
- Revenue Impact: $0
- Risk: Customer churn increases, competitive disadvantage
- NPV: -$486,340 (opportunity cost)

**Alternative 2: Build Minimal Version (MVP)**
- Cost: $40,000 (80 story points)
- Revenue Impact: ~60% of full feature ($484K over 3 years)
- Payback: 6 months
- ROI: 285%
- Tradeoff: Lower initial investment, but also lower value capture

**Alternative 3: Buy/Partner (Third-Party Integration)**
- Cost: $15,000 setup + $3,000/month ongoing
- Revenue Impact: ~40% of full feature (limited differentiation)
- 3-Year Cost: $123,000
- 3-Year Value: ~$322,000
- ROI: 162%
- Tradeoff: Faster time-to-market, but higher ongoing costs and less control

**Recommendation:** Build full feature. The ROI (433%) significantly outperforms MVP (285%) and buy/partner (162%) alternatives, and the payback period (4.5 months) is excellent.

---

## Appendix: Calculation Details

### NPV Calculation

```
NPV = Σ [Cash Flow(t) / (1 + r)^t] - Initial Investment

Where:
- t = time period (years)
- Cash Flow(t) = Revenue(t) - Ongoing Costs(t)

Year 1: $222,000 revenue - $24,000 costs = $198,000
Year 2: $292,000 revenue - $24,000 costs = $268,000
Year 3: $292,000 revenue - $24,000 costs = $268,000

PV(Year 1) = $198,000 / (1.15)^1 = $172,174
PV(Year 2) = $268,000 / (1.15)^2 = $202,778
PV(Year 3) = $268,000 / (1.15)^3 = $176,388

NPV = $172,174 + $202,778 + $176,388 - $75,000 = $486,340
```

### Payback Period Calculation

```
Cumulative Cash Flow by Month:

Month 0: -$75,000 (build cost)
Month 1: -$73,000 (small ramp revenue - ongoing costs)
Month 2: -$67,000
Month 3: -$57,000 (ramp complete)
Month 4: -$39,000 (steady state revenue)
Month 5: -$21,000
Month 6: +$12,000 ← Break-even around month 4.5
```

---

*Feature ROI Analysis - Product Finance Plugin*
*Analysis Confidence: Medium | Review quarterly to track actuals vs. projections*
```

### Console Output

**Summary displayed to user:**

```
Feature ROI Analysis Complete!
==============================

Feature: Advanced Analytics Dashboard
Strategic Purpose: Expansion Revenue
Urgency: High

RECOMMENDATION: BUILD ✓
Confidence: High

Key Metrics
-----------
ROI: 433% (5.33x return on investment)
Payback Period: 4.5 months (EXCELLENT - 7.5 months ahead of target)
NPV: $486,340 at 15% discount rate
Total Investment: $147,000 (build + 3-year ongoing)
3-Year Net Value: $659,000

Build Cost
----------
Total: $75,000
Method: Story Points (150 points @ $500/point)
Ongoing: $2,000/month

Revenue Impact (3 Years)
------------------------
Year 1: $222,000
Year 2: $292,000
Year 3: $292,000
Total: $806,000

Revenue Sources:
  - New Revenue: $495,000 (61%)
  - Expansion Revenue: $165,000 (20%)
  - Retention Value: $36,000 (4%)
  - Premium Pricing: $110,000 (14%)

Why BUILD
---------
✓ Excellent ROI (433%) well above 100% threshold
✓ Fast payback (4.5 months) reduces risk
✓ Strong NPV ($486K) indicates value creation
✓ Strategic alignment with expansion goals
✓ High urgency supports prioritization

Key Risks
---------
⚠ Revenue ramp may take longer than 3 months
⚠ Expansion revenue depends on customer adoption
⚠ Infrastructure costs may scale with usage

Next Steps
----------
1. Approve $75K budget for Q1 development
2. Assign 3 engineers + PM + designer (150 story points)
3. Create detailed implementation roadmap
4. Set up post-launch ROI tracking

Files Generated
---------------
✓ .product-finance/feature-roi-advanced-analytics-dashboard.json
✓ .product-finance/reports/feature-roi-advanced-analytics-dashboard-2026-01-23.md

Next Commands
-------------
- Run `/product-finance:health-check` for overall financial health
- Run `/product-finance:feature-roi` again to compare alternative features
- After launch: Update analysis with actuals vs. projections
```

## Implementation Notes

### For Claude Code Agent

**Interactive Data Collection:**
- Use progressive disclosure: required fields first, optional enhancements later
- Explain why each input matters for decision quality
- Provide examples and typical ranges
- Pre-populate from `.product-finance/assumptions.json` when available
- Allow "skip" for optional revenue dimensions

**Validation:**
- Build cost must be positive number
- Revenue projections must be realistic (warn if ROI >1000%)
- Payback period must be calculable (positive cash flow eventually)
- Discount rate typically 5-30%
- Time horizon typically 12-60 months

**Calculation Logic:**
1. Total Investment = Build Cost + (Ongoing Costs × Time Horizon Months)
2. Total Revenue = Sum of all revenue sources over time horizon
3. Net Value = Total Revenue - Total Investment
4. ROI % = (Net Value / Total Investment) × 100
5. Payback Period = Month when cumulative cash flow turns positive
6. NPV = Σ [CF(t) / (1+r)^t] - Initial Investment

**Decision Recommendation Logic:**

**BUILD if:**
- ROI > Minimum threshold (default 100%) AND
- Payback < Target period (default 12 months) AND
- NPV > 0 AND
- (Urgency = critical OR Urgency = high)

**DEFER if:**
- ROI > 0 BUT (Payback > Target period OR Urgency = low/medium)
- Positive but marginal ROI (50-100%)
- Strategic value exists but timing not optimal
- Higher priority features exist (if comparing multiple)

**DON'T BUILD if:**
- ROI < 0 (negative return)
- Payback > 24 months (excessive risk)
- NPV < 0 (destroys value)
- Strategic misalignment

**Confidence Levels:**
- **High:** Historical data, validated assumptions, multiple revenue sources
- **Medium:** Some assumptions, limited data, 1-2 revenue sources
- **Low:** Highly speculative, new market, many unknowns

**File Naming:**
- Sanitize feature name: lowercase, replace spaces with hyphens
- Example: "Advanced Analytics Dashboard" → "advanced-analytics-dashboard"
- JSON: `feature-roi-{sanitized-name}.json`
- Report: `feature-roi-{sanitized-name}-YYYY-MM-DD.md`

**Multi-Feature Comparison Mode:**
- If user provides multiple features, analyze each independently
- Generate comparison table ranking by ROI, payback, NPV
- Create combined report: `feature-roi-comparison-YYYY-MM-DD.md`
- Recommend prioritization based on ROI, strategic fit, resource constraints

**Integration with assumptions.json:**
- Read: Team costs, story point velocity, current metrics, targets
- Update: Add feature ROI data to assumptions for portfolio tracking
- Maintain: Historical feature ROI for learning/calibration

### Sensitivity Analysis (Optional Enhancement)

**Questions for sensitivity:**
- "Would you like to model sensitivity scenarios?" (yes/no)

**If yes, model three scenarios:**
1. **Optimistic:** 150% of projected revenue, 80% of projected costs
2. **Base Case:** As modeled
3. **Pessimistic:** 50% of projected revenue, 120% of projected costs

**Output:** Range of ROI, payback, NPV across scenarios

### Comparison Mode Details

**Multi-feature comparison prompt:**
- "Would you like to analyze another feature for comparison?" (yes/no)
- If yes, repeat full flow for Feature 2, Feature 3, etc.

**Comparison table format:**

```
Feature Comparison Matrix
=========================

| Feature | ROI | Payback | NPV | Investment | Recommendation |
|---------|-----|---------|-----|------------|----------------|
| Analytics Dashboard | 433% | 4.5mo | $486K | $147K | BUILD ✓ |
| Mobile App | 285% | 8mo | $320K | $220K | BUILD |
| Enterprise SSO | 125% | 14mo | $180K | $95K | DEFER |
| AI Chatbot | 65% | 18mo | $45K | $180K | DON'T BUILD |

Prioritization: Analytics Dashboard → Mobile App → Enterprise SSO (defer) → AI Chatbot (don't build)
```

## Examples

### Example 1: High-Value Expansion Feature

**Input:**
```
Feature: Advanced Analytics Dashboard
Purpose: expansion
Urgency: high
Build method: story_points (150 points @ $500/point = $75K)
Ongoing: $2K/month
New revenue: 10 customers/month @ $1,500 ARPC, 3-month ramp
Expansion: 25 customers @ $200/month increase
Retention: 0.5% churn reduction, 500 customers @ $1,500 ARPC
Premium pricing: 20% premium, 500 customers
Discount rate: 15%
Time horizon: 36 months
```

**Output:** BUILD recommendation, 433% ROI, 4.5-month payback

### Example 2: Strategic Feature with Marginal ROI

**Input:**
```
Feature: Enterprise SSO Integration
Purpose: competitive (table stakes)
Urgency: medium
Build method: time_based (4 weeks, 2 engineers @ $21K/month)
Ongoing: $500/month (maintenance)
New revenue: None (existing customers require it)
Expansion: 10 enterprise customers @ $500/month increase
Retention: 1% churn reduction on 50 enterprise customers @ $5,000 ARPC
Premium: None
Discount rate: 15%
Time horizon: 36 months
```

**Output:** DEFER recommendation, 125% ROI (positive but below threshold), 14-month payback (above 12-month target), recommend building after higher-priority features

### Example 3: Negative ROI Feature

**Input:**
```
Feature: AI-Powered Email Composer
Purpose: efficiency
Urgency: low
Build method: direct_cost ($180K)
Ongoing: $8K/month (AI API costs)
New revenue: None
Expansion: None
Retention: Minimal (0.1% churn reduction, 200 customers @ $800 ARPC)
Premium: None
Productivity: 500 hours/month saved @ $100/hour (internal efficiency)
Discount rate: 15%
Time horizon: 36 months
```

**Output:** DON'T BUILD recommendation, 65% ROI (below threshold), 18-month payback (excessive), negative NPV after discount, recommend exploring cheaper alternatives or third-party tools

## Success Criteria

1. **Clear recommendation:** `BUILD`, `DEFER` or `DON'T BUILD`, with the reasoning shown
2. **Accurate calculations:** ROI, payback, NPV all calculated correctly
3. **Risk transparency:** Key assumptions and risks clearly documented
4. **Actionable insights:** Specific next steps provided
5. **Multi-dimensional value:** Revenue, retention, efficiency all captured
6. **Sensitivity awareness:** Confidence levels and risk factors identified
7. **CFO-ready output:** Professional report suitable for leadership review

## Agent Dispatch

Read `${CLAUDE_PLUGIN_ROOT}/agents/roi-calculator.md` and follow it in this session: it asks the person, and a subagent cannot.

**Process:**
1. Agent loads assumptions from `.product-finance/assumptions.json`
2. Agent collects feature context and build cost data
3. Agent uses skills: cost-estimation, revenue-projection, npv-analysis
4. Agent calculates ROI metrics and payback period
5. Agent generates a `BUILD`, `DON'T BUILD` or `DEFER` recommendation

**Skills Used:**
- `cost-estimation` - Convert dev effort to fully-loaded costs (story points, FTE, time-based)
- `revenue-projection` - Model new revenue, expansion, retention, and premium pricing impact
- `npv-analysis` - Net present value calculation with configurable discount rate
- `payback-calculation` - Determine months to break-even on investment
- `roi-recommendation` - Generate a `BUILD`, `DEFER` or `DON'T BUILD` decision with the reasoning shown

**Output:**
- `.product-finance/feature-roi-{feature-name}.json` - Structured ROI analysis
- `.product-finance/reports/feature-roi-{feature-name}-YYYY-MM-DD.md` - Executive report
- Console summary with recommendation and key metrics

**User Interaction:** Medium (provides feature details, confirms cost estimates, reviews projections)

---

## References

- **Framework:** `BRAINSTORMING.md` - ROI methodology and decision framework
- **Assumptions Schema:** `templates/assumptions.json` - Baseline data structure
- **Integration:** Other product-finance commands for holistic analysis
- **Benchmarks:** Industry-standard ROI thresholds and payback targets

---

**Financial Intelligence as Code** - Make feature prioritization defensible, measurable, and strategic.
