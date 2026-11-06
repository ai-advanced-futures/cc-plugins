# Instrumentation Plan: DataSync Pro

**Generated:** January 23, 2026
**Codebase:** /app/datasync-pro
**Framework:** Django 4.2 + PostgreSQL 15.2

---

## Executive Summary

This plan outlines the implementation of comprehensive financial tracking instrumentation for DataSync Pro. The goal is to enable automated calculation of all board-level KPIs and financial metrics.

### Current State

| Category | Status | Coverage |
|----------|--------|----------|
| Subscription Lifecycle | Partial | 40% |
| AI Usage Tracking | None | 0% |
| Customer Lifecycle | Partial | 30% |
| Acquisition Tracking | Partial | 25% |
| **Overall** | **Incomplete** | **24%** |

### Target State

| Category | Target | Enables |
|----------|--------|---------|
| Subscription Lifecycle | Complete | MRR, ARR, Churn, NRR |
| AI Usage Tracking | Complete | AI Cost, AI ROI |
| Customer Lifecycle | Complete | Customer Count, Health |
| Acquisition Tracking | Complete | CAC, LTV:CAC |
| **Overall** | **Complete** | **All KPIs** |

### Implementation Summary

| Phase | Events | Effort | Metrics Enabled |
|-------|--------|--------|-----------------|
| 1 - Critical Subscription | 3 | 1-2 weeks | MRR, ARR, Churn |
| 2 - Expansion/Contraction | 3 | 1 week | NRR, Expansion |
| 3 - AI Cost Tracking | 3 | 1 week | AI Cost, AI ROI |
| 4 - Customer Acquisition | 3 | 1-2 weeks | CAC, LTV:CAC |
| 5 - Trial & Conversion | 2 | 1 week | Trial Conversion |
| **Total** | **14** | **5-7 weeks** | **All KPIs** |

---

## Gap Analysis

### Subscription Lifecycle

**Current State:** Partial (40%)

| Event | Status | Impact |
|-------|--------|--------|
| subscription_created | Exists (fair quality) | Missing MRR field |
| subscription_upgraded | Missing | Cannot track expansion |
| subscription_downgraded | Missing | Cannot track contraction |
| subscription_cancelled | Missing | Cannot calculate churn |
| subscription_renewed | Missing | Cannot track renewals |

**Metrics Blocked:**
- Net Revenue Retention (NRR)
- Churn Rate
- Expansion MRR
- Contraction MRR

### AI Usage Tracking

**Current State:** None (0%)

| Event | Status | Impact |
|-------|--------|--------|
| ai_request_completed | Missing | No usage tracking |
| ai_cost_incurred | Missing | No cost tracking |
| ai_feature_used | Missing | No adoption tracking |

**Metrics Blocked:**
- AI Cost per Request
- AI Cost per User
- AI ROI
- AI Adoption Rate

### Customer Lifecycle

**Current State:** Partial (30%)

| Event | Status | Impact |
|-------|--------|--------|
| user_signed_up | Exists (good) | User-level only |
| customer_created | Missing | No org-level tracking |
| customer_churned | Missing | No churn reason |

**Metrics Blocked:**
- Customer Count (accurate)
- Customer Health Score
- Churn by Reason

### Acquisition Tracking

**Current State:** Partial (25%)

| Event | Status | Impact |
|-------|--------|--------|
| lead_created | Missing | No funnel tracking |
| marketing_spend_recorded | Missing | No CAC calculation |
| trial_started | Missing | No trial tracking |
| trial_ended | Missing | No conversion tracking |

**Metrics Blocked:**
- CAC
- CAC by Channel
- Trial Conversion Rate

---

## Implementation Plan

### Phase 1: Critical Subscription Tracking

**Duration:** 1-2 weeks
**Priority:** Critical
**Metrics Enabled:** MRR, ARR, Churn Rate

#### Events to Implement

##### 1. subscription_created

