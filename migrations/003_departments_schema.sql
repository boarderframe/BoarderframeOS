-- Department Management Schema
-- Removes phases layer and implements department-centric structure
-- Supports manual agent assignment and registry integration

-- Core departments table (flattened from phases)
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    department_key VARCHAR(100) UNIQUE NOT NULL,
    department_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    department_purpose TEXT,
    priority INTEGER DEFAULT 5,
    legacy_phase VARCHAR(100),
    legacy_phase_priority INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Department leaders
CREATE TABLE IF NOT EXISTS department_leaders (
    id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Native agent types for each department
CREATE TABLE IF NOT EXISTS department_native_agents (
    id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    agent_type_name VARCHAR(255) NOT NULL,
    agent_description TEXT,
    specialization TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Live agent assignments (manual assignments)
CREATE TABLE IF NOT EXISTS agent_department_assignments (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    assignment_type VARCHAR(50) DEFAULT 'manual',
    assigned_by VARCHAR(255),
    assignment_status VARCHAR(50) DEFAULT 'active',
    assignment_reason TEXT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deassigned_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint to prevent duplicate active assignments
    UNIQUE(agent_id, department_id, assignment_status) 
    DEFERRABLE INITIALLY DEFERRED
);

-- Department status and metrics
CREATE TABLE IF NOT EXISTS department_status (
    id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    assigned_agents_count INTEGER DEFAULT 0,
    active_agents_count INTEGER DEFAULT 0,
    productivity_score DECIMAL(5,2) DEFAULT 0.0,
    health_score DECIMAL(5,2) DEFAULT 0.0,
    last_activity TIMESTAMP,
    status VARCHAR(50) DEFAULT 'inactive',
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- One status record per department
    UNIQUE(department_id)
);

-- Department hierarchy (for future organizational structure)
CREATE TABLE IF NOT EXISTS department_hierarchy (
    id SERIAL PRIMARY KEY,
    parent_department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    child_department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'reports_to',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent circular references
    CHECK (parent_department_id != child_department_id),
    UNIQUE(parent_department_id, child_department_id)
);

-- Assignment history for audit trail
CREATE TABLE IF NOT EXISTS department_assignment_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'assigned', 'deassigned', 'transferred'
    previous_department_id INTEGER REFERENCES departments(id),
    assigned_by VARCHAR(255),
    reason TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_departments_category ON departments(category);
CREATE INDEX IF NOT EXISTS idx_departments_active ON departments(is_active);
CREATE INDEX IF NOT EXISTS idx_departments_priority ON departments(priority);

CREATE INDEX IF NOT EXISTS idx_department_leaders_department ON department_leaders(department_id);
CREATE INDEX IF NOT EXISTS idx_department_leaders_primary ON department_leaders(department_id, is_primary);

CREATE INDEX IF NOT EXISTS idx_native_agents_department ON department_native_agents(department_id);

CREATE INDEX IF NOT EXISTS idx_agent_assignments_agent ON agent_department_assignments(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_assignments_department ON agent_department_assignments(department_id);
CREATE INDEX IF NOT EXISTS idx_agent_assignments_status ON agent_department_assignments(assignment_status);
CREATE INDEX IF NOT EXISTS idx_agent_assignments_active ON agent_department_assignments(agent_id, assignment_status) WHERE assignment_status = 'active';

CREATE INDEX IF NOT EXISTS idx_department_status_department ON department_status(department_id);
CREATE INDEX IF NOT EXISTS idx_department_status_health ON department_status(health_score);

CREATE INDEX IF NOT EXISTS idx_assignment_history_agent ON department_assignment_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_assignment_history_department ON department_assignment_history(department_id);
CREATE INDEX IF NOT EXISTS idx_assignment_history_created ON department_assignment_history(created_at);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON departments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_department_leaders_updated_at BEFORE UPDATE ON department_leaders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_department_native_agents_updated_at BEFORE UPDATE ON department_native_agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agent_assignments_updated_at BEFORE UPDATE ON agent_department_assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_department_status_updated_at BEFORE UPDATE ON department_status FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically update department status when assignments change
CREATE OR REPLACE FUNCTION update_department_assignment_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update for new assignment
    IF TG_OP = 'INSERT' THEN
        INSERT INTO department_status (department_id, assigned_agents_count, active_agents_count)
        VALUES (NEW.department_id, 1, CASE WHEN NEW.assignment_status = 'active' THEN 1 ELSE 0 END)
        ON CONFLICT (department_id) DO UPDATE SET
            assigned_agents_count = department_status.assigned_agents_count + 1,
            active_agents_count = department_status.active_agents_count + CASE WHEN NEW.assignment_status = 'active' THEN 1 ELSE 0 END,
            updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END IF;
    
    -- Update for assignment change
    IF TG_OP = 'UPDATE' THEN
        -- If status changed, update counts
        IF OLD.assignment_status != NEW.assignment_status THEN
            UPDATE department_status SET
                active_agents_count = (
                    SELECT COUNT(*) FROM agent_department_assignments 
                    WHERE department_id = NEW.department_id AND assignment_status = 'active'
                ),
                updated_at = CURRENT_TIMESTAMP
            WHERE department_id = NEW.department_id;
        END IF;
        RETURN NEW;
    END IF;
    
    -- Update for assignment removal
    IF TG_OP = 'DELETE' THEN
        UPDATE department_status SET
            assigned_agents_count = department_status.assigned_agents_count - 1,
            active_agents_count = department_status.active_agents_count - CASE WHEN OLD.assignment_status = 'active' THEN 1 ELSE 0 END,
            updated_at = CURRENT_TIMESTAMP
        WHERE department_id = OLD.department_id;
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_department_counts
    AFTER INSERT OR UPDATE OR DELETE ON agent_department_assignments
    FOR EACH ROW EXECUTE FUNCTION update_department_assignment_counts();

-- Views for easy data access
CREATE OR REPLACE VIEW department_overview AS
SELECT 
    d.id,
    d.department_key,
    d.department_name,
    d.category,
    d.description,
    d.department_purpose,
    d.priority,
    d.is_active,
    ds.assigned_agents_count,
    ds.active_agents_count,
    ds.productivity_score,
    ds.health_score,
    ds.status,
    ds.last_activity,
    COUNT(dl.id) as leaders_count,
    COUNT(dna.id) as native_agent_types_count
FROM departments d
LEFT JOIN department_status ds ON d.id = ds.department_id
LEFT JOIN department_leaders dl ON d.id = dl.department_id
LEFT JOIN department_native_agents dna ON d.id = dna.department_id
GROUP BY d.id, ds.assigned_agents_count, ds.active_agents_count, ds.productivity_score, ds.health_score, ds.status, ds.last_activity;

CREATE OR REPLACE VIEW agent_current_assignments AS
SELECT 
    ada.agent_id,
    ada.department_id,
    d.department_name,
    d.category,
    ada.assignment_type,
    ada.assigned_by,
    ada.assigned_at,
    ada.assignment_status
FROM agent_department_assignments ada
JOIN departments d ON ada.department_id = d.id
WHERE ada.assignment_status = 'active';

COMMENT ON TABLE departments IS 'Core departments table with flattened structure (phases layer removed)';
COMMENT ON TABLE department_leaders IS 'Leaders assigned to each department';
COMMENT ON TABLE department_native_agents IS 'Native agent types specialized for each department';
COMMENT ON TABLE agent_department_assignments IS 'Live agent assignments to departments (manual)';
COMMENT ON TABLE department_status IS 'Current status and metrics for each department';
COMMENT ON TABLE department_hierarchy IS 'Optional hierarchical relationships between departments';
COMMENT ON TABLE department_assignment_history IS 'Audit trail for all assignment changes';