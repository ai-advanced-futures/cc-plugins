---
name: ai-economics-value-attribution
description: Attribute business value to AI features including revenue, productivity, and retention
---

# AI Value Attribution Skill

## Purpose

Attribute business value to AI capabilities because demonstrating AI ROI requires quantifying the value AI creates across multiple dimensions.

## When to Use

- Justifying AI investments to CFO/board
- Measuring AI feature impact
- Prioritizing AI development roadmap
- Calculating AI contribution to revenue
- Evaluating AI product-market fit

## What This Skill Provides

Comprehensive AI value attribution including:
- AI-enabled revenue measurement
- Premium pricing value capture
- Productivity multiplier calculation
- Retention impact analysis
- Expansion revenue attribution
- Time-to-value acceleration value

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ai_enabled_revenue | float | Yes | Revenue from AI-powered features |
| non_ai_revenue | float | Yes | Revenue from non-AI features |
| premium_pricing_uplift | float | No | Price premium for AI capabilities (%) |
| time_saved_hours | float | No | Hours saved through AI automation |
| employee_fully_loaded_cost | float | No | Cost per employee hour |
| ai_feature_churn_rate | float | No | Churn rate with AI features (%) |
| non_ai_churn_rate | float | No | Churn rate without AI features (%) |
| ai_expansion_revenue | float | No | Expansion revenue from AI adoption |
| time_to_value_reduction_days | float | No | Days reduced in time-to-value |

## Value Attribution Framework

### 1. Direct AI Revenue
```
AI Revenue Value = Revenue from AI-enabled features
AI Revenue Percentage = AI Revenue / Total Revenue × 100
```

### 2. Premium Pricing Value
```
Baseline Revenue = AI Revenue / (1 + Premium Uplift %)
Premium Value = AI Revenue - Baseline Revenue
```

Example: $100K AI revenue with 25% premium
- Baseline: $100K / 1.25 = $80K
- Premium Value: $100K - $80K = $20K

### 3. Productivity Multiplier
```
Productivity Value = Hours Saved × Fully Loaded Cost per Hour
```

Example: 1,000 hours saved × $100/hour = $100K productivity value

### 4. Retention Impact
```
Churn Reduction = Non-AI Churn % - AI Feature Churn %
Retention Value = AI Revenue × Churn Reduction %
```

Example: 5% non-AI churn, 2% AI churn, $500K AI revenue
- Churn Reduction: 3%
- Retention Value: $500K × 3% = $15K

### 5. Expansion Revenue
```
Expansion Value = Net New Revenue from AI Feature Upsells
```

### 6. Time-to-Value Acceleration
```
Months Accelerated = Days Reduced / 30
TTV Value = (AI Revenue / 12) × Months Accelerated
```

Example: 45 days reduced, $600K AI revenue
- Months Accelerated: 1.5
- TTV Value: $50K × 1.5 = $75K

## Total AI Value Calculation

```
Total AI Value = AI Revenue
              + Premium Pricing Value
              + Productivity Value
              + Retention Value
              + Expansion Value
              + Time-to-Value Value
```

## Output Format

```json
{
  "ai_value": {
    "ai_enabled_revenue": 500000.00,
    "ai_revenue_percentage": 60.0,
    "total_ai_value": 685000.00,
    "value_breakdown": {
      "ai_enabled_revenue": 500000.00,
      "premium_pricing_value": 100000.00,
      "productivity_value": 50000.00,
      "retention_value": 15000.00,
      "expansion_value": 10000.00,
      "time_to_value_acceleration": 10000.00
    },
    "health_status": "excellent",
    "value_sources_count": 6,
    "primary_value_driver": "ai_enabled_revenue",
    "notes": "Strong value attribution across multiple dimensions."
  }
}
```

## Process

1. **Identify AI-Enabled Revenue:**
   - Tag features as AI-powered vs. non-AI
   - Attribute subscription revenue to features
   - Calculate AI revenue percentage

2. **Calculate Premium Pricing Value:**
   - Determine if AI commands price premium
   - Measure willingness-to-pay difference
   - Quantify premium value capture

