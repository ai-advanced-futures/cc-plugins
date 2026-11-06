---
description: Phase 6. Combine all findings into a GO, CONDITIONAL, or NO_GO recommendation.
argument-hint: "[--target <id or name>]"
---
# /corporate-development:recommend

Synthesize all M&A investigation findings and provide final GO/NO_GO/CONDITIONAL recommendation with deal thesis and conditions.

## When to use

- After completing discover, assess, audit, analyze, and plan phases
- Synthesizing all due diligence findings into final recommendation
- Preparing for board or investment committee presentation
- Documenting final deal thesis and key assumptions
- Before proceeding to letter of intent or term sheet negotiation

## What it does

1. **Findings Synthesis** - Consolidates results from all phases (discover, assess, audit, analyze, plan)
2. **Deal Thesis Development** - Creates clear investment thesis and value creation plan
3. **Recommendation Decision** - Provides GO/NO_GO/CONDITIONAL recommendation
4. **Condition Documentation** - If conditional, specifies conditions that must be met
5. **Risk/Reward Summary** - Quantifies upside potential and downside risk
6. **Board-Ready Documentation** - Generates executive summary for decision makers

## Required Input

```bash
/corporate-development:recommend --target TARGET_ID
```

Or run interactively:
```bash
/corporate-development:recommend
```

The command automatically aggregates all previous analysis files and prompts for:
- Final strategic rationale
- Deal thesis summary
- Key assumptions and conditions
- Executive sponsorship confirmation

## Interactive Flow

```
Generating recommendation based on previous analysis for: target_001

Previous Analysis Summary:
  Discovery: Found via PitchBook, fit score 8.5, qualified as hot prospect
  Assessment: Overall fit 82, GO recommendation, revenue synergies $8M
  Audit: Operational health 71, MODERATE integration risk
  Analysis: Financial health 78, Rule of 40: 47, asking price fair
  Plan: 12-month integration, $2.5M costs, synergy realization year 2

Final Recommendation Questions:

Deal Thesis (1-2 sentences):
Your answer: Strategic entry into enterprise AI/ML market with strong technical team and customer relationships. Acquire proven technology and talent to accelerate product roadmap.

Key Assumptions (list top 3):
1. Customer retention ≥95% through integration
2. Achieve $8M revenue synergies by end of year 2
3. Retain CEO and CTO through integration period

Are there any deal-breaker risks that changed since last analysis? (yes/no): no

Recommended entry price: 140M (vs ask of 150M)

Executive sponsorship: Yes, CEO and CFO aligned

What contingencies must be met before close? (if any):
- Exclude 3 customers with change of control clauses
- Cap seller reps and warranties at 20% purchase price
- Achieve 90% of key employee retention agreements pre-close
```

The command synthesizes all inputs and generates final recommendation.

## Outputs

