-- Migration: 001_create_financial_events
-- Description: Create table for storing financial lifecycle events
-- Generated: 2026-01-23
-- Product Finance Plugin v1.0.0

-- ============================================================================
-- FINANCIAL EVENTS TABLE
-- ============================================================================
-- Stores all subscription and customer lifecycle events for financial tracking.
-- This table enables calculation of MRR, ARR, Churn, NRR, and other metrics.

BEGIN;

-- Create financial_events table
CREATE TABLE IF NOT EXISTS financial_events (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,

    -- Event identification
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) DEFAULT '1.0.0',

    -- Entity references
    customer_id VARCHAR(255) NOT NULL,
    subscription_id VARCHAR(255),

    -- Event payload (flexible JSON storage)
    event_data JSONB NOT NULL,

    -- Pre-calculated financial impact (for fast aggregation)
    mrr_impact DECIMAL(10, 2),
    arr_impact DECIMAL(10, 2),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Idempotency key for duplicate prevention
    idempotency_key VARCHAR(255) UNIQUE
);

-- Add table comment
COMMENT ON TABLE financial_events IS 'Stores financial lifecycle events for metric calculation';

-- Add column comments
COMMENT ON COLUMN financial_events.event_name IS 'Event type: subscription_created, subscription_cancelled, etc.';
COMMENT ON COLUMN financial_events.event_version IS 'Schema version for backward compatibility';
COMMENT ON COLUMN financial_events.customer_id IS 'Organization/customer identifier';
COMMENT ON COLUMN financial_events.subscription_id IS 'Subscription identifier (nullable for non-subscription events)';
COMMENT ON COLUMN financial_events.event_data IS 'Full event payload as JSONB';
COMMENT ON COLUMN financial_events.mrr_impact IS 'MRR change from this event (positive or negative)';
COMMENT ON COLUMN financial_events.arr_impact IS 'ARR change (MRR * 12)';
COMMENT ON COLUMN financial_events.idempotency_key IS 'Unique key to prevent duplicate event processing';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for customer queries (most common)
CREATE INDEX idx_financial_events_customer_id
    ON financial_events (customer_id);

-- Index for subscription-level queries
CREATE INDEX idx_financial_events_subscription_id
    ON financial_events (subscription_id)
    WHERE subscription_id IS NOT NULL;

-- Index for event type filtering
CREATE INDEX idx_financial_events_event_name
    ON financial_events (event_name);

-- Index for time-based queries (crucial for MRR calculations)
CREATE INDEX idx_financial_events_created_at
    ON financial_events (created_at);

-- Composite index for common query pattern: customer + time range
CREATE INDEX idx_financial_events_customer_time
    ON financial_events (customer_id, created_at);

-- Composite index for event type + time (for aggregations)
CREATE INDEX idx_financial_events_event_time
    ON financial_events (event_name, created_at);

-- GIN index for JSONB queries on event_data
CREATE INDEX idx_financial_events_event_data
    ON financial_events USING GIN (event_data);

-- ============================================================================
-- TRIGGER: Auto-update updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_financial_events_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_financial_events_updated_at
    BEFORE UPDATE ON financial_events
    FOR EACH ROW
    EXECUTE FUNCTION update_financial_events_updated_at();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Current MRR by Customer
CREATE OR REPLACE VIEW v_customer_mrr AS
SELECT
    customer_id,
    SUM(mrr_impact) as current_mrr,
    MAX(created_at) as last_event_at
FROM financial_events
WHERE event_name IN (
    'subscription_created',
    'subscription_upgraded',
    'subscription_downgraded',
    'subscription_cancelled'
)
GROUP BY customer_id;

COMMENT ON VIEW v_customer_mrr IS 'Current MRR per customer calculated from events';

-- View: Monthly MRR Movements
CREATE OR REPLACE VIEW v_monthly_mrr_movements AS
SELECT
    DATE_TRUNC('month', created_at) as month,
    SUM(CASE WHEN event_name = 'subscription_created'
        THEN mrr_impact ELSE 0 END) as new_mrr,
    SUM(CASE WHEN event_name = 'subscription_upgraded'
        THEN mrr_impact ELSE 0 END) as expansion_mrr,
    SUM(CASE WHEN event_name = 'subscription_downgraded'
        THEN ABS(mrr_impact) ELSE 0 END) as contraction_mrr,
    SUM(CASE WHEN event_name = 'subscription_cancelled'
        THEN ABS(mrr_impact) ELSE 0 END) as churned_mrr,
    COUNT(DISTINCT CASE WHEN event_name = 'subscription_created'
        THEN customer_id END) as new_customers,
    COUNT(DISTINCT CASE WHEN event_name = 'subscription_cancelled'
        THEN customer_id END) as churned_customers
FROM financial_events
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;

COMMENT ON VIEW v_monthly_mrr_movements IS 'Monthly MRR movements by category';

-- ============================================================================
-- SAMPLE DATA VALIDATION QUERIES
-- ============================================================================

-- After implementation, run these queries to validate:

-- 1. Check event distribution
-- SELECT event_name, COUNT(*), MIN(created_at), MAX(created_at)
-- FROM financial_events
-- GROUP BY event_name;

-- 2. Verify MRR calculation matches expected
-- SELECT SUM(mrr_impact) as total_mrr
-- FROM financial_events
-- WHERE event_name IN ('subscription_created', 'subscription_upgraded',
--                      'subscription_downgraded', 'subscription_cancelled');

-- 3. Check for missing required fields
-- SELECT event_name, COUNT(*)
-- FROM financial_events
-- WHERE customer_id IS NULL OR event_data IS NULL
-- GROUP BY event_name;

-- 4. Verify idempotency key uniqueness
-- SELECT idempotency_key, COUNT(*)
-- FROM financial_events
-- WHERE idempotency_key IS NOT NULL
-- GROUP BY idempotency_key
-- HAVING COUNT(*) > 1;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (save separately as 001_create_financial_events_rollback.sql)
-- ============================================================================
-- BEGIN;
-- DROP VIEW IF EXISTS v_monthly_mrr_movements;
-- DROP VIEW IF EXISTS v_customer_mrr;
-- DROP TRIGGER IF EXISTS trigger_financial_events_updated_at ON financial_events;
-- DROP FUNCTION IF EXISTS update_financial_events_updated_at();
-- DROP TABLE IF EXISTS financial_events;
-- COMMIT;
