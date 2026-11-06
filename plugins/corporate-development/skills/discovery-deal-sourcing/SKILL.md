---
name: discovery-deal-sourcing
description: Identify, qualify, and pipeline acquisition targets from market data
---

# Deal Sourcing

Systematically identifies, qualifies, and pipelines potential acquisition targets by scanning market data, applying strategic criteria, and scoring opportunities based on fit and strategic value.

## What It Does

- Scans market databases and data sources for potential acquisition targets
- Qualifies prospects against buyer's strategic criteria and investment thesis
- Scores targets on market fit, technology fit, and acquisition viability
- Manages target pipeline with stage tracking (pipeline, qualified, interested, negotiating)
- Identifies synergy opportunities and strategic value drivers
- Tracks competitive landscape for each target
- Monitors market signals and transaction trends

## How to Use

This skill is invoked at the start of the acquisition investigation process. It identifies a universe of potential targets and narrows them down to a manageable set of qualified prospects ready for deeper assessment. Results from deal sourcing feed directly into target assessment.

## Inputs

```json
{
  "investment_thesis": {
    "strategic_priorities": ["string"],
    "target_market": "string",
    "revenue_range_min": "number",
    "revenue_range_max": "number",
    "geography": ["string"],
    "technology_focus": ["string"]
  },
  "search_criteria": {
    "industry_verticals": ["string"],
    "company_size": "string",
    "stage": "string",
    "growth_rate_min": "number"
  },
  "data_sources": ["string"],
  "exclusion_criteria": {
    "companies": ["string"],
    "industries": ["string"]
  }
}
```

## Outputs

```json
{
  "target_list": [
    {
      "company_id": "string",
      "company_name": "string",
      "industry": "string",
      "revenue_estimate": "number",
      "growth_rate": "number",
      "geography": ["string"],
      "key_products": ["string"],
      "fit_score": "number",
      "strategic_value": "string",
      "pipeline_stage": "string",
      "source": "string",
      "data_confidence": "number"
    }
  ],
  "pipeline_summary": {
    "total_identified": "number",
    "qualified": "number",
    "pipeline_stage_distribution": "object"
  },
  "market_insights": {
    "transaction_trends": "string",
    "competitive_activity": "string",
    "market_opportunities": ["string"]
  }
}
```

## Scoring Methodology

- **Fit Score (1-100)**: Evaluates strategic fit based on investment thesis alignment (40%), market position (30%), technology stack (20%), team quality (10%)
- **Acquisition Viability (1-10)**: Assesses likelihood of successful acquisition based on size, growth trajectory, and regulatory environment
- **Synergy Potential (1-10)**: Identifies potential for cost synergies, revenue synergies, and technology leverage

## Gate Logic

- **GO** - Target has fit score >75, acquisition viability >7, and strategic alignment with buyer priorities
- **NO_GO** - Target fit score <50, regulatory/compliance barriers exist, or direct competitor conflict
- **CONDITIONAL** - Go to deep assessment phase if fit score 50-75 or synergy potential is high despite lower fit

## Integrations

- **competitive-intelligence** - Leverages market data, competitor tracking, and transaction history
- **tech-budget** - Considers technology stack alignment and acquisition cost estimates

## Related Skills

- Target Assessment - Evaluates strategic fit and differentiation of sourced deals
- Financial Due Diligence - Analyzes unit economics and financial health

## Used By

- Command: `/corporate-development:discover`
- Agent: `deal-sourcer`

## Pipeline Stages

- **Pipeline**: Initial identification, needs qualification
- **Qualified**: Meets basic criteria, ready for deeper assessment
- **Interested**: Target has shown acquisition interest or fit is confirmed
- **Negotiating**: Deal terms being discussed
- **Archived**: Removed from active pipeline due to changed circumstances