**recommendation_report.json** - Complete recommendation document
```json
{
  "recommendation_date": "2026-02-03",
  "target": {
    "id": "target_001",
    "company_name": "Example Inc",
    "estimated_revenue": 25,
    "asking_price": 150
  },
  "recommendation": "GO",
  "confidence_level": "HIGH",
  "deal_thesis": "Strategic acquisition of enterprise AI/ML technology company with proven product-market fit, strong technical team, and valuable customer relationships. Accelerates our AI/ML capabilities, provides customer expansion opportunity, and generates $8M in revenue synergies.",
  "strategic_rationale": {
    "market_positioning": "Establishes presence in $50B enterprise AI market",
    "technology_fit": "Fills 18-month technology gap in our roadmap",
    "customer_expansion": "Brings 150 enterprise customers, 85% retention track record",
    "team_acquisition": "Gains 45-person team including proven founders and technical leaders"
  },
  "discovery_findings": {
    "strategic_fit_score": 8.5,
    "sources": ["PitchBook", "Crunchbase"],
    "qualified_status": "HOT_PROSPECT"
  },
  "assessment_findings": {
    "overall_fit_score": 82,
    "revenue_synergies": 8000000,
    "cost_synergies": 2500000,
    "recommendation": "GO"
  },
  "audit_findings": {
    "operational_health": 71,
    "integration_risk": "MODERATE",
    "key_concerns": [
      "Key person concentration with CEO",
      "Monolithic architecture needs refactoring"
    ],
    "mitigation_planned": true
  },
  "analysis_findings": {
    "financial_health": 78,
    "rule_of_40": 47,
    "business_quality": "ABOVE_AVERAGE",
    "valuation": "FAIR",
    "recommended_entry": 140
  },
  "plan_findings": {
    "integration_complexity": "MODERATE",
    "integration_cost": 2500000,
    "timeline_months": 12,
    "day_100_milestones": [
      "Customer communication complete",
      "Team structure finalized",
      "Retention agreements signed"
    ]
  },
  "deal_economics": {
    "asking_price": 150,
    "recommended_entry": 140,
    "price_range": {
      "low": 125,
      "high": 145
    },
    "value_creation_sources": {
      "revenue_synergies": 8000000,
      "cost_synergies": 2500000,
      "total_year_2": 10500000
    },
    "estimated_roi_year_3": 0.28,
    "payback_period_years": 3.2
  },
  "key_assumptions": [
    "Customer retention ≥95% through integration",
    "Achieve $8M revenue synergies by end of year 2",
    "Retain CEO and CTO through integration period",
    "Maintain revenue growth at 25%+ post-acquisition",
    "Successfully refactor technology within 18 months"
  ],
  "key_risks": [
    {
      "risk": "Key person turnover",
      "probability": "MEDIUM",
      "impact": "HIGH",
      "mitigation": "Retention bonuses, career path definition"
    },
    {
      "risk": "Customer change of control friction",
      "probability": "MEDIUM",
      "impact": "MEDIUM",
      "mitigation": "Proactive customer engagement, dedicated success team"
    },
    {
      "risk": "Technology integration delays",
      "probability": "LOW",
      "impact": "MEDIUM",
      "mitigation": "Phased architecture roadmap, parallel systems"
    }
  ],
  "conditions_precedent": [
    "Retention agreements signed with CEO, CTO, and top 3 engineers (>80% threshold)",
    "Customers with change of control clauses agree to continuation",
    "Cap seller representations at 20% of purchase price",
    "Complete reference calls with top 10 customers (>85% satisfaction required)",
    "Validate revenue forecast through customer interviews"
  ],
  "deal_committee_recommendation": {
    "recommendation": "GO",
    "sponsoring_executives": ["CEO", "CFO"],
    "board_recommendation": "Approve within price range of $130M-$145M",
    "contingencies": "Retain ≥80% of key personnel, cap seller reps at 20%"
  }
}
```

**recommendation_summary.md** - Executive summary with:
- Deal thesis (one-paragraph summary)
- Strategic rationale and value creation story
- Key findings from each phase (discover, assess, audit, analyze, plan)
- Deal economics and ROI projection
- Key assumptions and risks with mitigations
- Conditions precedent
- Board recommendation and voting guidance
- Next steps (LOI, term sheet, negotiations)

**decision_scorecard.pdf** - Visual scorecard showing:
- Phase-by-phase scores and recommendations
- GO/NO_GO/CONDITIONAL decision at each gate
- Key metrics and thresholds
- Overall recommendation with confidence level

## Recommendation Decision Framework

```
RECOMMENDATION LOGIC:

Phase 1: Strategic Fit (Assess)
  ├─ Score ≥ 75: Continue to operational review
  ├─ Score 60-74: Continue with conditions
  └─ Score < 60: NO_GO

Phase 2: Operational Health (Audit)
  ├─ Risk ≤ MODERATE + Score ≥ 70: Continue to financial review
  ├─ Risk = HIGH + Score 50-70: Flag risks, continue conditionally
  └─ Risk = HIGH + Score < 50: NO_GO

Phase 3: Financial Quality (Analyze)
  ├─ Health ≥ 75 + Valuation FAIR: Continue to planning
  ├─ Health 60-74 + Valuation FAIR: Continue with monitoring
  ├─ Health < 60 or Valuation HIGH: NO_GO or renegotiate price
  └─ Health ≥ 75 but Valuation VERY HIGH: NO_GO or renegotiate

Phase 4: Integration Readiness (Plan)
  ├─ Risk ≤ MODERATE + Cost ≤ Budget: Ready for final recommendation
  ├─ Risk = MODERATE + Cost > Budget: Flag for risk management
  └─ Risk = HIGH + Cost > Budget: NO_GO or renegotiate

Final Gate: All Phases Green?
  ├─ All scores GO: Recommend GO
  ├─ Most scores GO + mitigations clear: Recommend CONDITIONAL
  ├─ Multiple concerns + high risks: Recommend CONDITIONAL or NO_GO
  └─ Deal-breaker risk identified: Recommend NO_GO
```

