---
description: Guided onboarding to collect baseline financial assumptions for product finance analysis
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_read.py *), Edit(/.product-finance/**), Read(/${CLAUDE_PLUGIN_ROOT}/templates/auto-config.template.json), Read(/${CLAUDE_PLUGIN_ROOT}/commands/discover.md), Read(/${CLAUDE_PLUGIN_ROOT}/templates/assumptions.json), Read(/${CLAUDE_PLUGIN_ROOT}/docs/KPI_DEFINITIONS.md)
---

Run only this plugin's own scripts, as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py ...`, one command per Bash call. The grant of this command covers only those scripts, so run no inline code in any language, and write every file with the Write tool.

## Auto-config

Before you ask the person any question, check whether `.product-finance/auto-config.json` exists and has `"enabled": true`. When it does, take each answer from its `question_keys` and ask nothing.

**To use auto-config:** Copy `${CLAUDE_PLUGIN_ROOT}/templates/auto-config.template.json` to
`.product-finance/auto-config.json`, set `"enabled": true`, and change `question_keys` to your values.

---

# Product Finance Setup Command

## Purpose

The setup command collects baseline financial assumptions that serve as the foundation for all subsequent financial analyses. This is typically the first command you'll run when using the Product Finance plugin.

## When to Use

- First time using the Product Finance plugin
- Starting financial analysis for a new product or feature
- Establishing financial baseline for an existing product
- Updating assumptions when business model changes
- Resetting assumptions for a new planning cycle

## What It Does

1. Guides you through interactive data collection using AskUserQuestion
2. Collects essential financial assumptions across key categories
3. Validates inputs for reasonableness
4. Stores results in `.product-finance/assumptions.json`
5. Creates directory structure if it doesn't exist
6. Provides clear guidance on what data is needed and why

## Command Behavior

### Hybrid Approach: Essential Now, Refine Later

The setup command follows a **progressive disclosure** pattern:
- Collects **essential baseline assumptions** upfront (pricing model, basic costs)
- Allows placeholder/estimate values for unknowns
- Supports refinement through subsequent runs
- Other commands prompt for specific data they need

**Philosophy:** Get started quickly with reasonable estimates, improve accuracy as better data becomes available.

## Data Collection Flow

### Phase 1: Pricing Model (Required)

**Question:** "What is your pricing model?"

**Options:**
- `per_seat` - Per-user/per-seat subscription (e.g., $25/user/month)
- `usage_based` - Consumption-based pricing (e.g., $0.10/API call)
- `tiered` - Multiple pricing tiers with feature differentiation
- `freemium` - Free tier + paid upgrades
- `hybrid` - Combination of multiple models

**Why we need this:** Pricing model determines revenue projections, CAC payback calculations, and unit economics structure.

**Follow-up questions based on selection:**

#### For `per_seat`:
- "What is the price per seat per month?" (number)
- "Do you offer annual discounts? If yes, what percentage?" (number, 0-100)
- "What is your average seats per customer?" (number)

#### For `usage_based`:
- "What is the unit of measurement?" (e.g., "API call", "GB storage", "transaction")
- "What is the price per unit?" (number)
- "Are there any included units in the base subscription?" (number)

#### For `tiered`:
- "How many pricing tiers do you have?" (number, 1-10)
- For each tier:
  - "Tier name?" (e.g., "Starter", "Professional", "Enterprise")
  - "Monthly price?" (number)
  - "Annual price (if different)?" (number, optional)
  - "Key differentiator?" (brief description)

#### For `freemium`:
- "What percentage of free users convert to paid?" (number, 0-100)
- "What is the paid tier monthly price?" (number)
- "Average time to conversion (days)?" (number)

#### For `hybrid`:
- "Describe your hybrid model" (text)
- "What is the base subscription price?" (number)
- "What usage components have additional charges?" (text)

### Phase 2: Cost Structure (Required)

**Question:** "What are your primary cost categories?"

Collect **fully-loaded costs** (salary + benefits + overhead = typically 1.5-2x base salary).

#### 2a. Cost of Goods Sold (COGS)

**Guidance:** Direct costs to deliver service to customers. Target gross margin for SaaS: 70%+.

**Questions:**
- "Monthly hosting/infrastructure cost per user?" (number, can be estimate)
  - *Why: Determines gross margin and scalability*
- "Monthly AI/LLM cost per user?" (number, 0 if not applicable)
  - *Why: AI costs are significant for AI-powered products*
- "Monthly third-party service costs per user?" (number)
  - *Why: APIs, data providers, payment processing*
- "Monthly customer support cost per user?" (number)
  - *Why: Support is often a direct cost of servicing customers*

**Auto-calculate:** Total COGS per user per month

#### 2b. Research & Development (R&D)

**Questions:**
- "How many people on your R&D team?" (number)
- "What is the average fully-loaded annual cost per R&D team member?" (number)
  - *Guidance: Fully-loaded = base salary × 1.5 to 2.0*
  - *Examples: Junior Engineer ~$150K, Senior Engineer ~$250K, Staff Engineer ~$350K*

**Auto-calculate:** Total monthly R&D costs

#### 2c. Sales & Marketing

**Questions:**
- "Do you have a sales team?" (yes/no)

**If yes:**
- "How many Account Executives (AEs)?" (number)
- "Average fully-loaded annual cost per AE?" (number)
  - *Guidance: $150K-$300K typical range*
- "How many Sales Development Reps (SDRs)?" (number)
- "Average fully-loaded annual cost per SDR?" (number)
  - *Guidance: $80K-$150K typical range*

**For all:**
- "Monthly marketing budget?" (number)
- "What is your estimated Customer Acquisition Cost (CAC)?" (number)
  - *Guidance: If unknown, we'll calculate from spend/new customers*

**Auto-calculate:** Total monthly Sales & Marketing costs

#### 2d. General & Administrative (G&A)

**Question:** "Monthly G&A overhead (rent, legal, finance, HR, etc.)?" (number)
- *Guidance: If unknown, estimate 15-20% of total costs*

### Phase 3: Current Metrics (If Existing Product)

**Question:** "Is this for an existing product or a new product?"

**Options:**
- `existing` - Analyze current product
- `new` - Plan new product/feature
- `planning` - Pre-launch planning

#### If `existing`:

**Revenue Metrics:**
- "Current Monthly Recurring Revenue (MRR)?" (number)
- "Current Annual Recurring Revenue (ARR)?" (number)
  - *Note: ARR typically ≈ MRR × 12, but may differ with annual contracts*
- "Total paying customers?" (number)

**Customer Metrics:**
- "New customers last month?" (number)
- "Churned customers last month?" (number)
- "Monthly churn rate % (if known)?" (number, 0-100, optional)
- "Average customer lifetime (months)?" (number, optional)

#### If `new` or `planning`:

**Question:** "Do you have target metrics you're planning towards?"

**Target Metrics (all optional):**
- "Target ARR in first year?" (number)
- "Target customer count in first year?" (number)
- "Expected monthly churn rate %?" (number, 0-100)
  - *Guidance: 3-5% is typical for SMB SaaS, 1-2% for Enterprise*

### Phase 4: Market Sizing (Optional)

**Question:** "Do you have market sizing data?"

**Options:**
- `jtbd` - I've run the JTBD market discovery plugin
- `manual` - I'll provide market sizing manually
- `skip` - Skip for now (can add later)

#### If `jtbd`:
- Read the jtbd graph as **Person run** in `${CLAUDE_PLUGIN_ROOT}/commands/discover.md` says.
- On a `NO-JTBD:` line, show that line, and then ask this question again with only the options `manual` and `skip`:

  **Question:** "Do you have market sizing data?"

  Follow the option the person picks.
- Show each jtbd segment with its monthly willingness to pay, and ask the person to confirm each one.
- A confirmed segment becomes one of the person's own segments in `segments` of `.product-finance/assumptions.json`, and then the merge in **Person run** of `${CLAUDE_PLUGIN_ROOT}/commands/discover.md` applies.
- Store only the segment's `segment_name`: the merge sets its `willingness_to_pay` to 12 times the monthly value, and its `wtp_source` to the accepted file's path.
- Import no market size: jtbd gives none. TAM, SAM and SOM stay null, as with `skip`.

#### If `manual`:
- "Total Addressable Market (TAM) in USD?" (number)
- "Serviceable Addressable Market (SAM) in USD?" (number)
- "Serviceable Obtainable Market (SOM) in USD?" (number)
- "How many potential customers in your target market?" (number)

#### If `skip`:
- Store null values
- Can be populated by `/product-finance:discover` command later

### Phase 5: Team Structure (Optional but Recommended)

**Question:** "Would you like to provide detailed team structure for build cost estimation?"

**If yes:**

**Current Team:**
- "Engineering headcount?" (number)
- "Product management headcount?" (number)
- "Design headcount?" (number)

**Productivity Metrics:**
- "Average story points completed per sprint?" (number)
- "Sprint length in weeks?" (number, typically 1-2)
- "Estimated cost per story point?" (number)
  - *Guidance: (Total R&D monthly cost / story points per month)*

**If no:**
- Skip team details
- Use averages from R&D costs provided earlier

### Phase 6: Retention Assumptions (Optional but Recommended)

**Question:** "Would you like to set retention and growth assumptions?"

**If yes:**

**Retention:**
- "Target Gross Revenue Retention (GRR) %?" (number, 0-100)
  - *Guidance: 90%+ is healthy*
- "Target Net Revenue Retention (NRR) %?" (number, 0-100)
  - *Guidance: 110%+ is excellent (includes expansion)*
- "Expected expansion revenue as % of base?" (number, 0-100)
  - *Explanation: Upsell/cross-sell driving revenue growth from existing customers*

**Growth:**
- "Target ARR growth rate %?" (number)
  - *Guidance: Seed stage 100%+, Series A 50-100%, Series B 30-50%*
- "Average sales cycle length (days)?" (number)

**If no:**
- Use industry benchmarks as defaults

### Phase 7: Financial Targets (Optional)

**Question:** "Would you like to set specific financial health targets?"

**If yes:**

- "Target Rule of 40 score: 40, 50 or 60?" (default: 40)
  - *Explanation: 40 is Feld's rule (2015). 50 has no published benchmark: a bar you set. Vista (2026) calls 60 "an emerging aspiration, not a universal baseline".*
  - Store a chosen target as `targets.rule_of_40_target` in `.product-finance/assumptions.json`, written as a JSON integer (40, 50 or 60).
  - Pressing Enter at this question stores no target and removes any `targets.rule_of_40_target` already in the file, so runs report `(default)`. Typing 40 stores 40.
  - Tell the person: the health check and `rule_of_40.py --assumptions` use this target when a run gives none. A target given on a run wins.
  - Any answer other than 40, 50 or 60 is asked again once, with the three values. A second wrong answer stores no Rule of 40 target and removes any `targets.rule_of_40_target` already in the file, and the setup summary says `Rule of 40 target: not stored (<value> is not 40, 50 or 60); runs use 40.`
  - In automated mode, an auto answer (`target_rule_of_40`) that is not 40, 50 or 60 is not stored and removes any `targets.rule_of_40_target` already in the file, and the setup summary says `Rule of 40 target: not stored (<value> is not 40, 50 or 60); runs use 40.`
  - An automated run whose auto answers carry no `target_rule_of_40` stores no target and removes any `targets.rule_of_40_target` already in the file, so runs report `(default)`.
  - The setup summary's `Rule of 40 target:` line reports the target the next run will use: the stored target, or 40 when none is stored.
- "Target LTV:CAC ratio?" (number, default: 3.0)
  - *Guidance: 3:1 is minimum healthy, 5:1+ is excellent*
- "Target CAC payback period (months)?" (number, default: 12)
  - *Guidance: <12 months is excellent, 12-18 is acceptable*
- "Target gross margin %?" (number, default: 70)
  - *Guidance: 70%+ is typical for SaaS*
- "Target Magic Number?" (number, default: 0.75)
  - *Explanation: Sales efficiency metric, 0.75 or more is healthy*

**If no:**
- Use standard SaaS benchmarks as defaults
- Answering no to the targets question removes any `targets.rule_of_40_target` already in the file, so runs report `(default)`.

## Output

### File: `.product-finance/assumptions.json`

Creates/updates the assumptions file following the schema defined in `${CLAUDE_PLUGIN_ROOT}/templates/assumptions.json`.

**Location:** `.product-finance/assumptions.json` (relative to project root)

**Schema compliance:** Follows JSON schema from `${CLAUDE_PLUGIN_ROOT}/templates/assumptions.json`

**Structure:**
```json
{
  "pricing": { /* pricing model data */ },
  "costs": {
    "cogs": { /* COGS breakdown */ },
    "sales_marketing": { /* S&M costs */ },
    "rd": { /* R&D costs and team */ },
    "ga": { /* G&A overhead */ }
  },
  "market": { /* TAM/SAM/SOM, segments */ },
  "team": { /* headcount, productivity */ },
  "retention": { /* churn, expansion */ },
  "growth": { /* growth targets */ },
  "targets": { /* financial health targets */ },
  "metadata": {
    "created_at": "2026-01-23T10:00:00Z",
    "updated_at": "2026-01-23T10:00:00Z",
    "version": "1.0.0",
    "confidence_level": "medium",
    "source": "user-provided estimates",
    "notes": "Initial baseline assumptions"
  }
}
```

### File: `.product-finance/README.md` (if created new)

Creates a README explaining the directory structure and data files.

### Console Output

**Summary of collected assumptions:**
```
Product Finance Setup Complete!
================================

