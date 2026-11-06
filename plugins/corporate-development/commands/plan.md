---
description: Phase 5. Write the 100-day integration plan for one target.
argument-hint: "[--target <id or name>]"
---
# /corporate-development:plan

Create post-acquisition integration plan with 100-day roadmap, risk mitigation strategies, and team integration approach.

## When to use

- After financial analysis confirms deal attractiveness
- Before proceeding to final investment decision
- When you've passed all due diligence gates (assess, audit, analyze)
- Planning the actual acquisition integration work
- Building stakeholder alignment on integration approach

## What it does

1. **Integration Strategy Development** - Creates integration approach and timeline
2. **100-Day Planning** - Develops detailed day 100 integration roadmap
3. **Risk Mitigation Planning** - Addresses risks identified in audit and analyze phases
4. **Team Integration Design** - Plans organizational structure and team integration
5. **Success Metrics Definition** - Establishes KPIs to track integration progress
6. **Integration Timeline** - Creates phased integration schedule

## Required Input

```bash
/corporate-development:plan --target TARGET_ID
```

Or run interactively:
```bash
/corporate-development:plan
```

You'll provide:
- Target company ID
- Integration priority areas
- Timeline constraints
- Resource availability
- Key risks to mitigate

## Interactive Flow

```
Which target would you like to plan integration for?
Target ID or name: target_001

Integration Approach:
1. Integration strategy (full merge / maintain brand / semi-autonomous): Full merge
2. Timeline pressure (0-3 months / 3-6 months / 6-12 months): 6-12 months
3. Talent retention criticality (very high / high / medium): Very high
4. Customer continuity requirement (critical / important / standard): Critical

Day 100 Priorities (rank top 5):
1. Retain all key personnel
2. Consolidate customer relationships
3. Integrate sales teams
4. Establish technology roadmap
5. Define combined go-to-market strategy

Specific Risks to Address:
1. Technical debt mitigation timeline: 18 months phased
2. Customer change of control notifications: Week 1
3. Key person retention: Retention bonus structure
4. Sales team integration: Parallel territories approach

Post-Integration Success Metrics:
1. Customer retention (target %): 95%
2. Revenue growth target: 25% YoY
3. Team turnover (target %): <10%
4. Integration cost (budget $M): 2.5
```

The command creates comprehensive integration plan.

## Outputs

**integration_plan.json** - Complete integration planning document
```json
{
  "plan_date": "2026-02-03",
  "target": {
    "id": "target_001",
    "company_name": "Example Inc",
    "acquisition_date": "2026-04-01"
  },
  "integration_strategy": {
    "approach": "FULL_MERGE",
    "timeline_months": 12,
    "target_integration_cost": 2500000,
    "integration_lead": "VP Integration",
    "integration_team_size": 8
  },
  "day_100_roadmap": {
    "week_1": [
      {
        "initiative": "Executive alignment",
        "owner": "CEO",
        "effort": "Low",
        "risk_level": "Low",
        "description": "Establish integration governance, kickoff meetings"
      },
      {
        "initiative": "Customer communication",
        "owner": "VP Sales",
        "effort": "High",
        "risk_level": "High",
        "description": "Notify customers, manage change of control notifications"
      }
    ],
    "week_2_4": [
      {
        "initiative": "Team structure definition",
        "owner": "HR Director",
        "effort": "High",
        "risk_level": "Medium",
        "description": "Define org structure, identify overlaps, plan consolidation"
      },
      {
        "initiative": "Retention program launch",
        "owner": "VP People",
        "effort": "Medium",
        "risk_level": "Medium",
        "description": "Execute retention bonuses, long-term incentive plan"
      }
    ],
    "week_5_13": [
      {
        "initiative": "System integration planning",
        "owner": "CTO",
        "effort": "High",
        "risk_level": "High",
        "description": "Develop technology integration roadmap, identify critical systems"
      },
      {
        "initiative": "Sales team alignment",
        "owner": "VP Sales",
        "effort": "High",
        "risk_level": "Medium",
        "description": "Integrate sales teams, define territories, align compensation"
      }
    ]
  },
  "risk_mitigation": [
    {
      "risk": "Key person turnover",
      "probability": "HIGH",
      "impact": "HIGH",
      "mitigation_strategy": "Retention bonuses for top 5, defined career paths",
      "owner": "CHRO",
      "timeline": "Immediate"
    },
    {
      "risk": "Customer churn",
      "probability": "MEDIUM",
      "impact": "HIGH",
      "mitigation_strategy": "Dedicated customer success team, quarterly business reviews",
      "owner": "VP CS",
      "timeline": "Weeks 1-4"
    },
    {
      "risk": "Technology integration delays",
      "probability": "MEDIUM",
      "impact": "MEDIUM",
      "mitigation_strategy": "Detailed integration roadmap, phased approach, parallel systems",
      "owner": "CTO",
      "timeline": "Weeks 5-26"
    }
  ],
  "team_integration": {
    "organizational_structure": "Centralized with target as P&L",
    "reporting_lines": "Target CEO → VP Integration → CEO",
    "key_roles_mapped": [
      {
        "role": "CEO",
        "action": "Stay through year 1 (retention bonus)"
      },
      {
        "role": "CTO",
        "action": "Report to our CTO, lead technology roadmap"
      }
    ],
    "retention_plan": {
      "critical_roles_count": 5,
      "retention_bonus_budget": 500000,
      "vesting_cliff": "12 months",
      "back_half_vesting": "24 months"
    }
  },
  "success_metrics": {
    "customer_retention_target": 0.95,
    "employee_retention_target": 0.90,
    "revenue_growth_target": 0.25,
    "integration_budget_target": 2500000,
    "day_100_milestones": [
      "Customer communication complete",
      "Team structure finalized",
      "Retention agreements signed",
      "Technology roadmap defined"
    ]
  },
  "next_step": "recommend"
}
```

