-- BoarderframeOS Initial PostgreSQL Schema
-- Enhanced schema with pgvector support for agent memory and coordination

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search optimization

-- Set timezone
SET timezone = 'UTC';

-- ==============================================================================
-- CORE AGENT MANAGEMENT TABLES
-- ==============================================================================

-- Enhanced agents table with department hierarchy
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    agent_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused', 'error', 'creating')),
    configuration JSONB DEFAULT '{}',
    code TEXT,
    parent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    generation INTEGER DEFAULT 1 CHECK (generation > 0),
    fitness_score REAL DEFAULT 0.0 CHECK (fitness_score >= 0.0),
    capabilities JSONB DEFAULT '[]',  -- Array of capability strings
    resources JSONB DEFAULT '{}',     -- Resource requirements and allocations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_agent_name_per_department UNIQUE (name, department)
);

-- Enhanced agent memories with vector embeddings
CREATE TABLE agent_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    memory_type VARCHAR(100) DEFAULT 'short_term' CHECK (memory_type IN ('short_term', 'long_term', 'procedural', 'episodic', 'semantic')),
    importance REAL DEFAULT 0.5 CHECK (importance BETWEEN 0.0 AND 1.0),
    embedding VECTOR(1536),  -- OpenAI text-embedding-ada-002 dimensions
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    conversation_id UUID,
    workflow_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0
);

-- Agent interactions with enhanced coordination tracking
CREATE TABLE agent_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    target_agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100) NOT NULL,
    message_id UUID,  -- Link to message bus messages
    conversation_id UUID,
    workflow_id UUID,
    data JSONB DEFAULT '{}',
    response_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'timeout')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Performance tracking
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0.0
);

-- ==============================================================================
-- DEPARTMENT AND HIERARCHY MANAGEMENT
-- ==============================================================================

-- Department registry with hierarchy and configuration
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    phase INTEGER NOT NULL CHECK (phase BETWEEN 1 AND 7),
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 7),
    category VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'planning' CHECK (status IN ('planning', 'active', 'scaling', 'optimizing', 'maintenance')),
    leaders JSONB DEFAULT '[]',  -- Array of leader agent configurations
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    resource_requirements JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent roles within departments
CREATE TABLE agent_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    role_name VARCHAR(255) NOT NULL,
    role_type VARCHAR(100) NOT NULL CHECK (role_type IN ('leader', 'specialist', 'worker', 'coordinator')),
    permissions JSONB DEFAULT '[]',
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_agent_department_role UNIQUE (agent_id, department_id, role_name)
);

-- ==============================================================================
-- TASK AND WORKFLOW MANAGEMENT
-- ==============================================================================

-- Enhanced tasks with workflow coordination
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    workflow_id UUID,
    task_type VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    data JSONB DEFAULT '{}',
    requirements JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_progress', 'blocked', 'completed', 'failed', 'cancelled')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    dependencies UUID[] DEFAULT '{}',  -- Array of task IDs this task depends on
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_at TIMESTAMP WITH TIME ZONE,
    
    -- Resource tracking
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0.0
);

-- Workflow definitions and state management
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    workflow_type VARCHAR(100) NOT NULL,
    definition JSONB NOT NULL,  -- Workflow graph/state machine definition
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'failed', 'archived')),
    version INTEGER DEFAULT 1,
    created_by UUID REFERENCES agents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- METRICS AND PERFORMANCE TRACKING
-- ==============================================================================

-- Enhanced metrics with time-series optimization
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    workflow_id UUID,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value REAL NOT NULL,
    metric_type VARCHAR(100) DEFAULT 'counter' CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'timer')),
    unit VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Partitioning hint for time-series data
    CONSTRAINT check_recorded_at CHECK (recorded_at <= NOW() + INTERVAL '1 hour')
);

-- System health and performance metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value REAL NOT NULL,
    instance_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- EVOLUTION AND LEARNING SYSTEM
-- ==============================================================================

-- Agent evolution tracking
CREATE TABLE evolution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    child_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    generation INTEGER NOT NULL,
    evolution_type VARCHAR(100) NOT NULL CHECK (evolution_type IN ('mutation', 'crossover', 'adaptation', 'learning')),
    mutations JSONB DEFAULT '[]',
    fitness_improvement REAL,
    success_probability REAL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning experiences and knowledge accumulation
CREATE TABLE learning_experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    experience_type VARCHAR(100) NOT NULL,
    context TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    outcome TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
    embedding VECTOR(1536),  -- For similarity matching
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- BUSINESS AND REVENUE TRACKING
-- ==============================================================================

