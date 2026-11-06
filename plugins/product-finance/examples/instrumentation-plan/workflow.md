# Instrumentation Plan Workflow

This document outlines the step-by-step process for implementing comprehensive financial tracking instrumentation.

## Prerequisites

1. Claude Code CLI with Product Finance plugin installed
2. Access to your codebase
3. Database admin access for migrations
4. Analytics platform credentials (Segment, Amplitude, etc.)

## Workflow Overview

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Analyze    │───▶│   Generate   │───▶│   Implement  │───▶│   Validate   │
│   Codebase   │    │   Plan       │    │   Events     │    │   Tracking   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

## Step 1: Analyze Current Instrumentation

Run the instrumentation command to analyze your codebase.

```bash
/product-finance:instrumentation
```

### Expected Prompts

```
Q: What codebase would you like to analyze?
A: /path/to/your/project (or use current directory)

Q: What type of product are you instrumenting?
A: saas_subscription

Q: Do you have AI features that incur API costs?
A: yes
```

### Analysis Output

```
Analyzing codebase...

Framework Detection:
  ✓ Framework: Django 4.2
  ✓ Database: PostgreSQL 15.2
  ✓ Async Framework: Celery
  ✓ Analytics: Segment, Amplitude

Existing Tracking:
  ✓ Found 12 existing events
  ✓ Event quality: 6 good, 4 fair, 2 poor

Gap Analysis:
  ⚠ Critical gaps: 4
  ⚠ High priority gaps: 5
  ⚠ Medium priority gaps: 6

Generating instrumentation plan...
```

## Step 2: Review Generated Plan

The command generates several output files.

### Files Generated

```
.product-finance/instrumentation/
├── instrumentation-plan.json      # Complete structured plan
├── instrumentation-plan.md        # Human-readable guide
├── events.json                    # Event schemas
├── migrations/
│   ├── postgresql/
│   │   ├── 001_create_financial_events.sql
│   │   └── 002_create_ai_usage_events.sql
│   └── mysql/
│       └── ... (if applicable)
├── code-templates/
│   ├── event_emitter.py
│   ├── event_consumer.py
│   └── metric_calculator.py
└── api-spec.json
```

### Review Priorities

1. **Gap Analysis** - Understand what's missing
2. **Event Schemas** - Review required fields
3. **Implementation Phases** - Plan sprint work
4. **Database Migrations** - Review schema changes

## Step 3: Run Database Migrations

Execute migrations to create event storage tables.

### PostgreSQL Migrations

```bash
# Review migration
cat .product-finance/instrumentation/migrations/postgresql/001_create_financial_events.sql

# Apply migration
psql $DATABASE_URL -f .product-finance/instrumentation/migrations/postgresql/001_create_financial_events.sql

# Apply AI usage table
psql $DATABASE_URL -f .product-finance/instrumentation/migrations/postgresql/002_create_ai_usage_events.sql
```

### Verify Tables

```sql
-- Verify financial_events table
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'financial_events';

-- Verify ai_usage_events table
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ai_usage_events';
```

## Step 4: Implement Events by Phase

Follow the phased implementation approach.

### Phase 1: Critical Subscription Tracking (1-2 weeks)

**Events to implement:**
- `subscription_created`
- `subscription_cancelled`
- `payment_received`

**Implementation Steps:**

1. **Update Stripe webhook handler:**

```python
# billing/webhooks.py

from core.events import track_financial_event

@csrf_exempt
def stripe_webhook(request):
    event = stripe.Event.construct_from(
        json.loads(request.body), stripe.api_key
    )

    if event.type == 'customer.subscription.created':
        subscription = event.data.object
        track_financial_event('subscription_created', {
            'customer_id': subscription.customer,
            'subscription_id': subscription.id,
            'plan': subscription.items.data[0].price.id,
            'mrr': subscription.items.data[0].price.unit_amount / 100,
            'billing_cycle': subscription.items.data[0].price.recurring.interval,
            'start_date': datetime.fromtimestamp(subscription.start_date).isoformat()
        })

    elif event.type == 'customer.subscription.deleted':
        subscription = event.data.object
        track_financial_event('subscription_cancelled', {
            'customer_id': subscription.customer,
            'subscription_id': subscription.id,
            'plan': subscription.items.data[0].price.id,
            'mrr_lost': subscription.items.data[0].price.unit_amount / 100,
            'cancellation_date': datetime.utcnow().isoformat(),
            'effective_date': datetime.fromtimestamp(subscription.ended_at).isoformat()
        })
```

