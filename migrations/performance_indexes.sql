-- Performance Optimization Database Indexes
-- This script creates indexes for improved query performance

-- ================================
-- Pricing Snapshots Indexes
-- ================================

-- Index for provider and region queries
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_provider_region 
ON pricing_snapshots (provider, region);

-- Index for effective date queries
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_effective_date 
ON pricing_snapshots (effective_date DESC);

-- Index for current pricing queries
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_current 
ON pricing_snapshots (is_current) WHERE is_current = true;

-- Composite index for provider, region, and current status
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_provider_region_current 
ON pricing_snapshots (provider, region, is_current) WHERE is_current = true;

-- Index for service type queries
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_service_type 
ON pricing_snapshots (service_type);

-- Composite index for provider, service type, and effective date
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_provider_service_date 
ON pricing_snapshots (provider, service_type, effective_date DESC);

-- ================================
-- Calculation History Indexes
-- ================================

-- Index for session ID queries
CREATE INDEX IF NOT EXISTS idx_calculation_history_session_id 
ON calculation_history (session_id);

-- Index for calculation type queries
CREATE INDEX IF NOT EXISTS idx_calculation_history_type 
ON calculation_history (calculation_type);

-- Index for created_at queries (recent calculations)
CREATE INDEX IF NOT EXISTS idx_calculation_history_created_at 
ON calculation_history (created_at DESC);

-- Composite index for session and type queries
CREATE INDEX IF NOT EXISTS idx_calculation_history_session_type 
ON calculation_history (session_id, calculation_type);

-- Index for IP address queries (analytics)
CREATE INDEX IF NOT EXISTS idx_calculation_history_ip 
ON calculation_history (ip_address);

-- Composite index for type and date (analytics)
CREATE INDEX IF NOT EXISTS idx_calculation_history_type_date 
ON calculation_history (calculation_type, created_at DESC);

-- ================================
-- Cost Optimization Recommendations Indexes
-- ================================

-- Index for calculation history foreign key
CREATE INDEX IF NOT EXISTS idx_cost_optimization_calc_history_id 
ON cost_optimization_recommendations (calculation_history_id);

-- Index for recommendation type queries
CREATE INDEX IF NOT EXISTS idx_cost_optimization_type 
ON cost_optimization_recommendations (recommendation_type);

-- Index for created_at queries
CREATE INDEX IF NOT EXISTS idx_cost_optimization_created_at 
ON cost_optimization_recommendations (created_at DESC);

-- Index for confidence score queries
CREATE INDEX IF NOT EXISTS idx_cost_optimization_confidence 
ON cost_optimization_recommendations (confidence_score DESC);

-- Composite index for type and confidence
CREATE INDEX IF NOT EXISTS idx_cost_optimization_type_confidence 
ON cost_optimization_recommendations (recommendation_type, confidence_score DESC);

-- ================================
-- Price Change Alerts Indexes
-- ================================

-- Index for provider and region queries
CREATE INDEX IF NOT EXISTS idx_price_change_alerts_provider_region 
ON price_change_alerts (provider, region);

-- Index for detected_at queries
CREATE INDEX IF NOT EXISTS idx_price_change_alerts_detected_at 
ON price_change_alerts (detected_at DESC);

-- Index for significant changes
CREATE INDEX IF NOT EXISTS idx_price_change_alerts_significant 
ON price_change_alerts (is_significant) WHERE is_significant = true;

-- Index for service type queries
CREATE INDEX IF NOT EXISTS idx_price_change_alerts_service_type 
ON price_change_alerts (service_type);

-- Composite index for provider, service, and significance
CREATE INDEX IF NOT EXISTS idx_price_change_alerts_provider_service_significant 
ON price_change_alerts (provider, service_type, is_significant);

-- ================================
-- Automation Config Indexes
-- ================================

-- Index for user_id queries
CREATE INDEX IF NOT EXISTS idx_automation_config_user_id 
ON automation_configs (user_id);

-- Index for monitoring enabled queries
CREATE INDEX IF NOT EXISTS idx_automation_config_monitoring_enabled 
ON automation_configs (monitoring_enabled) WHERE monitoring_enabled = true;

-- Index for auto optimization enabled queries
CREATE INDEX IF NOT EXISTS idx_automation_config_auto_optimize_enabled 
ON automation_configs (auto_optimize_enabled) WHERE auto_optimize_enabled = true;

