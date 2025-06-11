-- BoarderframeOS Registry Schema
-- Adds registry tables for agents, servers, departments, tools, and workflows

-- ==============================================================================
-- AGENT REGISTRY
-- ==============================================================================

-- Enhanced agent registry with capabilities and health monitoring
CREATE TABLE agent_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    department_id UUID REFERENCES departments(id),
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'busy', 'error', 'maintenance')),

    -- Capabilities and endpoints
    capabilities JSONB DEFAULT '[]',
    supported_tools JSONB DEFAULT '[]',
    communication_endpoints JSONB DEFAULT '{}',
    api_endpoints JSONB DEFAULT '{}',

    -- Health and monitoring
    health_check_url VARCHAR(500),
    health_status VARCHAR(50) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'unhealthy', 'degraded', 'unknown')),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    last_health_check TIMESTAMP WITH TIME ZONE,
    response_time_ms INTEGER DEFAULT 0,

    -- Resource information
    resource_requirements JSONB DEFAULT '{}',
    current_load REAL DEFAULT 0.0 CHECK (current_load >= 0.0 AND current_load <= 100.0),
    max_concurrent_tasks INTEGER DEFAULT 1,
    current_tasks INTEGER DEFAULT 0,

    -- Metadata
    version VARCHAR(50),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_agent_registry UNIQUE (agent_id),
    CONSTRAINT valid_current_tasks CHECK (current_tasks <= max_concurrent_tasks)
);

-- ==============================================================================
-- SERVER REGISTRY
-- ==============================================================================

-- Server registry for MCP servers, APIs, and internal services
CREATE TABLE server_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    server_type VARCHAR(100) NOT NULL CHECK (server_type IN ('mcp', 'api', 'internal', 'external', 'database', 'cache')),
    status VARCHAR(50) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'starting', 'stopping', 'error', 'maintenance')),

    -- Connection information
    endpoint_url VARCHAR(500) NOT NULL,
    internal_url VARCHAR(500),
    health_check_url VARCHAR(500),
    authentication JSONB DEFAULT '{}',

    -- Capabilities
    capabilities JSONB DEFAULT '[]',
    supported_protocols JSONB DEFAULT '[]',
    api_version VARCHAR(50),

    -- Health and performance
    health_status VARCHAR(50) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'unhealthy', 'degraded', 'unknown')),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    last_health_check TIMESTAMP WITH TIME ZONE,
    response_time_ms INTEGER DEFAULT 0,
    uptime_seconds INTEGER DEFAULT 0,

    -- Load and performance metrics
    current_connections INTEGER DEFAULT 0,
    max_connections INTEGER DEFAULT 100,
    requests_per_minute INTEGER DEFAULT 0,
    error_rate REAL DEFAULT 0.0 CHECK (error_rate >= 0.0 AND error_rate <= 100.0),
    cpu_usage REAL DEFAULT 0.0 CHECK (cpu_usage >= 0.0 AND cpu_usage <= 100.0),
    memory_usage REAL DEFAULT 0.0 CHECK (memory_usage >= 0.0 AND memory_usage <= 100.0),

    -- Configuration
    configuration JSONB DEFAULT '{}',
    environment VARCHAR(50) DEFAULT 'development',
    deployment_info JSONB DEFAULT '{}',

    -- Metadata
    version VARCHAR(50),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_server_name UNIQUE (name),
    CONSTRAINT valid_connections CHECK (current_connections <= max_connections)
);

-- ==============================================================================
-- DEPARTMENT REGISTRY
-- ==============================================================================

-- Department registry with enhanced hierarchy and team management
CREATE TABLE department_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phase INTEGER NOT NULL CHECK (phase BETWEEN 1 AND 7),
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 7),
    category VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'planning' CHECK (status IN ('planning', 'active', 'scaling', 'optimizing', 'maintenance', 'deprecated')),

    -- Leadership and structure
    leaders JSONB DEFAULT '[]',
    team_structure JSONB DEFAULT '{}',
    reporting_hierarchy JSONB DEFAULT '{}',

    -- Capabilities and resources
    capabilities JSONB DEFAULT '[]',
    available_tools JSONB DEFAULT '[]',
    resource_allocation JSONB DEFAULT '{}',
    budget_allocation JSONB DEFAULT '{}',

    -- Performance metrics
    agent_count INTEGER DEFAULT 0,
    active_agents INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    average_task_completion_time INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0 CHECK (success_rate >= 0.0 AND success_rate <= 100.0),

    -- Configuration
    workflows JSONB DEFAULT '[]',
    policies JSONB DEFAULT '{}',
    escalation_rules JSONB DEFAULT '{}',

    -- Metadata
    description TEXT,
    objectives JSONB DEFAULT '[]',
    kpis JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_department_registry UNIQUE (department_id)
);

