---
name: instrumentation-event-schema-generation
description: Generate event schemas for financial tracking based on gap analysis
---

# Event Schema Generation Skill

## Purpose

Generate event schemas for financial tracking because consistent, well-documented schemas ensure data quality and enable accurate metric calculation.

## When to Use

- After gap analysis identifies missing events
- When adding new financial features
- Standardizing existing tracking events
- Creating documentation for engineering teams
- Setting up analytics data contracts

## What This Skill Provides

Comprehensive event schema generation including:
- JSON Schema definitions
- Required and optional fields
- Field types and validation
- Implementation examples
- Framework-specific code snippets

## Schema Template Structure

### Event Schema Format
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "subscription_created",
  "description": "Emitted when a new subscription is created",
  "type": "object",
  "event_metadata": {
    "event_name": "subscription_created",
    "event_category": "subscription",
    "event_version": "1.0.0",
    "trigger": "When customer completes signup and subscription is activated",
    "priority": "critical",
    "enables_metrics": ["MRR", "ARR", "New Subscriptions", "Customer Count"]
  },
  "required": ["customer_id", "subscription_id", "plan", "mrr", "start_date"],
  "properties": {
    "customer_id": {
      "type": "string",
      "description": "Unique customer identifier"
    },
    "subscription_id": {
      "type": "string",
      "description": "Unique subscription identifier"
    },
    "plan": {
      "type": "string",
      "description": "Subscription plan name"
    },
    "mrr": {
      "type": "number",
      "description": "Monthly recurring revenue",
      "minimum": 0
    },
    "start_date": {
      "type": "string",
      "format": "date-time",
      "description": "Subscription start date"
    },
    "trial": {
      "type": "boolean",
      "description": "Whether this is a trial subscription"
    },
    "source": {
      "type": "string",
      "description": "Acquisition source"
    }
  }
}
```

## Standard Event Schemas

### Subscription Events

#### subscription_created
```json
{
  "event_name": "subscription_created",
  "category": "subscription",
  "priority": "critical",
  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "subscription_id", "type": "string"},
    {"name": "plan", "type": "string"},
    {"name": "mrr", "type": "number"},
    {"name": "start_date", "type": "date-time"}
  ],
  "optional_fields": [
    {"name": "trial", "type": "boolean"},
    {"name": "source", "type": "string"},
    {"name": "campaign", "type": "string"}
  ],
  "enables_metrics": ["MRR", "ARR", "New Subscriptions"]
}
```

#### subscription_cancelled
```json
{
  "event_name": "subscription_cancelled",
  "category": "subscription",
  "priority": "critical",
  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "subscription_id", "type": "string"},
    {"name": "churned_mrr", "type": "number"},
    {"name": "cancellation_reason", "type": "string"},
    {"name": "subscription_lifetime_days", "type": "integer"}
  ],
  "optional_fields": [
    {"name": "feedback", "type": "string"},
    {"name": "will_return", "type": "boolean"}
  ],
  "enables_metrics": ["Churn Rate", "Churned MRR", "Average Lifetime"]
}
```

#### subscription_upgraded
```json
{
  "event_name": "subscription_upgraded",
  "category": "subscription",
  "priority": "critical",
  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "subscription_id", "type": "string"},
    {"name": "old_plan", "type": "string"},
    {"name": "new_plan", "type": "string"},
    {"name": "old_mrr", "type": "number"},
    {"name": "new_mrr", "type": "number"},
    {"name": "expansion_mrr", "type": "number"}
  ],
  "enables_metrics": ["Expansion MRR", "NRR", "Upgrade Rate"]
}
```

### AI Events

#### ai_request_completed
```json
{
  "event_name": "ai_request_completed",
  "category": "ai",
  "priority": "high",
  "required_fields": [
    {"name": "user_id", "type": "string"},
    {"name": "request_id", "type": "string"},
    {"name": "model", "type": "string"},
    {"name": "provider", "type": "string"},
    {"name": "tokens_input", "type": "integer"},
    {"name": "tokens_output", "type": "integer"},
    {"name": "cost", "type": "number"}
  ],
  "optional_fields": [
    {"name": "latency_ms", "type": "integer"},
    {"name": "feature", "type": "string"},
    {"name": "cached", "type": "boolean"},
    {"name": "success", "type": "boolean"}
  ],
  "enables_metrics": ["AI Cost per Request", "AI Cost per User", "Token Usage"]
}
```

### Payment Events

#### payment_received
```json
{
  "event_name": "payment_received",
  "category": "billing",
  "priority": "high",
  "required_fields": [
    {"name": "customer_id", "type": "string"},
    {"name": "payment_id", "type": "string"},
    {"name": "amount", "type": "number"},
    {"name": "payment_date", "type": "date-time"}
  ],
  "optional_fields": [
    {"name": "payment_method", "type": "string"},
    {"name": "invoice_id", "type": "string"},
    {"name": "currency", "type": "string"}
  ],
  "enables_metrics": ["Revenue", "Payment Collection Efficiency"]
}
```

## Process

1. **Receive Gap Analysis:**
   - Import gaps from gap-analysis skill
   - List events needing schemas

2. **Generate Base Schema:**
   - Apply template structure
   - Set event metadata
   - Define required fields

3. **Add Validation Rules:**
   - Field types and formats
   - Minimum/maximum values
   - Enum constraints

4. **Include Optional Fields:**
   - Context-enriching data
   - Analysis-enabling fields
   - Future-proofing fields

5. **Generate Code Examples:**
   - Framework-specific snippets
   - Test event generators
   - Validation helpers

## Output Format

### Schema Document
```json
{
  "schemas": [
    {
      "event_name": "subscription_created",
      "schema": { /* JSON Schema */ },
      "implementation": {
        "django": "/* Python code */",
        "flask": "/* Python code */",
        "fastapi": "/* Python code */",
        "express": "/* JavaScript code */"
      },
      "test_event": { /* Sample event */ }
    }
  ],
  "metadata": {
    "generated_at": "2024-01-15T10:00:00Z",
    "schema_version": "1.0.0",
    "events_count": 8
  }
}
```

## Implementation Templates

### Django Template
```python
# events/tracking.py
from datetime import datetime
import json
from typing import Optional

