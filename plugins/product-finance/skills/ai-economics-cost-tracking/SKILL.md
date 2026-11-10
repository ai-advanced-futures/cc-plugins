---
name: ai-economics-cost-tracking
description: Track AI costs per interaction, per user, and as percentage of revenue
---

# AI Cost Tracking Skill

## Purpose

Track AI costs comprehensively because understanding AI spend across dimensions enables cost optimization and sustainable AI feature investment.

## When to Use

- Monitoring AI API spend across providers
- Calculating cost per interaction/user
- Tracking AI costs as percentage of revenue
- Optimizing model selection and usage
- Preparing CFO-ready AI cost reports

## What This Skill Provides

Comprehensive AI cost analysis including:
- Cost per AI interaction/API call
- Cost per active user per month
- AI costs as percentage of revenue
- Provider cost breakdown
- Annualized cost projections
- Cost optimization opportunities

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| total_ai_cost | float | Yes | Total AI costs for the period |
| ai_interactions | int | Yes | Total AI interactions/API calls |
| active_users | int | Yes | Number of active users |
| total_revenue | float | Yes | Total revenue for the period |
| period_months | int | No | Period in months (default: 1) |
| provider_breakdown | dict | No | Cost breakdown by AI provider |
| infrastructure_cost | float | No | Additional AI infrastructure costs |
| infrastructure_monthly_cost | float | No | AI infrastructure cost of 1 month; the script adds it once for each month of the period |
| ai_engineers | float | No | Engineers on the AI features; give it with ai_engineer_annual_cost |
| ai_engineer_annual_cost | float | No | Fully loaded annual cost of 1 AI engineer; give it with ai_engineers |

## Key Metrics

### Cost Per Interaction
```
Cost per Interaction = Total AI Cost / Number of Interactions
```

### Cost Per User Per Month
```
Cost per User per Month = Total AI Cost / Active Users / Period Months
```

### AI Cost Percentage of Revenue
```
AI Cost % = (Total AI Cost / Total Revenue) × 100
```

### Annualized AI Cost
```
Annualized AI Cost = Total AI Cost × (12 / Period Months) + (Infrastructure Cost × 12)
```

## Benchmark Thresholds

### AI Cost % of Revenue
| Percentage | Status | Interpretation |
|------------|--------|----------------|
| < 5% | Excellent | Very efficient AI usage |
| 5-10% | Good | Healthy for AI-powered products |
| 10-20% | Warning | Monitor closely, optimize |
| > 20% | Critical | Urgent optimization needed |

### Cost Per Interaction
| Cost | Status | Typical Use Case |
|------|--------|------------------|
| < $0.01 | Excellent | Simple queries, cached responses |
| $0.01-$0.05 | Good | Standard AI features |
| $0.05-$0.10 | Warning | Complex queries, long context |
| > $0.10 | Critical | Needs optimization |

### Cost Per User Per Month
| Cost | Status | Consideration |
|------|--------|---------------|
| < $1 | Excellent | Minimal AI usage per user |
| $1-$5 | Good | Moderate AI-enhanced experience |
| $5-$15 | Warning | Heavy AI reliance |
| > $15 | Critical | High risk to unit economics |

## Output Format

```json
{
  "ai_costs": {
    "cost_per_interaction": 0.0350,
    "cost_per_user_per_month": 3.50,
    "ai_cost_percentage_of_revenue": 7.0,
    "total_ai_cost": 35000.00,
    "annualized_ai_cost": 420000.00,
    "health_status": "good",
    "cost_trend_analysis": "Good: AI costs 5-10% of revenue. Healthy range for AI-powered products.",
    "provider_breakdown": {
      "anthropic": {
        "cost": 20000,
        "percentage": 57.1,
        "cost_per_interaction": 0.04
      },
      "openai": {
        "cost": 15000,
        "percentage": 42.9,
        "cost_per_interaction": 0.03
      }
    },
    "optimization_opportunities": [
      "Consider prompt compression techniques to reduce API calls.",
      "Implement response caching with TTL for similar queries.",
      "Monitor and set rate limits per user to prevent abuse."
    ]
  }
}
```

## Process

1. **Collect Cost Data:**
   - Aggregate API costs across providers
   - Include infrastructure costs (hosting, storage)
   - Note measurement period

