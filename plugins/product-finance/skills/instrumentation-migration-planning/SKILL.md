---
name: instrumentation-migration-planning
description: Generate database migrations and implementation phasing for financial tracking
---

# Migration Planning Skill

## Purpose

Generate database migrations and implementation plans because proper data storage is essential for reliable financial metric calculation and historical analysis.

## When to Use

- Setting up financial event storage
- Adding new tracking tables
- Upgrading existing instrumentation
- Planning phased implementation
- Preparing for data warehouse integration

## What This Skill Provides

Comprehensive migration planning including:
- Database migration scripts
- Table schema designs
- Index optimization
- Implementation phasing
- Effort estimation
- Rollback strategies

## Input Requirements

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| database_type | enum | Yes | postgresql, mysql, mongodb |
| events_to_track | list | Yes | Events from gap analysis |
| existing_schema | object | No | Current database schema info |
| framework | enum | No | For ORM migration generation |

## Database Schema Designs

### Financial Events Table (PostgreSQL)
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
    CONSTRAINT idx_customer_id INDEX (customer_id),
    CONSTRAINT idx_subscription_id INDEX (subscription_id),
    CONSTRAINT idx_event_name INDEX (event_name),
    CONSTRAINT idx_created_at INDEX (created_at)
);

-- GIN index for JSONB queries
CREATE INDEX idx_event_data_gin ON financial_events USING GIN (event_data);

-- Composite index for cohort analysis
CREATE INDEX idx_cohort_analysis ON financial_events (customer_id, event_name, created_at);

COMMENT ON TABLE financial_events IS 'Stores subscription lifecycle events for financial metrics calculation';
```

### AI Usage Events Table (PostgreSQL)
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
    tokens_total INTEGER GENERATED ALWAYS AS (tokens_input + tokens_output) STORED,
    cost_usd DECIMAL(10, 6) NOT NULL,
    latency_ms INTEGER,
    feature VARCHAR(255),
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes
    CONSTRAINT idx_ai_user_id INDEX (user_id),
    CONSTRAINT idx_ai_customer_id INDEX (customer_id),
    CONSTRAINT idx_ai_model INDEX (model),
    CONSTRAINT idx_ai_created_at INDEX (created_at)
);

-- Composite index for cost analysis
CREATE INDEX idx_cost_analysis ON ai_usage_events (customer_id, created_at, cost_usd);

-- Index for provider analysis
CREATE INDEX idx_provider_analysis ON ai_usage_events (provider, model, created_at);

COMMENT ON TABLE ai_usage_events IS 'Tracks AI API usage and costs for ROI calculation';
```

### MySQL Equivalents
```sql
-- Financial Events Table (MySQL)
CREATE TABLE IF NOT EXISTS financial_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) DEFAULT '1.0.0',
    customer_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255),
    event_data JSON NOT NULL,
    mrr_impact DECIMAL(10, 2),
    arr_impact DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_customer_id (customer_id),
    INDEX idx_subscription_id (subscription_id),
    INDEX idx_event_name (event_name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Implementation Phases

### Phase 1: Critical Subscription Tracking (Week 1-2)

**Objectives:**
- Enable MRR/ARR calculation
- Enable churn rate tracking
- Establish event foundation

**Events to Implement:**
- subscription_created
- subscription_cancelled
- subscription_upgraded
- subscription_downgraded

**Database Changes:**
- Create financial_events table
- Create necessary indexes
- Set up event emitter

**Verification:**
- Calculate MRR from events
- Verify event completeness
- Test cohort queries

### Phase 2: AI Cost Tracking (Week 2-3)

**Objectives:**
- Track AI API costs
- Enable AI ROI calculation
- Per-user cost attribution

**Events to Implement:**
- ai_request_completed
- ai_cost_aggregated (daily rollup)

**Database Changes:**
- Create ai_usage_events table
- Create cost analysis indexes
- Set up aggregation jobs

**Verification:**
- Calculate cost per interaction
- Verify provider breakdown
- Test cost queries

### Phase 3: Payment and Revenue (Week 3-4)

**Objectives:**
- Track payment events
- Enable revenue analysis
- Collection efficiency metrics

**Events to Implement:**
- payment_received
- payment_failed
- refund_processed

**Database Changes:**
- Extend financial_events schema
- Add payment-specific indexes

**Verification:**
- Calculate collected revenue
- Verify payment attribution
- Test refund handling

### Phase 4: Advanced Metrics (Week 4-5)

**Objectives:**
- Enable CAC calculation
- Enable NRR analysis
- Complete instrumentation

**Events to Implement:**
- customer_created
- marketing_attribution
- feature_usage

**Database Changes:**
- Attribution tables
- Marketing spend tables

**Verification:**
- Calculate blended CAC
- Verify NRR components
- Full metric test suite

## Output Format

```json
{
  "migration_plan": {
    "database_type": "postgresql",
    "total_phases": 4,
    "estimated_effort_days": 25,
    "migrations": [
      {
        "migration_name": "001_create_financial_events",
        "phase": 1,
        "sql_script": "/* PostgreSQL migration */",
        "rollback_script": "DROP TABLE IF EXISTS financial_events;",
        "estimated_hours": 4
      }
    ],
    "implementation_phases": [
      {
        "phase_number": 1,
        "phase_name": "Critical Subscription Tracking",
        "duration": "1-2 weeks",
        "objectives": ["Enable MRR/ARR calculation"],
        "events_to_implement": ["subscription_created", "subscription_cancelled"],
        "metrics_enabled": ["MRR", "ARR", "Churn Rate"]
      }
    ]
  }
}
```

## Process

1. **Assess Current State:**
   - Review existing schema
   - Identify available tables
   - Check index coverage

2. **Design Target Schema:**
   - Event storage tables
   - Aggregation tables
   - Reporting views

3. **Generate Migrations:**
   - Create table scripts
   - Index creation
   - Data type selection

4. **Plan Implementation Phases:**
   - Group by priority
   - Sequence dependencies
   - Estimate effort

5. **Create Rollback Plans:**
   - Reversible migrations
   - Data preservation
   - Fallback strategies

## Effort Estimation

| Task | Hours | Complexity |
|------|-------|------------|
| Table creation | 2-4 | Low |
| Index design | 2-4 | Medium |
| Event implementation | 4-8 per event | Medium |
| Testing/validation | 4-8 per phase | Medium |
| Documentation | 2-4 | Low |

### Total Effort Calculation
```
Total Days = (Critical Events × 1.5 days) + (High Events × 1 day) + (Medium Events × 0.5 days)
           + (Migrations × 0.5 days) + (Testing × 1.5 days) + (Buffer × 30%)
