---
description: Phase 2. Score the strategic fit and the synergies of one target.
argument-hint: "[--target <id or name>]"
---
# /corporate-development:assess

Evaluate strategic fit, identify synergies, and score target company alignment with your organization.

## When to use

- After discovering a promising target with discover
- Evaluating a specific acquisition opportunity
- Determining if a target warrants deeper operational due diligence
- Building a decision matrix for target prioritization

## What it does

1. **Strategic Alignment Evaluation** - Assesses market positioning, customer overlap, competitive positioning
2. **Synergy Identification** - Identifies revenue synergies, cost synergies, and capability synergies
3. **Fit Scoring** - Calculates overall strategic fit score (0-100)
4. **Differentiation Analysis** - Evaluates unique capabilities and customer base value
5. **GO/NO_GO Assessment** - Determines readiness for deeper due diligence

## Required Input

```bash
/corporate-development:assess --target TARGET_ID
```

Or run interactively:
```bash
/corporate-development:assess
```

You'll be prompted to provide:
- Target company name or ID
- Current strategic priorities
- Market/customer overlap assessment
- Capability gap analysis

## Interactive Flow

```
Which target company would you like to assess?
Target ID or name: target_001

Strategic Alignment Questions:
1. How well does this target align with our core markets? (1-10): 8
2. Customer overlap with our base (%)? 35
3. Unique capabilities we'd gain: AI/ML capabilities, enterprise customer relationships
4. Competitive positioning: Direct competitor / Complementary / Adjacent

Revenue Synergy Analysis:
1. Cross-sell opportunity (estimated $M): $5M
2. New market entry potential (yes/no): yes
3. Geographic expansion: US + Europe presence

Cost Synergy Assessment:
1. Duplicate functions? (yes/no): yes
2. Estimated run-rate savings: $2M-$3M
3. One-time integration costs: $1M
```

After assessment, the command analyzes the responses and generates fit scores.

## Outputs

**assessment_report.json** - Detailed assessment data
```json
{
  "assessment_date": "2026-02-03",
  "target": {
    "id": "target_001",
    "company_name": "Example Inc",
    "estimated_revenue": "$25M"
  },
  "strategic_fit": {
    "market_alignment_score": 8,
    "customer_synergy_score": 7,
    "capability_fit_score": 9,
    "competitive_positioning_score": 8,
    "overall_fit_score": 82
  },
  "synergies": {
    "revenue_synergies": {
      "cross_sell": "$5M",
      "new_markets": "$3M",
      "total_estimated": "$8M"
    },
    "cost_synergies": {
      "duplicate_functions": true,
      "estimated_savings": "$2.5M",
      "one_time_costs": "$1M"
    },
    "capability_synergies": [
      "AI/ML development team",
      "Enterprise customer relationships"
    ]
  },
  "recommendation": "GO",
  "confidence_level": "HIGH",
  "next_step": "audit"
}
```

**assessment_summary.md** - Executive summary with:
- Strategic fit scorecard
- Key synergies identified
- Critical risks or concerns
- Recommended next actions
- Questions for deeper diligence

## Assessment Scoring Framework

Strategic fit score (0-100) calculated as weighted average:

```
Market Alignment (25%):
  - Customer segment fit: 0-10
  - Market position: 0-10
  - Geographic fit: 0-10

Synergy Potential (30%):
  - Revenue upside: 0-10
  - Cost savings: 0-10
  - Capability gaps: 0-10

Financial Attractiveness (25%):
  - Valuation range reasonable: 0-10
  - Revenue quality: 0-10
  - Growth trajectory: 0-10

Strategic Value (20%):
  - Competitive positioning: 0-10
  - Technology differentiation: 0-10
  - Customer base value: 0-10

Overall Score = (Market × 0.25) + (Synergy × 0.30) + (Financial × 0.25) + (Strategic × 0.20)
```

## GO/NO_GO Decision Logic

```
Overall Fit Score:
  ≥ 75: GO - Recommend proceed to operational due diligence
  60-74: CONDITIONAL - Recommend proceed with risk mitigation plan
  50-59: CONDITIONAL - Require additional information before proceeding
  < 50: NO_GO - Not recommended for deeper investment
```

Note: Both the 60-74 and 50-59 bands produce a CONDITIONAL gate. The score and reasoning output distinguish the required actions — check the assessment_report.json and assessment_summary.md artifacts for specific recommendations.

Decision also influenced by:
- Synergy magnitude (if minimal: lean NO_GO)
- Integration complexity (if high: lean conditional)
- Strategic urgency (if critical: can upgrade to GO)
- Management team quality (if weak: lean NO_GO)

## Next Steps

After assess completes:

1. **If GO or CONDITIONAL**:
   - Proceed to operational due diligence
   ```bash
   /corporate-development:audit --target target_001
   ```

2. **If NO_GO**:
   - Document reasons in pipeline
   - Set conditions for future reconsideration
   - Return to discover for alternative targets

## Related Skills

- `/corporate-development:discover` - Initial target identification
- `/corporate-development:audit` - Operational due diligence
- `/corporate-development:analyze` - Financial analysis
- Synergy identification and value creation frameworks

## Integrations

- Financial data sources for revenue/margin benchmarking
- Customer database for overlap analysis
- Competitive intelligence tools
- Internal capability inventory system