2. **Calculate Cost Metrics:**
   - Cost per interaction
   - Cost per user per month
   - AI cost as % of revenue
   - Annualize for projections

3. **Analyze by Provider:**
   - Break down costs per provider
   - Calculate efficiency per provider
   - Identify cost concentration

4. **Assess Health:**
   - Compare to benchmarks
   - Identify concerning trends
   - Flag critical thresholds

5. **Generate Optimization Opportunities:**
   - Based on cost patterns
   - Provider-specific suggestions
   - Usage pattern improvements

## Cost Tracking Architecture

### Data to Capture Per Request
```json
{
  "request_id": "uuid",
  "user_id": "user_123",
  "customer_id": "cust_456",
  "timestamp": "2024-01-15T10:30:00Z",
  "provider": "anthropic",
  "model": "claude-3-sonnet",
  "feature": "document_analysis",
  "tokens_input": 1500,
  "tokens_output": 500,
  "cost_usd": 0.0075,
  "latency_ms": 1200,
  "cached": false
}
```

### Aggregation Levels
1. **Per Request:** Real-time cost tracking
2. **Per User:** Daily/monthly cost per user
3. **Per Customer:** Customer-level cost allocation
4. **Per Feature:** Feature-level cost attribution
5. **Per Provider:** Provider cost comparison

## Provider Cost Comparison

### Current Model Pricing (Example - Verify Current Rates)
| Provider | Model | Input Cost/1M | Output Cost/1M |
|----------|-------|---------------|----------------|
| Anthropic | Claude 3 Opus | $15.00 | $75.00 |
| Anthropic | Claude 3 Sonnet | $3.00 | $15.00 |
| Anthropic | Claude 3 Haiku | $0.25 | $1.25 |
| OpenAI | GPT-4 Turbo | $10.00 | $30.00 |
| OpenAI | GPT-4o | $5.00 | $15.00 |
| OpenAI | GPT-3.5 Turbo | $0.50 | $1.50 |

### Cost Optimization by Model Selection
```
High complexity: Use Claude Opus / GPT-4
Medium complexity: Use Claude Sonnet / GPT-4o
Low complexity: Use Claude Haiku / GPT-3.5 Turbo

Potential savings: 50-90% by right-sizing model selection
```

## Cost Optimization Strategies

### Caching
- **Semantic caching:** Cache similar query responses
- **Result caching:** Cache identical requests
- **Expected savings:** 20-40% reduction

### Prompt Optimization
- **Shorter prompts:** Reduce input tokens
- **System prompt reuse:** Minimize repeated context
- **Expected savings:** 10-30% reduction

### Model Routing
- **Complexity scoring:** Route based on query complexity
- **Fallback chains:** Start small, escalate if needed
- **Expected savings:** 30-50% reduction

### Rate Limiting
- **Per-user limits:** Prevent abuse
- **Per-feature limits:** Control expensive features
- **Graceful degradation:** Non-AI fallbacks

## Reference Implementation

See `scripts/ai_roi_calculator.py` for the complete Python implementation with:
- `AICostInput` model for input validation
- `calculate_ai_costs()` function
- Provider breakdown analysis
- Cost optimization recommendations

## Example Calculation

**Monthly Data:**
```
Total AI Cost: $50,000
AI Interactions: 1,000,000
Active Users: 10,000
Total Revenue: $500,000
Period: 1 month

Cost per Interaction: $50,000 / 1,000,000 = $0.05
Cost per User/Month: $50,000 / 10,000 = $5.00
AI Cost %: ($50,000 / $500,000) × 100 = 10% (WARNING threshold)
Annualized: $50,000 × 12 = $600,000
```

**Interpretation:**
- Cost per interaction is at the upper end of acceptable
- Cost per user is moderate but should be monitored
- AI costs at 10% of revenue - at the warning threshold
- Consider optimization to reduce to <5%

## Monitoring Best Practices

### Real-Time Alerts
- Cost per interaction > threshold
- Daily spend > budget
- Unusual usage patterns

### Weekly Review
- Cost trends by provider
- Per-user cost distribution
- Feature-level cost breakdown

### Monthly Analysis
- AI cost % of revenue trend
- ROI evaluation
- Optimization impact measurement
