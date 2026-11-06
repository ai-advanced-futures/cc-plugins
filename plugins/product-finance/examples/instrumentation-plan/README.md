# Instrumentation Plan Example

This example demonstrates how to generate a comprehensive instrumentation plan for financial tracking. The scenario involves "DataSync Pro" implementing tracking to enable automated financial metrics calculation.

## Overview

DataSync Pro needs to implement financial instrumentation to:
1. Automatically calculate MRR, churn, and other board-level KPIs
2. Track AI feature costs and usage for ROI analysis
3. Enable real-time financial health dashboards
4. Support cohort analysis for investor reporting

## Current State

**Existing Tracking:**
- Basic Stripe webhooks for payment events
- User signup events in Segment
- Feature usage in Amplitude

**Gaps:**
- No subscription lifecycle tracking (upgrades, downgrades)
- No AI cost attribution
- No customer health scoring
- Missing expansion/contraction tracking

## Files Included

### Inputs

- **`inputs/current-tracking.json`** - Analysis of existing instrumentation
- **`inputs/target-metrics.json`** - Desired metrics and required events

### Outputs

- **`outputs/instrumentation-plan.md`** - Complete implementation plan
- **`outputs/event-schemas/`** - Event schema definitions
  - `subscription_events.json` - Subscription lifecycle events
  - `ai_usage_events.json` - AI cost tracking events
  - `customer_events.json` - Customer lifecycle events
- **`outputs/migrations/`** - Database migration scripts
  - `001_create_financial_events.sql` - Financial events table
  - `002_create_ai_usage_events.sql` - AI usage table

## Running This Example

### Step 1: Analyze Current State

```bash
# Run instrumentation analysis on your codebase
/product-finance:instrumentation
```

**Expected prompts:**
- Codebase path: `/path/to/your/project`
- Product type: `saas_subscription`
- AI features: `yes`

### Step 2: Review Gap Analysis

The command will scan your codebase and identify:
- Current tracking events
- Missing events for each metric
- Priority of each gap

### Step 3: Implement Events

Follow the generated plan to implement events in phases:
1. **Phase 1:** Critical subscription tracking (1-2 weeks)
2. **Phase 2:** Expansion & contraction (1 week)
3. **Phase 3:** AI cost tracking (1 week)
4. **Phase 4:** Customer acquisition (1-2 weeks)
5. **Phase 5:** Trial & conversion (1 week)

### Step 4: Validate Implementation

```bash
# After implementing, run health check to validate
/product-finance:health-check
```

## Key Insights from This Example

### Gap Analysis Summary

| Metric | Status | Missing Events |
|--------|--------|----------------|
| MRR | Partial | subscription_upgraded, subscription_downgraded |
| Churn Rate | Missing | subscription_cancelled |
| NRR | Missing | Multiple expansion/contraction events |
| AI Cost | Missing | ai_request_completed, ai_cost_incurred |
| CAC | Partial | marketing_spend_recorded |

### Implementation Priority

| Phase | Priority | Events | Effort | Metrics Enabled |
|-------|----------|--------|--------|-----------------|
| 1 | Critical | 3 | 1-2 weeks | MRR, ARR, Churn |
| 2 | High | 3 | 1 week | NRR, Expansion |
| 3 | High | 3 | 1 week | AI Cost, AI ROI |
| 4 | Medium | 3 | 1-2 weeks | CAC, LTV:CAC |
| 5 | Medium | 2 | 1 week | Trial Conversion |

### Event Schema Example

```json
{
  "event_name": "subscription_created",
  "event_category": "subscription",
  "priority": "critical",
  "required_fields": [
    {"field_name": "customer_id", "field_type": "string"},
    {"field_name": "subscription_id", "field_type": "string"},
    {"field_name": "plan", "field_type": "string"},
    {"field_name": "mrr", "field_type": "number"}
  ],
  "enables_metrics": ["MRR", "ARR", "Customer Count"]
}
```

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Application   │────▶│   Event Bus     │────▶│   Analytics DB  │
│   (Django)      │     │   (Kafka/SQS)   │     │   (PostgreSQL)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │                       ▼                       │
        │               ┌─────────────────┐             │
        │               │   Segment       │             │
        │               │   (Analytics)   │             │
        │               └─────────────────┘             │
        │                                               │
        ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│   Stripe        │                           │   Metric        │
│   (Billing)     │                           │   Calculator    │
└─────────────────┘                           └─────────────────┘
```

## Customizing This Example

To adapt for your infrastructure:

1. **Update current-tracking.json:**
   - Document your existing events
   - List current data sources
   - Note integration points

2. **Update target-metrics.json:**
   - Define required board-level KPIs
   - Specify metric calculation formulas
   - Set priority for each metric

3. **Run instrumentation command:**
   ```bash
   /product-finance:instrumentation
   ```

4. **Customize generated schemas:**
   - Adjust field names for your conventions
   - Add custom metadata fields
   - Update trigger points for your code

## Database Schema

The instrumentation plan creates two core tables:

### `financial_events`
Stores all subscription and customer lifecycle events.

```sql
CREATE TABLE financial_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255),
    event_data JSONB NOT NULL,
    mrr_impact DECIMAL(10, 2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `ai_usage_events`
Stores AI API usage for cost tracking.

```sql
CREATE TABLE ai_usage_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    request_id VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    tokens_total INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Related Examples

- [SaaS Product Analysis](../saas-product-analysis/) - Uses instrumented data for analysis
- [AI Feature ROI](../ai-feature-roi/) - Requires AI cost tracking

## References

- [Instrumentation Command](../../commands/instrumentation.md)
- [Event Schemas](../../templates/event-schemas/)
- [Methodology](../../docs/METHODOLOGY.md)
- [Integration Guide](../../docs/INTEGRATION_GUIDE.md)
