---
name: discovery-target-assessment
description: Evaluate strategic fit, differentiation, and acquisition viability of targets
---

# Target Assessment

Provides strategic evaluation of sourced acquisition targets by analyzing competitive positioning, strategic fit, differentiation, and acquisition viability to determine readiness for deeper due diligence.

## What It Does

- Scores strategic fit against buyer's strategic priorities and investment thesis
- Analyzes target's differentiation in market relative to competitors
- Identifies synergy opportunities (revenue, cost, technology) with buyer
- Evaluates competitive positioning and market impact of acquisition
- Assesses team quality and management depth
- Reviews technology stack and product-market fit indicators
- Identifies key risks and deal-breaking factors
- Generates strategic rationale memo

## How to Use

Target Assessment is performed after Deal Sourcing has identified qualified prospects. This skill provides deeper strategic analysis of why the target matters to the buyer and whether the strategic rationale is sound. Results inform the decision to proceed to comprehensive due diligence.

## Inputs

```json
{
  "target_company": {
    "company_name": "string",
    "industry": "string",
    "revenue": "number",
    "growth_rate": "number",
    "market_position": "string",
    "key_products": ["string"]
  },
  "buyer_context": {
    "strategic_priorities": ["string"],
    "current_market_position": "string",
    "technology_gaps": ["string"],
    "customer_base": "string"
  },
  "market_analysis": {
    "total_addressable_market": "number",
    "target_market_share": "number",
    "competitive_landscape": ["string"]
  }
}
```

## Outputs

```json
{
  "assessment_summary": {
    "strategic_fit_score": "number",
    "differentiation_score": "number",
    "synergy_potential": "number",
    "overall_attractiveness": "string"
  },
  "strategic_fit": {
    "alignment_with_priorities": "string",
    "fit_score": "number",
    "rationale": ["string"]
  },
  "competitive_analysis": {
    "market_position": "string",
    "differentiation": "string",
    "competitive_advantages": ["string"],
    "vulnerabilities": ["string"]
  },
  "synergy_analysis": {
    "revenue_synergies": {
      "description": "string",
      "opportunity_size": "number"
    },
    "cost_synergies": {
      "description": "string",
      "opportunity_size": "number"
    },
    "technology_synergies": {
      "description": "string",
      "details": ["string"]
    }
  },
  "risk_assessment": {
    "key_risks": ["string"],
    "deal_breakers": ["string"],
    "risk_mitigation_strategies": ["string"]
  },
  "recommendation": "string"
}
```

## Scoring Methodology

- **Strategic Fit (1-100)**: Alignment with buyer priorities (40%), gap filling capability (30%), market impact (20%), cultural fit (10%)
- **Differentiation (1-10)**: Unique technology (40%), market position (30%), customer relationships (20%), brand strength (10%)
- **Synergy Potential (1-10)**: Revenue synergies possible (30%), cost synergies possible (30%), technology leverage (20%), market expansion (20%)

## Gate Logic

- **GO** - Strategic fit >80, differentiation >7, synergy potential high, no identified deal breakers
- **NO_GO** - Strategic fit <60, poor differentiation, integration would be prohibitively complex
- **CONDITIONAL** - Proceed to due diligence if fit >70 and specific risk mitigation strategies identified

## Integrations

- **competitive-intelligence** - Competitive positioning data, market analysis, transaction comparables
- **product-finance** - Financial projections, unit economics baseline
- **ux-hci-design** - Product differentiation and UX quality assessment

## Related Skills

- Deal Sourcing - Identifies targets for assessment
- Operational Due Diligence - Evaluates execution capability
- Product Due Diligence - Assesses product-market fit deeper

## Used By

- Command: `/corporate-development:assess`
- Agent: `target-assessor`

