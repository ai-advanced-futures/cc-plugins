---
name: due-diligence-operational-dd
description: Conduct operational due diligence on acquisition target
---

# Operational Due Diligence

Assess operational health of acquisition target across 5 key dimensions.

## When to Use

Use this skill when:
- Performing Phase 3 operational assessment
- Target has passed financial screening (Phase 4)
- Need comprehensive operational readiness evaluation

## Process

### 1. Gather Target Information

Ask for:
- **Target company name**
- **Optional: Upload files** (org charts, tech docs, product docs, operations docs, market analysis)

### 2. Assess Each Dimension

#### Team Assessment (25% weight)
- Leadership quality (0-100)
- Skill coverage (0-100)
- Retention rate (0.0-1.0)
- Key person dependency risk (Yes/No)
- Headcount

**Current Plugin Integration:**
- ✅ `team-assessment` - Enhanced org structure and retention risk analysis

#### Technology Assessment (25% weight)
- Technology stack (list)
- Architecture quality (0-100)
- Technical debt level (LOW/MEDIUM/HIGH)
- Scalability score (0-100)
- Code repository URL (optional)

**Current Plugin Integration:**
- ✅ `tech-budget` - Enhanced technical debt and integration cost analysis

#### Product Assessment (20% weight)
- Product quality (0-100)
- Roadmap clarity (0-100)
- Customer satisfaction (0-100)
- Feature completeness (0-100)

#### Operations Assessment (20% weight)
- Process maturity (0-100)
- Workflow efficiency (0-100)
- Documentation quality (0-100)
- Scalability (0-100)

#### Market Position Assessment (10% weight)
- Competitive standing (0-100)
- Moat strength (0-100)
- Product differentiation (0-100)

### 3. Calculate Operational Health

Weighted average across dimensions:
- Score 70-100: ✅ GO - Strong operational health
- Score 50-69: ⚠️ CONDITIONAL - Proceed with conditions
- Score 0-49: ❌ NO_GO - Significant operational risks

### 4. Generate Reports

Creates 8 detailed reports:
1. `summary.md` - Executive summary
2. `results.json` - Machine-readable results
3. `01_team_assessment.md` - Team dimension details
4. `02_technology_assessment.md` - Technology dimension details
5. `03_product_assessment.md` - Product dimension details
6. `04_operations_assessment.md` - Operations dimension details
7. `05_market_position_assessment.md` - Market dimension details
8. `06_risk_analysis.md` - Aggregated risk analysis
9. `07_recommendations.md` - Actionable recommendations

All artifacts saved to: `.corporate-development/targets/{target-slug}/phase_3_operational_dd/`

### 5. Plugin Integration (Optional)

Enhances assessment when available:
- **team-assessment plugin**: Deeper team structure analysis
- **tech-budget plugin**: Technology cost insights

## Risk Identification

Three severity levels:
- `CRITICAL`: Immediate blockers requiring resolution
- `WARNING`: Concerns needing attention during integration
- **INFO**: Awareness items for planning

## Example Interaction

```
You: Run operational due diligence on Acme Corp

Claude: I'll conduct operational due diligence on Acme Corp across 5 dimensions.

[Interactive Q&A for each dimension]

Claude: Assessment complete!

**Overall Operational Health:** 78/100
**Gate Decision:** ✅ GO
**Risks:** 2 WARNING, 1 INFO

Generated 8 detailed reports in `.corporate-development/targets/acme-corp/phase_3_operational_dd/`
```

## Output Artifacts

All artifacts saved to: `.corporate-development/targets/{target-slug}/phase_3_operational_dd/`

Previous runs automatically archived to: `history/phase_3_operational_dd_{timestamp}/`

## Optional plugins

These plugins can help with some dimensions. Use a plugin only when Claude Code has it. If a plugin is not there, the assessment goes on without it, and the report says which plugin it did not use.

### Team Dimension (25%)
- **team-assessment** - Org structure, retention risk

### Technology Dimension (25%)
- **tech-budget** - Technical debt, integration costs
- **product** - Technology roadmap and architecture documentation

### Product Dimension (20%)
- **ux-hci-design** - Product design quality and UX maturity
- **product** - Product roadmap clarity and feature completeness
- **product-finance** - Unit economics and product profitability

### Operations Dimension (20%)
- **product** - Process documentation and operational workflows
- **product-finance** - Operational efficiency metrics

### Market Position Dimension (10%)
- **competitive-intelligence** - Competitive position and market threats
- **jtbd-market-discovery** - Customer job validation and willingness-to-pay

### Contracts
- **tech-contracts** - Contract risk review, called with the `Skill` tool

## Related Skills

- **financial-dd** - Revenue sustainability tied to team quality
- **product-dd** - Product execution tied to tech and team capability
- **integration-planning** - Operationalization of findings into day-100 roadmap

## Used By

- Command: `/corporate-development:audit`
- Agent: `operational-auditor`
