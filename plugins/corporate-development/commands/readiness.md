---
description: Phase 0. Check if the buyer is ready to acquire, and set the criteria for a target.
argument-hint: "[company name]"
---
# /corporate-development:readiness

Assess organizational readiness and define strategic acquisition criteria before initiating M&A activities.

## When to use

- Before starting any M&A investigation
- Evaluating if your organization is ready for acquisitions
- Defining strategic acquisition criteria
- Assessing CEO and leadership team readiness
- Establishing clear acquisition targets and parameters

## What it does

This is the foundational phase that ensures your organization is prepared for successful acquisitions. It evaluates readiness across five key contexts:

1. **CEO Readiness Assessment** - Evaluate leadership preparedness using the 3 A's framework (Attitude, Aptitude, Action)
2. **Strategic Target Definition** - Define clear acquisition criteria, market focus, and strategic priorities
3. **Organizational Capacity** - Assess integration capabilities, resources, and cultural readiness
4. **Financial Readiness** - Evaluate capital availability, valuation approach, and deal structure preferences
5. **Governance Framework** - Establish decision gates, approval processes, and risk thresholds

## Assessment Contexts

### 1. CEO Readiness (3 A's Framework)

**Attitude Assessment**:
- Growth mindset and learning orientation
- Resilience and handling of pressure
- Self-awareness and humility
- Integrity and ethical decision-making

**Aptitude Assessment**:
- Strategic thinking and vision
- Business acumen and decision quality
- Leadership and communication capability
- M&A experience and understanding

**Action Assessment**:
- Execution track record
- Change leadership experience
- Problem-solving in complex situations
- Accountability and results delivery

**Evaluation Methods**:
- Self-assessment interview
- Proxy assessment (mentor/advisor input)
- Team assessment (360 feedback)
- Board assessment (governance perspective)
- Profile assessment (objective background analysis)

### 2. Strategic Target Definition

**Target Profile Criteria**:
- Industry and market segments
- Revenue range and growth rate
- Geographic preferences
- Technology stack alignment
- Business model fit

**Strategic Value Drivers**:
- Market access and expansion
- Technology and IP acquisition
- Talent and team capabilities
- Customer base and relationships
- Operational synergies

**Acquisition Objectives**:
- Buy vs. Build decision framework
- Strategic gaps to address
- Competitive positioning goals
- Timeline and urgency factors

### 3. Organizational Capacity Assessment

**Integration Capabilities**:
- Prior M&A experience
- Integration team availability
- Process maturity and documentation
- Change management capability

**Resource Readiness**:
- Dedicated M&A team or resources
- External advisor relationships
- Legal and financial support
- Technical due diligence capability

**Cultural Alignment**:
- Organizational values and culture
- Integration philosophy (autonomy vs. absorption)
- Communication approach
- Employee engagement readiness

### 4. Financial Readiness

**Capital Structure**:
- Available capital for acquisitions
- Funding sources (cash, debt, equity)
- Board approval thresholds
- Deal size parameters

**Valuation Approach**:
- Valuation methodologies preferred
- Multiple ranges by industry
- Synergy valuation methodology
- Earnout and structure preferences

**Financial Thresholds**:
- Minimum revenue and growth requirements
- Profitability expectations
- Customer concentration limits
- Churn rate thresholds

### 5. Governance Framework

**Decision Gates**:
- Phase-by-phase approval process
- GO/NO_GO decision criteria
- Escalation procedures
- Timeline expectations per phase

**Risk Management**:
- Risk tolerance levels
- Deal breaker criteria
- Due diligence requirements
- Post-acquisition monitoring

**Stakeholder Management**:
- Board communication cadence
- Internal stakeholder alignment
- External advisor engagement
- Documentation requirements

## Outputs