-- Index for updated_at queries
CREATE INDEX IF NOT EXISTS idx_automation_config_updated_at 
ON automation_configs (updated_at DESC);

-- ================================
-- Cost Alerts Indexes
-- ================================

-- Index for user_id queries
CREATE INDEX IF NOT EXISTS idx_cost_alerts_user_id 
ON cost_alerts (user_id);

-- Index for active alerts
CREATE INDEX IF NOT EXISTS idx_cost_alerts_active 
ON cost_alerts (is_active) WHERE is_active = true;

-- Index for alert type queries
CREATE INDEX IF NOT EXISTS idx_cost_alerts_type 
ON cost_alerts (alert_type);

-- Composite index for user and active status
CREATE INDEX IF NOT EXISTS idx_cost_alerts_user_active 
ON cost_alerts (user_id, is_active) WHERE is_active = true;

-- ================================
-- Optimization History Indexes
-- ================================

-- Index for user_id queries
CREATE INDEX IF NOT EXISTS idx_optimization_history_user_id 
ON optimization_history (user_id);

-- Index for recommendation_id queries
CREATE INDEX IF NOT EXISTS idx_optimization_history_recommendation_id 
ON optimization_history (recommendation_id);

-- Index for optimization type queries
CREATE INDEX IF NOT EXISTS idx_optimization_history_type 
ON optimization_history (optimization_type);

-- Index for execution type queries
CREATE INDEX IF NOT EXISTS idx_optimization_history_execution_type 
ON optimization_history (execution_type);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_optimization_history_status 
ON optimization_history (status);

-- Index for executed_at queries
CREATE INDEX IF NOT EXISTS idx_optimization_history_executed_at 
ON optimization_history (executed_at DESC);

-- Composite index for user and type
CREATE INDEX IF NOT EXISTS idx_optimization_history_user_type 
ON optimization_history (user_id, optimization_type);

-- Composite index for user and execution date
CREATE INDEX IF NOT EXISTS idx_optimization_history_user_executed_at 
ON optimization_history (user_id, executed_at DESC);

-- ================================
-- Performance Monitoring Indexes
-- ================================

-- Partial indexes for better performance on filtered queries
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_recent 
ON pricing_snapshots (effective_date DESC, provider, region) 
WHERE effective_date >= NOW() - INTERVAL '7 days';

CREATE INDEX IF NOT EXISTS idx_calculation_history_recent 
ON calculation_history (created_at DESC, calculation_type) 
WHERE created_at >= NOW() - INTERVAL '24 hours';

-- Functional indexes for JSON queries
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_pricing_data_region 
ON pricing_snapshots USING GIN ((pricing_data::jsonb));

CREATE INDEX IF NOT EXISTS idx_calculation_history_configuration 
ON calculation_history USING GIN ((configuration::jsonb));

CREATE INDEX IF NOT EXISTS idx_calculation_history_results 
ON calculation_history USING GIN ((results::jsonb));

-- ================================
-- Maintenance Indexes
-- ================================

-- Index for data cleanup operations
CREATE INDEX IF NOT EXISTS idx_calculation_history_cleanup 
ON calculation_history (created_at) 
WHERE created_at < NOW() - INTERVAL '90 days';

CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_cleanup 
ON pricing_snapshots (created_at, is_current) 
WHERE created_at < NOW() - INTERVAL '30 days' AND is_current = false;

-- ================================
-- Statistics and Analytics Indexes
-- ================================

-- Index for daily statistics
CREATE INDEX IF NOT EXISTS idx_calculation_history_daily_stats 
ON calculation_history (DATE(created_at), calculation_type);

-- Index for monthly statistics
CREATE INDEX IF NOT EXISTS idx_calculation_history_monthly_stats 
ON calculation_history (DATE_TRUNC('month', created_at), calculation_type);

-- Index for provider statistics
CREATE INDEX IF NOT EXISTS idx_pricing_snapshots_provider_stats 
ON pricing_snapshots (provider, DATE(created_at));

-- ================================
-- Foreign Key Indexes
-- ================================

-- Ensure foreign key relationships are indexed for performance
CREATE INDEX IF NOT EXISTS idx_cost_optimization_recommendations_fk 
ON cost_optimization_recommendations (calculation_history_id);

-- ================================
-- Full-Text Search Indexes
-- ================================

