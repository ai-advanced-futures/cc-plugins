# Product Finance Methodology

## Overview

The Product Finance plugin implements a **hybrid methodology** that combines Jobs-to-be-Done (JTBD) thinking with stage-based financial checkpoints. Rather than treating financial analysis as a separate discipline, this methodology embeds financial intelligence directly into the product lifecycle, ensuring every product decision is informed by defensible financial data.

### Core Philosophy

**"Financial Intelligence as Code"**

Traditional product finance operates in spreadsheets, disconnected from the product development process. This plugin brings financial analysis into the developer workflow, providing:

1. **Contextual financial guidance** at each product lifecycle stage
2. **Automated calculations** with industry-standard methodologies
3. **CFO-ready outputs** that bridge product and finance teams
4. **Continuous financial health monitoring** rather than quarterly surprises

---

## The Jobs Framework

### What is a Financial "Job to be Done"?

Every product decision involves an implicit financial question. The Jobs Framework makes these questions explicit:

| Product Decision | Financial Job to be Done |
|-----------------|-------------------------|
| "Should we build this feature?" | "Calculate ROI and payback period for this investment" |
| "What should we charge?" | "Model pricing against unit economics and market positioning" |
| "Is this AI feature worth the cost?" | "Quantify AI ROI with multi-dimensional value attribution" |
| "Are we growing sustainably?" | "Assess Rule of 40 and financial health metrics" |
| "Where should we focus?" | "Prioritize features by NPV and strategic alignment" |

### Financial Jobs by Stakeholder

**Product Manager Jobs:**
- Justify feature investments with ROI calculations
- Prioritize backlog by financial impact
- Understand unit economics for pricing decisions
- Track feature-level profitability

**Engineering Leader Jobs:**
- Quantify technical debt in financial terms
- Calculate AI/infrastructure cost impact
- Model build vs. buy decisions
- Measure productivity multipliers

**Finance/CFO Jobs:**
- Generate board-ready financial reports
- Track KPIs with consistent methodology
- Model scenarios for planning
- Audit product financial assumptions

**Founder/Executive Jobs:**
- Assess overall financial health
- Make go/no-go investment decisions
- Communicate metrics to investors
- Set data-driven pricing strategy

---

## Company Stage Definitions

All stage-based benchmarks in this plugin use ARR to classify company stage:

| Stage  | ARR Range         | Description                             |
|--------|-------------------|-----------------------------------------|
| Early  | $0 – $1M ARR      | Pre-product-market-fit                  |
| Growth | $1M – $10M ARR    | Scaling go-to-market                    |
| Scale  | $10M – $50M ARR   | Expanding into new markets              |
| Mature | $50M+ ARR         | Optimizing for efficiency/profitability |

**Source:** `scripts/utils/constants.py::COMPANY_STAGES`

---

## The Product Lifecycle Financial Framework