2. **Validate events are firing:**

```bash
# Check event count
psql $DATABASE_URL -c "SELECT event_name, COUNT(*) FROM financial_events GROUP BY event_name;"
```

3. **Verify metrics calculable:**

```bash
/product-finance:health-check
```

### Phase 2: Expansion & Contraction (1 week)

**Events to implement:**
- `subscription_upgraded`
- `subscription_downgraded`
- `subscription_renewed`

**Implementation Steps:**

1. **Add subscription update handler:**

```python
# billing/webhooks.py

if event.type == 'customer.subscription.updated':
    subscription = event.data.object
    previous = event.data.previous_attributes

    if 'items' in previous:
        old_price = previous['items']['data'][0]['price']['unit_amount']
        new_price = subscription.items.data[0].price.unit_amount

        if new_price > old_price:
            track_financial_event('subscription_upgraded', {
                'customer_id': subscription.customer,
                'subscription_id': subscription.id,
                'previous_plan': previous['items']['data'][0]['price']['id'],
                'new_plan': subscription.items.data[0].price.id,
                'previous_mrr': old_price / 100,
                'new_mrr': new_price / 100,
                'mrr_change': (new_price - old_price) / 100
            })
        elif new_price < old_price:
            track_financial_event('subscription_downgraded', {
                'customer_id': subscription.customer,
                'subscription_id': subscription.id,
                'previous_plan': previous['items']['data'][0]['price']['id'],
                'new_plan': subscription.items.data[0].price.id,
                'previous_mrr': old_price / 100,
                'new_mrr': new_price / 100,
                'mrr_change': (old_price - new_price) / 100
            })
```

### Phase 3: AI Cost Tracking (1 week)

**Events to implement:**
- `ai_request_completed`
- `ai_cost_incurred`
- `ai_feature_used`

**Implementation Steps:**

1. **Create AI tracking decorator:**

```python
# ai/tracking.py

import functools
import time
from core.events import track_ai_event

def track_ai_request(feature: str):
    """Decorator to track AI API calls."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                latency_ms = int((time.time() - start_time) * 1000)

                # Extract usage from response
                usage = result.usage
                model = result.model

                # Calculate cost based on model
                cost = calculate_cost(model, usage.prompt_tokens, usage.completion_tokens)

                track_ai_event('ai_request_completed', {
                    'request_id': request_id,
                    'user_id': kwargs.get('user_id'),
                    'customer_id': kwargs.get('customer_id'),
                    'model': model,
                    'provider': get_provider(model),
                    'tokens_input': usage.prompt_tokens,
                    'tokens_output': usage.completion_tokens,
                    'tokens_total': usage.total_tokens,
                    'latency_ms': latency_ms,
                    'feature': feature,
                    'success': True
                })

                track_ai_event('ai_cost_incurred', {
                    'request_id': request_id,
                    'user_id': kwargs.get('user_id'),
                    'customer_id': kwargs.get('customer_id'),
                    'model': model,
                    'provider': get_provider(model),
                    'cost_usd': cost,
                    'tokens_total': usage.total_tokens,
                    'feature': feature
                })

                return result

            except Exception as e:
                track_ai_event('ai_request_completed', {
                    'request_id': request_id,
                    'user_id': kwargs.get('user_id'),
                    'customer_id': kwargs.get('customer_id'),
                    'model': kwargs.get('model', 'unknown'),
                    'provider': 'unknown',
                    'tokens_input': 0,
                    'tokens_output': 0,
                    'tokens_total': 0,
                    'latency_ms': int((time.time() - start_time) * 1000),
                    'feature': feature,
                    'success': False,
                    'error_code': str(e)
                })
                raise
        return wrapper
    return decorator

# Usage
@track_ai_request(feature='natural_language_query')
async def query_with_ai(prompt: str, user_id: str, customer_id: str):
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response
```

