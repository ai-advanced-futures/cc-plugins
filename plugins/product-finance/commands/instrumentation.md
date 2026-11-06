---
description: Generate comprehensive instrumentation plan for financial tracking with codebase analysis, event schemas, and implementation guidance
---

# Product Finance Instrumentation Command

## Purpose

The instrumentation command performs comprehensive codebase analysis to generate a complete financial tracking instrumentation plan. It analyzes your existing codebase for current tracking, identifies gaps in financial metrics coverage, generates event schemas, provides implementation guidance with code templates, and creates database migration scripts.

This command enables systematic instrumentation of financial tracking to ensure complete coverage of all board-level KPIs and financial metrics.

## When to Use

- **Before instrumenting financial tracking:** Generate comprehensive plan for new instrumentation
- **Auditing existing tracking:** Analyze current instrumentation coverage and identify gaps
- **Planning instrumentation sprints:** Organize implementation in phased rollout
- **Onboarding new products:** Establish baseline financial tracking for new products
- **Financial metrics gaps:** Identify missing data points preventing metric calculation
- **Standardizing tracking:** Ensure consistent event schemas across your product
- **Migration planning:** Plan database schema changes for financial data storage

## What It Does

1. **Codebase Analysis:**
   - Detects web framework (Django, Flask, FastAPI, Express, Rails, Next.js)
   - Identifies database type (PostgreSQL, MySQL, SQLite, MongoDB)
   - Discovers existing tracking and instrumentation
   - Detects subscription management patterns
   - Identifies AI/LLM API integrations
   - Finds payment provider integrations

2. **Gap Analysis:**
   - Maps existing events to calculable metrics
   - Identifies missing events preventing metric calculation
   - Prioritizes gaps by business impact (Critical, High, Medium, Low)
   - Determines which metrics each gap prevents

3. **Event Schema Generation:**
   - Creates event schemas for missing tracking
   - Specifies required and optional fields
   - Provides trigger points for event emission
   - Includes validation rules and data types
   - Maps events to enabled metrics

4. **Implementation Guidance:**
   - Generates framework-specific code templates
   - Provides example implementations for each event
   - Suggests implementation locations in codebase
   - Identifies dependencies and prerequisites

5. **Database Migration Scripts:**
   - Creates migration scripts for new tables
   - Generates indexes for query performance
   - Provides both PostgreSQL and MySQL versions
   - Includes rollback scripts for safety

6. **Phased Implementation Plan:**
   - Organizes work into logical phases
   - Prioritizes critical subscription tracking first
   - Estimates effort for each phase
   - Defines success criteria and metrics enabled

## Command Behavior

### Analysis Mode

The command operates in **automated analysis mode** by default:

1. **Codebase path provided:** Analyzes specified directory
2. **No path provided:** Uses current working directory
3. **Framework detection:** Automatically detects web framework and database
4. **Pattern matching:** Scans code for existing instrumentation patterns
5. **Gap identification:** Compares existing tracking to required metrics

### Output Structure

All outputs are saved to `.product-finance/instrumentation/` directory:

```
.product-finance/instrumentation/
├── instrumentation-plan.json        # Complete plan with all analysis
├── instrumentation-plan.md          # Human-readable report
├── events.json                      # Event schemas for implementation
├── migrations/
│   ├── postgresql/
│   │   ├── 001_create_financial_events.sql
│   │   └── 002_create_ai_usage_events.sql
│   └── mysql/
│       ├── 001_create_financial_events.sql
│       └── 002_create_ai_usage_events.sql
├── code-templates/
│   ├── event_emitter.py            # Event emission templates
│   ├── event_consumer.py           # Event processing templates
│   └── metric_calculator.py        # Metric calculation templates
└── api-spec.json                   # API endpoint specifications
```

## Data Collection Flow

### Phase 1: Initial Setup

**Question:** "What codebase would you like to analyze for financial instrumentation?"

**Options:**
- Provide absolute path to codebase root directory
- Use current working directory (default)
- Specify GitHub repository URL for remote analysis