The plugin organizes financial analysis around four product lifecycle stages, each with specific financial lenses, metrics, and recommended commands.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRODUCT LIFECYCLE STAGES                              │
├─────────────┬─────────────┬──────────────────┬────────────────────────────┤
│  DISCOVERY  │  PLANNING   │  IMPLEMENTATION  │        OPERATIONS          │
│             │             │                  │                            │
│ • Market    │ • ROI       │ • Cost           │ • Health                   │
│   sizing    │   modeling  │   tracking       │   monitoring               │
│ • Opp       │ • Pricing   │ • Instrument-    │ • Unit                     │
│   analysis  │   strategy  │   ation          │   economics                │
│ • TAM/SAM   │ • Resource  │ • AI cost        │ • Trend                    │
│             │   planning  │   attribution    │   analysis                 │
├─────────────┼─────────────┼──────────────────┼────────────────────────────┤
│  discover   │ feature-roi │ instrumentation  │ health-check               │
│             │             │ ai-economics     │ unit-economics             │
└─────────────┴─────────────┴──────────────────┴────────────────────────────┘
```

---

## Stage 1: Discovery

### Financial Lens: Market Validation

Before building, understand the financial opportunity. Discovery-stage financial analysis answers:

- **How big is this opportunity?** (TAM, SAM, SOM)
- **What can customers pay?** (Pricing anchors, willingness-to-pay)
- **Is this market worth entering?** (Market attractiveness score)

### Key Metrics

| Metric | Definition | Healthy Range |
|--------|------------|---------------|
| Total Addressable Market (TAM) | Maximum revenue if 100% market share | Depends on segment |
| Serviceable Addressable Market (SAM) | Realistic target market | 10-30% of TAM |
| Serviceable Obtainable Market (SOM) | Achievable near-term market | 1-5% of SAM |
| Market Growth Rate | Annual market expansion | >10% for SaaS |
| Average Contract Value (ACV) | Typical customer spend | Varies by segment |

### Command: `/product-finance:discover`

**Purpose:** Market sizing and opportunity analysis for new products or features.

**Inputs:**
- Target market segment
- Competitive landscape
- Customer research data
- Pricing benchmarks

**Outputs:**
- TAM/SAM/SOM calculations
- Market attractiveness score
- Competitive positioning analysis
- Pricing recommendation

**Best Practice:** Run discovery analysis before committing significant engineering resources. A $100K feature investment should target at least $1M+ market opportunity.

---

## Stage 2: Planning

### Financial Lens: Investment Justification

Planning-stage financial analysis builds the business case. This stage answers:

- **What's the expected return?** (ROI, NPV, payback period)
- **How should we price this?** (Value-based pricing model)
- **What resources do we need?** (Cost modeling)
- **How does this compare to alternatives?** (Opportunity cost)

### Key Metrics

| Metric | Definition | Healthy Range |
|--------|------------|---------------|
| Return on Investment (ROI) | (Value - Cost) / Cost | >100% |
| Net Present Value (NPV) | Discounted future cash flows | Positive |
| Payback Period | Time to recover investment | <12 months |
| Internal Rate of Return (IRR) | Discount rate where NPV = 0 | >20% |
| Cost of Delay | Revenue lost per time unit | Feature-specific |

### Command: `/product-finance:feature-roi`

**Purpose:** Calculate expected ROI for feature investments with strategic alignment scoring.

**Inputs:**
- Development cost estimate
- Expected revenue impact
- Time to market
- Strategic alignment factors
- Risk assessment

**Outputs:**
- ROI percentage and ratio
- NPV with sensitivity analysis
- Payback period
- Strategic alignment score
- Prioritization recommendation

**Best Practice:** Use feature ROI analysis to inform sprint planning and roadmap prioritization. Features should clear a minimum ROI threshold (typically 100%+) unless strategically critical.

### ROI Calculation Methodology

The plugin uses a multi-factor ROI framework:

```
Feature ROI = (Expected Annual Value - Annual Cost) / Investment Cost × 100