**readiness_assessment.json** - Comprehensive readiness evaluation
```json
{
  "assessment_date": "2026-02-04",
  "ceo_readiness": {
    "attitude_score": 8.5,
    "aptitude_score": 7.8,
    "action_score": 8.2,
    "overall_rating": "Ready Now",
    "key_strengths": ["Strategic vision", "Execution track record"],
    "development_areas": ["M&A experience", "Integration leadership"]
  },
  "strategic_targets": {
    "industries": ["SaaS", "Developer Tools", "AI/ML"],
    "revenue_range": "$5M-$50M",
    "growth_threshold": "30%+ YoY",
    "geographic_focus": "US-based",
    "strategic_priorities": ["Technology acquisition", "Market expansion"]
  },
  "organizational_capacity": {
    "integration_maturity": "Moderate",
    "resources_available": true,
    "cultural_readiness": "High",
    "prior_mna_experience": "Limited"
  },
  "financial_readiness": {
    "available_capital": "$50M-$100M",
    "preferred_structure": "Cash + Earnout",
    "valuation_approach": "Revenue multiple + Synergy premium",
    "deal_size_range": "$10M-$40M"
  },
  "governance": {
    "decision_gates": "Phase-by-phase board approval",
    "risk_tolerance": "Moderate",
    "timeline_expectation": "3-6 months per deal"
  },
  "readiness_recommendation": "GO",
  "next_phase": "discover"
}
```

**readiness_summary.md** - Executive readiness report with:
- Overall readiness assessment
- CEO and leadership evaluation summary
- Strategic acquisition criteria defined
- Organizational capability gaps and mitigation
- Financial parameters and constraints
- Governance and decision framework
- Recommended next steps

**acquisition_playbook.md** - Strategic guide containing:
- Target profile definition
- Evaluation criteria and weights
- Decision gates and approval process
- Integration approach and philosophy
- Risk management framework
- Success metrics and KPIs

## Interactive Flow

The readiness command walks you through a structured assessment:

```
=== Phase 0: Acquisition Readiness Assessment ===

Part 1: CEO Readiness
- Would you like to conduct a full CEO readiness assessment? (yes/no)
- If yes: Initiates 3 A's framework evaluation
- If no: Records assumption of CEO readiness

Part 2: Strategic Target Definition
- What industries are you targeting? (comma-separated)
- Target company revenue range? ($XM-$YM)
- Minimum growth rate? (%)
- Geographic focus? (US/Europe/Global/etc.)
- Primary acquisition objective? (technology/market/talent/revenue)

Part 3: Organizational Capacity
- Prior M&A experience? (None/Limited/Moderate/Extensive)
- Dedicated M&A resources? (yes/no)
- Integration team size? (number)
- Integration philosophy? (autonomous/collaborative/absorbed)

Part 4: Financial Readiness
- Available acquisition capital? ($XM-$YM)
- Preferred deal structure? (cash/stock/earnout/hybrid)
- Valuation methodology? (revenue_multiple/ebitda/dcf/comparable)
- Maximum deal size? ($XM)

Part 5: Governance Framework
- Board approval required per phase? (yes/no)
- Risk tolerance level? (low/moderate/high)
- Timeline expectations? (X months per deal)
- Deal breaker criteria? (list key exclusions)
```

After completing the assessment, the command generates all output artifacts.

## Readiness Scoring

The readiness assessment produces an overall readiness score (0-100) based on weighted factors:

```
CEO Readiness (30%):
  - Attitude (10%): Growth mindset, character, resilience
  - Aptitude (10%): Strategic thinking, leadership, business acumen
  - Action (10%): Execution track record, results delivery

Strategic Clarity (20%):
  - Clear target definition
  - Aligned acquisition objectives
  - Defined evaluation criteria

Organizational Capability (25%):
  - Integration maturity
  - Resource availability
  - Cultural readiness
  - M&A experience

Financial Preparedness (15%):
  - Capital availability
  - Valuation methodology
  - Structure preferences
  - Financial thresholds

Governance Maturity (10%):
  - Decision framework
  - Risk management
  - Stakeholder alignment

Overall Readiness = Weighted sum of above components
```

