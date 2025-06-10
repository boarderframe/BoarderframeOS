-- BoarderframeOS Enhanced Registry Tables
-- Additional tables and enhancements for the comprehensive registry system

-- ==============================================================================
-- LEADER REGISTRY (Enhanced from agent_registry)
-- ==============================================================================

-- Add leader-specific columns to agent_registry
ALTER TABLE agent_registry 
ADD COLUMN IF NOT EXISTS leadership_tier VARCHAR(50),
ADD COLUMN IF NOT EXISTS biblical_archetype VARCHAR(100),
ADD COLUMN IF NOT EXISTS authority_level INTEGER DEFAULT 5 CHECK (authority_level BETWEEN 1 AND 10),
ADD COLUMN IF NOT EXISTS delegation_capacity INTEGER DEFAULT 10,
ADD COLUMN IF NOT EXISTS subordinate_ids JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS departments_managed JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS divisions_managed JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS strategic_initiatives JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS leadership_style VARCHAR(100);

-- ==============================================================================
-- DATABASE REGISTRY
-- ==============================================================================

CREATE TABLE IF NOT EXISTS database_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    db_type VARCHAR(50) NOT NULL CHECK (db_type IN ('postgresql', 'sqlite', 'redis', 'mongodb', 'mysql', 'cassandra')),
    status VARCHAR(50) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'maintenance', 'error', 'degraded')),
    
    -- Connection details
    host VARCHAR(255) DEFAULT 'localhost',
    port INTEGER NOT NULL,
    database_name VARCHAR(255),
    connection_string TEXT,
    ssl_enabled BOOLEAN DEFAULT FALSE,
    
    -- Connection pool settings
    max_connections INTEGER DEFAULT 100,
    current_connections INTEGER DEFAULT 0,
    connection_pool_size INTEGER DEFAULT 10,
    
    -- Performance metrics
    query_performance REAL DEFAULT 0.0, -- avg query time in ms
    cache_hit_rate REAL DEFAULT 0.0 CHECK (cache_hit_rate >= 0.0 AND cache_hit_rate <= 100.0),
    slow_query_count INTEGER DEFAULT 0,
    
    -- Storage metrics
    storage_used_gb REAL DEFAULT 0.0,
    storage_limit_gb REAL,
    table_count INTEGER DEFAULT 0,
    index_count INTEGER DEFAULT 0,
    
    -- Replication and backup
    replication_status VARCHAR(50),
    replication_lag_seconds INTEGER DEFAULT 0,
    backup_status VARCHAR(50),
    last_backup TIMESTAMP WITH TIME ZONE,
    backup_retention_days INTEGER DEFAULT 30,
    
    -- Health monitoring
    health_status VARCHAR(50) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'warning', 'critical', 'unknown')),
    health_score REAL DEFAULT 100.0 CHECK (health_score >= 0.0 AND health_score <= 100.0),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    version VARCHAR(50),
    capabilities JSONB DEFAULT '[]',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_database_host_port UNIQUE (host, port, database_name)
);

-- ==============================================================================
-- ENHANCED SERVER REGISTRY
-- ==============================================================================

-- Add additional columns to server_registry for better categorization
ALTER TABLE server_registry 
ADD COLUMN IF NOT EXISTS server_category VARCHAR(50) CHECK (server_category IN ('core_system', 'mcp_server', 'business_service', 'infrastructure', 'monitoring')),
ADD COLUMN IF NOT EXISTS base_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS api_endpoints JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS rate_limit INTEGER,
ADD COLUMN IF NOT EXISTS rate_limit_window_seconds INTEGER DEFAULT 60,
ADD COLUMN IF NOT EXISTS ssl_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS cors_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS authentication_required BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS authentication_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS total_requests BIGINT DEFAULT 0,
ADD COLUMN IF NOT EXISTS failed_requests BIGINT DEFAULT 0,
ADD COLUMN IF NOT EXISTS average_response_time REAL DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS p95_response_time REAL DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS p99_response_time REAL DEFAULT 0.0;

