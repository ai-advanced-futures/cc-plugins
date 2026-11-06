---
description: Launch AI Economics Calculator to analyze AI costs, value attribution, and ROI with CFO-ready reporting
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# AI Economics Calculator Command

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `uv run python`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because only the plugin's own scripts are tested.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them".

## Every run

0. **Read the start time and the version** — run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py now` on its own and keep its output as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. Never type a time yourself, because a typed time is a guess and not the time of the run. The result file needs both.
1. Do the work the rest of this file describes.
2. **Write the result file** — Read `${CLAUDE_PLUGIN_ROOT}/agents/ai-economist.md` with the Read tool and follow its `## Result file` section, in every run.

## Purpose

The AI Economics Calculator is the **critical differentiator** for the Product Finance plugin. It enables teams to quantify AI investments with defensible ROI calculations, track AI costs across providers/models, attribute business value to AI capabilities, and identify cost optimization opportunities.

This command produces CFO-ready reports that justify AI investments with clear, data-driven analysis.

## When to Use

- **Before building AI features:** Estimate AI costs and projected ROI to justify investment
- **After launching AI features:** Measure actual AI costs and value attribution
- **Monthly/quarterly reviews:** Track AI economics trends and optimize spending
- **Board presentations:** Provide evidence-based AI ROI analysis
- **Cost optimization:** Identify opportunities to reduce AI spending
- **Pricing decisions:** Understand AI cost structure to inform pricing strategy
- **Vendor selection:** Compare AI provider costs and ROI

## What It Does

1. **Collects AI cost data** across all dimensions:
   - API costs by provider/model
   - Infrastructure costs (compute, storage, vector databases)
   - Development costs (AI engineering team)
   - Per-interaction, per-user, and percentage-of-revenue metrics

2. **Collects AI value data** across multiple attribution dimensions:
   - AI-enabled revenue (revenue from AI-powered features)
   - Premium pricing capture (price premium for AI capabilities)
   - Productivity multiplier (time saved × fully-loaded employee cost)
   - Retention impact (churn reduction from AI features)
   - Expansion revenue (upsell/cross-sell driven by AI)
   - Time-to-value acceleration

3. **Calculates comprehensive AI ROI:**
   - AI ROI percentage: `(AI Value - AI Costs) / AI Costs × 100`
   - AI ROI ratio: `AI Value / AI Costs`
   - Net AI value (annual)
   - Break-even analysis
   - Payback period

4. **Generates CFO-ready report** with:
   - Executive summary with key metrics
   - AI cost breakdown by provider/model
   - AI value attribution across dimensions
   - ROI calculation with clear methodology
   - Cost optimization recommendations
   - Strategic recommendations

5. **Saves results** to `.product-finance/ai-economics.json` for tracking over time

## Command Behavior

### Two Analysis Modes

**Mode 1: New AI Feature Analysis (Projections)**
- Estimate AI costs for planned feature
- Project AI value based on assumptions
- Calculate projected ROI to justify investment

**Mode 2: Existing Product Analysis (Actuals)**
- Analyze actual AI costs from production data
- Measure real AI value attribution
- Calculate actual ROI and identify optimizations

The command automatically detects which mode based on data availability.

## Question Flow

### Phase 1: Analysis Context

**Question** (AskUserQuestion [q: ai_product]): "Which AI product or feature is this analysis for?"
- **Type:** text

**Question** (AskUserQuestion [q: analysis_subject]): "What are you analyzing?"

**Options:**
- `new_feature` - New AI feature planning (projections)
- `existing_product` - Existing product with AI (actuals)
- `existing_feature` - Specific AI feature analysis

**Follow-up** (AskUserQuestion [q: analysis_period]): "What time period for this analysis?"

**Options:**
- `1_month` - 1 month (default)
- `3_months` - 3 months (quarterly)
- `6_months` - 6 months (biannual)
- `12_months` - 12 months (annual)