-- Customer management
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    stripe_customer_id VARCHAR(255) UNIQUE,
    subscription_status VARCHAR(100) DEFAULT 'trial' CHECK (subscription_status IN ('trial', 'active', 'paused', 'cancelled', 'expired')),
    subscription_plan VARCHAR(100),
    monthly_value DECIMAL(10,2) DEFAULT 0.0,
    total_spent DECIMAL(10,2) DEFAULT 0.0,
    created_by_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Revenue transaction tracking
CREATE TABLE revenue_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,  -- Which agent generated this revenue
    transaction_type VARCHAR(100) NOT NULL CHECK (transaction_type IN ('subscription', 'usage', 'one_time', 'refund')),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    product VARCHAR(255),
    description TEXT,
    stripe_payment_intent_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API usage tracking for billing
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    requests_count INTEGER DEFAULT 1,
    cost_usd DECIMAL(10,6) DEFAULT 0.0,
    response_time_ms INTEGER,
    status_code INTEGER,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- MESSAGE BUS AND COMMUNICATION
-- ==============================================================================

-- Message bus persistence and routing
CREATE TABLE message_bus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    conversation_id UUID,
    workflow_id UUID,
    source_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    target_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    message_type VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    subject VARCHAR(500),
    content TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'delivered', 'acknowledged', 'failed', 'expired')),
    delivery_attempts INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    expires_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE
);

-- ==============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ==============================================================================

-- Agent indexes
CREATE INDEX idx_agents_department ON agents(department);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_generation ON agents(generation);
CREATE INDEX idx_agents_fitness ON agents(fitness_score DESC);
CREATE INDEX idx_agents_last_seen ON agents(last_seen DESC);

-- Memory indexes including vector similarity
CREATE INDEX idx_agent_memories_agent_id ON agent_memories(agent_id);
CREATE INDEX idx_agent_memories_type ON agent_memories(memory_type);
CREATE INDEX idx_agent_memories_importance ON agent_memories(importance DESC);
CREATE INDEX idx_agent_memories_conversation ON agent_memories(conversation_id);
CREATE INDEX idx_agent_memories_accessed ON agent_memories(accessed_at DESC);
CREATE INDEX idx_agent_memories_tags ON agent_memories USING GIN(tags);

-- Vector similarity index for semantic search
CREATE INDEX ON agent_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Learning experiences vector index
CREATE INDEX ON learning_experiences USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Interaction indexes
CREATE INDEX idx_agent_interactions_source ON agent_interactions(source_agent_id);
CREATE INDEX idx_agent_interactions_target ON agent_interactions(target_agent_id);
CREATE INDEX idx_agent_interactions_type ON agent_interactions(interaction_type);
CREATE INDEX idx_agent_interactions_conversation ON agent_interactions(conversation_id);
CREATE INDEX idx_agent_interactions_status ON agent_interactions(status);
CREATE INDEX idx_agent_interactions_started ON agent_interactions(started_at DESC);

-- Task indexes
CREATE INDEX idx_tasks_agent ON tasks(agent_id);
CREATE INDEX idx_tasks_department ON tasks(department_id);
CREATE INDEX idx_tasks_workflow ON tasks(workflow_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX idx_tasks_due ON tasks(due_at);

-- Metrics indexes (optimized for time-series queries)
CREATE INDEX idx_metrics_agent_time ON metrics(agent_id, recorded_at DESC);
CREATE INDEX idx_metrics_name_time ON metrics(metric_name, recorded_at DESC);
CREATE INDEX idx_metrics_department_time ON metrics(department_id, recorded_at DESC);
CREATE INDEX idx_metrics_tags ON metrics USING GIN(tags);

-- Business indexes
CREATE INDEX idx_customers_subscription ON customers(subscription_status);
CREATE INDEX idx_customers_created_by ON customers(created_by_agent_id);
CREATE INDEX idx_revenue_customer ON revenue_transactions(customer_id);
CREATE INDEX idx_revenue_agent ON revenue_transactions(agent_id);
CREATE INDEX idx_revenue_processed ON revenue_transactions(processed_at DESC);
CREATE INDEX idx_api_usage_customer_time ON api_usage(customer_id, timestamp DESC);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);

-- Message bus indexes
CREATE INDEX idx_message_bus_conversation ON message_bus(conversation_id);
CREATE INDEX idx_message_bus_workflow ON message_bus(workflow_id);
CREATE INDEX idx_message_bus_source ON message_bus(source_agent_id);
CREATE INDEX idx_message_bus_target ON message_bus(target_agent_id);
CREATE INDEX idx_message_bus_status ON message_bus(status);
CREATE INDEX idx_message_bus_priority ON message_bus(priority DESC);
CREATE INDEX idx_message_bus_sent ON message_bus(sent_at DESC);

