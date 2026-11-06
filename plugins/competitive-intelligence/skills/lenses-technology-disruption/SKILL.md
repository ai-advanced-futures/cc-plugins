---
name: lenses-technology-disruption
description: Runs when the lens executor or the skill analyze needs the technology disruption lens. It assesses the risk from AI platforms and new technology.
user-invocable: false
---

# Technology Disruption Assessment Lens

## Purpose

Assess whether AI platforms or emerging technologies could disrupt the market because technology shifts can obsolete products faster than competitive dynamics.

## Input Required

- `intelligence-data.json` - Competitive data
- `jtbd-analysis.json` - Job steps (for replaceability assessment)
- `context-config.json` - Scope

## Multi-Factor Assessment Framework

### Factor 1: Capability Maturity

Can AI/technology do this job?

| Level | Description | Timeline |
|-------|-------------|----------|
| Current | AI does this well today | Now |
| Emerging | AI can do this in 12-24 months | Near-term |
| Potential | AI might eventually do this | Long-term |
| Unlikely | Structural barriers to AI | Protected |

### Factor 2: Economic Feasibility

Is AI/tech more cost-effective?

- API costs vs software subscription
- Total cost of ownership
- Implementation and maintenance
- Economies at scale

### Factor 3: Adoption Barriers

What prevents adoption?

**Technical barriers:**
- Integration complexity
- Reliability requirements
- Security/compliance needs
- Data requirements

**Organizational barriers:**
- Change management
- Trust and accountability
- Skill requirements
- Cultural resistance

**Workflow barriers:**
- Process redesign needed
- Existing tool dependencies
- Collaboration requirements

### Factor 4: Timing

How quickly could disruption occur?

- Leading indicators
- Adoption curve signals
- Investment trends
- Regulatory changes

## Specific Assessments

### A. Job Replaceability

For each job step from JTBD analysis:
- Can AI platforms do this step directly?
- What quality level vs. dedicated software?
- What's the trend trajectory?

Example: "Claude, generate this report" vs dedicated reporting software

### B. Feature Commoditization

Which features become trivial with AI?
- Template generation
- Data analysis
- Content creation
- Basic automation

What remains differentiating?
- Complex workflows
- Deep integrations
- Domain expertise
- Regulatory compliance

### C. DIY Enablement

Can customers build their own with AI + basic tools?
- Effort required
- Quality achievable
- Maintenance burden
- Total cost comparison

### D. Unbundling Risk

Can AI do specific job steps better than integrated product?
- Cherry-pick best-of-breed AI for each step
- Does integration remain valuable?
- Platform vs point solution dynamics

### E. Integration Bypass

Can AI eliminate need for middleware/connectors?
- AI as universal translator
- Direct API access
- Workflow automation

## Process

### 1. Job Step Disruption Mapping

For each job step:
```
Step 3: Generate report
- AI Capability: High (GPT-4, Claude do this well)
- Economic Feasibility: Medium (API costs add up at scale)
- Adoption Barriers: Low (easy to try)
- Timing: Now (already happening)
- Disruption Risk: HIGH
```

### 2. Aggregate Assessment

Calculate overall disruption risk:
- % of job steps at risk
- Timeline to significant impact
- Defensible capabilities
- Strategic response options

### 3. Competitive Disruption Comparison

How exposed are competitors?
- Same risks apply to all?
- Different exposure levels?
- Who's responding better?

## Output Format

Generate `technology-disruption.json`:

```json
{
  "overall_assessment": {
    "disruption_risk": "medium-high",
    "timeline": "12-24 months",
    "confidence": "medium"
  },
  "job_step_analysis": [
    {
      "step_id": "step-3",
      "description": "Generate report",
      "disruption_assessment": {
        "capability_maturity": "current",
        "economic_feasibility": "medium",
        "adoption_barriers": "low",
        "timing": "now"
      },
      "risk_level": "high",
      "ai_alternative": "Claude/GPT-4 with templates",
      "quality_comparison": "80% of dedicated tool quality",
      "confidence": "high"
    }
  ],
  "feature_analysis": {
    "commoditizing": [
      {
        "feature": "Basic report generation",
        "timeline": "now",
        "impact": "table stakes, no longer differentiating"
      }
    ],
    "defensible": [
      {
        "feature": "Compliance workflow orchestration",
        "reason": "Requires deep domain expertise + integrations",
        "timeline": "3+ years protected"
      }
    ]
  },
  "competitive_exposure": {
    "your_product": {
      "exposure": "medium",
      "at_risk_revenue": "30%",
      "defensible_revenue": "70%"
    },
    "competitor_a": {
      "exposure": "high",
      "at_risk_revenue": "50%",
      "defensible_revenue": "50%"
    }
  },
  "strategic_recommendations": [
    {
      "recommendation": "Invest in workflow orchestration, not content generation",
      "rationale": "Content generation commoditizing, orchestration remains defensible",
      "confidence": "high"
    },
    {
      "recommendation": "Integrate AI capabilities rather than compete",
      "rationale": "Augment with AI rather than replace",
      "confidence": "medium"
    }
  ]
}
```

## Philosophy

### Disruption is real

AI platforms are competitors.
"Why not just use Claude?" is a valid question.
Denial is not a strategy.

### Defensible niches

Not everything gets disrupted equally.
Complex workflows, integrations, compliance remain valuable.
Find and defend your niches.

### Adapt to survive

Integrate AI rather than compete.
Augmentation beats replacement.
Embrace rather than fear.

## Cascading Outputs

This lens informs:
- **Synthesis:** Strategic risks from technology
- **Recommendations:** Build vs integrate decisions

## Completion Protocol

After writing all output files:

**Write technology-summary.json** to `data_dir` (from dispatch context):
{
  "lens": "technology-disruption",
  "completed_at": "{ISO 8601 timestamp}",
  "competitors_analyzed": N,
  "headline": "High AI disruption risk: job steps {list}; {top_competitor} leads AI investment",
  "key_findings": [
    "High disruption risk steps: {list} ({rationale})",
    "Low disruption risk steps: {list}",
    "AI leader: {competitor} ({capability})",
    "Your AI exposure: {High|Medium|Low} ({timeline})"
  ],
  "confidence": "{HIGH|MEDIUM|LOW|SPECULATIVE}",
  "warnings": [],
  "data_file": "technology-disruption.json"
}

**Return to caller:** DONE: lens-technology