**Why we need this:** Determines whether to use estimates or actuals, and sets the time horizon for calculations.

### Phase 2: AI Cost Data Collection

**Introduction:**
```
AI Cost Tracking
================
We'll collect AI costs across three categories:
1. API/LLM costs (OpenAI, Anthropic, etc.)
2. Infrastructure costs (compute, storage, vector DBs)
3. Development costs (AI engineering team)

Let's start with the most significant cost: API/LLM usage.
```

#### 2a. API/LLM Costs

**Question** (AskUserQuestion [q: total_ai_api_cost]): "What is your total AI API/LLM cost for the whole analysis period (`analysis_period`)?"
- **Type:** number
- **Guidance:** "Include all costs from OpenAI, Anthropic, Google, AWS Bedrock, etc."
- **Example:** "$50,000 for 1 month"

**Question** (AskUserQuestion [q: ai_interactions]): "How many AI interactions/API calls during this period?"
- **Type:** integer
- **Guidance:** "Total number of API calls across all models and providers"
- **Example:** "1,000,000 interactions"

**Question** (AskUserQuestion [q: active_users]): "How many active users during this period?"
- **Type:** integer
- **Guidance:** "Users who used AI features at least once"
- **Example:** "5,000 active users"

**Question** (AskUserQuestion [q: provider_breakdown]): "Do you have a breakdown by provider/model?" (yes/no)

**If yes:**
- **Question** (AskUserQuestion [q: providers]): "How many different providers/models?"
- **Type:** integer (1-10)

For each provider/model:
- **Question** (AskUserQuestion [q: providers]): "Provider/model name?" (e.g., "OpenAI GPT-4", "Anthropic Claude Sonnet")
- **Question** (AskUserQuestion [q: providers]): "Cost for this provider/model?"
- **Type:** number

**Auto-calculate:**
- Cost per interaction: `Total AI Cost / Total Interactions`
- Cost per user per month: `Total AI Cost / Active Users / Period Months`

#### 2b. Infrastructure Costs (Optional but Recommended)

**Question** (AskUserQuestion [q: has_infrastructure_costs]): "Do you have AI infrastructure costs beyond API calls?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: infrastructure_monthly_cost]): "Monthly infrastructure costs?"
- **Categories:**
  - Compute costs (GPUs, specialized hardware): number
  - Storage costs (model storage, training data): number
  - Vector database costs (embeddings, RAG): number
  - Caching infrastructure: number
  - Monitoring/observability: number

**Auto-calculate:** Total infrastructure costs

#### 2c. Development Costs (Optional)

**Question** (AskUserQuestion [q: include_dev_costs]): "Do you want to include AI development costs?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: ai_engineers]): "How many engineers dedicated to AI features?"
- **Type:** number

**Question** (AskUserQuestion [q: ai_engineer_annual_cost]): "Average fully-loaded annual cost per AI engineer?"
- **Type:** number
- **Guidance:** "Base salary × 1.7 to 2.0. Typical range: $180K-$350K"
- **Default:** $220,000

**Auto-calculate:** Monthly AI development costs

**Question** (AskUserQuestion [q: training_costs]): "Any training data or fine-tuning costs?"
- **Type:** number (optional)

#### 2d. Revenue Context

**Question** (AskUserQuestion [q: total_revenue]): "What was your total revenue for this period?"
- **Type:** number
- **Guidance:** "Total company/product revenue (not just AI-enabled)"
- **Why:** "Needed to calculate AI costs as % of revenue"

**Auto-calculate:**
- Monthly total AI cost = `total_ai_api_cost` / the months of `analysis_period` + `infrastructure_monthly_cost`; development cost is reported apart and is not added in, because the monthly figure covers running cost only.
- AI costs as % of revenue
- Annualized AI costs

**Health Assessment:**
- Excellent: AI costs < 5% of revenue
- Good: AI costs 5-10% of revenue
- Warning: AI costs 10-20% of revenue
- Critical: AI costs > 20% of revenue

