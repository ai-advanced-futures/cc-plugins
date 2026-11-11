---
name: instrumentation-gap-analysis
description: Identify missing tracking and instrumentation for financial metrics
---

# Instrumentation Gap Analysis Skill

## Purpose

Identify missing tracking and instrumentation because you can't calculate financial metrics without proper data collection - gap analysis reveals what needs to be instrumented.

## When to Use

- Setting up financial tracking for the first time
- Auditing existing instrumentation completeness
- Preparing for investor due diligence
- Troubleshooting metric calculation failures
- Planning instrumentation improvements

## What This Skill Provides

Comprehensive gap analysis including:
- Inventory of existing instrumentation
- Identification of missing events
- Impact assessment by metric
- Prioritized implementation plan
- Framework-specific recommendations

## Input Requirements

### Analysis Parameters
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| codebase_path | string | Yes | Path to codebase root |
| target_metrics | list | No | Specific metrics to analyze |

### Automatic Detection
The analyzer automatically detects:
- Web framework (Django, Flask, FastAPI, Express, etc.)
- Database type (PostgreSQL, MySQL, MongoDB, etc.)
- AI providers (Anthropic, OpenAI, etc.)
- Payment providers (Stripe, PayPal, etc.)
- Existing tracking implementations

## Required Events by Metric

### MRR/ARR Calculation
| Required Event | Priority | Data Points |
|----------------|----------|-------------|
| subscription_created | Critical | customer_id, plan, mrr, start_date |
| subscription_upgraded | Critical | customer_id, old_mrr, new_mrr, date |
| subscription_downgraded | Critical | customer_id, old_mrr, new_mrr, date |
| subscription_cancelled | Critical | customer_id, churned_mrr, date, reason |

### Churn Rate Calculation
| Required Event | Priority | Data Points |
|----------------|----------|-------------|
| subscription_cancelled | Critical | customer_id, subscription_id, lifetime |
| customer_id tracking | Critical | Consistent across all events |
| subscription_start_date | High | For cohort analysis |

### CAC Calculation
| Required Event | Priority | Data Points |
|----------------|----------|-------------|
| customer_created | High | customer_id, acquisition_source |
| marketing_spend | Medium | campaign, spend, date |
| sales_expense | Medium | type, amount, date |

### LTV Calculation
| Required Event | Priority | Data Points |
|----------------|----------|-------------|
| subscription_created | Critical | customer_id, mrr |
| payment_received | High | customer_id, amount, date |
| subscription_lifetime | High | Calculated or tracked |

### AI Cost Tracking
| Required Event | Priority | Data Points |
|----------------|----------|-------------|
| ai_request_completed | High | user_id, model, tokens, cost |
| ai_cost_incurred | High | provider, cost, timestamp |

### Net Revenue Retention
| Required Event | Priority | Data Points |
|----------------|----------|-------------|
| subscription_upgraded | Critical | customer_id, expansion_mrr |
| subscription_downgraded | Critical | customer_id, contraction_mrr |
| subscription_cancelled | Critical | customer_id, churned_mrr |

## Output Format

```json
{
  "gap_analysis": {
    "codebase_analysis": {
      "framework": "django",
      "database": "postgresql",
      "has_subscription_model": true,
      "has_ai_integration": true,
      "existing_tracking_count": 5,
      "ai_providers_detected": ["anthropic", "openai"],
      "payment_providers_detected": ["stripe"]
    },
    "existing_instrumentation": [
      {
        "event_name": "user_signup",
        "location": "accounts/views.py",
        "data_captured": ["user_id", "email", "source"],
        "quality": "good"
      }
    ],
    "gaps": [
      {
        "metric": "MRR",
        "missing_data": ["subscription_created", "subscription_upgraded"],
        "impact": "critical",
        "enables_metrics": ["MRR", "ARR", "Growth Rate"]
      },
      {
        "metric": "AI Cost",
        "missing_data": ["ai_request_completed"],
        "impact": "high",
        "enables_metrics": ["AI Cost per Request", "AI ROI"]
      }
    ],
    "coverage_score": 35,
    "priority_actions": [
      "Implement subscription lifecycle events (critical)",
      "Add AI cost tracking (high)",
      "Track payment events (high)"
    ]
  }
}
```

