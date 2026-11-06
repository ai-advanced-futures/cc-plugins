---
name: due-diligence-product-dd
description: Assess product market fit, differentiation, and roadmap alignment
---

# Product Due Diligence

Comprehensive evaluation of the target's product offering, market fit, competitive differentiation, and strategic alignment with buyer's product vision to assess the value of the acquisition and integration feasibility.

## What It Does

- Evaluates product-market fit strength and validation evidence
- Analyzes competitive differentiation and unique value proposition
- Reviews product roadmap alignment with buyer's strategic direction
- Assesses UX/design quality and product usability
- Evaluates feature set completeness and roadmap maturity
- Reviews customer feedback on product positioning
- Analyzes product innovation rate and technical roadmap
- Identifies product integration opportunities and complexity
- Assesses product compliance and security features
- Reviews product moat and defensibility

## How to Use

Product Due Diligence is conducted during the comprehensive investigation phase to understand the strategic value of the product and identify opportunities for integration with the buyer's product portfolio. Strong product-market fit and differentiation validate the acquisition rationale and reduce integration risk.

## Inputs

```json
{
  "product_info": {
    "product_name": "string",
    "primary_features": ["string"],
    "target_market": "string",
    "pricing_model": "string"
  },
  "market_position": {
    "market_size": "number",
    "target_addressable_market": "number",
    "market_share": "number"
  },
  "competitive_data": {
    "primary_competitors": ["string"],
    "differentiation_factors": ["string"]
  }
}
```

## Outputs

```json
{
  "product_market_fit": {
    "pmf_score": "number",
    "pmf_validation": "string",
    "customer_demand_indicators": ["string"],
    "market_traction": "string"
  },
  "competitive_analysis": {
    "competitive_positioning": "string",
    "unique_value_proposition": "string",
    "differentiation_factors": ["string"],
    "competitive_advantages": {
      "technology": ["string"],
      "features": ["string"],
      "cost": ["string"]
    },
    "competitive_vulnerabilities": ["string"]
  },
  "product_quality": {
    "ux_assessment": "string",
    "design_quality_score": "number",
    "usability_score": "number",
    "feature_completeness": "string"
  },
  "roadmap_alignment": {
    "buyer_strategic_fit": "string",
    "integration_opportunities": ["string"],
    "feature_gaps": ["string"],
    "alignment_score": "number"
  },
  "technical_assessment": {
    "technology_stack": ["string"],
    "technical_debt_level": "string",
    "scalability": "string",
    "security_posture": "string"
  },
  "product_moat": {
    "defensibility_score": "number",
    "barriers_to_entry": ["string"],
    "patent_ip_protection": "string"
  },
  "innovation_assessment": {
    "innovation_rate": "string",
    "r_and_d_focus": "string",
    "emerging_opportunities": ["string"]
  },
  "product_risks": {
    "key_risks": ["string"],
    "obsolescence_risk": "string",
    "integration_complexity": "string"
  },
  "product_health_score": "number"
}
```

## Scoring Methodology

- **Product-Market Fit (1-10)**: Customer demand validation (30%), market traction (30%), pricing power (20%), retention indicators (20%)
  - Strong fit: High retention, pricing power, customer pull
  - Weak fit: High churn, price resistance, feature request churn
- **Differentiation (1-10)**: Unique technology (35%), feature leadership (30%), market positioning (20%), customer perception (15%)
- **UX/Design Quality (1-10)**: Usability score (40%), design consistency (30%), accessibility (20%), modern UX patterns (10%)
- **Roadmap Alignment (1-10)**: Strategic fit (40%), integration ease (30%), feature gap closure (20%), resource requirements (10%)

## Product-Market Fit Indicators

- **Strong**: High retention, customers request new features (not fixes), pricing power, word-of-mouth adoption
- **Moderate**: Stable customer base, feature/fix request balance, some pricing traction
- **Weak**: High churn, primarily bug/fix requests, price sensitivity, acquisition-driven growth

## Gate Logic

- **GO** - PMF score >7, differentiation >7, design quality >7, roadmap alignment >7, strong market traction
- **NO_GO** - PMF score <5, weak differentiation, significant integration complexity, or questionable market viability
- **CONDITIONAL** - Proceed if scores 5-7 with clear product strategy for strengthening fit or differentiation

## Integrations

- **ux-hci-design** - UX assessment, design quality evaluation, usability testing
- **competitive-intelligence** - Competitive positioning, market analysis, feature benchmarking
- **tech-budget** - Technical stack evaluation, modernization assessment

## Related Skills

- Target Assessment - Product differentiation validates strategic rationale
- Operational Due Diligence - Product development team capability
- Customer Due Diligence - NPS and retention validate product quality
- Financial Due Diligence - Unit economics supported by product-market fit

## Used By

- Command: `/corporate-development:audit`
- Agent: `product-strategist`