### Phase 3: AI Value Attribution

**Introduction:**
```
AI Value Attribution
====================
Now let's quantify the value AI delivers to your business.
We'll track value across multiple dimensions:
- Direct revenue from AI features
- Premium pricing capture
- Productivity gains (time savings)
- Retention improvements
- Expansion revenue
- Time-to-value acceleration

The more dimensions we capture, the stronger your ROI case.
```

#### 3a. AI-Enabled Revenue (Required)

**Question** (AskUserQuestion [q: ai_revenue]): "What revenue is enabled by AI features?"
- **Type:** number
- **Guidance:** "Revenue specifically from customers/plans with AI capabilities"
- **Example:** "If AI is a premium tier, revenue from that tier"

**Question** (AskUserQuestion [q: non_ai_revenue]): "What is your non-AI revenue for comparison?"
- **Type:** number
- **Guidance:** "Revenue from non-AI features/tiers for baseline comparison"

**Auto-calculate:**
- Total revenue: `AI Revenue + Non-AI Revenue`
- AI revenue percentage: `(AI Revenue / Total Revenue) × 100`

**Question** (AskUserQuestion [q: accept_before_after]): "There is no controlled data for a feature. Use a before/after comparison instead? The confidence is lower." (yes/no)
- **Ask only when:** a feature has no controlled data
- **Default:** yes. Say in the report that the confidence is low.

#### 3b. Premium Pricing (Optional)

**Question** (AskUserQuestion [q: charges_ai_premium]): "Do you charge a premium for AI capabilities?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: ai_premium_percent]): "What is the pricing premium percentage?"
- **Type:** number (0-1000)
- **Guidance:** "How much more do customers pay for AI? (e.g., 20% = AI tier is 20% more expensive)"
- **Example:** "AI Pro tier is $49/mo vs. Standard tier at $39/mo = 25.6% premium"

**Auto-calculate:**
- Baseline revenue without premium: `AI Revenue / (1 + Premium % / 100)`
- Premium pricing value: `AI Revenue - Baseline Revenue`

#### 3c. Productivity Multiplier (Optional but Recommended)

**Question** (AskUserQuestion [q: saves_time]): "Does AI save time for your users or team?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: hours_saved_per_month]): "How many hours saved per month through AI automation?"
- **Type:** number
- **Guidance:** "Total hours saved across all users/employees"
- **Example:** "If 100 users each save 10 hours/month = 1,000 hours"

**Question** (AskUserQuestion [q: cost_per_hour]): "What is the fully-loaded cost per employee hour?"
- **Type:** number
- **Guidance:** "Annual salary × 1.7 / 2080 hours"
- **Example:** "$150K salary → $122/hour fully-loaded"
- **Default:** $100/hour

**Auto-calculate:**
- Productivity value: `Hours Saved × Cost per Hour`
- Monthly and annual productivity value

#### 3d. Retention Impact (Optional but Recommended)

**Question** (AskUserQuestion [q: ai_improves_retention]): "Does AI improve customer retention?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: churn_with_ai]): "What is the churn rate for customers WITH AI features?"
- **Type:** number (0-100)
- **Guidance:** "Monthly churn % for AI-enabled customers"

**Question** (AskUserQuestion [q: churn_without_ai]): "What is the churn rate for customers WITHOUT AI features?"
- **Type:** number (0-100)
- **Guidance:** "Monthly churn % for non-AI customers (baseline)"

**Auto-calculate:**
- Churn reduction: `Non-AI Churn % - AI Churn %`
- Retention value: `AI Revenue × (Churn Reduction / 100)` (annual)
- **Why:** Reduced churn = retained revenue that would have been lost

#### 3e. Expansion Revenue (Optional)

