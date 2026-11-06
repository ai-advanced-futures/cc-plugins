---
name: execution-integration-planning
description: Create detailed post-acquisition integration roadmap and day-100 plan
---

# Integration Planning

Develops a comprehensive post-acquisition integration roadmap that outlines key workstreams, milestones, risks, and resource requirements for the first 100 days and beyond to ensure smooth organizational integration and value realization.

## What It Does

- Creates detailed day-100 integration roadmap with phased milestones
- Plans customer communication strategy and retention measures
- Develops product integration approach and timeline
- Plans technology integration and infrastructure consolidation
- Plans team integration, org structure, and retention strategy
- Identifies critical success factors and integration milestones
- Estimates integration costs and resource requirements
- Assesses integration risks and mitigation strategies
- Develops executive and stakeholder communication plan
- Creates integration governance and decision-making framework
- Generates integration project schedule and dependencies

## How to Use

Integration Planning is performed after the GO decision to move forward with acquisition. It translates the findings from due diligence into an actionable integration roadmap that guides the post-close team. This skill should be informed by all due diligence findings, especially operational, financial, and product assessments.

## Inputs

```json
{
  "deal_info": {
    "target_company": "string",
    "acquisition_price": "number",
    "close_date": "string",
    "strategic_rationale": "string"
  },
  "integration_priorities": [
    "customer_retention",
    "product_integration",
    "technology_consolidation",
    "team_integration",
    "cost_synergies"
  ],
  "due_diligence_findings": {
    "operational_summary": "string",
    "financial_summary": "string",
    "product_integration_opportunities": ["string"],
    "key_risks": ["string"]
  },
  "integration_constraints": {
    "budget": "number",
    "timeline_days": "number",
    "resource_availability": "string"
  }
}
```

## Outputs

```json
{
  "integration_roadmap": {
    "timeline": "string",
    "phases": [
      {
        "phase": "string",
        "duration_days": "number",
        "key_milestones": ["string"],
        "critical_path_activities": ["string"]
      }
    ]
  },
  "workstreams": [
    {
      "workstream": "string",
      "objectives": ["string"],
      "activities": ["string"],
      "timeline": "string",
      "owner": "string",
      "dependencies": ["string"],
      "resource_requirement": "number",
      "budget": "number"
    }
  ],
  "customer_integration": {
    "retention_strategy": "string",
    "communication_plan": {
      "announcement": "string",
      "key_messages": ["string"],
      "timeline": "string"
    },
    "customer_success_plan": ["string"],
    "pricing_and_packaging_changes": "string"
  },
  "product_integration": {
    "integration_approach": "string",
    "product_roadmap_changes": "string",
    "technology_consolidation_plan": "string",
    "integration_timeline": "string",
    "estimated_engineering_effort": "string"
  },
  "team_integration": {
    "organizational_structure": "string",
    "role_mapping": ["string"],
    "retention_strategy": {
      "key_persons": ["string"],
      "retention_agreements": ["string"],
      "incentives": ["string"]
    },
    "cultural_integration": ["string"]
  },
  "cost_synergies": [
    {
      "synergy": "string",
      "category": "string",
      "estimated_savings": "number",
      "timeline_to_realization": "string",
      "risks": ["string"]
    }
  ],
  "revenue_synergies": [
    {
      "synergy": "string",
      "description": "string",
      "estimated_uplift": "number",
      "timeline": "string"
    }
  ],
  "integration_risks": {
    "critical_risks": [
      {
        "risk": "string",
        "impact": "string",
        "mitigation": "string"
      }
    ],
    "contingency_plans": ["string"]
  },
  "integration_governance": {
    "governance_structure": "string",
    "steering_committee": ["string"],
    "decision_making_cadence": "string",
    "communication_plan": "string"
  },
  "integration_budget": {
    "total_integration_cost": "number",
    "by_workstream": "object",
    "contingency": "number"
  },
  "success_metrics": {
    "customer_retention": "number",
    "employee_retention": "number",
    "product_integration_completion": "number",
    "synergy_realization": "number"
  }
}
```

## Integration Workstreams

- **Customer Integration**: Retention, communication, success planning
- **Product Integration**: Roadmap alignment, feature prioritization, consolidation
- **Technology Integration**: Infrastructure, systems, data migration
- **Team Integration**: Org structure, retention, culture
- **Finance/Operations**: Cost synergies, process harmonization
- **Compliance/Legal**: Contract updates, regulatory filings

## Critical Success Factors

- Customer retention >95% in first 12 months
- Retention of 90%+ of key technical talent
- Synergy realization >80% of plan within 18 months
- Integration project completion within budget
- Successful product integration with no major service disruptions

## Gate Logic

- **GO** - Clear integration path, identified workstreams, risk mitigation strategies, committed resources
- **NO_GO** - Integration complexity overwhelming, key resource unavailable, strategic fit unclear
- **CONDITIONAL** - Proceed with modified timeline, reduced scope, or additional resources

## Integrations

- **tech-budget** - Technology integration costs, infrastructure requirements (optional plugin)

## Related Skills

- Deal Recommendation - Provides deal context and strategic rationale
- Operational Due Diligence - Team and process integration insights
- Financial Due Diligence - Cost and synergy basis
- Product Due Diligence - Product integration approach

## Used By

- Command: `/corporate-development:plan`
- Agent: `integration-planner`

