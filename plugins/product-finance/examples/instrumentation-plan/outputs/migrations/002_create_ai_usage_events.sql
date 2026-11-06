-- Migration: 002_create_ai_usage_events
-- Description: Create table for storing AI usage and cost events
-- Generated: 2026-01-23
-- Product Finance Plugin v1.0.0

-- ============================================================================
-- AI USAGE EVENTS TABLE
-- ============================================================================
-- Stores all AI API usage events for cost tracking and ROI calculation.
-- This table enables calculation of AI Cost per Request, AI Cost per User,
-- AI ROI, and other AI economics metrics.

BEGIN;

-- Create ai_usage_events table
CREATE TABLE IF NOT EXISTS ai_usage_events (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,

    -- Event identification
    event_name VARCHAR(255) NOT NULL,
    event_version VARCHAR(50) DEFAULT '1.0.0',

    -- User/Customer attribution
    user_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,

    -- Request identification
    request_id VARCHAR(255) NOT NULL,

    -- AI Model details
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,

    -- Token usage
    tokens_input INTEGER NOT NULL DEFAULT 0,
    tokens_output INTEGER NOT NULL DEFAULT 0,
    tokens_total INTEGER NOT NULL DEFAULT 0,

    -- Cost (6 decimal places for precision)
    cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0,

    -- Performance
    latency_ms INTEGER,

    -- Feature attribution
    feature VARCHAR(255),

    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_code VARCHAR(100),

    -- Cache tracking
    cache_hit BOOLEAN DEFAULT FALSE,

    -- Flexible metadata
    event_data JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT ai_usage_tokens_check CHECK (tokens_total = tokens_input + tokens_output),
    CONSTRAINT ai_usage_cost_check CHECK (cost_usd >= 0)
);

-- Add table comment
COMMENT ON TABLE ai_usage_events IS 'Stores AI API usage events for cost tracking and ROI calculation';

-- Add column comments
COMMENT ON COLUMN ai_usage_events.event_name IS 'Event type: ai_request_completed, ai_cost_incurred, ai_feature_used';
COMMENT ON COLUMN ai_usage_events.user_id IS 'User who initiated the AI request';
COMMENT ON COLUMN ai_usage_events.customer_id IS 'Organization for cost attribution';
COMMENT ON COLUMN ai_usage_events.request_id IS 'Unique request ID for correlation';
COMMENT ON COLUMN ai_usage_events.model IS 'AI model used (gpt-4, claude-sonnet-4, etc.)';
COMMENT ON COLUMN ai_usage_events.provider IS 'AI provider (openai, anthropic)';
COMMENT ON COLUMN ai_usage_events.tokens_input IS 'Input/prompt tokens';
COMMENT ON COLUMN ai_usage_events.tokens_output IS 'Output/completion tokens';
COMMENT ON COLUMN ai_usage_events.tokens_total IS 'Total tokens (input + output)';
COMMENT ON COLUMN ai_usage_events.cost_usd IS 'Cost in USD with 6 decimal precision';
COMMENT ON COLUMN ai_usage_events.latency_ms IS 'Request latency in milliseconds';
COMMENT ON COLUMN ai_usage_events.feature IS 'Product feature that triggered request';
COMMENT ON COLUMN ai_usage_events.cache_hit IS 'Whether response was served from cache';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for customer queries (for billing/attribution)
CREATE INDEX idx_ai_usage_events_customer_id
    ON ai_usage_events (customer_id);

-- Index for user queries (for per-user limits)
CREATE INDEX idx_ai_usage_events_user_id
    ON ai_usage_events (user_id);

-- Index for model analysis
CREATE INDEX idx_ai_usage_events_model
    ON ai_usage_events (model);

-- Index for provider analysis
CREATE INDEX idx_ai_usage_events_provider
    ON ai_usage_events (provider);

-- Index for time-based queries (crucial for cost aggregations)
CREATE INDEX idx_ai_usage_events_created_at
    ON ai_usage_events (created_at);

-- Index for feature attribution
CREATE INDEX idx_ai_usage_events_feature
    ON ai_usage_events (feature)
    WHERE feature IS NOT NULL;

-- Composite index for common query: customer + time
CREATE INDEX idx_ai_usage_events_customer_time
    ON ai_usage_events (customer_id, created_at);

-- Composite index for model + time (for cost by model over time)
CREATE INDEX idx_ai_usage_events_model_time
    ON ai_usage_events (model, created_at);

-- Index for request correlation
CREATE INDEX idx_ai_usage_events_request_id
    ON ai_usage_events (request_id);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Daily AI Costs by Customer
CREATE OR REPLACE VIEW v_daily_ai_costs_by_customer AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    customer_id,
    SUM(cost_usd) as total_cost,
    COUNT(*) as request_count,
    SUM(tokens_total) as total_tokens,
    AVG(latency_ms) as avg_latency_ms
FROM ai_usage_events
WHERE event_name = 'ai_cost_incurred'
GROUP BY DATE_TRUNC('day', created_at), customer_id;

COMMENT ON VIEW v_daily_ai_costs_by_customer IS 'Daily AI costs aggregated by customer';

-- View: AI Costs by Model
CREATE OR REPLACE VIEW v_ai_costs_by_model AS
SELECT
    model,
    provider,
    COUNT(*) as request_count,
    SUM(cost_usd) as total_cost,
    AVG(cost_usd) as avg_cost_per_request,
    SUM(tokens_total) as total_tokens,
    AVG(latency_ms) as avg_latency_ms