def track_subscription_created(
    customer_id: str,
    subscription_id: str,
    plan: str,
    mrr: float,
    start_date: datetime,
    trial: bool = False,
    source: Optional[str] = None
) -> None:
    """Track subscription creation for MRR calculation."""
    event = {
        'event_name': 'subscription_created',
        'event_version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'customer_id': customer_id,
        'subscription_id': subscription_id,
        'plan': plan,
        'mrr': mrr,
        'start_date': start_date.isoformat(),
        'trial': trial,
        'source': source,
    }

    # Send to tracking service
    _emit_event(event)
```

### FastAPI Template
```python
# app/events/subscription.py
from datetime import datetime
from pydantic import BaseModel

class SubscriptionCreatedEvent(BaseModel):
    customer_id: str
    subscription_id: str
    plan: str
    mrr: float
    start_date: datetime
    trial: bool = False
    source: str | None = None

async def track_subscription_created(event: SubscriptionCreatedEvent) -> None:
    """Track subscription creation for MRR calculation."""
    event_data = {
        'event_name': 'subscription_created',
        'event_version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        **event.model_dump()
    }

    await emit_event(event_data)
```

### Express Template
```javascript
// events/subscription.js
const { DateTime } = require('luxon');

const trackSubscriptionCreated = async ({
  customerId,
  subscriptionId,
  plan,
  mrr,
  startDate,
  trial = false,
  source = null
}) => {
  const event = {
    event_name: 'subscription_created',
    event_version: '1.0.0',
    timestamp: DateTime.utc().toISO(),
    customer_id: customerId,
    subscription_id: subscriptionId,
    plan,
    mrr,
    start_date: startDate.toISOString(),
    trial,
    source
  };

  await emitEvent(event);
};

module.exports = { trackSubscriptionCreated };
```

## Schema Versioning

### Version Format
```
MAJOR.MINOR.PATCH
```

- **MAJOR:** Breaking changes (removed required fields)
- **MINOR:** New optional fields added
- **PATCH:** Documentation/description changes

### Migration Strategy
1. New version maintains backward compatibility
2. Old events processed with defaults
3. Deprecation period before breaking changes

## Validation Examples

### Python Validation
```python
from pydantic import BaseModel, validator
from datetime import datetime

class SubscriptionCreatedEvent(BaseModel):
    customer_id: str
    subscription_id: str
    plan: str
    mrr: float
    start_date: datetime

    @validator('mrr')
    def mrr_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('MRR must be non-negative')
        return v

    @validator('plan')
    def plan_must_be_valid(cls, v):
        valid_plans = ['starter', 'pro', 'enterprise']
        if v not in valid_plans:
            raise ValueError(f'Plan must be one of {valid_plans}')
        return v
```

## Reference Templates

See `templates/event-schemas/` for pre-built schema files:
- `subscription_events.json` - All subscription lifecycle events
- `ai_usage_events.json` - AI cost and usage tracking events

## Best Practices

### Field Naming
- Use snake_case for all fields
- Be descriptive but concise
- Include units in description (e.g., "Cost in USD")

### Required vs. Optional
- Required: Essential for metric calculation
- Optional: Enriches analysis but not blocking

### Timestamps
- Always include event timestamp
- Use ISO 8601 format
- Include timezone (UTC preferred)

### IDs
- Use string type for flexibility
- Ensure consistency across events
- Document ID format (UUID, etc.)