**Question** (AskUserQuestion [q: ai_drives_expansion]): "Has AI driven expansion revenue?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: ai_expansion_revenue]): "How much expansion revenue is attributable to AI adoption?"
- **Type:** number
- **Guidance:** "Upsell/cross-sell driven by customers adopting AI features"
- **Example:** "Customers upgrade to higher tiers for more AI capacity"

#### 3f. Time-to-Value Acceleration (Optional)

**Question** (AskUserQuestion [q: reduces_time_to_value]): "Does AI reduce time-to-value for customers?" (yes/no)

**If yes:**

**Question** (AskUserQuestion [q: days_faster]): "How many days faster do customers achieve value with AI?"
- **Type:** number
- **Guidance:** "Time-to-first-value reduction (e.g., onboarding, setup, first win)"
- **Example:** "AI reduces onboarding from 30 days to 15 days = 15 days saved"

**Auto-calculate:**
- Months accelerated: `Days Saved / 30`
- Acceleration value: `(AI Revenue / 12) × Months Accelerated`
- **Why:** Faster value recognition = earlier revenue capture

### Phase 4: Calculate and Report

**Processing:**
1. Call `scripts/ai_roi_calculator.py` with collected data
2. Generate the AI ROI analysis: cost, value, ROI and break-even
3. Create CFO-ready report (markdown)
4. Save structured results (JSON)

**Output files:**
- `.product-finance/ai-economics.json` - Structured data
- `.product-finance/reports/ai-economics-report-YYYY-MM-DD.md` - CFO report

## Output

### File 1: `.product-finance/ai-economics.json`

Structured data following `templates/ai-economics.json` schema:

```json
{
  "ai_costs": {
    "api_costs": {
      "total_monthly": 50000,
      "cost_per_api_call": 0.05,
      "total_api_calls_monthly": 1000000,
      "by_model": [
        {
          "model_name": "gpt-4",
          "provider": "OpenAI",
          "monthly_cost": 30000,
          "api_calls": 500000,
          "average_cost_per_call": 0.06
        },
        {
          "model_name": "claude-sonnet-4",
          "provider": "Anthropic",
          "monthly_cost": 20000,
          "api_calls": 500000,
          "average_cost_per_call": 0.04
        }
      ]
    },
    "infrastructure_costs": {
      "compute_monthly": 5000,
      "storage_monthly": 1000,
      "vector_database_monthly": 2000,
      "caching_monthly": 500,
      "monitoring_monthly": 500
    },
    "development_costs": {
      "ai_engineering_headcount": 3,
      "monthly_personnel_cost": 55000
    },
    "per_user_costs": {
      "cost_per_user_monthly": 10.0,
      "cost_per_interaction": 0.05
    },
    "total_ai_costs": {
      "monthly": 59000,
      "annual": 708000,
      "as_pct_revenue": 11.8
    }
  },
  "ai_value": {
    "revenue_impact": {
      "ai_enabled_revenue_monthly": 300000,
      "ai_enabled_arr": 3600000,
      "revenue_premium_pct": 25
    },
    "retention_impact": {
      "churn_reduction_pct": 2.0,
      "nrr_improvement_pct": 5.0
    },
    "productivity_gains": {
      "time_saved_hours_monthly": 1000,
      "productivity_multiplier": 1.5,
      "value_of_time_saved": 100000
    },
    "total_ai_value": {
      "monthly": 350000,
      "annual": 4200000
    }
  },
  "ai_roi": {
    "roi": 4.93,
    "payback_period_months": 2.4,
    "net_value_monthly": 291000,
    "net_value_annual": 3492000
  },
  "usage_patterns": {
    "interactions_monthly": 1000000,
    "interactions_per_user_monthly": 200,
    "active_ai_users": 5000,
    "ai_adoption_rate_pct": 62.5
  },
  "optimization_opportunities": {
    "cost_optimization": [
      {
        "opportunity": "Implement aggressive caching for repeated queries",
        "potential_savings_monthly": 8000,
        "implementation_effort": "medium",
        "priority": "high"
      },
      {
        "opportunity": "Route simple queries to Claude Haiku instead of GPT-4",
        "potential_savings_monthly": 12000,
        "implementation_effort": "low",
        "priority": "high"
      }
    ],
    "strategic_recommendations": [
      "AI costs are 11.8% of revenue - within healthy range (5-15%)",
      "Excellent ROI of 493% justifies continued AI investment",
      "Consider expanding AI features based on strong value attribution"
    ]
  },
  "metadata": {
    "analysis_date": "2026-01-23T10:00:00Z",
    "period_start": "2026-01-01",
    "period_end": "2026-01-31",
    "methodology": "Multi-dimensional value attribution with provider cost breakdown",
    "confidence_level": "high"
  }
}
```