Pricing Model: Per-Seat
  - $29/user/month
  - 15% annual discount
  - Avg 5 seats per customer

Cost Structure:
  - COGS per user: $4.50/month (84% gross margin)
  - Monthly R&D: $75,000 (5 person team)
  - Monthly S&M: $50,000
  - Monthly G&A: $15,000

Current Metrics (Existing Product):
  - MRR: $85,000
  - ARR: $1,020,000
  - Customers: 120
  - Monthly Churn: 3%

Targets:
  - Rule of 40 target: 40
  - LTV:CAC: ≥3.0
  - CAC Payback: ≤12 months
  - Gross Margin: ≥70%

Assumptions stored in: .product-finance/assumptions.json

Next steps:
  - Run `/product-finance:health-check` to assess current financial health
  - Run `/product-finance:unit-economics` for detailed CAC/LTV analysis
  - Run `/product-finance:ai-economics` if you have AI features
```

## Implementation Notes

### For Claude Code Agent

**Use AskUserQuestion tool** for all interactive prompts:
- Present options clearly
- Explain why each piece of data is needed
- Provide guidance and examples
- Show typical ranges/benchmarks
- Allow "skip" or "unknown" for optional fields

**Validation:**
- Numeric fields: positive numbers, except a field that can be negative by its meaning
- Percentages: Ensure 0-100 range
- Required fields: Pricing model and basic costs
- Warn if values seem unusual (e.g., gross margin <30%)

**Error Handling:**
- If `.product-finance/` directory doesn't exist, create it
- If `assumptions.json` exists, ask: "Assumptions file exists. Update (merge) or overwrite?"
- Validate against JSON schema from `${CLAUDE_PLUGIN_ROOT}/templates/assumptions.json`
- Provide helpful error messages if validation fails

**Smart Defaults:**
- Annual discount: 10-15%
- Fully-loaded cost multiplier: 1.7x base salary
- Churn rate: 3-5% for SMB, 1-2% for enterprise
- Rule of 40 target: 40
- LTV:CAC target: 3.0
- CAC payback target: 12 months
- Gross margin target: 70%

**Progressive Enhancement:**
- Store confidence levels with data
- Track data sources (user-provided, calculated, estimated)
- Support incremental updates
- Ask again only for data that changed

### Integration with Other Commands

**Data reuse:**
- All other product-finance commands read from `assumptions.json`
- Commands can update specific sections as better data becomes available
- `/product-finance:discover` can populate market sizing
- `/product-finance:unit-economics` can refine CAC/LTV assumptions
- `/product-finance:ai-economics` can populate AI cost data

**JTBD Integration:** see Phase 4, option `jtbd`.

### Validation Rules

**Critical validations:**
- Pricing model must be one of: per_seat, usage_based, tiered, freemium, hybrid
- Prices must be positive numbers
- Percentages must be 0-100
- COGS should typically be <30% of price (gross margin >70%) for healthy SaaS
- LTV:CAC target should be ≥1.0 (warn if <3.0)
- Churn rate should be <10% monthly (warn if higher)

**Warnings (not errors):**
- Gross margin <70%: "Warning: Low gross margin for SaaS. Target is 70%+"
- CAC payback >18 months: "Warning: Long CAC payback period. Target is <12 months"
- Churn >5%: "Warning: High churn rate. Target is 3-5% for SMB, 1-2% for enterprise"

## Examples

### Example 1: New SaaS Product (Per-Seat)

**Setup flow:**
```
Pricing model: per_seat
Price per seat: $49/month
Annual discount: 15%
Avg seats per customer: 3

