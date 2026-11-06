---
name: due-diligence-legal-dd
description: Review contracts, compliance, and legal risks
---

# Legal Due Diligence

Comprehensive legal and compliance review of the target company to identify material legal risks, compliance issues, and contractual obligations that could impact acquisition value or integration.

## What It Does

- Reviews key customer contracts for change-of-control provisions
- Analyzes vendor and supplier agreements
- Assesses regulatory compliance and licensing requirements
- Identifies legal liabilities and pending litigation
- Reviews intellectual property holdings and licensing agreements
- Evaluates employment agreements and key person contracts
- Assesses export control and sanctions compliance
- Reviews data protection and privacy compliance (GDPR, CCPA, etc.)
- Analyzes real estate leases and facility agreements
- Reviews corporate structure and governance documents
- Identifies material contracts requiring renegotiation

## How to Use

Legal Due Diligence is a critical component of the comprehensive investigation phase. Legal risks can materially impact deal value, timeline, and integration success. This skill identifies issues early so they can be incorporated into valuation and integration planning.

## Inputs

```json
{
  "company_info": {
    "company_name": "string",
    "jurisdiction": "string",
    "industry": "string",
    "revenue": "number",
    "customer_count": "number"
  },
  "contract_categories": [
    "customer_contracts",
    "vendor_contracts",
    "employment_agreements",
    "ip_licenses",
    "real_estate"
  ],
  "compliance_areas": [
    "data_protection",
    "export_control",
    "regulatory",
    "industry_specific"
  ]
}
```

## Outputs

```json
{
  "contract_analysis": {
    "customer_contracts": {
      "total_reviewed": "number",
      "change_of_control_provisions": "number",
      "termination_rights": ["string"],
      "key_terms_requiring_renegotiation": ["string"],
      "revenue_at_risk": "number"
    },
    "vendor_contracts": {
      "critical_vendors": ["string"],
      "change_of_control_impact": ["string"],
      "license_requirements": ["string"]
    },
    "employment_agreements": {
      "key_person_agreements": "number",
      "change_of_control_triggers": ["string"],
      "severance_obligations": "number",
      "retention_agreements": ["string"]
    },
    "ip_licenses": {
      "third_party_licenses": ["string"],
      "license_restrictions": ["string"],
      "compliance_status": "string"
    }
  },
  "intellectual_property": {
    "patents_owned": "number",
    "patents_pending": "number",
    "trademarks": ["string"],
    "copyrights_registered": ["string"],
    "trade_secrets": ["string"],
    "ip_defensibility": "string"
  },
  "regulatory_compliance": {
    "licenses_required": ["string"],
    "compliance_status": "string",
    "regulatory_agencies": ["string"],
    "pending_reviews": ["string"]
  },
  "litigation_and_disputes": {
    "pending_litigation": ["string"],
    "regulatory_investigations": ["string"],
    "dispute_resolution_history": "string",
    "potential_exposure": "number"
  },
  "data_privacy": {
    "gdpr_compliance": "string",
    "ccpa_compliance": "string",
    "data_handling_practices": "string",
    "breach_history": "string",
    "compliance_rating": "number"
  },
  "environmental_health_safety": {
    "compliance_status": "string",
    "permits_required": ["string"],
    "violations_history": "string"
  },
  "legal_risks": {
    "critical_risks": [
      {
        "risk": "string",
        "severity": "string",
        "potential_exposure": "number"
      }
    ],
    "deal_breakers": ["string"],
    "mitigatable_risks": ["string"]
  },
  "contract_obligations": {
    "material_contracts": ["string"],
    "renegotiation_required": ["string"],
    "consent_requirements": ["string"]
  },
  "legal_health_score": "number"
}
```

## Scoring Methodology

- **Contract Risk (1-10)**: Material change-of-control provisions (30%), customer contract risk (30%), vendor dependencies (20%), employee retention obligations (20%)
- **Compliance (1-10)**: Data protection compliance (30%), regulatory compliance (30%), industry-specific requirements (20%), licensing status (20%)
- **Litigation Risk (1-10)**: Pending litigation severity (40%), regulatory investigation risk (30%), historical dispute patterns (20%), remedy potential (10%)

## Risk Severity Levels

- **Critical**: Deal-breaking issues, material financial exposure (>5% of purchase price), regulatory barriers
- **Major**: Requires renegotiation, moderate exposure (1-5% of purchase price), manageable compliance issues
- **Moderate**: Minor renegotiation, <1% financial exposure, compliance gaps with clear remediation
- **Low**: Administrative issues, no financial impact, standard compliance process

## Gate Logic

- **GO** - Legal health score >8, no critical risks, compliance status acceptable, no deal-breaking litigation
- **NO_GO** - Legal health score <5, deal-breaking IP/regulatory issues, excessive litigation exposure, unsolvable contract barriers
- **CONDITIONAL** - Proceed if scores 5-8 with clear risk mitigation, escrow provisions, or indemnification agreements

## Integrations

- **tech-contracts** - Contract review (optional plugin)
- **product-finance** - Financial impact of legal obligations and contingencies (optional plugin)

## Related Skills

- Operational Due Diligence - Employment and organizational structure
- Financial Due Diligence - Financial impact of legal obligations
- Deal Recommendation - Synthesizes legal findings into GO/NO_GO decision

## Used By

- Part of comprehensive due diligence process
- Integrates with Deal Recommendation skill
- Typically conducted alongside Financial and Operational DD

