---
name: analysis-market-sizing
description: Perform TAM/SAM/SOM market sizing analysis with multiple methodologies
---

# Market Sizing Analysis Skill

## Purpose

Perform TAM/SAM/SOM market sizing because understanding market opportunity is essential for investment decisions, resource allocation, and growth strategy.

## When to Use

- Discovery stage financial analysis
- Preparing investor pitch materials
- Evaluating new market opportunities
- Setting realistic growth targets
- Product-market fit validation

## What This Skill Provides

Comprehensive market sizing including:
- TAM (Total Addressable Market) calculation
- SAM (Serviceable Addressable Market) filtering
- SOM (Serviceable Obtainable Market) projection
- Multiple calculation methodologies
- Revenue opportunity by segment
- Health assessment and recommendations

## Input Requirements

### TAM Calculation (choose one method)

**Top-Down Method:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total_market_size | float | Yes | Total market size from industry reports |
| icp_filter_percent | float | Yes | Percentage relevant to your ICP |

**Bottom-Up Method:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| potential_customers | int | Yes | Number of potential customers |
| target_acv | float | Yes | Target annual contract value |

**Value Theory Method:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| economic_value_per_customer | float | Yes | Value created for each customer |
| value_capture_percent | float | Yes | Percentage of value you can capture |
| potential_customers | int | Yes | Number of potential customers |

### SAM Filters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| geographic_filter | float | Yes | % of TAM geographically accessible |
| customer_size_filter | float | Yes | % of TAM by customer size fit |
| channel_filter | float | Yes | % of TAM reachable by your channels |

### SOM Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timeframe_years | int | Yes | Years to achieve SOM (1-10) |
| market_share_percent | float | Yes | Realistic market share target |

## Formulas

### TAM - Top-Down
```
TAM = Total Market Size × ICP Filter %
```

### TAM - Bottom-Up
```
TAM = Potential Customers × Target ACV
```

### TAM - Value Theory
```
Price = Economic Value per Customer × Value Capture %
TAM = Potential Customers × Price
```

### SAM Calculation
```
SAM = TAM × Geographic Filter × Customer Size Filter × Channel Filter
```

### SOM Calculation
```
SOM = SAM × Market Share %
```

## Methodology Comparison

| Method | Best For | Data Sources |
|--------|----------|--------------|
| Top-Down | Established markets | Gartner, IDC, industry reports |
| Bottom-Up | Niche markets | Customer surveys, CRM data |
| Value Theory | New categories | Customer interviews, ROI studies |

## Output Format

```json
{
  "market_sizing": {
    "tam": {
      "value": 5000000000,
      "calculation_method": "top_down",
      "assumptions": {
        "total_market_size": 10000000000,
        "icp_filter_percent": 50
      }
    },
    "sam": {
      "value": 1000000000,
      "filters": {
        "geographic": 80,
        "customer_size": 50,
        "channel": 50
      },
      "sam_to_tam_ratio": 0.20
    },
    "som": {
      "value": 50000000,
      "timeframe_years": 5,
      "market_share_pct": 5.0,
      "som_to_sam_ratio": 0.05
    }
  },
  "health_assessment": {
    "market_opportunity": "good",
    "overall": "good"
  },
  "recommendations": {
    "primary_channel": "inbound_marketing",
    "target_segment_priority": ["Enterprise", "Mid-Market", "SMB"],
    "risk_flags": []
  }
}
```

## Process

1. **Select Calculation Method:**
   - Top-down for established markets with good data
   - Bottom-up for direct counting of prospects
   - Value theory for new market categories

2. **Calculate TAM:**
   - Apply chosen methodology
   - Document each assumption with its source
   - Sanity check against industry reports

3. **Apply SAM Filters:**
   - Geographic accessibility
   - Customer size/segment fit
   - Channel reach capability
   - Be conservative with estimates

4. **Project SOM:**
   - Set realistic timeframe (typically 3-5 years)
   - Research competitor market shares
   - Account for market growth/contraction

5. **Validate Results:**
   - Cross-check with multiple methods
   - Compare TAM to competitor revenues
   - Verify SAM filters are realistic

6. **Document Assumptions:**
   - List all input sources
   - Note confidence levels
   - Track assumptions for revision

## Health Assessment Criteria

| Metric | Excellent | Good | Warning | Critical |
|--------|-----------|------|---------|----------|
| SOM | > $50M | $10M-$50M | $1M-$10M | < $1M |
| SOM/SAM Ratio | < 5% | 5-10% | 10-20% | > 20% |
| TAM Growth | > 20% | 10-20% | 0-10% | < 0% |

## Common Pitfalls

1. **TAM Too Large:** Using total industry size without filtering for ICP
2. **Ignoring Competition:** SOM should account for realistic competitive dynamics
3. **Static Analysis:** Markets change - update sizing annually
4. **Single Method:** Use multiple methods for triangulation
5. **Aspirational vs. Realistic:** SOM should be achievable, not hopeful

## No Script

Work out each figure with the formulas of this page. Do not look for a script, because no script of this plugin computes this result from the inputs above.

## Example Calculations

**Top-Down Example:**
```
Total SaaS Market: $200B
Developer Tools Segment: 15% = $30B
Your ICP (Enterprise only): 40% = $12B TAM

SAM Filters:
- Geographic (US + Europe): 60%
- Customer Size (>500 employees): 50%
- Channel (Direct sales capable): 70%
SAM = $12B × 0.60 × 0.50 × 0.70 = $2.52B

SOM (5-year, 2% share): $50.4M
```

**Bottom-Up Example:**
```
Potential Customers: 50,000 companies
Target ACV: $24,000/year
TAM = 50,000 × $24,000 = $1.2B

SAM (similar filters): $252M
SOM (3-year, 3%): $7.56M
```

## Investor Expectations

| Stage | Expected TAM | Expected SOM Path |
|-------|--------------|-------------------|
| Seed | > $1B | Prove product works |
| Series A | > $5B | $1-5M ARR achievable |
| Series B | > $10B | $10M+ ARR trajectory |
| Growth | > $20B | $100M+ ARR potential |

## Segment Prioritization

When TAM analysis reveals multiple segments, prioritize by:

1. **Revenue Opportunity** = Customers × ACV × Conversion Rate
2. **Ease of Acquisition** = Low CAC, short sales cycle
3. **Strategic Value** = Expansion potential, reference customers
4. **Willingness to Pay** = JTBD validation data

## Integration with Financial Model

Market sizing feeds into:
- Revenue projections (SOM trajectory)
- CAC budgets (based on segment size)
- Hiring plans (sales capacity for SOM)
- Fundraising targets (capital for market capture)
