-- Performance optimization queries for MCP Server Management
-- These queries help monitor and optimize database performance

-- ============================================================
-- 1. INDEX ANALYSIS AND MONITORING
-- ============================================================

-- Check index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    CASE WHEN idx_scan = 0 THEN 'UNUSED' 
         WHEN idx_scan < 100 THEN 'LOW_USAGE'
         ELSE 'ACTIVE' END as usage_status
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Find missing indexes for foreign keys
SELECT 
    c.conrelid::regclass as table_name,
    a.attname as column_name,
    c.confrelid::regclass as referenced_table,
    'CREATE INDEX idx_' || c.conrelid::regclass || '_' || a.attname || 
    ' ON ' || c.conrelid::regclass || ' (' || a.attname || ');' as suggested_index
FROM pg_constraint c
JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
WHERE c.contype = 'f'
  AND NOT EXISTS (
    SELECT 1 FROM pg_index i 
    WHERE i.indrelid = c.conrelid 
      AND a.attnum = ANY(i.indkey)
      AND i.indnatts = 1
  );

-- Identify duplicate indexes
WITH index_definitions AS (
    SELECT 
        schemaname,
        tablename,
        indexname,
        array_to_string(array_agg(attname ORDER BY attnum), ',') as column_list
    FROM pg_indexes i
    JOIN pg_attribute a ON a.attrelid = (schemaname||'.'||tablename)::regclass
    JOIN pg_index idx ON idx.indexrelid = (schemaname||'.'||indexname)::regclass
    WHERE a.attnum = ANY(idx.indkey)
    GROUP BY schemaname, tablename, indexname
)
SELECT 
    id1.schemaname,
    id1.tablename,
    id1.indexname as index1,
    id2.indexname as index2,
    id1.column_list
FROM index_definitions id1
JOIN index_definitions id2 ON 
    id1.schemaname = id2.schemaname AND
    id1.tablename = id2.tablename AND
    id1.column_list = id2.column_list AND
    id1.indexname < id2.indexname;

-- ============================================================
-- 2. QUERY PERFORMANCE MONITORING
-- ============================================================

-- Top 10 slowest queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE query LIKE '%mcp_servers%' OR query LIKE '%audit_logs%'
ORDER BY mean_time DESC 
LIMIT 10;

-- Most frequently executed queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE calls > 100
ORDER BY calls DESC 
LIMIT 10;

-- ============================================================
-- 3. TABLE SIZE AND BLOAT ANALYSIS
-- ============================================================

-- Table sizes and row counts
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
    (SELECT reltuples::bigint FROM pg_class WHERE oid = (schemaname||'.'||tablename)::regclass) as row_count
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Estimate table bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    CASE 
        WHEN cc.reltuples = 0 THEN 0
        ELSE (pg_relation_size(schemaname||'.'||tablename) / cc.reltuples)
    END as bytes_per_row,
    cc.reltuples as estimated_rows
FROM pg_tables pt
JOIN pg_class cc ON cc.relname = pt.tablename AND cc.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = pt.schemaname)
WHERE schemaname = 'public'
ORDER BY pg_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================
-- 4. AUDIT LOG PERFORMANCE QUERIES
-- ============================================================

-- Audit log query performance patterns
-- Most common audit actions by time period
SELECT 
    action_type,
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as action_count,
    AVG(duration_ms) as avg_duration_ms
FROM audit_logs 
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY action_type, DATE_TRUNC('hour', created_at)
ORDER BY hour DESC, action_count DESC;

-- Audit log performance by user
SELECT 
    u.username,
    COUNT(al.*) as total_actions,
    AVG(al.duration_ms) as avg_duration_ms,
    COUNT(CASE WHEN al.success = false THEN 1 END) as failed_actions,
    MAX(al.created_at) as last_activity
FROM audit_logs al
JOIN users u ON u.id = al.user_id
WHERE al.created_at >= NOW() - INTERVAL '7 days'
GROUP BY u.id, u.username
ORDER BY total_actions DESC
LIMIT 20;

-- ============================================================
-- 5. MCP SERVER PERFORMANCE QUERIES
-- ============================================================

-- Server performance metrics
SELECT 
    ms.name,
    ms.status,
    ms.cpu_usage,
    ms.memory_usage,
    ms.restart_count,
    ms.error_count,
    EXTRACT(EPOCH FROM (NOW() - ms.last_health_check)) / 60 as minutes_since_health_check,
    EXTRACT(EPOCH FROM (NOW() - ms.last_activity_at)) / 60 as minutes_since_activity
FROM mcp_servers ms
WHERE ms.is_enabled = true
ORDER BY ms.cpu_usage DESC NULLS LAST, ms.memory_usage DESC NULLS LAST;

-- Server health check performance
SELECT 
    ms.name,
    COUNT(al.*) as health_checks,
    AVG(al.duration_ms) as avg_health_check_duration_ms,
    MAX(al.duration_ms) as max_health_check_duration_ms,
    COUNT(CASE WHEN al.success = false THEN 1 END) as failed_health_checks