## Confidence Level Classification

```
VERY_HIGH (90%+): All phases green, assumptions validated, low risk
  → Strong recommendation, proceed with confidence
  → Example: Target 1, all scores GO, validated assumptions

HIGH (75-90%): Most phases green, minor risks identified, mitigations clear
  → Recommend GO, monitor conditions closely
  → Example: Target 2, slight operational concern but plan addresses

MEDIUM (50-75%): Mixed results, several risks identified, meaningful conditions
  → Recommend CONDITIONAL on meeting conditions
  → Example: Target 3, financial concern but growth potential high

LOW (<50%): Multiple red flags, significant risks, unclear assumptions
  → Recommend NO_GO or major renegotiation
  → Example: Target 4, multiple phases flagged, integration complex
```

## Deal Economics Projection

```
Entry Price: $140M (at 5.6x revenue)

Year 1 Standalone Financials:
  Revenue: $28M (12% growth from $25M baseline)
  EBITDA: $3.5M

Year 2 with Synergies:
  Revenue: $38.5M ($3.5M from synergies)
  EBITDA: $7M ($2.5M from cost synergies, $2M from revenue)

Year 3:
  Revenue: $47M
  EBITDA: $9M

Cumulative Synergies (Years 1-3): $12M+
Less Integration Costs: ($2.5M)
Net Value Created: $9.5M+

Payback Period: ~3.2 years
Year 3 IRR: 28%
```

## Key Assumption Validation

Before recommendation, verify:

- **Customer Retention**: Call top 10 customers for post-acquisition confidence
- **Revenue Synergies**: Quantify with specific cross-sell opportunities
- **Cost Synergies**: Detail specific duplicate functions and consolidation plans
- **Growth Trajectory**: Stress test maintaining 25%+ growth post-close
- **Key Person Retention**: Confirm CEO/CTO willing to stay with documented plans
- **Integration Timeline**: Validate 12-month plan is realistic with IT team
- **Valuation Reasonableness**: Compare to recent public/private comp transactions

## Conditions Precedent Framework

Conditions should be:
- **Specific and Measurable** - Not subjective
- **Achievable** - Shouldn't undermine deal intent
- **Material** - Truly a "must-have" before closing
- **Realistic** - Can be confirmed pre-close

Examples:

```
GOOD: "Retention agreements signed with CEO, CTO, and top 3 engineers"
  → Specific, measurable, achievable

WEAK: "Target's team will be motivated and committed"
  → Subjective, unmeasurable

GOOD: "Customer satisfaction score ≥85% based on reference calls with top 10"
  → Specific, measurable, validates assumption

WEAK: "Customers will be happy with acquisition"
  → Subjective, unmeasurable
```

## Next Steps

After recommend completes:

1. **If GO or CONDITIONAL**:
   - Present to board/investment committee
   - Prepare LOI or term sheet
   - Begin negotiation phase
   - Monitor conditions pre-close

2. **If CONDITIONAL**:
   - Define specific conditions to resolve
   - Establish timeline for condition satisfaction
   - Plan renegotiation if conditions not met
   - Conduct additional diligence if needed

3. **If NO_GO**:
   - Document reasons for future reference
   - Return to discover for alternatives
   - Schedule quarterly review for changed conditions

## Related Skills

- `/corporate-development:discover` - Pipeline sourcing
- `/corporate-development:assess` - Strategic assessment
- `/corporate-development:audit` - Operational audit
- `/corporate-development:analyze` - Financial analysis
- `/corporate-development:plan` - Integration planning
- Investment thesis and M&A decision frameworks

## Integrations

- Board and committee reporting
- Deal documentation and tracking
- Stakeholder communication systems
- Financial modeling and scenario analysis
- Risk management and contingency tracking

## After the decision

The post-close checklist runs for 30 days and checks that the key assumptions hold.