```json
{
  "event_name": "subscription_created",
  "priority": "critical",
  "trigger": "Stripe webhook: customer.subscription.created",

  "required_fields": [
    {"name": "customer_id", "type": "string", "source": "subscription.customer"},
    {"name": "subscription_id", "type": "string", "source": "subscription.id"},
    {"name": "plan", "type": "string", "source": "subscription.items.data[0].price.id"},
    {"name": "mrr", "type": "number", "source": "subscription.items.data[0].price.unit_amount / 100"},
    {"name": "billing_cycle", "type": "string", "source": "subscription.items.data[0].price.recurring.interval"},
    {"name": "start_date", "type": "datetime", "source": "subscription.start_date"}
  ],

  "optional_fields": [
    {"name": "discount_pct", "type": "number"},
    {"name": "promo_code", "type": "string"},
    {"name": "source_channel", "type": "string"},
    {"name": "sales_rep_id", "type": "string"}
  ],

  "enables_metrics": ["MRR", "ARR", "Customer Count", "New MRR"]
}
```

**Implementation Location:** `billing/webhooks.py`

**Code Example:**

```python
@csrf_exempt
def stripe_webhook(request):
    event = stripe.Event.construct_from(
        json.loads(request.body), stripe.api_key
    )

    if event.type == 'customer.subscription.created':
        subscription = event.data.object
        plan_item = subscription['items']['data'][0]

        track_financial_event('subscription_created', {
            'customer_id': subscription['customer'],
            'subscription_id': subscription['id'],
            'plan': plan_item['price']['id'],
            'mrr': plan_item['price']['unit_amount'] / 100,
            'billing_cycle': plan_item['price']['recurring']['interval'],
            'start_date': datetime.fromtimestamp(
                subscription['start_date']
            ).isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        })

    return HttpResponse(status=200)
```

##### 2. subscription_cancelled

```json
{
  "event_name": "subscription_cancelled",
  "priority": "critical",
  "trigger": "Stripe webhook: customer.subscription.deleted",

  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "subscription_id", "type": "string"},
    {"name": "plan", "type": "string"},
    {"name": "mrr_lost", "type": "number"},
    {"name": "cancellation_date", "type": "datetime"},
    {"name": "effective_date", "type": "datetime"}
  ],

  "optional_fields": [
    {"name": "cancellation_reason", "type": "string"},
    {"name": "feedback", "type": "string"},
    {"name": "win_back_eligible", "type": "boolean"}
  ],

  "enables_metrics": ["Churn Rate", "Churned MRR", "NRR"]
}
```

##### 3. payment_received (Update Existing)

Enhance existing event with MRR impact:

```python
track_financial_event('payment_received', {
    'customer_id': invoice['customer'],
    'invoice_id': invoice['id'],
    'amount': invoice['amount_paid'] / 100,
    'mrr_impact': invoice['lines']['data'][0]['amount'] / 100,
    'currency': invoice['currency'],
    'timestamp': datetime.utcnow().isoformat()
})
```

#### Validation Criteria

- [ ] All subscription creates emit events
- [ ] All cancellations emit events
- [ ] MRR calculable from events matches Stripe
- [ ] Churn rate calculable

---

### Phase 2: Expansion & Contraction Tracking

**Duration:** 1 week
**Priority:** High
**Metrics Enabled:** NRR, Expansion MRR, Contraction MRR

#### Events to Implement

##### 1. subscription_upgraded

```json
{
  "event_name": "subscription_upgraded",
  "priority": "critical",
  "trigger": "Stripe webhook: customer.subscription.updated (price increased)",

  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "subscription_id", "type": "string"},
    {"name": "previous_plan", "type": "string"},
    {"name": "new_plan", "type": "string"},
    {"name": "previous_mrr", "type": "number"},
    {"name": "new_mrr", "type": "number"},
    {"name": "mrr_change", "type": "number"}
  ],

  "enables_metrics": ["Expansion MRR", "NRR"]
}
```

##### 2. subscription_downgraded

```json
{
  "event_name": "subscription_downgraded",
  "priority": "critical",
  "trigger": "Stripe webhook: customer.subscription.updated (price decreased)",

  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "subscription_id", "type": "string"},
    {"name": "previous_plan", "type": "string"},
    {"name": "new_plan", "type": "string"},
    {"name": "previous_mrr", "type": "number"},
    {"name": "new_mrr", "type": "number"},
    {"name": "mrr_change", "type": "number"}
  ],

  "enables_metrics": ["Contraction MRR", "NRR"]
}
```