3. **Measure Productivity Impact:**
   - Identify time-saving use cases
   - Survey users on time saved
   - Apply fully loaded cost multiplier

4. **Analyze Retention Impact:**
   - Compare churn rates by AI feature adoption
   - Calculate revenue saved from retention
   - Attribute to AI value

5. **Track Expansion Revenue:**
   - Identify AI-driven upsells
   - Measure expansion from AI adoption
   - Attribute to AI value

6. **Calculate TTV Impact:**
   - Measure onboarding time with/without AI
   - Calculate revenue acceleration value

## Value Attribution Methods

### A/B Testing
- Split users into AI vs. non-AI groups
- Measure conversion, retention, expansion
- Statistically validate AI impact

### Cohort Comparison
- Compare pre-AI vs. post-AI cohorts
- Control for other variables
- Measure behavioral changes

### Survey-Based Attribution
- Ask users about AI feature value
- Measure willingness to pay for AI
- Gather time savings estimates

### Usage Correlation
- Correlate AI usage with outcomes
- Higher AI usage → higher retention?
- AI feature adoption → expansion?

## Health Assessment

### Value Diversity Score
| Sources | Status | Interpretation |
|---------|--------|----------------|
| 1 | Warning | Single-dimensional value |
| 2-3 | Good | Moderate diversification |
| 4+ | Excellent | Multi-dimensional value |

### AI Revenue Percentage
| Percentage | Status | Interpretation |
|------------|--------|----------------|
| < 10% | Warning | AI not core to value prop |
| 10-30% | Good | AI contributing meaningfully |
| 30-50% | Good | AI-enhanced product |
| > 50% | Excellent | AI-native product |

## Value Attribution Challenges

### Attribution Complexity
- **Challenge:** Multiple factors affect outcomes
- **Solution:** Use controlled experiments, cohort analysis

### Time Lag
- **Challenge:** AI value may take time to materialize
- **Solution:** Track leading indicators, use cohort curves

### Indirect Value
- **Challenge:** Some AI value is hard to quantify
- **Solution:** Survey users, proxy metrics

### Cannibalization
- **Challenge:** AI may shift value between features
- **Solution:** Net value analysis, customer surveys

## Use Case Examples

### Customer Support AI
```
Time Saved: 500 agent hours/month
Cost per Hour: $50 (fully loaded)
Productivity Value: $25,000/month = $300,000/year

Ticket Resolution: 2x faster
Customer Satisfaction: +15% NPS
Retention Impact: 2% churn reduction on $2M ARR = $40,000/year

Total Value: $340,000/year
```

### AI Writing Assistant
```
Premium Pricing: 40% uplift for AI tier
AI Tier Revenue: $200,000/month
Premium Value: $200K - ($200K/1.4) = $57,143/month = $685,716/year

User Time Saved: 5 hours/user/month × 1,000 users = 5,000 hours
User Time Value: 5,000 × $75/hour = $375,000/month = $4.5M/year
(Note: This is customer value, not captured revenue)

Willingness to Pay Captured: ~15% = $675,000/year
```

### AI-Powered Analytics
```
Insights Accuracy: +30% vs. manual analysis
Decision Speed: 5x faster
Expansion Revenue: $100,000/year from AI feature upsells
Retention Impact: 3% churn reduction = $150,000/year saved

Total Attributable Value: $250,000/year
```

## Reference Implementation

See `scripts/ai_roi_calculator.py` for the complete Python implementation with:
- `AIValueInput` model for input validation
- `calculate_ai_value()` function
- Value breakdown calculation
- Health assessment logic

## Investor-Ready Value Attribution

For board/investor presentations:

1. **Lead with Total AI Value:** "$X million in attributed AI value"
2. **Show Value Breakdown:** Pie chart of value sources
3. **Compare to AI Costs:** AI ROI = Value / Cost
4. **Trend Over Time:** Growing AI value contribution
5. **Customer Evidence:** Quotes on AI feature value