COGS:
  - Hosting per user: $2.50
  - AI per user: $0
  - Third-party per user: $1.00
  - Support per user: $0.50
  Total COGS: $4.00/user (92% gross margin)

R&D:
  - Team size: 8
  - Avg cost: $180,000/year fully-loaded
  Total R&D: $120,000/month

S&M:
  - Has sales team: No
  - Marketing budget: $20,000/month
  - Estimated CAC: $1,500

G&A: $12,000/month

Product status: planning
  - Target ARR year 1: $1,200,000
  - Target customers year 1: 200
  - Expected churn: 3%

Market sizing: skip

Team structure: skip

Retention assumptions:
  - GRR target: 92%
  - NRR target: 115%
  - Expansion revenue: 20%

Growth assumptions:
  - ARR growth target: 100%
  - Sales cycle: 30 days

Targets: use defaults
```

### Example 2: Existing Enterprise SaaS (Tiered)

**Setup flow:**
```
Pricing model: tiered
Number of tiers: 3

Tier 1: Starter
  - Monthly: $99
  - Annual: $950 (20% discount)

Tier 2: Professional
  - Monthly: $299
  - Annual: $2,870 (20% discount)

Tier 3: Enterprise
  - Monthly: Custom
  - Annual: $50,000 (average)

COGS:
  - Hosting: $5/user
  - AI: $3/user
  - Third-party: $2/user
  - Support: $1/user
  Total: $11/user

