# Unit Economics Examples

Worked examples for `/product-finance:unit-economics`.

### Example 1: Growth-Stage SaaS with Strong Unit Economics

**Input:**
```
Period: Last 6 months (H2 2025)
Mode: Actual data
S&M Spend: $500,000
New Customers: 250
ARPC: $500/month
Gross Margin: 75%
Monthly Churn: 3%
Net New ARR: $600,000
Cohort data: 12 cohorts with retention curves
```

**Output:**
- CAC: $2,000
- LTV: $12,500
- LTV:CAC: 6.25:1 (Excellent)
- Payback: 5.3 months (Excellent)
- Magic Number: 4.8 (Excellent)
- Health Score: 92/100
- Recommendation: Scale S&M investment aggressively

### Example 2: Early-Stage Startup with Marginal Unit Economics

**Input:**
```
Period: Last 3 months (Q4 2025)
Mode: Actual data
S&M Spend: $150,000
New Customers: 50
ARPC: $300/month
Gross Margin: 65%
Monthly Churn: 5%
Net New ARR: $90,000
```

**Output:**
- CAC: $3,000
- LTV: $3,900
- LTV:CAC: 1.3:1 (Acceptable for early-stage)
- Payback: 15.4 months (Poor)
- Magic Number: 0.6 (Acceptable)
- Health Score: 58/100
- Recommendation: Focus on reducing churn and improving ARPC before scaling

### Example 3: Projected Analysis for Series A Fundraising

**Input:**
```
Period: Next 12 months projection
Mode: Projected
S&M Spend: $2M (projected)
New Customers: 500 (target)
ARPC: $600/month (with new premium tier)
Gross Margin: 78%
Monthly Churn: 2.5% (target improvement)
Net New ARR: $3M (projected)
```

**Output:**
- Projected CAC: $4,000
- Projected LTV: $18,720
- LTV:CAC: 4.68:1 (Good)
- Payback: 8.5 months (Good)
- Magic Number: 1.5 (Excellent)
- Health Score: 85/100
- Use case: Demonstrate healthy unit economics to investors