Where:
- Expected Annual Value = Revenue Impact + Cost Savings + Strategic Value
- Annual Cost = Maintenance + Infrastructure + Opportunity Cost
- Investment Cost = Development + QA + Launch Costs
```

**Strategic Value** — This is a qualitative dimension and is NOT included in numeric calculations.
Document it as a narrative in the analysis report. It cannot be reliably quantified without
customer data from a JTBD discovery session. Run `/jtbd-market-discovery:discover` first
to obtain defensible WTP and strategic value estimates.

**Strategic Alignment Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Revenue Potential | 25% | Direct revenue impact |
| Customer Demand | 20% | Validated customer need |
| Competitive Advantage | 20% | Differentiation value |
| Strategic Fit | 20% | Alignment with company direction |
| Technical Leverage | 15% | Platform/efficiency gains |

---

## Stage 3: Implementation

### Financial Lens: Cost Attribution

During implementation, track costs as they accrue. This stage answers:

- **What is this actually costing?** (Real-time cost tracking)
- **How do we attribute AI costs?** (Multi-dimensional attribution)
- **Are we on budget?** (Variance analysis)
- **What should we instrument?** (Financial tracking gaps)

### Key Metrics

| Metric | Definition | Healthy Range |
|--------|------------|---------------|
| AI Cost per Request | Total AI cost / API calls | <$0.10 |
| AI Cost per User | Total AI cost / active users | <$10/month |
| AI Cost % of Revenue | AI costs / revenue | <15% |
| Development Cost | Engineering investment | Per budget |
| Infrastructure Cost | Compute, storage, services | <20% of revenue |

### Command: `/product-finance:ai-economics`

**Purpose:** Calculate AI ROI with multi-dimensional value attribution.

**Inputs:**
- AI API costs by provider/model
- Infrastructure costs
- Development costs
- AI-enabled revenue
- Value attribution dimensions (retention, productivity, premium pricing)

**Outputs:**
- AI ROI percentage
- Cost per interaction/user
- Value attribution breakdown
- Cost optimization recommendations
- CFO-ready report

**Best Practice:** Run AI economics analysis monthly for products with significant AI costs. Target AI ROI >200% and AI costs <15% of revenue.

### Command: `/product-finance:instrumentation`

**Purpose:** Generate comprehensive instrumentation plan for financial tracking.

**Inputs:**
- Codebase path
- Product type (SaaS, marketplace, AI product)
- Current tracking analysis

**Outputs:**
- Gap analysis (missing events)
- Event schemas with code templates
- Database migration scripts
- Phased implementation plan
- API specifications

**Best Practice:** Run instrumentation analysis before implementing financial tracking. Instrument critical subscription events first (created, cancelled, upgraded) to enable MRR/churn calculation.

### AI Value Attribution Methodology

The plugin uses multi-dimensional value attribution:

```
Total AI Value = AI-Enabled Revenue
              + Premium Pricing Value
              + Productivity Value
              + Retention Value
              + Expansion Revenue
              + Time-to-Value Acceleration

Where:
- Premium Pricing Value = AI Revenue × Premium %
- Productivity Value = Hours Saved × Fully-Loaded Cost
- Retention Value = AI Revenue × Churn Reduction %
- Time-to-Value Acceleration = (AI Revenue / 12) × Months Saved
```

**AI Value Generated** = Productivity Value + Revenue Attribution

Where:
- **Productivity Value** = Productivity gain (hours/month) × Blended hourly rate (fully-loaded)
- **Revenue Attribution** = ARR directly attributed to AI-assisted features (from feature-level tracking)

> **Note:** If feature-level tracking is unavailable, use AI cost attribution percentage × Total ARR as a proxy.

---

## Stage 4: Operations

### Financial Lens: Health Monitoring

In production, continuously monitor financial health. This stage answers:

- **Is the business healthy?** (Rule of 40, financial health score)
- **Are unit economics sustainable?** (LTV:CAC, payback period)
- **Where are the trends heading?** (Growth rates, efficiency metrics)
- **What needs attention?** (Alerts and recommendations)

### Key Metrics

| Metric | Definition | Healthy Range |
|--------|------------|---------------|
| MRR/ARR | Monthly/Annual Recurring Revenue | Growing >10%/year |
| Rule of 40 | Growth Rate + Profit Margin | >40 |
| Churn Rate | Customers lost / starting customers | <3%/month |
| Net Revenue Retention | Revenue including expansion/contraction | >100% |
| LTV:CAC Ratio | Lifetime Value / Acquisition Cost | >3:1 |
| CAC Payback Period | Months to recover acquisition cost | <12 months |
| Magic Number | Net New ARR / S&M Spend | >0.75 |
| Gross Margin | (Revenue - COGS) / Revenue | >70% (SaaS) |

### Command: `/product-finance:health-check`

**Purpose:** Comprehensive financial health assessment with executive dashboard.

**Inputs:**
- Revenue data (MRR, growth rate)
- Cost structure (COGS, S&M, R&D, G&A)
- Customer metrics (count, churn, ARPU)
- Runway information (cash, burn rate)

**Outputs:**
- Financial health score (0-100)
- Rule of 40 assessment
- Efficiency ratios analysis
- Trend indicators
- Prioritized recommendations
- Executive dashboard

**Best Practice:** Run health check monthly and before board meetings. Target health score >75 and Rule of 40 >40.

### Command: `/product-finance:unit-economics`

**Purpose:** Deep dive into customer-level profitability and acquisition efficiency.

**Inputs:**
- Customer acquisition costs (by channel)
- Customer lifetime value components
- Churn data
- Cohort retention curves

**Outputs:**
- LTV:CAC ratio with benchmarks
- CAC payback period
- Magic Number (sales efficiency)
- Cohort analysis with retention curves
- Scenario modeling
- Optimization recommendations

**Best Practice:** Run unit economics quarterly and when evaluating growth investments. Target LTV:CAC >3:1 and payback <12 months.

### Rule of 40 Framework

The Rule of 40 balances growth and profitability:

```
Rule of 40 Score = Revenue Growth Rate % + Profit Margin %