-- ==============================================================================
-- TOOL REGISTRY
-- ==============================================================================

-- Tool registry for tracking available tools and capabilities
CREATE TABLE tool_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    tool_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'available' CHECK (status IN ('available', 'unavailable', 'deprecated', 'beta', 'maintenance')),

    -- Tool information
    description TEXT,
    version VARCHAR(50),
    provider VARCHAR(255),
    server_id UUID REFERENCES server_registry(id) ON DELETE SET NULL,

    -- Capabilities and requirements
    capabilities JSONB DEFAULT '{}',
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    requirements JSONB DEFAULT '{}',

    -- Access control
    permissions JSONB DEFAULT '{}',
    access_level VARCHAR(50) DEFAULT 'public' CHECK (access_level IN ('public', 'restricted', 'private', 'admin')),
    allowed_agents UUID[] DEFAULT '{}',
    allowed_departments UUID[] DEFAULT '{}',

    -- Usage metrics
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    average_execution_time INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,

    -- Performance metrics
    reliability_score REAL DEFAULT 0.0 CHECK (reliability_score >= 0.0 AND reliability_score <= 100.0),
    performance_score REAL DEFAULT 0.0 CHECK (performance_score >= 0.0 AND performance_score <= 100.0),
    user_rating REAL DEFAULT 0.0 CHECK (user_rating >= 0.0 AND user_rating <= 5.0),

    -- Configuration
    configuration JSONB DEFAULT '{}',
    limits JSONB DEFAULT '{}',

    -- Metadata
    documentation_url VARCHAR(500),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_tool_name_version UNIQUE (name, version)
);

-- ==============================================================================
-- WORKFLOW REGISTRY
-- ==============================================================================

-- Workflow registry for LangGraph and CrewAI workflow management
CREATE TABLE workflow_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    workflow_type VARCHAR(100) NOT NULL CHECK (workflow_type IN ('langgraph', 'crewai', 'sequential', 'parallel', 'conditional')),
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'deprecated', 'testing')),

    -- Workflow definition
    definition JSONB NOT NULL,
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',

    -- Ownership and access
    created_by UUID REFERENCES agents(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    visibility VARCHAR(50) DEFAULT 'department' CHECK (visibility IN ('public', 'department', 'private')),

    -- Version management
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    parent_workflow_id UUID REFERENCES workflow_registry(id) ON DELETE SET NULL,
    is_template BOOLEAN DEFAULT FALSE,

    -- Execution information
    required_agents JSONB DEFAULT '[]',
    required_tools JSONB DEFAULT '[]',
    required_permissions JSONB DEFAULT '[]',
    estimated_duration INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 3600,

    -- Performance metrics
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    average_duration INTEGER DEFAULT 0,
    last_executed TIMESTAMP WITH TIME ZONE,

    -- Configuration
    configuration JSONB DEFAULT '{}',
    environment_requirements JSONB DEFAULT '{}',

    -- Metadata
    description TEXT,
    documentation TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_workflow_name_version UNIQUE (name, version)
);

-- ==============================================================================
-- RESOURCE REGISTRY
-- ==============================================================================

-- Resource registry for compute and infrastructure resources
CREATE TABLE resource_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL CHECK (resource_type IN ('compute', 'memory', 'storage', 'network', 'gpu', 'api_quota')),
    status VARCHAR(50) DEFAULT 'available' CHECK (status IN ('available', 'allocated', 'reserved', 'maintenance', 'unavailable')),

    -- Resource specifications
    total_capacity REAL NOT NULL CHECK (total_capacity > 0),
    allocated_capacity REAL DEFAULT 0.0 CHECK (allocated_capacity >= 0),
    reserved_capacity REAL DEFAULT 0.0 CHECK (reserved_capacity >= 0),
    unit VARCHAR(50) NOT NULL,

    -- Location and access
    location VARCHAR(255),
    endpoint VARCHAR(500),
    access_credentials JSONB DEFAULT '{}',

    -- Allocation tracking
    current_allocations JSONB DEFAULT '[]',
    allocation_history JSONB DEFAULT '[]',

    -- Performance metrics
    utilization_percentage REAL DEFAULT 0.0 CHECK (utilization_percentage >= 0.0 AND utilization_percentage <= 100.0),
    performance_score REAL DEFAULT 0.0 CHECK (performance_score >= 0.0 AND performance_score <= 100.0),

    -- Configuration
    configuration JSONB DEFAULT '{}',
    policies JSONB DEFAULT '{}',

    -- Metadata
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_resource_name UNIQUE (name),
    CONSTRAINT valid_capacity CHECK (allocated_capacity + reserved_capacity <= total_capacity)
);