##### 3. subscription_renewed

```json
{
  "event_name": "subscription_renewed",
  "priority": "high",
  "trigger": "Stripe webhook: invoice.paid for renewal",

  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "subscription_id", "type": "string"},
    {"name": "plan", "type": "string"},
    {"name": "mrr", "type": "number"},
    {"name": "renewal_date", "type": "datetime"},
    {"name": "next_renewal_date", "type": "datetime"}
  ],

  "enables_metrics": ["Renewal Rate", "GRR"]
}
```

---

### Phase 3: AI Cost Tracking

**Duration:** 1 week
**Priority:** High
**Metrics Enabled:** AI Cost per Request, AI Cost per User, AI ROI

#### Events to Implement

##### 1. ai_request_completed

```json
{
  "event_name": "ai_request_completed",
  "priority": "high",
  "trigger": "After each AI API call completes",

  "required_fields": [
    {"name": "request_id", "type": "string"},
    {"name": "user_id", "type": "string"},
    {"name": "customer_id", "type": "string"},
    {"name": "model", "type": "string"},
    {"name": "provider", "type": "string"},
    {"name": "tokens_input", "type": "integer"},
    {"name": "tokens_output", "type": "integer"},
    {"name": "tokens_total", "type": "integer"},
    {"name": "latency_ms", "type": "integer"}
  ],

  "optional_fields": [
    {"name": "feature", "type": "string"},
    {"name": "success", "type": "boolean"},
    {"name": "error_code", "type": "string"},
    {"name": "cache_hit", "type": "boolean"}
  ],

  "enables_metrics": ["AI Usage", "AI Latency"]
}
```

**Implementation Location:** `ai/client.py`

**Code Example:**

```python
import functools
import time
import uuid

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

                track_ai_event('ai_request_completed', {
                    'request_id': request_id,
                    'user_id': kwargs.get('user_id'),
                    'customer_id': kwargs.get('customer_id'),
                    'model': result.model,
                    'provider': 'openai' if 'gpt' in result.model else 'anthropic',
                    'tokens_input': result.usage.prompt_tokens,
                    'tokens_output': result.usage.completion_tokens,
                    'tokens_total': result.usage.total_tokens,
                    'latency_ms': latency_ms,
                    'feature': feature,
                    'success': True,
                    'timestamp': datetime.utcnow().isoformat()
                })

                return result
            except Exception as e:
                # Track failed requests too
                track_ai_event('ai_request_completed', {
                    'request_id': request_id,
                    'success': False,
                    'error_code': str(type(e).__name__),
                    # ... other fields
                })
                raise

        return wrapper
    return decorator
```

##### 2. ai_cost_incurred

```json
{
  "event_name": "ai_cost_incurred",
  "priority": "high",
  "trigger": "After calculating cost for AI request",

  "required_fields": [
    {"name": "request_id", "type": "string"},
    {"name": "user_id", "type": "string"},
    {"name": "customer_id", "type": "string"},
    {"name": "model", "type": "string"},
    {"name": "provider", "type": "string"},
    {"name": "cost_usd", "type": "decimal"},
    {"name": "tokens_total", "type": "integer"}
  ],

  "enables_metrics": ["AI Cost", "AI Cost per User", "AI Cost per Request"]
}
```

##### 3. ai_feature_used

```json
{
  "event_name": "ai_feature_used",
  "priority": "medium",
  "trigger": "When user interacts with AI feature",

  "required_fields": [
    {"name": "user_id", "type": "string"},
    {"name": "customer_id", "type": "string"},
    {"name": "feature", "type": "string"},
    {"name": "action", "type": "string"}
  ],

  "enables_metrics": ["AI Adoption", "AI Feature Usage"]
}
```

---

### Phase 4: Customer Acquisition

**Duration:** 1-2 weeks
**Priority:** Medium
**Metrics Enabled:** CAC, CAC by Channel, LTV:CAC