FROM mcp_servers ms
LEFT JOIN audit_logs al ON al.mcp_server_id = ms.id AND al.action_type = 'SERVER_START'
WHERE al.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY ms.id, ms.name
ORDER BY avg_health_check_duration_ms DESC NULLS LAST;

-- ============================================================
-- 6. OPTIMIZATION RECOMMENDATIONS
-- ============================================================

-- Generate ANALYZE recommendations for stale statistics
SELECT 
    schemaname,
    tablename,
    n_tup_ins + n_tup_upd + n_tup_del as total_modifications,
    last_analyze,
    last_autoanalyze,
    CASE 
        WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN 'NEVER_ANALYZED'
        WHEN (n_tup_ins + n_tup_upd + n_tup_del) > 1000 AND 
             (last_analyze < NOW() - INTERVAL '1 day' OR last_analyze IS NULL) AND
             (last_autoanalyze < NOW() - INTERVAL '1 day' OR last_autoanalyze IS NULL) 
        THEN 'NEEDS_ANALYZE'
        ELSE 'OK'
    END as analyze_status
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY total_modifications DESC;

-- Vacuum recommendations
SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    n_live_tup,
    CASE 
        WHEN n_live_tup > 0 THEN (n_dead_tup::float / n_live_tup::float) * 100
        ELSE 0
    END as dead_tuple_percent,
    last_vacuum,
    last_autovacuum,
    CASE 
        WHEN n_dead_tup > 1000 AND 
             (n_dead_tup::float / NULLIF(n_live_tup::float, 0)) > 0.1
        THEN 'NEEDS_VACUUM'
        ELSE 'OK'
    END as vacuum_status
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY dead_tuple_percent DESC;

-- ============================================================
-- 7. MAINTENANCE QUERIES
-- ============================================================

-- Archive old audit logs (older than 90 days)
-- This should be run as part of a maintenance job
/*
INSERT INTO audit_logs_archive (original_audit_log_id, audit_data, checksum, archive_reason)
SELECT 
    al.id,
    row_to_json(al.*),
    encode(sha256(row_to_json(al.*)::text::bytea), 'hex'),
    'retention_policy'
FROM audit_logs al
WHERE al.created_at < NOW() - INTERVAL '90 days'
  AND NOT EXISTS (
    SELECT 1 FROM audit_logs_archive ala 
    WHERE ala.original_audit_log_id = al.id
  );

DELETE FROM audit_logs 
WHERE created_at < NOW() - INTERVAL '90 days';
*/

-- Cleanup expired user sessions
/*
UPDATE user_sessions 
SET is_active = false, revoked_at = NOW()
WHERE expires_at < NOW() AND is_active = true;
*/

-- Reset rate limit windows that have expired
/*
UPDATE rate_limits 
SET current_count = 0, window_start = NOW()
WHERE (EXTRACT(EPOCH FROM (NOW() - window_start)) > window_size_seconds)
  AND is_active = true;
*/

-- ============================================================
-- 8. SECURITY MONITORING QUERIES
-- ============================================================

-- Recent security events by severity
SELECT 
    severity,
    event_type,
    COUNT(*) as event_count,
    COUNT(CASE WHEN resolved = false THEN 1 END) as unresolved_count,
    MAX(occurred_at) as last_occurrence
FROM security_events 
WHERE occurred_at >= NOW() - INTERVAL '24 hours'
GROUP BY severity, event_type
ORDER BY 
    CASE severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        WHEN 'MEDIUM' THEN 3 
        WHEN 'LOW' THEN 4 
    END,
    event_count DESC;

-- Failed login attempts by IP
SELECT 
    ip_address,
    COUNT(*) as failed_attempts,
    MIN(occurred_at) as first_attempt,
    MAX(occurred_at) as last_attempt,
    COUNT(DISTINCT user_id) as unique_users_targeted
FROM security_events 
WHERE event_type = 'failed_login' 
  AND occurred_at >= NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(*) >= 5
ORDER BY failed_attempts DESC;

-- ============================================================
-- 9. PERFORMANCE BENCHMARKING QUERIES
-- ============================================================

-- Benchmark: User authentication query
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT u.*, ur.name as role_name, ur.permissions
FROM users u
JOIN user_roles ur ON ur.id = u.role_id
WHERE u.username = 'test_user' AND u.is_active = true;

-- Benchmark: MCP server status query
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT ms.*, sp.name as security_policy_name
FROM mcp_servers ms
LEFT JOIN security_policies sp ON sp.id = ms.security_policy_id
WHERE ms.owner_id = 1 AND ms.is_enabled = true
ORDER BY ms.last_activity_at DESC;

-- Benchmark: Audit log search query
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT al.*, u.username
FROM audit_logs al
LEFT JOIN users u ON u.id = al.user_id
WHERE al.created_at >= NOW() - INTERVAL '24 hours'
  AND al.action_type IN ('CREATE', 'UPDATE', 'DELETE')
ORDER BY al.created_at DESC
LIMIT 100;