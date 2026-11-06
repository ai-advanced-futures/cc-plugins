---
description: Phase 3. Do the operational due diligence of one target and find its risks.
argument-hint: "[--target <id or name>]"
---
# /corporate-development:audit

Perform operational due diligence: assess organizational structure, technology stack, team quality, and identify risks.

## When to use

- After strategic assessment indicates GO or CONDITIONAL
- Evaluating operational health and integration risk
- Assessing team quality and retention risk
- Identifying technology debt and technical risks
- Before proceeding to financial deep-dive (analyze)

## What it does

1. **Organizational Assessment** - Evaluates team structure, key person risk, org health
2. **Technology Evaluation** - Assesses tech stack, architecture, technical debt, scalability
3. **Process Audit** - Reviews operational processes, sales, customer success, R&D
4. **Risk Identification** - Flags integration risks, technical risks, people risks
5. **Health Scoring** - Generates operational health score (0-100)

## Required Input

```bash
/corporate-development:audit --target TARGET_ID
```

Or run interactively:
```bash
/corporate-development:audit
```

You'll provide:
- Target company ID or name
- Access to target's organizational information
- Assessment of their technology and processes
- Key risk factors you're aware of

## Interactive Flow

```
Which target would you like to audit?
Target ID or name: target_001

Organizational Structure Assessment:
1. Organization size (# of employees): 45
2. Management team experience level: Experienced, 3+ exits each
3. Key person concentration risk (% revenue in top 3): 40%
4. Employee turnover rate (%): 8%
5. Bench strength for key roles (1-10): 4

Technology Stack Review:
1. Primary technology stack: Python, React, PostgreSQL
2. Infrastructure: AWS, Kubernetes, managed services
3. Code quality indicators (1-10): 7
4. Test coverage (%): 65%
5. Technical debt level: Moderate
6. Key architectural concerns: Monolith needs refactoring, scaling at limits

Operational Processes:
1. Sales process maturity (1-10): 6
2. Customer success/retention: 5-year retention 85%
3. R&D efficiency (revenue per R&D dollar): $2.50
4. Product roadmap clarity (1-10): 7
5. Security/compliance practices (1-10): 6

Integration Risk Assessment:
1. System integration difficulty (1-10): 6
2. Data migration complexity (1-10): 7
3. Customer/vendor contracts with change of control clauses: 3 customers require consent
4. Regulatory/compliance concerns: GDPR compliant
```

After assessment, the command analyzes all inputs and generates risk profile and health score.

## Outputs

**audit_report.json** - Comprehensive audit findings
```json
{
  "audit_date": "2026-02-03",
  "target": {
    "id": "target_001",
    "company_name": "Example Inc"
  },
  "organizational_health": {
    "team_size": 45,
    "management_quality_score": 8,
    "key_person_risk": "MODERATE",
    "turnover_rate": 8,
    "bench_strength_score": 4,
    "org_health_score": 72
  },
  "technology_assessment": {
    "tech_stack": ["Python", "React", "PostgreSQL"],
    "infrastructure": "AWS + Kubernetes",
    "code_quality_score": 7,
    "technical_debt": "MODERATE",
    "test_coverage": 65,
    "scalability_concerns": ["Monolith architecture", "Database scaling limits"],
    "tech_health_score": 68
  },
  "operational_processes": {
    "sales_maturity": 6,
    "customer_retention": 0.85,
    "rd_efficiency": 2.50,
    "process_health_score": 72
  },
  "risk_profile": {
    "high_risks": [
      {
        "category": "People",
        "risk": "CEO concentration, limited bench strength",
        "impact": "HIGH",
        "mitigation": "Retention bonuses, succession planning"
      },
      {
        "category": "Technology",
        "risk": "Monolithic architecture limits scalability",
        "impact": "MEDIUM",
        "mitigation": "Phased refactoring plan, 18-month roadmap"
      }
    ],
    "medium_risks": [
      {
        "category": "Integration",
        "risk": "3 customers require change of control consent",
        "impact": "MEDIUM",
        "mitigation": "Customer engagement plan"
      }
    ],
    "low_risks": [
      {
        "category": "Compliance",
        "risk": "GDPR compliance needed in EU",
        "impact": "LOW",
        "mitigation": "Already compliant"
      }
    ]
  },
  "overall_operational_health": 71,
  "integration_risk_level": "MODERATE",
  "next_step": "analyze"
}
```