## GO/NO_GO Decision Logic

```
Readiness Score:
  ≥ 80: GO - Organization is ready to begin M&A activities
  65-79: CONDITIONAL - Proceed with conditions: capability development recommended
  50-64: CONDITIONAL - Address readiness gaps before active deal sourcing
  < 50: NO_GO - Not ready for acquisitions; focus on capability building

Decision influenced by:
- CEO readiness (critical factor: must be ≥7.0 to proceed)
- Strategic clarity (must have defined targets)
- Financial capacity (must have committed capital)
- Board alignment (must have governance support)
```

Both the 65-79 and 50-64 bands produce a CONDITIONAL gate. The score and reasoning output distinguish the required actions — check the readiness_summary.md artifact for specific recommendations.

## Next Steps

After completing Phase 0 readiness assessment:

1. **If GO**:
   - Proceed to Phase 1: Target Discovery
   ```bash
   /corporate-development:discover
   ```
   - Use strategic criteria from readiness to guide discovery
   - Apply decision gates established in governance framework

2. **If CONDITIONAL**:
   - Address specific capability gaps identified
   - Build out integration team/resources
   - Refine strategic criteria
   - Re-assess readiness in 30-60 days (score 65-79) or 6-12 months (score 50-64)

3. **If NO_GO**:
   - Execute capability development plan
   - Gain M&A experience through smaller transactions
   - Strengthen CEO/leadership team
   - Revisit readiness in 6-12 months

## Method for a phase agent

The pipeline runs this command in the agent `readiness-assessor`, which cannot ask the person. That agent takes the inputs from `phase_inputs` (`company_name`, `ceo_readiness`, `strategic_targets`, `organizational_capacity`, `financial_readiness`, `governance`) and `assessment_date` from the dispatch (the date of today, `YYYY-MM-DD`), and skips each step that asks a question. It writes the artifacts to `.corporate-development/targets/{slug}/phase_0_readiness/` and the handoff to `.corporate-development/targets/{slug}/handoffs/phase_0_handoff.json`. The shape of the handoff is in `${CLAUDE_PLUGIN_ROOT}/docs/phase-handoff.md`. If an input is missing, it writes `.corporate-development/targets/{slug}/handoffs/phase_0_questions.md` with one question for each missing input, writes no handoff, and returns a line `QUESTIONS: <path>`.

## Related Skills

- `/corporate-development:discover` - Phase 1: Target Discovery and Pipeline Management
- CEO Readiness Assessment (evaluation skill)
- Target Definition Framework (evaluation skill)
- Strategic acquisition planning best practices

## Optional plugins

Use these plugins only when Claude Code has them:

- **product-finance** - Financial readiness and valuation methodology
- **team-assessment** - Leadership and organizational capability evaluation
- **competitive-intelligence** - Market analysis and strategic positioning

## Agent

Run alone, this command runs in the main conversation and asks the questions. In the full pipeline, the command `pipeline` starts the agent **readiness-assessor** for Phase 0, and that agent reads this file.

## Success Factors

Key indicators of acquisition readiness:

✓ CEO demonstrates growth mindset and M&A understanding
✓ Clear strategic criteria and target definition
✓ Committed capital with board approval
✓ Integration team and resources identified
✓ Decision gates and governance established
✓ Cultural values and integration philosophy defined
✓ Risk tolerance and deal breakers documented
✓ Stakeholder alignment on acquisition strategy

Red flags indicating lack of readiness:

✗ CEO lacks strategic vision or M&A experience
✗ Unclear acquisition objectives or criteria
✗ No committed capital or board support
✗ No integration resources or plan
✗ Weak governance or decision framework
✗ Cultural misalignment with M&A activity
✗ Unrealistic expectations or risk tolerance
✗ Poor stakeholder communication