## Process

1. **Scan Codebase:**
   - Detect framework and patterns
   - Find existing tracking calls
   - Identify subscription/payment code
   - Locate AI integration points

2. **Inventory Existing Instrumentation:**
   - Map tracking calls to events
   - Assess data completeness
   - Evaluate quality

3. **Compare to Requirements:**
   - For each target metric
   - Identify required events
   - Check for presence/absence

4. **Assess Gaps:**
   - Calculate coverage score
   - Determine impact by metric
   - Prioritize by importance

5. **Generate Recommendations:**
   - Prioritized list of gaps to fill
   - Implementation guidance
   - Effort estimates

## Gap Severity Classification

### Critical Gaps
- Blocks calculation of core financial metrics
- Required for investor reporting
- Impacts decision-making ability

**Examples:**
- No subscription lifecycle tracking (blocks MRR)
- No churn event tracking (blocks churn rate)

### High Priority Gaps
- Limits accuracy of metrics
- Prevents segment-level analysis
- Impacts optimization efforts

**Examples:**
- No AI cost tracking (blocks AI ROI)
- No payment event tracking (limits revenue analysis)

### Medium Priority Gaps
- Nice-to-have for analysis
- Enables advanced features
- Supports optimization

**Examples:**
- No marketing attribution (limits CAC by channel)
- No feature usage tracking (limits feature ROI)

## Coverage Score Calculation

```
Coverage Score = (Events Tracked / Events Required) × Quality Multiplier × 100

Quality Multiplier:
- All required fields: 1.0
- Most fields: 0.8
- Some fields: 0.5
- Minimal fields: 0.3
```

### Score Interpretation
| Score | Status | Interpretation |
|-------|--------|----------------|
| 80-100% | Excellent | Minor gaps only |
| 60-80% | Good | Key metrics trackable |
| 40-60% | Warning | Significant gaps |
| < 40% | Critical | Major instrumentation needed |

## Framework-Specific Patterns

### Django
```python
# Look for patterns:
- signals.py files
- @receiver decorators
- tracking() calls
- analytics integrations
```

### Flask
```python
# Look for patterns:
- @app.after_request
- before_request handlers
- analytics module imports
```

### Express
```javascript
// Look for patterns:
- app.use() middleware
- segment.track()
- amplitude.track()
- custom tracking modules
```

## No Script

Do the steps of the Process section. Do not look for a script, because no script of this plugin makes this analysis from the inputs above.

## Common Gap Patterns

### Subscription-Based Products
**Typically Missing:**
- Upgrade/downgrade events
- Cancellation reasons
- Trial conversion tracking
- Plan change history

### AI-Powered Products
**Typically Missing:**
- Per-request cost tracking
- Token usage logging
- Model selection tracking
- Feature-level AI usage

### Multi-Channel Products
**Typically Missing:**
- Attribution tracking
- Channel-specific conversion
- Campaign performance events
- Cross-channel journey

## Prioritization Framework

| Factor | Weight | Consideration |
|--------|--------|---------------|
| Metric Impact | 40% | Which metrics does this enable? |
| Implementation Effort | 25% | How hard to implement? |
| Data Availability | 20% | Is the data accessible? |
| Business Priority | 15% | How urgent for business? |

## Gap Resolution Workflow

1. **Identify Gap** - What's missing?
2. **Assess Impact** - What can't we calculate?
3. **Design Event** - What data to capture?
4. **Locate Trigger** - Where in code to emit?
5. **Implement** - Add tracking code
6. **Validate** - Verify data quality
7. **Calculate** - Use for metrics

## Next Steps After Gap Analysis

After identifying gaps, use these companion skills:
- **event-schema-generation** - Generate schemas for missing events
- **migration-planning** - Plan database changes for new events