**audit_summary.md** - Executive summary with:
- Organizational health scorecard
- Technology assessment and technical debt overview
- Key risks with mitigation strategies
- Integration complexity assessment
- Team retention and key person risk analysis
- Recommendations for deeper analysis

## Operational Health Scoring

Overall operational health score (0-100) combines 5 weighted dimensions:

```
Team (25%):
  - Leadership capability and depth: 0-100
  - Skill coverage across critical functions: 0-100
  - Employee retention and culture: 0-100
  - Key person dependency risks: 0-100 (inverted: high dependency = low score)
  - Organizational structure clarity: 0-100

Technology (25%):
  - Technology stack modernity and sustainability: 0-100
  - Architecture quality and scalability: 0-100
  - Technical debt levels: 0-100 (inverted: high debt = low score)
  - Development velocity indicators: 0-100
  - Infrastructure robustness: 0-100

Product (20%):
  - Product quality and user satisfaction: 0-100
  - Roadmap clarity and execution: 0-100
  - Feature completeness vs. market needs: 0-100
  - Customer satisfaction metrics: 0-100
  - Product-market fit indicators: 0-100

Operations (20%):
  - Process maturity and documentation: 0-100
  - Workflow efficiency: 0-100
  - Operational scalability: 0-100
  - Automation and tooling: 0-100
  - Quality control mechanisms: 0-100

Market Position (10%):
  - Competitive standing: 0-100
  - Defensive moat strength: 0-100
  - Product differentiation: 0-100
  - Market trends alignment: 0-100

Overall Health = (Team × 0.25) + (Technology × 0.25) + (Product × 0.20) + (Operations × 0.20) + (Market × 0.10)
```

Gate thresholds:
- **70–100**: ✅ GO
- **50–69**: ⚠️ CONDITIONAL
- **0–49**: ❌ NO_GO

## Risk Classification Framework

```
HIGH RISKS:
  - Key person concentration > 50% revenue
  - Customer concentration > 30% revenue with change of control clauses
  - Critical regulatory non-compliance
  - Severe technical debt blocking scalability

MEDIUM RISKS:
  - Key person concentration 30-50%
  - Integration complexity requiring 6+ months
  - Technology refactoring needed within 12 months
  - Some process/compliance gaps addressable in 6 months

LOW RISKS:
  - Minor technical debt
  - Normal employee turnover
  - Routine compliance/process improvements
  - Scalable architecture with minor updates
```

## Integration Readiness Assessment

Rated on scale of SIMPLE → MODERATE → COMPLEX:

- **SIMPLE** (≤3 months): Minimal system changes, similar tech stacks, no contracts affected
- **MODERATE** (3-6 months): System integration needed, some refactoring, customer communication required
- **COMPLEX** (6-12+ months): Major architecture changes, significant technical debt, multiple contract negotiations

## Next Steps

After audit completes:

1. **If MODERATE or LOW integration risk**:
   - Proceed to financial analysis
   ```bash
   /corporate-development:analyze --target target_001
   ```

2. **If HIGH integration risk**:
   - Develop detailed integration plan before proceeding
   - Consider risk mitigation requirements
   - Re-evaluate whether to proceed to financial analysis

3. **For any risks flagged**:
   - Develop mitigation plans
   - Identify resource needs for integration
   - Update financial model with integration costs

## Related Skills

- `/corporate-development:assess` - Strategic fit assessment
- `/corporate-development:analyze` - Financial due diligence
- `/corporate-development:plan` - Integration planning
- Operational risk assessment and mitigation frameworks

## Integrations

- IT infrastructure assessment tools
- Code quality and technical debt analysis
- Organizational design and HR assessment tools
- Process documentation and workflow systems
- Compliance and regulatory databases

## Question strategy

Ask clear, specific questions. Give a scale or a list of choices.

Good:
- "On a scale of 0-100, how would you rate the architecture quality?"
- "What is the technical debt level: LOW, MEDIUM, or HIGH?"
- "Does the business have critical key person dependencies? (Yes/No)"

Avoid:
- Open-ended questions without a scale
- Vague terms such as "good" or "adequate"
- More than one question in one prompt

Offer a file upload (org charts, technical documents) to reduce the number of questions.