Assessment:
- Excellent: >60 (high growth AND profitable)
- Good: 40-60 (healthy balance)
- Acceptable: 25-40 (needs improvement)
- Poor: <25 (unsustainable)
```

**Growth-Profitability Trade-off Matrix:**

| Scenario | Growth | Margin | Rule of 40 | Guidance |
|----------|--------|--------|------------|----------|
| Hypergrowth | 80% | -20% | 60 | Acceptable if path to profit |
| Balanced | 40% | 10% | 50 | Ideal state |
| Profitable | 15% | 35% | 50 | Good, invest in growth |
| Struggling | 10% | 5% | 15 | Needs intervention |

---

## Command-to-Stage Mapping

| Command | Primary Stage | Secondary Stages | Key Output |
|---------|--------------|------------------|------------|
| `discover` | Discovery | Planning | Market sizing, opportunity score |
| `feature-roi` | Planning | Discovery, Operations | ROI analysis, prioritization |
| `ai-economics` | Implementation | Operations | AI ROI, cost attribution |
| `instrumentation` | Implementation | Operations | Event schemas, migration scripts |
| `health-check` | Operations | All | Health score, executive dashboard |
| `unit-economics` | Operations | Planning | LTV:CAC, cohort analysis |

---

## Integration Philosophy

### Plugin Ecosystem Integration

The Product Finance plugin is designed to integrate with the broader Claude Code plugin ecosystem:

#### With JTBD Plugin

**Integration Pattern:** JTBD provides customer needs; Product Finance quantifies value.

```
JTBD Analysis → Customer job identified
     ↓
Product Finance → Market size for that job
     ↓