#### Events to Implement

1. **customer_created** - Organization-level tracking
2. **lead_created** - Funnel tracking
3. **marketing_spend_recorded** - Cost tracking

---

### Phase 5: Trial & Conversion

**Duration:** 1 week
**Priority:** Medium
**Metrics Enabled:** Trial Conversion Rate

#### Events to Implement

1. **trial_started**
2. **trial_ended**

---

## Database Migrations

### Migration 1: Financial Events Table

**File:** `001_create_financial_events.sql`

```sql
CREATE TABLE IF NOT EXISTS financial_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) DEFAULT '1.0.0',
    customer_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255),
    event_data JSONB NOT NULL,
    mrr_impact DECIMAL(10, 2),
    arr_impact DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT financial_events_customer_id_idx
        FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Performance indexes
CREATE INDEX idx_financial_events_customer_id
    ON financial_events (customer_id);
CREATE INDEX idx_financial_events_subscription_id
    ON financial_events (subscription_id);
CREATE INDEX idx_financial_events_event_name
    ON financial_events (event_name);
CREATE INDEX idx_financial_events_created_at
    ON financial_events (created_at);
CREATE INDEX idx_financial_events_event_data
    ON financial_events USING GIN (event_data);
```

### Migration 2: AI Usage Events Table

**File:** `002_create_ai_usage_events.sql`

```sql
CREATE TABLE IF NOT EXISTS ai_usage_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) DEFAULT '1.0.0',
    user_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    request_id VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    tokens_total INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    latency_ms INTEGER,
    feature VARCHAR(255),
    success BOOLEAN DEFAULT TRUE,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_ai_usage_events_customer_id
    ON ai_usage_events (customer_id);
CREATE INDEX idx_ai_usage_events_user_id
    ON ai_usage_events (user_id);
CREATE INDEX idx_ai_usage_events_model
    ON ai_usage_events (model);
CREATE INDEX idx_ai_usage_events_created_at
    ON ai_usage_events (created_at);
CREATE INDEX idx_ai_usage_events_feature
    ON ai_usage_events (feature);
```

---

## Validation Checklist

### Phase 1 Complete

- [ ] subscription_created events firing correctly
- [ ] subscription_cancelled events firing correctly
- [ ] payment_received events include MRR impact
- [ ] MRR calculation matches Stripe dashboard
- [ ] Churn rate calculable

### Phase 2 Complete

- [ ] subscription_upgraded events firing correctly
- [ ] subscription_downgraded events firing correctly
- [ ] subscription_renewed events firing correctly
- [ ] NRR calculable from events

### Phase 3 Complete

- [ ] ai_request_completed events firing correctly
- [ ] ai_cost_incurred events firing correctly
- [ ] ai_feature_used events firing correctly
- [ ] AI cost per request calculable
- [ ] AI ROI calculable

### Phase 4 Complete

- [ ] customer_created events firing correctly
- [ ] lead_created events firing correctly
- [ ] marketing_spend_recorded events firing correctly
- [ ] CAC calculable from events

### Phase 5 Complete

- [ ] trial_started events firing correctly
- [ ] trial_ended events firing correctly
- [ ] Trial conversion rate calculable

### Full Validation

- [ ] All board-level KPIs calculable
- [ ] Health check command passes
- [ ] AI economics command passes
- [ ] Unit economics command passes

---

## Success Criteria

### Data Quality

| Metric | Target | Validation |
|--------|--------|------------|
| Event completeness | 100% | No missing required fields |
| Event accuracy | 99%+ | Matches source systems |
| Event latency | <1 minute | Real-time tracking |
| Data consistency | 100% | Customer IDs match across events |

### Metric Calculability

| Metric | Status | Notes |
|--------|--------|-------|
| MRR | Must match Stripe | Within 1% variance |
| Churn Rate | Must be calculable | From events alone |
| NRR | Must be calculable | From events alone |
| AI Cost | Must be calculable | From events alone |
| CAC | Must be calculable | With marketing data |

---

*Generated by Product Finance Plugin v1.0.0*