```

## Index Strategy

### Query Patterns to Optimize

| Query Type | Index Strategy |
|------------|----------------|
| MRR by date | (created_at, mrr_impact) |
| Customer history | (customer_id, created_at) |
| Cohort analysis | (customer_id, event_name, created_at) |
| Event type filter | (event_name, created_at) |
| AI cost by provider | (provider, model, created_at) |
| AI cost by customer | (customer_id, created_at, cost_usd) |

### Index Guidelines
- Index columns used in WHERE clauses
- Composite indexes for multi-column filters
- Partial indexes for common filters
- GIN/JSONB indexes for flexible queries

## Data Retention

### Retention Policies
| Data Type | Hot Storage | Warm Storage | Archive |
|-----------|-------------|--------------|---------|
| Raw events | 90 days | 1 year | 7 years |
| Aggregations | 1 year | 5 years | Forever |
| AI usage | 30 days | 1 year | 3 years |

### Partitioning Strategy
```sql
-- Monthly partitioning for financial_events
CREATE TABLE financial_events (
    id BIGSERIAL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE financial_events_2024_01 PARTITION OF financial_events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## ORM Migration Examples

### Django Migration
```python
# migrations/0001_create_financial_events.py
from django.db import migrations, models
import django.contrib.postgres.fields

class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='FinancialEvent',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('event_name', models.CharField(max_length=255, db_index=True)),
                ('event_version', models.CharField(max_length=50, default='1.0.0')),
                ('customer_id', models.CharField(max_length=255, db_index=True)),
                ('subscription_id', models.CharField(max_length=255, null=True, db_index=True)),
                ('event_data', models.JSONField()),
                ('mrr_impact', models.DecimalField(max_digits=10, decimal_places=2, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'db_table': 'financial_events',
                'indexes': [
                    models.Index(fields=['customer_id', 'event_name', 'created_at'],
                                name='idx_cohort_analysis'),
                ],
            },
        ),
    ]
```

### SQLAlchemy Migration (Alembic)
```python
# alembic/versions/001_create_financial_events.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    op.create_table(
        'financial_events',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('event_name', sa.String(255), nullable=False, index=True),
        sa.Column('customer_id', sa.String(255), nullable=False, index=True),
        sa.Column('event_data', JSONB, nullable=False),
        sa.Column('mrr_impact', sa.Numeric(10, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_cohort_analysis', 'financial_events',
                   ['customer_id', 'event_name', 'created_at'])

def downgrade():
    op.drop_table('financial_events')
```

## No Script

Do the steps of the Process section. Do not look for a script, because no script of this plugin makes this analysis from the inputs above.

## Rollback Procedures

### Safe Rollback Steps
1. Verify no active writes to table
2. Export data if needed for preservation
3. Execute rollback migration
4. Verify application handles missing table
5. Update application to remove references