### File 2: `.product-finance/reports/ai-economics-report-YYYY-MM-DD.md`

CFO-ready markdown report:

```markdown
# AI Economics Analysis

**Overall Health:** GOOD

## Executive Summary

- **AI ROI:** 493.0% (4.93x return)
- **Net Annual Value:** $3,492,000
- **Break-Even Period:** 2.4 months
- **AI Cost as % of Revenue:** 11.8%
- **AI-Enabled Revenue:** $300,000 (60.0% of total)

## AI Cost Analysis

**Health Status:** GOOD

- **Total Annual AI Cost:** $708,000
- **Cost per Interaction:** $0.0500
- **Cost per User per Month:** $10.00
- **AI Cost % of Revenue:** 11.80%

### Provider Cost Breakdown

- **OpenAI:**
  - Cost: $30,000 (60.0% of total)
  - Cost per interaction: $0.0600
- **Anthropic:**
  - Cost: $20,000 (40.0% of total)
  - Cost per interaction: $0.0400

### Cost Optimization Opportunities

1. Implement aggressive caching strategy for repeated queries
2. Optimize prompts to reduce token usage
3. Route simple queries to more cost-efficient models (Haiku, GPT-3.5)
4. Consider usage-based pricing to pass costs proportionally
5. Monitor and set rate limits per user to prevent abuse

## AI Value Attribution

**Health Status:** EXCELLENT

- **Total AI Value (Annual):** $4,200,000
- **AI-Enabled Revenue:** $300,000
- **AI Revenue %:** 60.0% of total revenue

### Value Sources

- **AI Enabled Revenue:** $3,600,000 (85.7% of total)
- **Premium Pricing Value:** $600,000 (14.3% of total)
- **Productivity Value:** $100,000 (2.4% of total)

**Productivity Multiplier:** $100,000 in time savings value

**Retention Impact:** $60,000 in churn reduction value

## ROI Framework

```
AI Value (Annual):     $    4,200,000
AI Costs (Annual):   - $      708,000
                       ==============================
Net AI Value:          $    3,492,000

AI ROI = (Value - Cost) / Cost × 100
AI ROI = 493.0%
Return Ratio = 4.93x
```

## Break-Even Analysis

- **Break-Even Period:** 2.4 months
- **Monthly Net Value:** $291,000

## Recommendations

1. Excellent AI ROI (>200%): Strong business case. Consider expanding AI features and increasing investment.
2. Document AI value attribution methodology for CFO and board presentations.
3. Fast payback period: Excellent. Use this as evidence to justify additional AI investments.
4. Track AI ROI monthly and set quarterly OKRs for improvement.
5. Implement A/B testing to measure incremental value of AI features vs. non-AI alternatives.
6. Create AI economics dashboard for real-time monitoring of costs, value, and ROI trends.

---
*AI Economics Analysis - Product Finance Plugin*
*Based on industry-standard AI cost tracking and value attribution frameworks*
```

### Console Output

**Summary displayed to user:**