FROM ai_usage_events
WHERE event_name IN ('ai_request_completed', 'ai_cost_incurred')
GROUP BY model, provider;

COMMENT ON VIEW v_ai_costs_by_model IS 'AI cost summary by model';

-- View: AI Feature Usage
CREATE OR REPLACE VIEW v_ai_feature_usage AS
SELECT
    feature,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(*) as total_requests,
    SUM(cost_usd) as total_cost,
    AVG(latency_ms) as avg_latency_ms
FROM ai_usage_events
WHERE feature IS NOT NULL
GROUP BY feature;

COMMENT ON VIEW v_ai_feature_usage IS 'AI usage aggregated by feature';

-- View: Monthly AI Economics
CREATE OR REPLACE VIEW v_monthly_ai_economics AS
SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(DISTINCT customer_id) as ai_customers,
    COUNT(DISTINCT user_id) as ai_users,
    COUNT(*) as total_requests,
    SUM(cost_usd) as total_cost,
    AVG(cost_usd) as avg_cost_per_request,
    SUM(cost_usd) / NULLIF(COUNT(DISTINCT user_id), 0) as cost_per_user,
    SUM(tokens_total) as total_tokens,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float /
        NULLIF(COUNT(*), 0) * 100 as cache_hit_rate_pct
FROM ai_usage_events
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;

COMMENT ON VIEW v_monthly_ai_economics IS 'Monthly AI economics summary';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Calculate cost for a given model and tokens
CREATE OR REPLACE FUNCTION calculate_ai_cost(
    p_model VARCHAR,
    p_tokens_input INTEGER,
    p_tokens_output INTEGER
) RETURNS DECIMAL(10, 6) AS $$
DECLARE
    v_input_cost_per_1k DECIMAL(10, 6);
    v_output_cost_per_1k DECIMAL(10, 6);
    v_total_cost DECIMAL(10, 6);
BEGIN
    -- Model pricing (update as prices change)
    CASE p_model
        WHEN 'gpt-4' THEN
            v_input_cost_per_1k := 0.03;
            v_output_cost_per_1k := 0.06;
        WHEN 'gpt-4-turbo' THEN
            v_input_cost_per_1k := 0.01;
            v_output_cost_per_1k := 0.03;
        WHEN 'gpt-3.5-turbo' THEN
            v_input_cost_per_1k := 0.0005;
            v_output_cost_per_1k := 0.0015;
        WHEN 'claude-opus-4' THEN
            v_input_cost_per_1k := 0.015;
            v_output_cost_per_1k := 0.075;
        WHEN 'claude-sonnet-4' THEN
            v_input_cost_per_1k := 0.003;
            v_output_cost_per_1k := 0.015;
        WHEN 'claude-haiku' THEN
            v_input_cost_per_1k := 0.00025;
            v_output_cost_per_1k := 0.00125;
        ELSE
            -- Default pricing for unknown models
            v_input_cost_per_1k := 0.01;
            v_output_cost_per_1k := 0.03;
    END CASE;

    v_total_cost := (p_tokens_input::DECIMAL / 1000 * v_input_cost_per_1k) +
                    (p_tokens_output::DECIMAL / 1000 * v_output_cost_per_1k);

    RETURN v_total_cost;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_ai_cost IS 'Calculate AI cost based on model and token usage';

-- ============================================================================
-- SAMPLE QUERIES FOR VALIDATION
-- ============================================================================

-- After implementation, run these queries to validate:

-- 1. Check AI cost distribution by provider
-- SELECT provider, model, COUNT(*), SUM(cost_usd), AVG(cost_usd)
-- FROM ai_usage_events
-- GROUP BY provider, model;

-- 2. Calculate AI cost per user per month
-- SELECT
--     DATE_TRUNC('month', created_at) as month,
--     customer_id,
--     COUNT(DISTINCT user_id) as users,
--     SUM(cost_usd) as total_cost,
--     SUM(cost_usd) / COUNT(DISTINCT user_id) as cost_per_user
-- FROM ai_usage_events
-- GROUP BY DATE_TRUNC('month', created_at), customer_id;

-- 3. Check cache effectiveness
-- SELECT
--     DATE_TRUNC('day', created_at) as date,
--     COUNT(*) FILTER (WHERE cache_hit) as cache_hits,
--     COUNT(*) as total_requests,
--     COUNT(*) FILTER (WHERE cache_hit)::float / COUNT(*) * 100 as cache_hit_rate
-- FROM ai_usage_events
-- GROUP BY DATE_TRUNC('day', created_at);

-- 4. Identify high-cost users
-- SELECT user_id, customer_id, SUM(cost_usd), COUNT(*)
-- FROM ai_usage_events
-- WHERE created_at > NOW() - INTERVAL '30 days'
-- GROUP BY user_id, customer_id
-- ORDER BY SUM(cost_usd) DESC
-- LIMIT 20;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (save separately as 002_create_ai_usage_events_rollback.sql)
-- ============================================================================
-- BEGIN;
-- DROP VIEW IF EXISTS v_monthly_ai_economics;
-- DROP VIEW IF EXISTS v_ai_feature_usage;
-- DROP VIEW IF EXISTS v_ai_costs_by_model;
-- DROP VIEW IF EXISTS v_daily_ai_costs_by_customer;
-- DROP FUNCTION IF EXISTS calculate_ai_cost(VARCHAR, INTEGER, INTEGER);
-- DROP TABLE IF EXISTS ai_usage_events;
-- COMMIT;