-- ==============================================================================
-- REGISTRY EVENT LOG
-- ==============================================================================

CREATE TABLE IF NOT EXISTS registry_event_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(255),
    
    -- Event details
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_source VARCHAR(100) DEFAULT 'registry',
    event_data JSONB NOT NULL,
    
    -- Tracking
    correlation_id UUID,
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Status
    processed BOOLEAN DEFAULT FALSE,
    processing_timestamp TIMESTAMP WITH TIME ZONE,
    processing_result JSONB,
    
    -- Indexing for queries
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- REGISTRY SUBSCRIPTIONS
-- ==============================================================================

CREATE TABLE IF NOT EXISTS registry_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_id UUID NOT NULL,
    subscriber_type VARCHAR(50) NOT NULL,
    
    -- Subscription details
    event_types TEXT[] DEFAULT '{}',
    entity_types TEXT[] DEFAULT '{}',
    entity_ids TEXT[] DEFAULT '{}',
    
    -- Delivery settings
    delivery_method VARCHAR(50) DEFAULT 'websocket' CHECK (delivery_method IN ('websocket', 'webhook', 'redis', 'kafka')),
    delivery_endpoint TEXT,
    delivery_config JSONB DEFAULT '{}',
    
    -- Status
    active BOOLEAN DEFAULT TRUE,
    last_delivery TIMESTAMP WITH TIME ZONE,
    delivery_count INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT unique_subscription UNIQUE (subscriber_id, subscriber_type)
);

-- ==============================================================================
-- REGISTRY CACHE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS registry_cache (
    cache_key VARCHAR(500) PRIMARY KEY,
    cache_value JSONB NOT NULL,
    cache_type VARCHAR(50) NOT NULL,
    
    -- TTL management
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    entity_ids TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}'
);

-- ==============================================================================
-- SERVICE DEPENDENCIES
-- ==============================================================================

CREATE TABLE IF NOT EXISTS service_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    depends_on_id UUID NOT NULL,
    depends_on_type VARCHAR(50) NOT NULL,
    
    -- Dependency details
    dependency_type VARCHAR(50) DEFAULT 'required' CHECK (dependency_type IN ('required', 'optional', 'preferred')),
    dependency_strength INTEGER DEFAULT 5 CHECK (dependency_strength BETWEEN 1 AND 10),
    
    -- Health impact
    health_impact_factor REAL DEFAULT 1.0 CHECK (health_impact_factor >= 0.0 AND health_impact_factor <= 1.0),
    cascading_failure BOOLEAN DEFAULT TRUE,
    
    -- Timeouts and retries
    timeout_seconds INTEGER DEFAULT 30,
    retry_attempts INTEGER DEFAULT 3,
    circuit_breaker_threshold INTEGER DEFAULT 5,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    last_check TIMESTAMP WITH TIME ZONE,
    check_result JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_dependency UNIQUE (service_id, depends_on_id),
    CONSTRAINT no_self_dependency CHECK (service_id != depends_on_id)
);

-- ==============================================================================
-- REGISTRY METRICS
-- ==============================================================================