### Phase 4: Customer Acquisition (1-2 weeks)

**Events to implement:**
- `customer_created`
- `lead_created`
- `marketing_spend_recorded`

### Phase 5: Trial & Conversion (1 week)

**Events to implement:**
- `trial_started`
- `trial_ended`

## Step 5: Validate Implementation

After implementing all phases, validate the instrumentation.

### Data Quality Checks

```sql
-- Check for missing required fields
SELECT event_name, COUNT(*) as missing_customer_id
FROM financial_events
WHERE customer_id IS NULL
GROUP BY event_name;

-- Check event volume
SELECT
    event_name,
    COUNT(*) as event_count,
    MIN(created_at) as first_event,
    MAX(created_at) as last_event
FROM financial_events
GROUP BY event_name
ORDER BY event_count DESC;

-- Check MRR consistency
SELECT
    DATE_TRUNC('day', created_at) as date,
    SUM(CASE WHEN event_name = 'subscription_created' THEN (event_data->>'mrr')::numeric ELSE 0 END) as new_mrr,
    SUM(CASE WHEN event_name = 'subscription_cancelled' THEN (event_data->>'mrr_lost')::numeric ELSE 0 END) as churned_mrr
FROM financial_events
WHERE event_name IN ('subscription_created', 'subscription_cancelled')
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC
LIMIT 30;
```

### Run Health Check

```bash
/product-finance:health-check
```

**Expected output:**
```
Financial Health Assessment Complete!
=====================================

Overall Health: GOOD

Data Quality:
  ✓ MRR calculable from events
  ✓ Churn rate calculable
  ✓ NRR calculable
  ✓ AI costs tracked

Files Generated:
  - .product-finance/health-report.json
  - .product-finance/reports/health-report-2026-01-23.md
```

### Run AI Economics

```bash
/product-finance:ai-economics
```

**Expected output:**
```
AI Economics Analysis Complete!
================================

AI Cost Tracking:
  ✓ Total requests: 45,000
  ✓ Total cost: $3,600
  ✓ Cost per request: $0.08
  ✓ Cost per user: $12.00

Files Generated:
  - .product-finance/ai-economics.json
  - .product-finance/reports/ai-economics-report-2026-01-23.md
```

## Troubleshooting

### Events Not Appearing

1. **Check webhook configuration:**
   ```bash
   stripe webhooks list
   ```

2. **Check event emission:**
   ```python
   # Add logging to track_financial_event
   import logging
   logger = logging.getLogger(__name__)

   def track_financial_event(event_name, event_data):
       logger.info(f"Tracking event: {event_name}")
       # ... rest of function
   ```

3. **Check database connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

### Missing Fields

1. **Review event schema:**
   ```bash
   cat .product-finance/instrumentation/events.json | jq '.subscription_events[0]'
   ```

2. **Update implementation:**
   ```python
   # Ensure all required fields are included
   required_fields = ['customer_id', 'subscription_id', 'plan', 'mrr']
   for field in required_fields:
       if field not in event_data:
           raise ValueError(f"Missing required field: {field}")
   ```

### Metrics Still Not Calculable

1. **Check event coverage:**
   ```sql
   SELECT DISTINCT event_name FROM financial_events;
   ```

2. **Verify data quality:**
   ```sql
   SELECT
       event_name,
       COUNT(*) FILTER (WHERE event_data->>'mrr' IS NOT NULL) as has_mrr,
       COUNT(*) FILTER (WHERE event_data->>'mrr' IS NULL) as missing_mrr
   FROM financial_events
   GROUP BY event_name;
   ```

## Maintenance

### Weekly Tasks

1. Check event volume trends
2. Review data quality metrics
3. Monitor for anomalies

### Monthly Tasks

1. Validate calculated metrics against source systems
2. Review and update event schemas if needed
3. Optimize query performance

### Quarterly Tasks

1. Full data quality audit
2. Review and update benchmarks
3. Plan for new metrics/events

## Related Documentation

- [Instrumentation Command](../../commands/instrumentation.md)
- [Event Schemas](../../templates/event-schemas/)
- [Health Check Command](../../commands/health-check.md)
- [AI Economics Command](../../commands/ai-economics.md)