Combined Output → Prioritized opportunity with financial justification
```

**Example Workflow:**
1. Run `/jtbd:discover` to identify customer jobs
2. Run `/product-finance:discover` to size the market for top jobs
3. Run `/product-finance:feature-roi` to calculate ROI for solutions
4. Prioritize by combined JTBD importance + financial return

### Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA FLOW ARCHITECTURE                         │
│                                                                   │
│  ┌─────────────────┐       ┌─────────────────────────────────┐  │
│  │  assumptions.   │◄─────►│         All Commands            │  │
│  │      json       │       │                                 │  │
│  └─────────────────┘       │  discover → feature-roi →       │  │
│          │                 │  ai-economics → health-check    │  │
│          │                 └─────────────────────────────────┘  │
│          ▼                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              .product-finance/ directory                 │    │
│  │                                                          │    │
│  │  ├── assumptions.json      (shared assumptions)         │    │
│  │  ├── discover.json         (market analysis)            │    │
│  │  ├── feature-roi.json      (feature ROI data)           │    │
│  │  ├── ai-economics.json     (AI cost/value data)         │    │
│  │  ├── health-check.json     (health metrics)             │    │
│  │  ├── unit-economics.json   (unit economics data)        │    │
│  │  ├── instrumentation/      (tracking plans)             │    │
│  │  └── reports/              (generated reports)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Shared Assumptions Model

The `assumptions.json` file serves as the single source of truth:

```json
{
  "company": {
    "name": "Acme SaaS",
    "stage": "growth",
    "industry": "B2B SaaS"
  },
  "revenue": {
    "mrr": 125000,
    "growth_rate": 15,
    "arpu": 500
  },
  "costs": {
    "gross_margin": 75,
    "s&m_percent": 40,
    "r&d_percent": 30
  },
  "customers": {
    "count": 250,
    "churn_rate": 3,
    "cac": 2000
  },
  "ai": {
    "monthly_cost": 50000,
    "cost_per_request": 0.05,
    "enabled_revenue_percent": 60
  }
}
```

Commands read from and write to this file, maintaining consistency across analyses.

---

## Best Practices for Adoption

### Getting Started

**Week 1: Foundation**
1. Run `/product-finance:setup` to configure the plugin
2. Run `/product-finance:instrumentation` to identify tracking gaps
3. Establish baseline assumptions in `assumptions.json`

**Week 2-4: Core Workflows**
1. Run `/product-finance:health-check` to establish baseline health
2. Run `/product-finance:unit-economics` to understand customer economics
3. Begin instrumenting critical events (subscriptions, payments)

**Month 2+: Integration**
1. Run `/product-finance:feature-roi` for all significant investments
2. Run `/product-finance:ai-economics` monthly (if applicable)
3. Run `/product-finance:health-check` before board meetings
4. Establish regular financial review cadence

### Recommended Cadence

| Command | Cadence | Trigger Events |
|---------|---------|----------------|
| `health-check` | Monthly | Board meetings, planning cycles |
| `unit-economics` | Quarterly | Strategy reviews, fundraising |
| `feature-roi` | Per feature | Before significant investments |
| `ai-economics` | Monthly | AI cost changes, provider updates |
| `discover` | Per initiative | New market entry, expansion |
| `instrumentation` | Quarterly | New features, audit cycles |

### Common Pitfalls to Avoid

**1. Analysis Paralysis**
- Don't over-analyze small decisions
- Use quick ROI estimates for features <$10K investment
- Reserve deep analysis for strategic bets

**2. Stale Assumptions**
- Update `assumptions.json` monthly
- Refresh unit economics quarterly
- Validate market sizing annually

**3. Ignoring Qualitative Factors**
- Financial metrics inform but don't dictate decisions
- Strategic value may exceed calculated ROI
- Customer satisfaction matters beyond retention numbers

**4. Cherry-Picking Metrics**
- Report both successes and challenges
- Compare actual vs. projected consistently
- Acknowledge uncertainty in projections

### Organizational Alignment

**For Product Teams:**
- Use financial frameworks to strengthen business cases
- Document assumptions for transparency
- Track actual vs. projected outcomes

**For Finance Teams:**
- Collaborate on assumptions and methodology
- Review outputs for consistency
- Provide feedback to improve models

**For Leadership:**
- Set threshold expectations (minimum ROI, health score targets)
- Review financial dashboards regularly
- Use data to inform strategy, not replace judgment

---

## Methodology References

### Industry Frameworks

The Product Finance plugin incorporates methodologies from industry thought leaders:

- **David Skok (Matrix Partners):** SaaS metrics playbook, CAC/LTV framework
- **Tomasz Tunguz (Theory Ventures):** Growth benchmarks, efficiency metrics
- **Bessemer Venture Partners:** Cloud metrics guide, Rule of 40
- **SaaS Capital:** Annual SaaS benchmarking surveys
- **OpenView Partners:** Product-led growth metrics

### Calculation Standards

All calculations follow industry-standard methodologies:

- **LTV Calculation:** Traditional formula with gross margin adjustment
- **CAC Calculation:** Fully-loaded with optional channel breakdown
- **Churn Calculation:** Customer-based and revenue-based variants
- **ROI Calculation:** Multi-factor with strategic alignment weighting
- **NPV Calculation:** Discounted cash flow with sensitivity analysis

### Benchmark Sources

Benchmarks are derived from:
- Public SaaS company filings
- Industry surveys (SaaS Capital, KeyBanc, OpenView)
- Venture capital portfolio data
- Academic research on technology economics

---

## Summary

The Product Finance methodology transforms financial analysis from a periodic exercise into a continuous practice embedded in the product lifecycle. By providing:

1. **Stage-appropriate financial lenses** - Right analysis at the right time
2. **Automated calculations** - Consistent, defensible methodology
3. **CFO-ready outputs** - Bridge product and finance teams
4. **Integration patterns** - Work within existing workflows

Teams can make better financial decisions faster, with confidence that their analysis follows industry best practices.

**The goal is not perfect prediction, but informed decision-making.**

---

*Product Finance Plugin - Financial Intelligence as Code*