```
AI Economics Analysis Complete!
================================

Executive Summary
-----------------
AI ROI: 493.0% (4.93x return on investment)
Net Annual Value: $3,492,000
Break-Even Period: 2.4 months
Overall Health: GOOD

AI Cost Analysis
----------------
Total Annual AI Costs: $708,000
Cost per Interaction: $0.0500
Cost per User/Month: $10.00
AI Cost as % of Revenue: 11.8% (GOOD)

Provider Breakdown:
  - OpenAI: $30,000/month (60% of costs)
  - Anthropic: $20,000/month (40% of costs)

AI Value Attribution
--------------------
Total Annual Value: $4,200,000
AI-Enabled Revenue: $3,600,000 (60% of total revenue)
Productivity Value: $100,000
Retention Value: $60,000

Top 3 Recommendations
---------------------
1. Excellent ROI justifies expanding AI investment
2. Fast payback (2.4 months) - use as board evidence
3. Implement caching to reduce costs further

Files Generated
---------------
✓ .product-finance/ai-economics.json
✓ .product-finance/reports/ai-economics-report-2026-01-23.md

Next Steps
----------
- Share report with CFO/finance team
- Track AI ROI monthly for trend analysis
- Implement top cost optimization opportunities
- Use ROI data to justify next AI feature investments
- Run `/product-finance:health-check` for overall financial health
```

## Implementation Notes

### For Claude Code Agent

**Interactive Data Collection:**
- Use progressive disclosure - collect required data first, optional later
- Explain WHY each metric matters (business context)
- Provide examples and typical ranges
- Allow "skip" for optional metrics
- Pre-fill data from `.product-finance/assumptions.json` if available

**Validation:**
- Ensure all costs are positive numbers
- Validate percentages are 0-100
- Warn if AI costs exceed 20% of revenue (critical threshold)
- Warn if insufficient value dimensions captured (suggest tracking more)
- Ensure total revenue = AI revenue + non-AI revenue

**Python Script Integration:**
1. Prepare input JSON matching `AIROIInput` schema from `ai_roi_calculator.py`
2. Write the input JSON with the Write tool to `<run folder>/ai-roi-input.json`, where the run folder is `.product-finance/<run_id>/` in a plugin run and `.product-finance/` in a person's run, then call the script as one command: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ai_roi_calculator.py --input <run folder>/ai-roi-input.json --format json`. The script needs `pydantic`; when the command fails, work the figures out with the formulas of this file, with no code at all, and end each result's `method` with: Computed by the model from the formula stated in the command; no script ran.
3. Parse JSON output
4. Generate markdown report using `--format markdown`
5. Save both formats under `.product-finance/`

**Error Handling:**
- If script fails, provide clear error message
- Validate input data before calling script
- If missing required data, prompt for it
- If calculation errors, show intermediate values for debugging

**Data Persistence:**
- Save to `.product-finance/ai-economics.json` (structured)
- Save report to `.product-finance/reports/ai-economics-report-YYYY-MM-DD.md`
- Update `.product-finance/assumptions.json` with AI cost/value data
- Maintain history for trend analysis

**Integration with assumptions.json:**
- Read existing assumptions if available
- Pre-populate revenue, user counts, team costs
- Update assumptions with new AI economics data
- Maintain data consistency across files

### Health Status Logic

**Overall Health Assessment:**
- **EXCELLENT:** AI ROI > 200% AND AI costs < 5% of revenue
- **GOOD:** AI ROI > 100% AND AI costs < 15% of revenue
- **Warning:** AI ROI > 0% OR AI costs 15-20% of revenue
- **Critical:** AI ROI ≤ 0% OR AI costs > 20% of revenue

**Cost Health:**
- **EXCELLENT:** AI costs < 5% of revenue
- **GOOD:** AI costs 5-10% of revenue
- **Warning:** AI costs 10-20% of revenue
- **Critical:** AI costs > 20% of revenue

**Value Health:**
- **EXCELLENT:** AI revenue > 50% AND 3+ value sources
- **GOOD:** AI revenue > 30% AND 2+ value sources
- **Warning:** AI revenue > 10% OR 1+ value source
- **Critical:** AI revenue < 10% AND single/no value source