**Why we need this:** Establishes the codebase to analyze for existing tracking and instrumentation opportunities.

### Phase 2: Scope Configuration

**Question:** "What type of product are you instrumenting?"

**Options:**
- `saas_subscription` - SaaS product with subscription billing (default)
- `saas_usage` - SaaS with usage-based billing
- `saas_hybrid` - Hybrid subscription + usage billing
- `marketplace` - Marketplace or platform with transactions
- `ai_product` - AI-powered product with API costs

**Why we need this:** Determines which event schemas and metrics are most relevant.

**Question:** "Do you have AI features that incur API costs?"

**Options:**
- `yes` - AI features present (triggers AI cost tracking)
- `no` - No AI features
- `planned` - AI features planned for future

**Why we need this:** Determines whether to include AI cost tracking instrumentation.

### Phase 3: Framework Detection

The command automatically detects:

**Framework Detection:**
```
Detecting framework...
✓ Framework: Django
✓ Database: PostgreSQL
✓ Subscription model: Detected
✓ AI integration: Detected (anthropic, openai)
✓ Payment provider: stripe
```

**Manual Override (if needed):**

If framework detection fails or is incorrect:

**Question:** "Framework detection uncertain. What framework are you using?"

**Options:**
- `django` - Django
- `flask` - Flask
- `fastapi` - FastAPI
- `express` - Express.js
- `rails` - Ruby on Rails
- `nextjs` - Next.js
- `other` - Other framework

### Phase 4: Existing Tracking Analysis

The command scans your codebase for:

**Analytics Platforms:**
- Segment
- Amplitude
- Mixpanel
- Custom tracking implementations

**Tracking Patterns:**
- `track()` function calls
- `analytics.` method calls
- Event emission patterns
- Webhook handlers
- Database event logs

**Output:**
```
Scanning for existing instrumentation...
✓ Found 23 existing tracking events
✓ Events cover 12 unique event types
✓ Quality: 15 good, 6 fair, 2 poor
```

### Phase 5: Gap Analysis

The command identifies missing instrumentation:

**Required Metrics Check:**

For each board-level KPI, the command verifies required event coverage:

```
Gap Analysis Results
====================

MRR (Monthly Recurring Revenue)
  Status: ⚠ Incomplete
  Missing Events:
    - subscription_created (CRITICAL)
    - subscription_upgraded (HIGH)
    - subscription_downgraded (HIGH)

Churn Rate
  Status: ✗ Cannot Calculate
  Missing Events:
    - subscription_cancelled (CRITICAL)
    - subscription_start_date (CRITICAL)

AI Cost per Request
  Status: ✗ Cannot Calculate
  Missing Events:
    - ai_request_completed (HIGH)
    - ai_cost_incurred (HIGH)
```

### Phase 6: Event Schema Generation

The command generates event schemas for missing tracking:

**Subscription Events (if applicable):**
- `subscription_created` - New subscription tracking
- `subscription_upgraded` - Plan upgrade tracking
- `subscription_downgraded` - Plan downgrade tracking
- `subscription_cancelled` - Churn tracking
- `subscription_renewed` - Renewal tracking
- `payment_received` - Payment collection tracking
- `trial_started` - Trial start tracking
- `trial_ended` - Trial conversion tracking

**AI Cost Events (if applicable):**
- `ai_request_completed` - AI API request tracking
- `ai_cost_incurred` - AI cost attribution
- `ai_feature_used` - AI feature usage

**Customer Events:**
- `customer_created` - New customer acquisition
- `customer_updated` - Profile updates
- `customer_churned` - Customer churn

Each event includes:
- Event name and category
- Description and trigger point
- Priority level (Critical, High, Medium, Low)
- Required fields with types and validation
- Optional fields for enrichment
- Metrics enabled by this event
- Framework-specific code example
- Suggested implementation location

### Phase 7: Database Migration Generation

The command generates database migrations for:

**Financial Events Table:**
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
    INDEX idx_customer_id (customer_id),
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_event_name (event_name),
    INDEX idx_created_at (created_at)
);
```

**AI Usage Events Table (if AI detected):**
```sql
CREATE TABLE IF NOT EXISTS ai_usage_events (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
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
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Phase 8: Code Template Generation

The command generates framework-specific code templates:

**Event Emitter Template (Django example):**
```python
# Event emission helper
from datetime import datetime
from decimal import Decimal
import json

def track_financial_event(event_name: str, event_data: dict) -> None:
    """Track financial event for analytics.

    Args:
        event_name: Name of event (e.g., 'subscription_created')
        event_data: Event data dictionary
    """
    from myapp.models import FinancialEvent

    # Add timestamp if not present
    if 'timestamp' not in event_data:
        event_data['timestamp'] = datetime.utcnow().isoformat()

    # Calculate MRR/ARR impact if applicable
    mrr_impact = event_data.get('mrr', 0) if 'mrr' in event_data else None
    arr_impact = mrr_impact * 12 if mrr_impact else None

    # Store event
    FinancialEvent.objects.create(
        event_name=event_name,
        customer_id=event_data.get('customer_id'),
        subscription_id=event_data.get('subscription_id'),
        event_data=event_data,
        mrr_impact=mrr_impact,
        arr_impact=arr_impact
    )

    # Send to analytics platform (if configured)
    if hasattr(settings, 'ANALYTICS_ENABLED') and settings.ANALYTICS_ENABLED:
        analytics.track(
            user_id=event_data.get('customer_id'),
            event=event_name,
            properties=event_data
        )
```

**Metric Calculator Template:**
```python
# Metric calculation helper
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

class FinancialMetricsCalculator:
    """Calculate financial metrics from event data."""

    @staticmethod
    def calculate_mrr(as_of_date: Optional[datetime] = None) -> Decimal:
        """Calculate Monthly Recurring Revenue as of specific date.

        Args:
            as_of_date: Date to calculate MRR for (defaults to now)

        Returns:
            MRR as Decimal
        """
        if as_of_date is None:
            as_of_date = datetime.utcnow()

        from myapp.models import FinancialEvent

        # Get all subscription_created events
        created = FinancialEvent.objects.filter(
            event_name='subscription_created',
            created_at__lte=as_of_date
        )

        # Get all subscription_cancelled events
        cancelled = FinancialEvent.objects.filter(
            event_name='subscription_cancelled',
            created_at__lte=as_of_date
        )

        # Calculate net MRR
        mrr = Decimal('0')
        for event in created:
            mrr += event.mrr_impact or Decimal('0')

        for event in cancelled:
            mrr -= abs(event.mrr_impact or Decimal('0'))

        return mrr

    @staticmethod
    def calculate_churn_rate(period_days: int = 30) -> float:
        """Calculate churn rate over period.

        Args:
            period_days: Number of days to calculate over

        Returns:
            Churn rate as percentage
        """
        from myapp.models import FinancialEvent

        start_date = datetime.utcnow() - timedelta(days=period_days)

        # Count active subscriptions at start of period
        active_start = FinancialEvent.objects.filter(
            event_name='subscription_created',
            created_at__lt=start_date
        ).exclude(
            subscription_id__in=FinancialEvent.objects.filter(
                event_name='subscription_cancelled',
                created_at__lt=start_date
            ).values('subscription_id')
        ).count()

        # Count cancellations during period
        churned = FinancialEvent.objects.filter(
            event_name='subscription_cancelled',
            created_at__gte=start_date
        ).count()

        if active_start == 0:
            return 0.0

        return (churned / active_start) * 100
```

### Phase 9: API Endpoint Specification

The command generates API endpoint specifications for exposing financial data:

**Financial Health API:**
```json
{
  "endpoint": "/api/financial-health",
  "method": "GET",
  "purpose": "Retrieve current financial health metrics",
  "authentication": "Bearer token required",
  "rate_limit": "100 requests per hour",
  "metrics_exposed": [
    "MRR",
    "ARR",
    "Churn Rate",
    "Net Revenue Retention",
    "Rule of 40 Score"
  ],
  "response_schema": {
    "mrr": "number",
    "mrr_growth_rate": "number",
    "arr": "number",
    "churn_rate": "number",
    "nrr": "number",
    "rule_of_40": "number",
    "as_of_date": "string (ISO 8601)"
  },
  "caching_strategy": "Cache for 1 hour, refresh on demand",
  "example_request": "GET /api/financial-health?as_of_date=2026-01-23",
  "example_response": {
    "mrr": 125000,
    "mrr_growth_rate": 15.2,
    "arr": 1500000,
    "churn_rate": 2.3,
    "nrr": 112,
    "rule_of_40": 67.5,
    "as_of_date": "2026-01-23T00:00:00Z"
  }
}
```

**AI Economics API:**
```json
{
  "endpoint": "/api/ai-economics",
  "method": "GET",
  "purpose": "Retrieve AI cost and ROI metrics",
  "authentication": "Bearer token required",
  "rate_limit": "100 requests per hour",
  "metrics_exposed": [
    "Total AI Cost",
    "AI Cost per User",
    "AI Cost per Request",
    "AI ROI"
  ],
  "query_parameters": {
    "start_date": "ISO 8601 date",
    "end_date": "ISO 8601 date",
    "group_by": "day|week|month"
  },
  "response_schema": {
    "total_ai_cost": "number",
    "ai_cost_per_user": "number",
    "ai_cost_per_request": "number",
    "total_requests": "number",
    "ai_roi": "number",
    "period_start": "string",
    "period_end": "string"
  }
}
```

### Phase 10: Implementation Phases

The command organizes implementation into logical phases:

**Phase 1: Critical Subscription Tracking (1-2 weeks)**
- Objectives:
  - Implement core subscription lifecycle tracking
  - Enable MRR/ARR calculation
  - Enable churn rate tracking
- Events to implement:
  - `subscription_created`
  - `subscription_cancelled`
  - `payment_received`
- Metrics enabled:
  - MRR, ARR, New Subscriptions, Churn Rate
- Success criteria:
  - All subscription events emitting correctly
  - MRR calculation matches billing system
  - Churn rate calculable from events

**Phase 2: Expansion & Contraction Tracking (1 week)**
- Objectives:
  - Track subscription plan changes
  - Enable Net Revenue Retention calculation
  - Identify expansion revenue opportunities
- Events to implement:
  - `subscription_upgraded`
  - `subscription_downgraded`
  - `subscription_renewed`
- Metrics enabled:
  - Expansion MRR, Contraction MRR, Net Revenue Retention
- Success criteria:
  - Plan changes tracked accurately
  - NRR calculation working
  - Expansion/contraction trends visible

**Phase 3: AI Cost Tracking (1 week)** *(if AI detected)*
- Objectives:
  - Track AI API usage and costs
  - Enable AI ROI calculation
  - Identify cost optimization opportunities
- Events to implement:
  - `ai_request_completed`
  - `ai_cost_incurred`
  - `ai_feature_used`
- Metrics enabled:
  - AI Cost per Request, AI Cost per User, AI ROI
- Success criteria:
  - All AI requests tracked
  - Cost attribution working
  - ROI calculable

**Phase 4: Customer Acquisition Tracking (1-2 weeks)**
- Objectives:
  - Track customer acquisition sources
  - Enable CAC calculation
  - Measure channel effectiveness
- Events to implement:
  - `customer_created`
  - `lead_converted`
  - `marketing_spend_recorded`
- Metrics enabled:
  - CAC, LTV:CAC Ratio, Payback Period
- Success criteria:
  - All new customers tracked
  - CAC by channel calculable
  - LTV:CAC ratio available

**Phase 5: Trial & Conversion Tracking (1 week)**
- Objectives:
  - Track trial starts and conversions
  - Measure trial effectiveness
  - Identify conversion optimization opportunities
- Events to implement:
  - `trial_started`
  - `trial_ended`
- Metrics enabled:
  - Trial Conversion Rate, Trial-to-Paid Time
- Success criteria:
  - All trials tracked
  - Conversion funnel visible
  - Optimization insights available

### Phase 11: Validation & Testing

The command provides validation requirements:

**Unit Tests:**
```python
# Test event emission
def test_subscription_created_event():
    """Test subscription_created event emits correctly."""
    customer = create_test_customer()
    subscription = create_test_subscription(customer, plan='professional')

    # Verify event was created
    event = FinancialEvent.objects.filter(
        event_name='subscription_created',
        customer_id=customer.id
    ).first()

    assert event is not None
    assert event.event_data['plan'] == 'professional'
    assert event.mrr_impact == Decimal('99.00')

# Test metric calculation
def test_mrr_calculation():
    """Test MRR calculation from events."""
    # Create test events
    create_subscription_event(mrr=100)
    create_subscription_event(mrr=200)
    create_cancellation_event(mrr=50)

    # Calculate MRR
    calculator = FinancialMetricsCalculator()
    mrr = calculator.calculate_mrr()

    assert mrr == Decimal('250.00')
```

**Data Quality Checks:**
```sql
-- Check for missing required fields
SELECT event_name, COUNT(*) as missing_count
FROM financial_events
WHERE customer_id IS NULL
   OR event_data IS NULL
GROUP BY event_name;

-- Check for orphaned events (missing related events)
SELECT s.subscription_id, s.event_name
FROM financial_events s
LEFT JOIN financial_events c
  ON s.subscription_id = c.subscription_id
  AND c.event_name = 'subscription_created'
WHERE s.event_name = 'subscription_cancelled'
  AND c.id IS NULL;

-- Check for data consistency
SELECT
  event_name,
  COUNT(*) as event_count,
  COUNT(DISTINCT customer_id) as unique_customers,
  MIN(created_at) as first_event,
  MAX(created_at) as last_event
FROM financial_events
GROUP BY event_name
ORDER BY event_count DESC;
```

## Output Summary

After completion, the command displays:

```
Instrumentation Plan Generated
==============================

Codebase Analysis:
  Framework: Django
  Database: PostgreSQL
  Subscription model: Yes
  AI integration: Yes (anthropic, openai)
  Payment provider: Stripe
  Existing tracking: 23 events

Gap Analysis:
  Identified gaps: 8
  Critical gaps: 3
  High priority gaps: 5

Event Recommendations:
  Total events: 15
  Critical priority: 5
  High priority: 7
  Medium priority: 3

Database Migrations:
  New tables: 2
  Table modifications: 0

Implementation Plan:
  Total phases: 5
  Estimated effort: 12 days
  First phase: Critical Subscription Tracking (1-2 weeks)

Files Created:
  ✓ .product-finance/instrumentation/instrumentation-plan.json
  ✓ .product-finance/instrumentation/instrumentation-plan.md
  ✓ .product-finance/instrumentation/events.json
  ✓ .product-finance/instrumentation/migrations/ (4 files)
  ✓ .product-finance/instrumentation/code-templates/ (3 files)
  ✓ .product-finance/instrumentation/api-spec.json

Next Steps:
  1. Review instrumentation-plan.md for detailed analysis
  2. Review event schemas in events.json
  3. Run database migrations (start with Phase 1)
  4. Implement critical events first (subscription_created, subscription_cancelled)
  5. Deploy and validate with test data
  6. Monitor data quality with provided validation queries
  7. Proceed to Phase 2 once Phase 1 is validated
```

## Integration with Other Commands

### With `/product-finance:setup`

After running setup, instrumentation provides the implementation roadmap:

```bash
# Run setup first to configure plugin
/product-finance:setup

# Then generate instrumentation plan
/product-finance:instrumentation
```

### With `/product-finance:health-check`

Instrumentation identifies which health-check metrics are currently unavailable:

```bash
# Generate instrumentation plan
/product-finance:instrumentation

# After implementing events, validate with health check
/product-finance:health-check
```

The health-check command will show which metrics are now available vs. still missing.

### With `/product-finance:discover`

Discovery analysis benefits from proper instrumentation:

```bash
# Instrument tracking first
/product-finance:instrumentation

# Then run discovery with actual data
/product-finance:discover
```

## Best Practices

### Event Naming

**Use verb-noun pattern:**
- Good: `subscription_created`, `payment_received`, `trial_started`
- Bad: `new_subscription`, `got_payment`, `start_trial`

**Be specific:**
- Good: `subscription_cancelled`, `subscription_upgraded`
- Bad: `subscription_changed`

**Use past tense:**
- Good: `customer_created`, `invoice_sent`
- Bad: `create_customer`, `sending_invoice`

### Event Data

**Include context:**
```json
{
  "event": "subscription_created",
  "timestamp": "2026-01-23T10:30:00Z",
  "customer_id": "cus_123",
  "subscription_id": "sub_456",
  "plan": "professional",
  "mrr": 99.00,
  "source": "organic",
  "metadata": {
    "campaign": "holiday_promo",
    "referrer": "partner_xyz"
  }
}
```

**Avoid PII in events:**
- Leave out email addresses, phone numbers and full names, because the plan needs events, not people
- Do include: customer IDs, anonymized identifiers

**Use consistent IDs:**
- Maintain same customer_id across all events
- Use same subscription_id for lifecycle events

### Database Schema

**Use indexes strategically:**
```sql
-- Critical for queries
CREATE INDEX idx_customer_id ON financial_events (customer_id);
CREATE INDEX idx_event_name ON financial_events (event_name);
CREATE INDEX idx_created_at ON financial_events (created_at);

-- For time-series analysis
CREATE INDEX idx_customer_date ON financial_events (customer_id, created_at);

-- For JSONB queries (PostgreSQL)
CREATE INDEX idx_event_data_gin ON financial_events USING GIN (event_data);
```

**Data types:**
- Use `DECIMAL(10,2)` for currency, not `FLOAT`
- Use `TIMESTAMP WITH TIME ZONE` for timestamps
- Use `JSONB` for flexible event data (PostgreSQL)
- Use `JSON` for flexible event data (MySQL)

### Implementation

**Emit events asynchronously:**
```python
# Good: Non-blocking event emission
from celery import shared_task

@shared_task
def emit_financial_event(event_name, event_data):
    track_financial_event(event_name, event_data)

# In your code
emit_financial_event.delay('subscription_created', event_data)
```

**Use idempotency keys:**
```python
def track_financial_event(event_name, event_data, idempotency_key=None):
    """Track event with idempotency protection."""
    if idempotency_key:
        existing = FinancialEvent.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        if existing:
            return existing  # Event already processed

    event = FinancialEvent.objects.create(
        event_name=event_name,
        event_data=event_data,
        idempotency_key=idempotency_key
    )
    return event
```

**Validate event schemas:**
```python
from pydantic import BaseModel, Field, validator

class SubscriptionCreatedEvent(BaseModel):
    """Schema for subscription_created event."""
    event: str = Field(default='subscription_created')
    timestamp: datetime
    customer_id: str
    subscription_id: str
    plan: str
    mrr: Decimal = Field(ge=0)
    currency: str = Field(default='USD')

    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD']
        if v not in valid_currencies:
            raise ValueError(f'Invalid currency: {v}')
        return v

# Validate before emitting
def emit_subscription_created(event_data: dict):
    try:
        validated = SubscriptionCreatedEvent(**event_data)
        track_financial_event('subscription_created', validated.dict())
    except ValidationError as e:
        logger.error(f'Event validation failed: {e}')
        raise
```

## Troubleshooting

### Framework Not Detected

**Problem:** Framework detection shows "unknown"

**Solution:**
```bash
# Provide framework hint in codebase path
/product-finance:instrumentation --codebase=/path/to/project --framework=django

# Or check for framework files
ls requirements.txt  # Python projects
ls package.json      # Node.js projects
ls Gemfile          # Ruby projects
```

### Missing Events Not Identified

**Problem:** Gap analysis doesn't find expected missing events

**Solution:**
- Verify codebase path is correct
- Check that tracking patterns are recognized
- Look for custom tracking implementations
- Manually specify required metrics

### Database Migration Fails

**Problem:** Migration script fails to run

**Solution:**
```sql
-- Check database version
SELECT version();

-- Check for existing tables
SELECT table_name
FROM information_schema.tables
WHERE table_name IN ('financial_events', 'ai_usage_events');

-- Check for column conflicts
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'financial_events';
```

### Event Validation Errors

**Problem:** Events fail validation after implementation

**Solution:**
```python
# Add detailed error logging
import logging
logger = logging.getLogger(__name__)

def track_financial_event(event_name, event_data):
    try:
        # Validate required fields
        required_fields = ['customer_id', 'timestamp']
        missing = [f for f in required_fields if f not in event_data]
        if missing:
            logger.error(f'Missing required fields: {missing}')
            return None

        # Validate data types
        if not isinstance(event_data['customer_id'], str):
            logger.error('customer_id must be string')
            return None

        # Store event
        event = FinancialEvent.objects.create(...)
        logger.info(f'Event tracked: {event_name}')
        return event

    except Exception as e:
        logger.exception(f'Failed to track event: {e}')
        raise
```

## Technical Details

### Codebase Scanning

The analyzer uses pattern matching to detect frameworks and tracking:

**Framework Detection Patterns:**
```python
FRAMEWORK_PATTERNS = {
    'django': [r'from django\.', r'Django', r'settings\.py'],
    'flask': [r'from flask import', r'Flask\(', r'@app\.route'],
    'fastapi': [r'from fastapi import', r'FastAPI\('],
    'express': [r"require\(['\"]express['\"]\)", r'app\.(get|post)'],
    'rails': [r'Rails\.application', r'ApplicationController'],
    'nextjs': [r'next/', r'getServerSideProps']
}
```

**Tracking Pattern Detection:**
```python
TRACKING_PATTERNS = [
    r'track\(',
    r'analytics\.',
    r'segment\.',
    r'amplitude\.',
    r'mixpanel\.',
    r'log_event',
    r'emit_event'
]
```

### Gap Analysis Algorithm

The analyzer maps events to metrics:

```python
# Define metric dependencies
METRIC_DEPENDENCIES = {
    'MRR': ['subscription_created', 'subscription_upgraded',
            'subscription_downgraded', 'subscription_cancelled'],
    'Churn Rate': ['subscription_cancelled', 'subscription_start_date'],
    'CAC': ['customer_created', 'marketing_spend'],
    'LTV': ['subscription_created', 'payment_received'],
    'AI Cost': ['ai_request_completed', 'ai_cost_incurred'],
    'NRR': ['subscription_upgraded', 'subscription_downgraded',
            'subscription_cancelled']
}

# Identify gaps
tracked_events = get_existing_events()
for metric, required_events in METRIC_DEPENDENCIES.items():
    missing = [e for e in required_events if e not in tracked_events]
    if missing:
        create_gap(metric, missing)
```

### Priority Calculation

Event priority is determined by:

1. **Critical:** Required for board-level KPIs (MRR, Churn)
2. **High:** Required for operational metrics (CAC, LTV)
3. **Medium:** Nice-to-have for deeper analysis
4. **Low:** Enrichment data

```python
def calculate_priority(event_name, enables_metrics):
    """Calculate event implementation priority."""
    critical_metrics = ['MRR', 'ARR', 'Churn Rate']
    high_metrics = ['CAC', 'LTV', 'AI Cost']

    for metric in enables_metrics:
        if metric in critical_metrics:
            return Priority.CRITICAL
        if metric in high_metrics:
            return Priority.HIGH

    return Priority.MEDIUM
```

### Effort Estimation

Implementation effort is estimated using:

```python
def estimate_effort():
    """Estimate implementation effort in days."""
    effort = 0

    # Events: 0.5-2 days per event by priority
    for event in recommended_events:
        if event.priority == Priority.CRITICAL:
            effort += 2
        elif event.priority == Priority.HIGH:
            effort += 1
        else:
            effort += 0.5

    # Database migrations: 1.5 days per migration
    effort += len(database_migrations) * 1.5

    # Testing and QA: 30% overhead
    effort *= 1.3

    return int(effort) + 1
```

## Example Output

### Complete Instrumentation Plan

See `.product-finance/instrumentation/instrumentation-plan.json` for the complete structured output.

### Human-Readable Report

See `.product-finance/instrumentation/instrumentation-plan.md` for the detailed implementation guide.

### Event Schema Example

```json
{
  "event_name": "subscription_created",
  "event_category": "subscription",
  "description": "Emitted when a new subscription is created",
  "trigger": "When customer completes signup and subscription is activated",
  "priority": "critical",
  "required_fields": [
    {
      "field_name": "customer_id",
      "field_type": "string",
      "description": "Unique customer identifier"
    },
    {
      "field_name": "subscription_id",
      "field_type": "string",
      "description": "Unique subscription identifier"
    },
    {
      "field_name": "plan",
      "field_type": "string",
      "description": "Subscription plan name"
    },
    {
      "field_name": "mrr",
      "field_type": "number",
      "description": "Monthly recurring revenue"
    }
  ],
  "enables_metrics": [
    "MRR",
    "ARR",
    "New Subscriptions",
    "Customer Count"
  ],
  "example_code": "# Django example\nfrom datetime import datetime\n\ndef create_subscription(customer, plan):\n    subscription = Subscription.objects.create(\n        customer=customer,\n        plan=plan,\n        start_date=datetime.now()\n    )\n    \n    track_event('subscription_created', {\n        'customer_id': str(customer.id),\n        'subscription_id': str(subscription.id),\n        'plan': plan.name,\n        'mrr': float(plan.monthly_price),\n        'timestamp': datetime.utcnow().isoformat(),\n    })\n    \n    return subscription"
}
```

## Agent Dispatch

Dispatch the `product-finance:instrumentation-planner` agent (Sonnet) with the `Agent` tool.

**Process:**
1. Agent analyzes codebase to detect framework, database, and existing tracking
2. Agent identifies gaps in financial metrics coverage
3. Agent uses skills: gap-analysis, event-schema-generation, migration-planning
4. Agent generates implementation plan with phased rollout
5. Agent creates code templates and migration scripts

**Skills Used:**
- `codebase-analysis` - Detect framework, database, subscription patterns, AI integrations
- `gap-analysis` - Map existing events to metrics, identify missing instrumentation
- `event-schema-generation` - Create event schemas with fields, triggers, and validation
- `migration-planning` - Generate database migrations for PostgreSQL and MySQL
- `code-template-generation` - Create framework-specific implementation templates
- `phased-implementation` - Organize work into logical phases with effort estimates

**Output:**
- `.product-finance/instrumentation/instrumentation-plan.json` - Complete plan
- `.product-finance/instrumentation/instrumentation-plan.md` - Human-readable report
- `.product-finance/instrumentation/events.json` - Event schemas
- `.product-finance/instrumentation/migrations/` - Database migration scripts
- `.product-finance/instrumentation/code-templates/` - Implementation templates
- `.product-finance/instrumentation/api-spec.json` - API endpoint specifications

**User Interaction:** Low (provides codebase path and product type, reviews generated plan)

---

## Related Commands

- `/product-finance:setup` - Initial plugin configuration (run first)
- `/product-finance:health-check` - Validate implemented instrumentation
- `/product-finance:discover` - Use instrumented data for market analysis
- `/product-finance:ai-economics` - Use AI cost tracking from instrumentation

## References

- **Event schemas:** See `templates/event-schemas/` for complete schemas
- **Python analyzer:** See `scripts/instrumentation_analyzer.py` for analysis implementation
- **Template plan:** See `templates/instrumentation-plan.json` for output structure

---

**Pro tip:** Implement instrumentation in phases. Start with critical subscription tracking (Phase 1), validate data quality, then proceed to subsequent phases. This reduces risk and ensures each phase is working correctly before moving forward.