-- ==============================================================================
-- FUNCTIONS AND TRIGGERS
-- ==============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON departments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically update agent last_seen on interaction
CREATE OR REPLACE FUNCTION update_agent_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE agents SET last_seen = NOW() WHERE id = NEW.source_agent_id;
    IF NEW.target_agent_id IS NOT NULL THEN
        UPDATE agents SET last_seen = NOW() WHERE id = NEW.target_agent_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agent_last_seen_on_interaction 
    AFTER INSERT ON agent_interactions 
    FOR EACH ROW EXECUTE FUNCTION update_agent_last_seen();

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION search_similar_memories(
    query_embedding VECTOR(1536),
    similarity_threshold REAL DEFAULT 0.8,
    max_results INTEGER DEFAULT 10,
    agent_filter UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    agent_id UUID,
    content TEXT,
    memory_type VARCHAR(100),
    importance REAL,
    similarity REAL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.agent_id,
        m.content,
        m.memory_type,
        m.importance,
        1 - (m.embedding <=> query_embedding) as similarity,
        m.metadata,
        m.created_at
    FROM agent_memories m
    WHERE 
        (agent_filter IS NULL OR m.agent_id = agent_filter)
        AND 1 - (m.embedding <=> query_embedding) > similarity_threshold
    ORDER BY m.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ language 'plpgsql';

-- ==============================================================================
-- INITIAL DATA SEEDING
-- ==============================================================================

-- Insert initial departments from the reorganized structure
INSERT INTO departments (name, phase, priority, category, description, status) VALUES
-- Phase 1: Trinity
('Executive Leadership', 1, 1, 'Trinity', 'Strategic Command Center with Solomon and David', 'active'),
('Coordination & Orchestration', 1, 1, 'Trinity', 'Multi-Department Command Center with Michael', 'active'),
('Agent Development', 1, 1, 'Trinity', 'Creation & Evolution Center with Adam and Eve', 'active'),

-- Phase 2: Essential Infrastructure  
('Engineering Department', 2, 2, 'Essential Infrastructure', 'Code Creation & System Building with Bezalel', 'planning'),
('Infrastructure Department', 2, 2, 'Essential Infrastructure', 'Communication & Protocol Mastery with Gabriel', 'planning'),
('Operations Department', 2, 2, 'Essential Infrastructure', 'Infrastructure & System Mastery with Naphtali', 'planning'),
('Security Department', 2, 2, 'Essential Infrastructure', 'Defense & Protection Mastery with Gad', 'planning'),
('Data Management Department', 2, 2, 'Essential Infrastructure', 'Data Sanctuaries & Archives with Ezra', 'planning');

-- Insert system metrics for monitoring
INSERT INTO system_metrics (service_name, metric_name, metric_value, metadata) VALUES
('postgresql', 'schema_version', 1.0, '{"migration": "001_initial_schema", "completed_at": "' || NOW() || '"}'),
('boarderframeos', 'initialization', 1.0, '{"status": "completed", "tables_created": 15}');

-- ==============================================================================
-- COMMENTS AND DOCUMENTATION
-- ==============================================================================

COMMENT ON TABLE agents IS 'Core agent registry with hierarchy and capabilities';
COMMENT ON TABLE agent_memories IS 'Agent memory storage with vector embeddings for semantic search';
COMMENT ON TABLE departments IS 'Department structure and configuration management';
COMMENT ON TABLE tasks IS 'Task management and workflow coordination';
COMMENT ON TABLE metrics IS 'Performance and operational metrics collection';
COMMENT ON TABLE customers IS 'Customer management and subscription tracking';
COMMENT ON TABLE revenue_transactions IS 'Revenue and payment transaction history';
COMMENT ON TABLE message_bus IS 'Inter-agent message persistence and routing';

COMMENT ON COLUMN agent_memories.embedding IS 'Vector embedding for semantic similarity search (1536 dimensions for OpenAI ada-002)';
COMMENT ON COLUMN learning_experiences.embedding IS 'Vector embedding for experience similarity matching';
COMMENT ON FUNCTION search_similar_memories IS 'Semantic search function for finding similar memories using vector similarity';

-- Schema initialization complete
SELECT 'BoarderframeOS PostgreSQL schema initialized successfully' AS status;