### Optimization Recommendations

**Automatic recommendations based on thresholds:**

**High cost per interaction (>$0.10):**
- Implement aggressive caching
- Optimize prompts to reduce tokens
- Consider prompt compression

**Moderate cost per interaction ($0.05-$0.10):**
- Implement semantic caching
- Review prompt efficiency

**AI costs > 15% of revenue:**
- Evaluate model selection (cheaper models for non-critical)
- Implement tiered AI features (basic vs. premium)
- Consider usage-based pricing

**AI costs 10-15% of revenue:**
- Consider usage-based pricing to pass costs proportionally

**Multi-provider setup:**
- Optimize routing logic for cost efficiency
- Benchmark provider cost/performance

**General recommendations (always include):**
- Response caching with TTL
- Rate limiting per user
- Batch API calls where possible
- Monitor for abuse/unusual patterns

**Low AI costs (<5%):**
- Focus on maximizing value vs. cost cutting
- Consider expanding AI capabilities

### ROI Recommendations

**Excellent ROI (>200%):**
- Expand AI features and investment
- Document methodology for board
- Use as evidence for additional funding

**Positive ROI (100-200%):**
- Continue current strategy with optimizations
- Highlight payback period in communications

**Marginal ROI (0-100%):**
- Need to improve value capture or cost efficiency
- Focus on increasing AI-enabled revenue
- Reduce churn before expanding

**Negative ROI (<0%):**
- Critical: Review AI strategy urgently
- Consider reducing scope, increasing pricing, or improving efficiency

### Value Attribution Guidance

**Single value source:**
- Recommend diversifying attribution
- Track productivity, retention, expansion

**Low AI revenue percentage (<20%):**
- Increase AI feature adoption
- Develop new AI capabilities
- Market AI value proposition better

**Strong multi-dimensional value:**
- Document for CFO/board presentations
- Use as competitive differentiator
- Justify pricing premium

## Examples

### Example 1: New AI Feature (Projections)

**Scenario:** Planning to add AI-powered analytics feature

**Input:**
```
Analysis type: new_feature
Period: 3_months
Total AI cost (projected): $15,000
AI interactions (projected): 300,000
Active users (projected): 1,000
Provider breakdown: Yes
  - OpenAI GPT-4: $10,000
  - Anthropic Claude: $5,000
Infrastructure costs: No
Development costs: Yes
  - AI engineers: 1
  - Cost per engineer: $200,000/year
Total revenue (projected): $150,000
AI-enabled revenue: $75,000
Non-AI revenue: $75,000
Premium pricing: Yes (20%)
Productivity multiplier: Yes
  - Hours saved: 500
  - Cost per hour: $120
Retention: No
Expansion: No
TTV acceleration: Yes (15 days)
```

**Output:** ROI analysis showing projected 250% ROI, justifying feature investment

### Example 2: Existing SaaS Product with AI

**Scenario:** Quarterly review of AI economics

**Input:**
```
Analysis type: existing_product
Period: 3_months
Total AI cost: $180,000
AI interactions: 5,000,000
Active users: 10,000
Provider breakdown: Yes
  - OpenAI: $100,000
  - Anthropic: $50,000
  - AWS Bedrock: $30,000
Infrastructure: Yes
  - Compute: $15,000/month
  - Vector DB: $8,000/month
  - Caching: $2,000/month
Development: Yes
  - Engineers: 4
  - Cost: $220,000/year avg
Total revenue: $2,000,000
AI-enabled revenue: $1,200,000
Non-AI revenue: $800,000
Premium pricing: Yes (30%)
Productivity: Yes
  - Hours saved: 5,000
  - Cost per hour: $100
Retention: Yes
  - AI churn: 2%
  - Non-AI churn: 5%
Expansion: Yes ($150,000)
TTV acceleration: Yes (30 days)
```

**Output:** Comprehensive quarterly report with optimization opportunities