CREATE TABLE IF NOT EXISTS registry_metrics (
    id SERIAL PRIMARY KEY,
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Entity counts
    total_agents INTEGER DEFAULT 0,
    online_agents INTEGER DEFAULT 0,
    total_leaders INTEGER DEFAULT 0,
    total_departments INTEGER DEFAULT 0,
    total_divisions INTEGER DEFAULT 0,
    total_servers INTEGER DEFAULT 0,
    total_databases INTEGER DEFAULT 0,
    
    -- Health metrics
    healthy_entities INTEGER DEFAULT 0,
    warning_entities INTEGER DEFAULT 0,
    critical_entities INTEGER DEFAULT 0,
    average_health_score REAL DEFAULT 0.0,
    
    -- Performance metrics
    total_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    average_response_time REAL DEFAULT 0.0,
    cache_hit_rate REAL DEFAULT 0.0,
    
    -- System metrics
    event_queue_size INTEGER DEFAULT 0,
    websocket_connections INTEGER DEFAULT 0,
    memory_usage_mb REAL DEFAULT 0.0,
    cpu_usage_percent REAL DEFAULT 0.0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- ==============================================================================
-- INDEXES FOR PERFORMANCE
-- ==============================================================================

-- Database Registry Indexes
CREATE INDEX idx_database_registry_type ON database_registry(db_type);
CREATE INDEX idx_database_registry_status ON database_registry(status);
CREATE INDEX idx_database_registry_health ON database_registry(health_status);
CREATE INDEX idx_database_registry_host_port ON database_registry(host, port);

-- Event Log Indexes
CREATE INDEX idx_event_log_entity ON registry_event_log(entity_id, event_timestamp DESC);
CREATE INDEX idx_event_log_type ON registry_event_log(event_type, event_timestamp DESC);
CREATE INDEX idx_event_log_correlation ON registry_event_log(correlation_id);
CREATE INDEX idx_event_log_unprocessed ON registry_event_log(processed) WHERE processed = FALSE;

-- Subscription Indexes
CREATE INDEX idx_subscriptions_subscriber ON registry_subscriptions(subscriber_id, subscriber_type);
CREATE INDEX idx_subscriptions_active ON registry_subscriptions(active) WHERE active = TRUE;

-- Cache Indexes
CREATE INDEX idx_cache_expires ON registry_cache(expires_at);
CREATE INDEX idx_cache_type ON registry_cache(cache_type);

-- Dependency Indexes
CREATE INDEX idx_dependencies_service ON service_dependencies(service_id);
CREATE INDEX idx_dependencies_depends_on ON service_dependencies(depends_on_id);
CREATE INDEX idx_dependencies_status ON service_dependencies(status);

-- Metrics Indexes
CREATE INDEX idx_metrics_timestamp ON registry_metrics(metric_timestamp DESC);

-- ==============================================================================
-- FUNCTIONS AND TRIGGERS
-- ==============================================================================

-- Function to clean expired cache entries
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM registry_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate entity dependencies health impact
CREATE OR REPLACE FUNCTION calculate_dependency_health_impact(entity_id UUID)
RETURNS REAL AS $$
DECLARE
    total_impact REAL := 100.0;
    dep RECORD;
BEGIN
    FOR dep IN 
        SELECT d.*, 
               CASE 
                   WHEN sr.health_score IS NOT NULL THEN sr.health_score
                   WHEN ar.health_score IS NOT NULL THEN ar.health_score
                   WHEN dr.health_score IS NOT NULL THEN dr.health_score
                   ELSE 100.0
               END as dep_health_score
        FROM service_dependencies d
        LEFT JOIN server_registry sr ON d.depends_on_id = sr.id
        LEFT JOIN agent_registry ar ON d.depends_on_id = ar.id
        LEFT JOIN database_registry dr ON d.depends_on_id = dr.id
        WHERE d.service_id = entity_id AND d.status = 'active'
    LOOP
        IF dep.dependency_type = 'required' AND dep.dep_health_score < 50 THEN
            total_impact := total_impact * (dep.dep_health_score / 100.0) * dep.health_impact_factor;
        END IF;
    END LOOP;
    
    RETURN total_impact;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update registry metrics periodically
CREATE OR REPLACE FUNCTION update_registry_metrics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO registry_metrics (
        total_agents, online_agents, total_leaders,
        total_departments, total_divisions, total_servers, total_databases,
        healthy_entities, warning_entities, critical_entities,
        average_health_score
    )
    SELECT 
        COUNT(CASE WHEN agent_type = 'agent' THEN 1 END),
        COUNT(CASE WHEN agent_type = 'agent' AND status = 'online' THEN 1 END),
        COUNT(CASE WHEN agent_type = 'leader' THEN 1 END),
        (SELECT COUNT(*) FROM department_registry),
        (SELECT COUNT(*) FROM divisions WHERE is_active = true),
        (SELECT COUNT(*) FROM server_registry),
        (SELECT COUNT(*) FROM database_registry),
        COUNT(CASE WHEN health_score >= 80 THEN 1 END),
        COUNT(CASE WHEN health_score >= 50 AND health_score < 80 THEN 1 END),
        COUNT(CASE WHEN health_score < 50 THEN 1 END),
        AVG(health_score)
    FROM agent_registry;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_database_registry_timestamp 
    BEFORE UPDATE ON database_registry 
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

CREATE TRIGGER update_registry_subscriptions_timestamp 
    BEFORE UPDATE ON registry_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

-- ==============================================================================
-- VIEWS FOR EASY ACCESS
-- ==============================================================================

-- Comprehensive Entity View
CREATE OR REPLACE VIEW registry_all_entities AS
SELECT 
    id, name, 'agent' as entity_type, status, health_score, last_heartbeat
FROM agent_registry
WHERE agent_type = 'agent'
UNION ALL
SELECT 
    id, name, 'leader' as entity_type, status, health_score, last_heartbeat
FROM agent_registry
WHERE agent_type = 'leader'
UNION ALL
SELECT 
    id, name, 'server' as entity_type, status, health_score, last_heartbeat
FROM server_registry
UNION ALL
SELECT 
    id, name, 'database' as entity_type, status, health_score, last_heartbeat
FROM database_registry
UNION ALL
SELECT 
    department_id as id, name, 'department' as entity_type, 
    status, 100.0 as health_score, updated_at as last_heartbeat
FROM department_registry
UNION ALL
SELECT 
    division_key::uuid as id, division_name as name, 'division' as entity_type,
    CASE WHEN is_active THEN 'online' ELSE 'offline' END as status,
    100.0 as health_score, updated_at as last_heartbeat
FROM divisions;

-- Service Health Overview
CREATE OR REPLACE VIEW service_health_overview AS
SELECT 
    e.id,
    e.name,
    e.entity_type,
    e.status,
    e.health_score,
    COUNT(d.id) as dependency_count,
    MIN(calculate_dependency_health_impact(e.id)) as dependency_health_impact,
    CASE 
        WHEN e.health_score >= 80 AND MIN(calculate_dependency_health_impact(e.id)) >= 80 THEN 'healthy'
        WHEN e.health_score >= 50 OR MIN(calculate_dependency_health_impact(e.id)) >= 50 THEN 'warning'
        ELSE 'critical'
    END as overall_health
FROM registry_all_entities e
LEFT JOIN service_dependencies d ON e.id = d.service_id
GROUP BY e.id, e.name, e.entity_type, e.status, e.health_score;

-- Recent Events View
CREATE OR REPLACE VIEW recent_registry_events AS
SELECT 
    event_type,
    entity_type,
    entity_name,
    event_timestamp,
    event_data->>'old_status' as old_status,
    event_data->>'new_status' as new_status,
    correlation_id
FROM registry_event_log
WHERE event_timestamp > NOW() - INTERVAL '1 hour'
ORDER BY event_timestamp DESC
LIMIT 100;

-- ==============================================================================
-- INITIAL DATA AND PERMISSIONS
-- ==============================================================================

-- Grant permissions to boarderframe user
GRANT ALL ON ALL TABLES IN SCHEMA public TO boarderframe;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO boarderframe;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO boarderframe;

-- Insert initial registry metrics
INSERT INTO system_metrics (service_name, metric_name, metric_value, metadata) VALUES
('enhanced_registry', 'schema_version', 6.0, '{"migration": "006_enhanced_registry_tables", "features": ["leader_registry", "database_registry", "event_log", "subscriptions", "dependencies"]}');

-- Create initial scheduled job for cache cleanup (if pg_cron is available)
-- SELECT cron.schedule('clean-registry-cache', '*/15 * * * *', 'SELECT clean_expired_cache();');

SELECT 'Enhanced Registry Tables created successfully' AS status;