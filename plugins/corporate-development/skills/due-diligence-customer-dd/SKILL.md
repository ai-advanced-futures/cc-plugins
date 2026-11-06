---
name: due-diligence-customer-dd
description: Evaluate customer satisfaction, retention, and business health indicators
---

# Customer Due Diligence

Assessment of the target's customer base, customer satisfaction, retention, and business health to evaluate the sustainability of the revenue base and identify integration risks related to customer relationships.

## What It Does

- Assesses customer satisfaction levels through NPS, CSAT, and sentiment analysis
- Analyzes customer retention and churn patterns by segment
- Reviews customer success metrics and health scores
- Identifies key customer relationships and concentration risks
- Evaluates customer support quality and satisfaction
- Assesses customer product adoption and engagement levels
- Reviews customer feedback and sentiment on product roadmap
- Identifies at-risk customers and churn prevention opportunities
- Analyzes customer segment profitability
- Evaluates buyer persona and customer acquisition quality

## How to Use

Customer Due Diligence is performed during the investigation phase to ensure the revenue base is healthy and sustainable. Poor customer satisfaction or high churn can indicate fundamental product or service delivery issues that impact deal economics and integration success.

## Inputs

```json
{
  "customer_metrics": {
    "nps_score": "number",
    "csat_score": "number",
    "churn_rate": "number",
    "net_dollar_retention": "number"
  },
  "customer_data": {
    "total_customers": "number",
    "customers_by_segment": "object",
    "customer_tenure_distribution": "object"
  },
  "engagement_metrics": {
    "feature_adoption_rate": "number",
    "daily_active_users_percentage": "number",
    "support_ticket_volume": "number"
  }
}
```

## Outputs

```json
{
  "customer_satisfaction": {
    "nps_score": "number",
    "nps_breakdown": {
      "promoters": "number",
      "passives": "number",
      "detractors": "number"
    },
    "csat_score": "number",
    "satisfaction_trend": "string",
    "sentiment_analysis": "string"
  },
  "customer_retention": {
    "overall_churn_rate": "number",
    "monthly_churn_rate": "number",
    "churn_by_segment": "object",
    "cohort_retention": "object",
    "net_dollar_retention": "number"
  },
  "customer_health": {
    "at_risk_customers": [
      {
        "customer_name": "string",
        "health_score": "number",
        "churn_risk": "string",
        "reason": "string"
      }
    ],
    "customer_success_score": "number",
    "support_quality_assessment": "string"
  },
  "customer_base_quality": {
    "key_customer_concentration": {
      "top_10_customers_percentage": "number",
      "top_customer_percentage": "number",
      "risk_level": "string"
    },
    "customer_segment_analysis": "object",
    "buyer_persona_quality": "string"
  },
  "engagement_metrics": {
    "product_adoption_rate": "number",
    "feature_adoption": ["string"],
    "engagement_level": "string"
  },
  "customer_risks": {
    "key_risks": ["string"],
    "at_risk_revenue": "string",
    "integration_risks": ["string"]
  },
  "customer_health_score": "number",
  "recommendations": ["string"]
}
```

## Scoring Methodology

- **Satisfaction (1-10)**: NPS score (40%), CSAT (30%), support quality (20%), sentiment (10%)
  - NPS >50: Strong loyalty
  - NPS 0-50: Adequate but room for improvement
  - NPS <0: Significant satisfaction concerns
- **Retention (1-10)**: Churn rate (40%), net dollar retention (30%), cohort trend (20%), segment stability (10%)
  - Healthy: <5% monthly churn, NDR >110%
- **Health (1-10)**: Engagement level (30%), support ticket volume (20%), feature adoption (20%), customer concentration risk (30%)

## Risk Levels

- **Low Risk**: NPS >50, monthly churn <5%, NDR >110%, dispersed customer base
- **Medium Risk**: NPS 0-50, churn 5-8%, NDR 100-110%, some concentration
- **High Risk**: NPS <0, churn >8%, NDR <100%, heavy concentration

## Gate Logic

- **GO** - Customer health >7, NPS >50, churn <5%, NDR >110%, no key customer dependencies
- **NO_GO** - Customer health <5, NPS <0, churn >10%, significant revenue concentration, key customers in churn
- **CONDITIONAL** - Proceed if scores 5-7 with identified customer success or satisfaction improvements

## Integrations

- **product-finance** - Customer cohort economics, CAC payback analysis (optional plugin)

## Related Skills

- Financial Due Diligence - Revenue sustainability depends on customer retention
- Product Due Diligence - Product satisfaction drives NPS and retention
- Operational Due Diligence - Support team capability impacts satisfaction

## Used By

- Command: `/corporate-development:audit` or `/corporate-development:analyze`
- Agent: `customer-health-analyst`