### Example 3: AI-First Startup

**Scenario:** Investor presentation - prove AI ROI

**Input:**
```
Analysis type: existing_product
Period: 6_months
Total AI cost: $300,000
AI interactions: 10,000,000
Active users: 8,000
Provider breakdown: Yes
  - Anthropic Claude: $200,000
  - OpenAI: $100,000
Infrastructure: Yes
  - All categories: $25,000/month
Development: Yes
  - Engineers: 6
  - Cost: $230,000/year avg
Total revenue: $2,500,000
AI-enabled revenue: $2,500,000 (100% - AI-first product)
Non-AI revenue: $0
Premium pricing: No (all AI)
Productivity: Yes
  - Hours saved: 10,000
  - Cost per hour: $125
Retention: Yes
  - AI churn: 1.5%
  - Non-AI churn: N/A (benchmark: 4%)
Expansion: Yes ($400,000)
TTV acceleration: Yes (45 days)
```

**Output:** Investor-grade report showing AI as core business driver with 350%+ ROI

## Success Criteria

1. **Accurate ROI calculation:** Python script produces defensible numbers
2. **CFO-ready output:** Report is clear, professional, presentation-ready
3. **Actionable insights:** Specific, prioritized optimization recommendations
4. **Data persistence:** Results saved for tracking trends over time
5. **Complete attribution:** Multiple value dimensions captured and quantified
6. **Cost transparency:** Clear breakdown by provider/model for optimization
7. **Benchmark context:** Health status provides industry context

## References

- **Calculation Script:** `scripts/ai_roi_calculator.py` - Core ROI logic
- **Output Schema:** `templates/ai-economics.json` - Structured data format
- **Framework:** `BRAINSTORMING.md` - AI Economics Calculator methodology
- **Methodology:** Industry-standard AI cost tracking and value attribution

## Agent Dispatch

Read `${CLAUDE_PLUGIN_ROOT}/agents/ai-economist.md` and follow it in this session: it asks the person, and a subagent cannot.

**Process:**
1. Agent loads assumptions from `.product-finance/assumptions.json`
2. Agent collects AI cost data (API costs, infrastructure, development)
3. Agent uses skills: ai-cost-tracking, value-attribution, roi-calculation
4. Agent identifies cost optimization opportunities
5. Agent generates CFO-ready AI economics report

**Skills Used:**
- `ai-cost-tracking` - Track API costs by provider/model, infrastructure costs, development costs
- `value-attribution` - Attribute business value to AI (revenue, productivity, retention, premium pricing)
- `roi-calculation` - Calculate AI ROI, payback period, and net value
- `cost-optimization` - Identify opportunities to reduce AI costs (caching, model routing, batching)
- `benchmark-assessment` - Evaluate AI cost health against industry standards

**Output:**
- `.product-finance/ai-economics.json` - Structured AI economics data
- `.product-finance/reports/ai-economics-report-YYYY-MM-DD.md` - CFO-ready report
- Console summary with ROI and optimization recommendations

**User Interaction:** Medium (provides AI cost data, confirms value attribution, reviews recommendations)

---

## Integration with Other Commands

**Data Sources:**
- Read from `.product-finance/assumptions.json` for revenue, users, costs
- Update assumptions with AI-specific data
- Store historical data for trend analysis

**Downstream Commands:**
- `/product-finance:health-check` includes AI ROI in overall health
- `/product-finance:unit-economics` factors in AI costs for CAC/LTV
- `/product-finance:feature-roi` uses AI economics for feature prioritization

**Upstream Commands:**
- `/product-finance:setup` collects baseline assumptions
- `/product-finance:discover` provides market sizing context

---

**Critical Differentiator:** This AI Economics Calculator enables CFOs to make data-driven decisions about AI investments with clear, defensible ROI analysis. It's not just tracking costs - it's proving business value.

**Financial Intelligence as Code** - Make AI investments defensible, measurable, and optimizable.