**integration_roadmap.md** - Executive summary with:
- Integration strategy overview
- 100-day roadmap summary with key milestones
- Risk mitigation plan with owner and timeline
- Team integration and retention strategy
- Success metrics and tracking dashboard
- Monthly integration progress template

## Integration Planning Framework

**Phase 1: Foundation (Weeks 1-4)**
- Establish governance and integration team
- Customer communication and retention
- Team structure planning
- Critical system inventory

**Phase 2: Alignment (Weeks 5-13)**
- Detailed technology roadmap
- Sales team integration
- HR/compensation alignment
- Initial synergy capture

**Phase 3: Execution (Weeks 14-26)**
- System integration work begins
- Organizational consolidation
- Process alignment
- Cross-functional initiatives

**Phase 4: Stabilization (Months 7-12)**
- Post-integration optimization
- Knowledge capture and documentation
- Performance improvement initiatives
- Long-term integration completion

## Day 100 Roadmap Structure

Each initiative includes:
- **Owner** - Who's accountable
- **Effort** - Resource requirement (Low/Medium/High)
- **Risk Level** - Execution risk
- **Completion Target** - Within day 100
- **Success Criteria** - How we measure success
- **Dependencies** - Other initiatives that must happen first

## Risk Mitigation Planning

For each major risk identified in audit/analyze phases:

```
Risk Category → Detection Method → Prevention → Response Plan

Personnel Risks:
  - Top person departures → Retention agreements → Bonus/career path → Succession plan

Technology Risks:
  - Integration delays → Architecture review → Phased approach → Parallel systems

Customer Risks:
  - Customer churn → Customer surveys → Business reviews → Win-back program

Regulatory Risks:
  - Compliance gaps → Compliance audit → Remediation plan → External counsel
```

## Team Integration Approach

Three integration models:

**Full Merge** - Combined org under unified structure
- Best for: Complementary capabilities, strategic integration
- Timeline: 6-12 months
- Complexity: High
- Cost: Higher

**Maintain Semi-Autonomous** - Keep separate with connection points
- Best for: Distinct markets, different business models
- Timeline: 3-6 months
- Complexity: Medium
- Cost: Medium

**Brand Consolidation** - Merge brand/market but separate operations initially
- Best for: Brand value, customer relationships
- Timeline: 6-12 months
- Complexity: Medium-High
- Cost: Medium-High

## Success Metrics Framework

**Customer Metrics**
- Retention rate (target 95%+)
- NPS trend (should not drop)
- Revenue from target (maintain/grow)

**Employee Metrics**
- Retention rate (target 90%+)
- Engagement scores
- Turnover of key roles

**Financial Metrics**
- Synergy realization (target 80%+ in year 1)
- Integration budget variance (target ±10%)
- Revenue growth (maintain plan)

**Integration Metrics**
- Milestones on schedule
- Risk issues resolved
- Stakeholder satisfaction

## Next Steps

After plan completes:

1. **If integration plan is solid**:
   - Proceed to final recommendation
   ```bash
   /corporate-development:recommend --target target_001
   ```

2. **If risks require additional mitigation**:
   - Develop detailed mitigation plans
   - Refine integration timeline
   - Identify resource needs

3. **For executive review**:
   - Present roadmap to board/exec team
   - Get buy-in on integration approach
   - Secure integration budget approval

## Related Skills

- `/corporate-development:audit` - Risk identification input
- `/corporate-development:analyze` - Synergy and cost data
- `/corporate-development:recommend` - Final deal recommendation
- Change management and organizational design frameworks
- Integration playbooks and best practices

## Integrations

- Project management tools (Jira, Asana)
- HR systems for team mapping
- Financial systems for synergy tracking
- Communication tools for stakeholder management
- CRM for customer tracking