R&D: 35 people @ $200K avg = $583,333/month
S&M: 12 AEs @ $250K, 8 SDRs @ $120K, Marketing $150K/month
G&A: $100,000/month

Product status: existing
  - MRR: $850,000
  - ARR: $10,200,000
  - Customers: 450
  - New customers last month: 25
  - Churned: 5
  - Churn rate: 1.1%

Market sizing: manual
  - TAM: $50B
  - SAM: $5B
  - SOM: $500M

Team: detailed
  - Engineering: 30
  - Product: 3
  - Design: 2
  - Story points/sprint: 120
  - Sprint length: 2 weeks

Retention:
  - GRR: 95%
  - NRR: 125%
  - Expansion: 30%

Growth:
  - ARR growth target: 60%
  - Sales cycle: 90 days

Targets: custom
  - Rule of 40 target: 50
  - LTV:CAC: 4.0
  - CAC payback: 10 months
  - Gross margin: 75%
  - Magic number: 0.9
```

### Example 3: AI-First Product (Hybrid)

**Setup flow:**
```
Pricing model: hybrid
Description: $25/user/month base + $0.10 per AI query over 100
Base subscription: $25
Usage components: AI queries beyond included 100/month

COGS:
  - Hosting: $1/user
  - AI: $5/user (significant AI usage)
  - Third-party: $0.50/user
  - Support: $0.50/user
  Total: $7/user

