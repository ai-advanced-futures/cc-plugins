---
name: lenses-economic-value
description: Runs when the lens executor or the skill analyze needs the economic value lens. It measures the value that the offering and a competitor create, with the EVC framework.
user-invocable: false
---

# Economic Value Analysis Lens

## Purpose

Quantify the economic value each solution delivers because buyers ultimately choose based on value relative to price, not features.

## Input Required

- `intelligence-data.json` - Competitive data
- `jtbd-analysis.json` - Performance metrics (cascading input)
- `context-config.json` - Scope and customer context

## The Economic Value Framework

Based on McKinsey's Economic Value to Customer (EVC):

```
Total Value = Time Savings + Error Reduction + Revenue Impact + Risk Reduction
```

Each component:
- **Time Savings:** Hours saved × hourly cost
- **Error Reduction:** Errors avoided × cost per error
- **Revenue Impact:** Additional revenue × margin
- **Risk Reduction:** Risk probability reduction × cost if occurs

## Process

### 1. Time Savings Calculation

For each job step:
- Current time to complete (your product)
- Current time to complete (competitor)
- Time difference × frequency × hourly cost

```
Time Value = (Hours_Saved) × (Frequency/Month) × (Hourly_Cost)
```

### 2. Error Reduction Calculation

For each job step:
- Error rate with your product
- Error rate with competitor
- Difference × cost per error

```
Error Value = (Error_Rate_Reduction) × (Frequency) × (Cost_Per_Error)
```

### 3. Revenue Impact Calculation

Identify revenue-affecting outcomes:
- Faster time to market
- Higher conversion rates
- Better customer retention

```
Revenue Value = (Revenue_Increase) × (Margin) × (Probability_of_Achieving)
```

### 4. Risk Reduction Calculation

Identify risk mitigation:
- Compliance risk reduction
- Data loss prevention
- Business continuity

```
Risk Value = (Risk_Probability_Reduction) × (Cost_If_Risk_Occurs)
```

### 5. Value-to-Price Ratio

Compare total value to pricing:
- Your value / your price
- Competitor value / competitor price
- Ratio comparison

## Output Format

Generate `value-analysis.json`:

```json
{
  "value_calculation": {
    "your_product": {
      "time_savings": {
        "monthly_value": 2400,
        "calculation": "10 hours × $240/hour",
        "confidence": "high",
        "job_steps": ["step-2", "step-4"]
      },
      "error_reduction": {
        "monthly_value": 800,
        "calculation": "4 errors × $200/error",
        "confidence": "medium",
        "job_steps": ["step-3", "step-5"]
      },
      "revenue_impact": {
        "monthly_value": 1500,
        "calculation": "3% conversion increase × $50k pipeline",
        "confidence": "low",
        "assumptions": ["Pipeline size", "Conversion attribution"]
      },
      "risk_reduction": {
        "monthly_value": 500,
        "calculation": "5% compliance risk reduction × $10k potential fine",
        "confidence": "medium"
      },
      "total_monthly_value": 5200,
      "annual_value": 62400
    },
    "competitor_a": {
      "time_savings": {
        "monthly_value": 3000,
        "calculation": "12.5 hours × $240/hour",
        "confidence": "medium"
      },
      "total_monthly_value": 5800,
      "annual_value": 69600
    }
  },
  "pricing_comparison": {
    "your_product": {
      "monthly_price": 500,
      "annual_price": 6000
    },
    "competitor_a": {
      "monthly_price": 800,
      "annual_price": 9600
    }
  },
  "value_to_price": {
    "your_product": {
      "ratio": 10.4,
      "interpretation": "10.4x value vs price"
    },
    "competitor_a": {
      "ratio": 7.25,
      "interpretation": "7.25x value vs price"
    }
  },
  "roi_comparison": {
    "your_product": {
      "annual_roi": "940%",
      "calculation": "(62400 - 6000) / 6000"
    },
    "competitor_a": {
      "annual_roi": "625%",
      "calculation": "(69600 - 9600) / 9600"
    }
  },
  "summary": {
    "highest_absolute_value": "competitor_a",
    "best_value_to_price": "your_product",
    "recommendation": "Position on value efficiency, not absolute capability"
  }
}
```

## Confidence Guidelines

Apply the standard confidence scale (HIGH/MEDIUM/LOW/SPECULATIVE, defined in confidence_scoring.py). Assign based on:

**High confidence:**
- Time savings verified with customers
- Error rates from actual usage data
- Pricing publicly available

**Medium confidence:**
- Time estimates from demos
- Error rates from reviews
- Pricing from sales intelligence

**Low confidence:**
- Time estimates from marketing
- Assumed error rates
- Estimated pricing

## Philosophy

<value_not_features>
Buyers care about outcomes, not capabilities.
Quantified value beats feature lists.
ROI is the ultimate comparison.
</value_not_features>

<conservative_estimates>
Under-promise on value calculations.
Start each assumption with the word "Assumption:".
Conservative estimates build credibility.
</conservative_estimates>

## Cascading Outputs

This lens informs:
- **Synthesis:** Value positioning recommendations
- **Recommendations:** Pricing strategy, value messaging

## Completion Protocol

After writing all output files:

**Write value-summary.json** to `data_dir` (from dispatch context):
{
  "lens": "economic-value",
  "completed_at": "{ISO 8601 timestamp}",
  "competitors_analyzed": N,
  "headline": "Best value/price ratio: {winner}; highest absolute EVC: {competitor}",
  "key_findings": [
    "Your EVC: ${amount} ({breakdown: time+error+revenue+risk})",
    "Best competitor EVC: ${amount} ({competitor})",
    "Your value/price ratio: {ratio} ({vs_competitors})",
    "TCO advantage: {you|competitor} by {amount} over {ANALYSIS_YEARS} years"
  ],
  "confidence": "{HIGH|MEDIUM|LOW|SPECULATIVE}",
  "warnings": [],
  "data_file": "value-analysis.json"
}

**Return to caller:** DONE: lens-economic-value
