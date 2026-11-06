---
name: execution-deal-recommendation
description: Synthesize findings and provide GO/NO_GO recommendation with executive summary
---

# Deal Recommendation

Final synthesis skill that aggregates all investigation findings across discovery and due diligence workstreams to provide a clear GO/NO_GO recommendation with supporting rationale, risk mitigation strategies, and executive memo for decision-makers.

## What It Does

- Aggregates findings from all investigation workstreams (discovery, due diligence)
- Applies multi-factor decision logic to evaluate overall deal attractiveness
- Performs risk/reward analysis and sensitivity analysis
- Identifies must-have conditions and deal breakers
- Evaluates valuation reasonableness and deal economics
- Assesses integration feasibility and risk mitigation
- Generates executive memo with key decision points
- Identifies open items and conditions to closing
- Provides contingency and risk mitigation recommendations
- Scores overall deal quality and decision confidence

## How to Use

Deal Recommendation is the final skill in the investigation process. It synthesizes all prior findings into a clear recommendation for senior leadership. The output provides a structured decision memo that captures why the deal is recommended (or not), key risks, and conditions for proceeding.

## Inputs

```json
{
  "investigation_findings": {
    "deal_sourcing": "object",
    "target_assessment": "object",
    "operational_dd": "object",
    "financial_dd": "object",
    "customer_dd": "object",
    "product_dd": "object",
    "legal_dd": "object",
    "integration_plan": "object"
  },
  "acquisition_criteria": {
    "strategic_priorities": ["string"],
    "financial_thresholds": "object",
    "risk_tolerance": "string"
  },
  "valuation_analysis": {
    "proposed_price": "number",
    "valuation_range": "object",
    "transaction_assumptions": "object"
  }
}
```

## Outputs

```json
{
  "recommendation": {
    "decision": "string",
    "confidence_level": "number",
    "recommendation_summary": "string"
  },
  "decision_analysis": {
    "strategic_fit_score": "number",
    "financial_attractiveness_score": "number",
    "operational_feasibility_score": "number",
    "overall_deal_quality_score": "number",
    "scoring_methodology": "string"
  },
  "risk_reward_analysis": {
    "upside_potential": {
      "revenue_synergies": "number",
      "cost_synergies": "number",
      "strategic_benefits": ["string"],
      "market_impact": "string"
    },
    "downside_risks": {
      "customer_retention_risk": "string",
      "team_retention_risk": "string",
      "integration_risk": "string",
      "financial_risk": "string",
      "market_risk": "string"
    },
    "risk_mitigation_strategies": [
      {
        "risk": "string",
        "mitigation": "string",
        "cost": "number"
      }
    ]
  },
  "financial_analysis": {
    "proposed_valuation": "number",
    "valuation_range": {
      "bear_case": "number",
      "base_case": "number",
      "bull_case": "number"
    },
    "valuation_multiple": "number",
    "comparable_multiples": "object",
    "price_assessment": "string",
    "deal_economics": {
      "irr_potential": "number",
      "payback_period": "number",
      "value_creation_potential": "string"
    }
  },
  "must_have_conditions": [
    {
      "condition": "string",
      "rationale": "string",
      "priority": "string"
    }
  ],
  "deal_breakers_identified": [
    {
      "issue": "string",
      "severity": "string",
      "mitigation_possible": "boolean"
    }
  ],
  "open_items": [
    {
      "item": "string",
      "owner": "string",
      "timeline": "string",
      "impact_if_unresolved": "string"
    }
  ],
  "conditions_to_closing": [
    "string"
  ],
  "integration_assessment": {
    "integration_complexity": "string",
    "integration_timeline": "string",
    "key_integration_risks": ["string"],
    "integration_cost_estimate": "number",
    "integration_probability_of_success": "number"
  },
  "executive_memo": {
    "recommendation": "string",
    "key_investment_thesis": "string",
    "strategic_rationale": "string",
    "financial_highlights": "string",
    "key_risks": ["string"],
    "key_opportunities": ["string"],
    "recommended_actions": ["string"],
    "decision_timeline": "string"
  },
  "contingency_recommendations": [
    {
      "scenario": "string",
      "trigger": "string",
      "actions": ["string"]
    }
  ]
}
```

## Scoring Methodology

- **Strategic Fit (0-100)**: Aligns with buyer priorities (25%), market impact (25%), technology fit (25%), cultural fit (25%)
- **Financial Attractiveness (0-100)**: Valuation reasonableness (30%), growth potential (25%), profitability (25%), synergy potential (20%)
- **Operational Feasibility (0-100)**: Team retention likelihood (25%), integration complexity (25%), customer retention (25%), risk mitigation feasibility (25%)
- **Overall Deal Quality (0-100)**: Average of above three, weighted by buyer's strategic priorities

## Decision Framework

**GO Recommendation (Score >75)**
- Clear strategic fit with buyer priorities
- Attractive financial economics
- Manageable integration risk with identified mitigations
- Strong team and customer retention prospects
- Valuation within reasonable range

**CONDITIONAL GO (Score 60-75)**
- Good strategic fit with manageable concerns
- Acceptable financial terms with specific conditions
- Integration feasible with elevated risk management
- Specific conditions must be met (pricing, reps/warranties, etc.)
- Recommend phased approach or earnout structure

**NO_GO (Score <60)**
- Strategic fit unclear or weak
- Unfavorable financial economics or valuation
- Integration risk overwhelming
- Critical deal breakers identified
- Better opportunities likely available

## Gate Logic

- **GO** - Overall score >75, no unmitigated deal breakers, integration feasible, valuation reasonable
- **NO_GO** - Overall score <60, deal breaker identified, integration risk unacceptable, better alternatives available
- **CONDITIONAL** - Score 60-75, with specific conditions identified and remediation feasible

## Sensitivity Analysis

Identify key assumptions most sensitive to outcome:
- Revenue growth rate impact on valuation
- Customer churn rate impact on synergies
- Team retention rate impact on integration success
- Integration cost variance scenarios
- Market condition changes

## Risk Assessment Output

- **Critical Risks**: Require executive escalation and mitigation plan
- **Major Risks**: Require contingency planning and monitoring
- **Moderate Risks**: Standard integration management addresses

## Integrations

- All upstream skills - Receives aggregated findings from discovery and DD workstreams

## Related Skills

- All Discovery Skills - Provide strategic context and rationale
- All Due Diligence Skills - Provide detailed risk assessment and financial analysis
- Integration Planning - Provides feasibility assessment and execution plan

## Used By

- Command: `/corporate-development:recommend`
- Agent: `deal-advisor`
- Final decision input to executive steering committee