-- Full-text search on recommendation reasoning
CREATE INDEX IF NOT EXISTS idx_cost_optimization_reasoning_fts 
ON cost_optimization_recommendations USING gin(to_tsvector('english', reasoning));

-- ================================
-- Performance Monitoring Queries
-- ================================

-- View for index usage statistics
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- View for table statistics
CREATE OR REPLACE VIEW table_stats AS
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- View for slow queries (requires pg_stat_statements extension)
CREATE OR REPLACE VIEW slow_queries AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
WHERE mean_time > 100  -- queries taking more than 100ms on average
ORDER BY mean_time DESC;

-- ================================
-- Performance Optimization Functions
-- ================================

-- Function to get table size information
CREATE OR REPLACE FUNCTION get_table_sizes()
RETURNS TABLE(
    schema_name TEXT,
    table_name TEXT,
    table_size TEXT,
    index_size TEXT,
    total_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname::TEXT,
        tablename::TEXT,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))::TEXT as table_size,
        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename))::TEXT as index_size,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) + pg_indexes_size(schemaname||'.'||tablename))::TEXT as total_size
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to analyze query performance
CREATE OR REPLACE FUNCTION analyze_query_performance(query_text TEXT)
RETURNS TABLE(
    plan_line TEXT
) AS $$
BEGIN
    RETURN QUERY
    EXECUTE 'EXPLAIN ANALYZE ' || query_text;
END;
$$ LANGUAGE plpgsql;

-- ================================
-- Maintenance Scripts
-- ================================

-- Function to update table statistics
CREATE OR REPLACE FUNCTION update_table_statistics()
RETURNS VOID AS $$
DECLARE
    table_record RECORD;
BEGIN
    FOR table_record IN 
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'ANALYZE ' || table_record.schemaname || '.' || table_record.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to reindex tables
CREATE OR REPLACE FUNCTION reindex_tables()
RETURNS VOID AS $$
DECLARE
    table_record RECORD;
BEGIN
    FOR table_record IN 
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'REINDEX TABLE ' || table_record.schemaname || '.' || table_record.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ================================
-- Performance Monitoring Triggers
-- ================================

-- Function to log slow queries
CREATE OR REPLACE FUNCTION log_slow_query()
RETURNS TRIGGER AS $$
BEGIN
    -- This would be implemented based on specific requirements
    -- For now, it's a placeholder
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ================================
-- Optimization Recommendations
-- ================================

-- Function to get optimization recommendations
CREATE OR REPLACE FUNCTION get_optimization_recommendations()
RETURNS TABLE(
    table_name TEXT,
    recommendation TEXT,
    priority TEXT,
    estimated_impact TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'pricing_snapshots'::TEXT,
        'Consider partitioning by effective_date for better performance'::TEXT,
        'high'::TEXT,
        'Significant improvement for time-based queries'::TEXT
    UNION ALL
    SELECT 
        'calculation_history'::TEXT,
        'Archive old calculations to reduce table size'::TEXT,
        'medium'::TEXT,
        'Moderate improvement for recent data queries'::TEXT
    UNION ALL
    SELECT 
        'all_tables'::TEXT,
        'Run VACUUM and ANALYZE regularly'::TEXT,
        'high'::TEXT,
        'Maintains optimal query performance'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ================================
-- Comments for Documentation
-- ================================

COMMENT ON INDEX idx_pricing_snapshots_provider_region IS 'Optimizes queries filtering by provider and region';
COMMENT ON INDEX idx_calculation_history_session_id IS 'Optimizes queries for user session data';
COMMENT ON INDEX idx_cost_optimization_type IS 'Optimizes queries for recommendation types';
COMMENT ON VIEW index_usage_stats IS 'Monitors index usage for optimization decisions';
COMMENT ON FUNCTION get_table_sizes() IS 'Returns table and index sizes for monitoring';
COMMENT ON FUNCTION update_table_statistics() IS 'Updates table statistics for query optimization';

-- ================================
-- Performance Monitoring Setup
-- ================================

-- Enable query statistics collection (requires restart)
-- Add to postgresql.conf:
-- shared_preload_libraries = 'pg_stat_statements'
-- pg_stat_statements.max = 10000
-- pg_stat_statements.track = all
-- track_activity_query_size = 2048

-- Create the extension if it doesn't exist
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Performance monitoring complete
SELECT 'Performance indexes and monitoring setup completed successfully.' AS status;