-- ==============================================================================
-- CONFIGURATION REGISTRY
-- ==============================================================================

-- Configuration registry for centralized configuration and feature flags
CREATE TABLE configuration_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL,
    config_type VARCHAR(100) NOT NULL CHECK (config_type IN ('feature_flag', 'setting', 'secret', 'environment', 'policy')),
    scope VARCHAR(100) NOT NULL CHECK (scope IN ('global', 'department', 'agent', 'workflow', 'tool')),
    scope_id UUID,

    -- Configuration data
    value JSONB NOT NULL,
    default_value JSONB,
    data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('string', 'number', 'boolean', 'object', 'array')),

    -- Access control
    access_level VARCHAR(50) DEFAULT 'public' CHECK (access_level IN ('public', 'restricted', 'private', 'admin')),
    permissions JSONB DEFAULT '{}',

    -- Validation
    validation_schema JSONB DEFAULT '{}',
    constraints JSONB DEFAULT '{}',

    -- Lifecycle
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated', 'testing')),
    effective_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effective_until TIMESTAMP WITH TIME ZONE,

    -- Metadata
    description TEXT,
    documentation TEXT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',

    -- Audit
    created_by UUID REFERENCES agents(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES agents(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_config_key_scope UNIQUE (key, scope, scope_id)
);

-- ==============================================================================
-- REGISTRY INDEXES FOR PERFORMANCE
-- ==============================================================================

-- Agent Registry Indexes
CREATE INDEX idx_agent_registry_agent_id ON agent_registry(agent_id);
CREATE INDEX idx_agent_registry_department ON agent_registry(department_id);
CREATE INDEX idx_agent_registry_status ON agent_registry(status);
CREATE INDEX idx_agent_registry_health ON agent_registry(health_status);
CREATE INDEX idx_agent_registry_heartbeat ON agent_registry(last_heartbeat DESC);
CREATE INDEX idx_agent_registry_capabilities ON agent_registry USING GIN(capabilities);
CREATE INDEX idx_agent_registry_tags ON agent_registry USING GIN(tags);

-- Server Registry Indexes
CREATE INDEX idx_server_registry_name ON server_registry(name);
CREATE INDEX idx_server_registry_type ON server_registry(server_type);
CREATE INDEX idx_server_registry_status ON server_registry(status);
CREATE INDEX idx_server_registry_health ON server_registry(health_status);
CREATE INDEX idx_server_registry_heartbeat ON server_registry(last_heartbeat DESC);
CREATE INDEX idx_server_registry_capabilities ON server_registry USING GIN(capabilities);
CREATE INDEX idx_server_registry_environment ON server_registry(environment);

-- Department Registry Indexes
CREATE INDEX idx_department_registry_dept_id ON department_registry(department_id);
CREATE INDEX idx_department_registry_phase ON department_registry(phase);
CREATE INDEX idx_department_registry_priority ON department_registry(priority);
CREATE INDEX idx_department_registry_status ON department_registry(status);
CREATE INDEX idx_department_registry_capabilities ON department_registry USING GIN(capabilities);

-- Tool Registry Indexes
CREATE INDEX idx_tool_registry_name ON tool_registry(name);
CREATE INDEX idx_tool_registry_type ON tool_registry(tool_type);
CREATE INDEX idx_tool_registry_status ON tool_registry(status);
CREATE INDEX idx_tool_registry_server ON tool_registry(server_id);
CREATE INDEX idx_tool_registry_access_level ON tool_registry(access_level);
CREATE INDEX idx_tool_registry_usage ON tool_registry(usage_count DESC);
CREATE INDEX idx_tool_registry_capabilities ON tool_registry USING GIN(capabilities);

-- Workflow Registry Indexes
CREATE INDEX idx_workflow_registry_name ON workflow_registry(name);
CREATE INDEX idx_workflow_registry_type ON workflow_registry(workflow_type);
CREATE INDEX idx_workflow_registry_status ON workflow_registry(status);
CREATE INDEX idx_workflow_registry_department ON workflow_registry(department_id);
CREATE INDEX idx_workflow_registry_created_by ON workflow_registry(created_by);
CREATE INDEX idx_workflow_registry_template ON workflow_registry(is_template);

-- Resource Registry Indexes
CREATE INDEX idx_resource_registry_name ON resource_registry(name);
CREATE INDEX idx_resource_registry_type ON resource_registry(resource_type);
CREATE INDEX idx_resource_registry_status ON resource_registry(status);
CREATE INDEX idx_resource_registry_utilization ON resource_registry(utilization_percentage);

-- Configuration Registry Indexes
CREATE INDEX idx_config_registry_key ON configuration_registry(key);
CREATE INDEX idx_config_registry_type ON configuration_registry(config_type);
CREATE INDEX idx_config_registry_scope ON configuration_registry(scope, scope_id);
CREATE INDEX idx_config_registry_status ON configuration_registry(status);
CREATE INDEX idx_config_registry_effective ON configuration_registry(effective_from, effective_until);

-- ==============================================================================
-- TRIGGERS AND FUNCTIONS FOR REGISTRY MANAGEMENT
-- ==============================================================================

-- Function to update registry timestamps
CREATE OR REPLACE FUNCTION update_registry_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_agent_registry_timestamp
    BEFORE UPDATE ON agent_registry
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

CREATE TRIGGER update_server_registry_timestamp
    BEFORE UPDATE ON server_registry
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

CREATE TRIGGER update_department_registry_timestamp
    BEFORE UPDATE ON department_registry
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

CREATE TRIGGER update_tool_registry_timestamp
    BEFORE UPDATE ON tool_registry
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

CREATE TRIGGER update_workflow_registry_timestamp
    BEFORE UPDATE ON workflow_registry
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

CREATE TRIGGER update_resource_registry_timestamp
    BEFORE UPDATE ON resource_registry
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

CREATE TRIGGER update_config_registry_timestamp
    BEFORE UPDATE ON configuration_registry
    FOR EACH ROW EXECUTE FUNCTION update_registry_timestamp();

-- Function for registry health scoring
CREATE OR REPLACE FUNCTION calculate_agent_health_score(agent_reg_id UUID)
RETURNS REAL AS $$
DECLARE
    health_score REAL := 0.0;
    heartbeat_score REAL := 0.0;
    response_score REAL := 0.0;
    load_score REAL := 0.0;
    agent_data RECORD;
BEGIN
    SELECT * INTO agent_data FROM agent_registry WHERE id = agent_reg_id;

    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;

    -- Heartbeat score (40% weight)
    IF agent_data.last_heartbeat > NOW() - INTERVAL '1 minute' THEN
        heartbeat_score := 40.0;
    ELSIF agent_data.last_heartbeat > NOW() - INTERVAL '5 minutes' THEN
        heartbeat_score := 20.0;
    END IF;

    -- Response time score (30% weight)
    IF agent_data.response_time_ms < 1000 THEN
        response_score := 30.0;
    ELSIF agent_data.response_time_ms < 5000 THEN
        response_score := 15.0;
    END IF;

    -- Load score (30% weight)
    IF agent_data.current_load < 50.0 THEN
        load_score := 30.0;
    ELSIF agent_data.current_load < 80.0 THEN
        load_score := 15.0;
    END IF;

    health_score := heartbeat_score + response_score + load_score;

    RETURN health_score;
END;
$$ language 'plpgsql';

-- ==============================================================================
-- INITIAL REGISTRY DATA
-- ==============================================================================

-- Insert system metrics for registry initialization
INSERT INTO system_metrics (service_name, metric_name, metric_value, metadata) VALUES
('registry', 'schema_version', 2.0, '{"migration": "002_registry_schema", "completed_at": "' || NOW() || '"}'),
('registry', 'tables_created', 7.0, '{"agent_registry": true, "server_registry": true, "department_registry": true, "tool_registry": true, "workflow_registry": true, "resource_registry": true, "configuration_registry": true}');

-- Registry initialization complete
SELECT 'BoarderframeOS Registry Schema initialized successfully' AS status;