R&D: 12 people @ $190K = $190,000/month

S&M: No sales team, marketing $30K/month, CAC $800

G&A: $15,000/month

Product status: existing
  - MRR: $125,000
  - ARR: $1,500,000
  - Customers: 350

Market sizing: jtbd (segments confirmed from the jtbd graph; no market size)

Team: skip

Retention: defaults

Growth: defaults

Targets: defaults
```

## Success Criteria

1. **Essential data collected:** Pricing model and cost structure stored
2. **Valid JSON generated:** Output passes JSON schema validation
3. **User understands:** Clear explanations provided for why data is needed
4. **Quick start:** Can complete minimal setup in <5 minutes
5. **Refinement supported:** Can update assumptions without starting over
6. **Integration works:** Other commands successfully read assumptions.json

## References

- **Schema:** `${CLAUDE_PLUGIN_ROOT}/templates/assumptions.json` - Full JSON schema definition
- **Methodology:** `BRAINSTORMING.md` - Design philosophy and financial frameworks
- **KPI Definitions:** `${CLAUDE_PLUGIN_ROOT}/docs/KPI_DEFINITIONS.md` - Detailed metric explanations (coming soon)
- **Benchmarks:** Industry standard ranges for validation

---

**Financial Intelligence as Code** - Start with what you know, refine as you learn.
