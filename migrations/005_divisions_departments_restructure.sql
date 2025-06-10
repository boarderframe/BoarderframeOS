-- BoarderframeOS Divisions & Departments Restructure
-- Complete reorganization with Divisions > Departments > Leaders structure
-- Maintains existing data while adding new organizational layers

-- Drop existing views that depend on current structure
DROP VIEW IF EXISTS department_overview;
DROP VIEW IF EXISTS agent_current_assignments;

-- Create new organizational hierarchy tables

-- 1. DIVISIONS TABLE (9 major divisions)
CREATE TABLE IF NOT EXISTS divisions (
    id SERIAL PRIMARY KEY,
    division_key VARCHAR(100) UNIQUE NOT NULL,
    division_name VARCHAR(255) NOT NULL,
    division_description TEXT,
    division_purpose TEXT,
    priority INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ENHANCED DEPARTMENTS TABLE (28 departments under divisions)
-- Add division relationship and enhance existing structure
ALTER TABLE departments 
ADD COLUMN IF NOT EXISTS division_id INTEGER REFERENCES divisions(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS department_type VARCHAR(50) DEFAULT 'standard',
ADD COLUMN IF NOT EXISTS parent_department_id UUID REFERENCES departments(id),
ADD COLUMN IF NOT EXISTS leadership_model VARCHAR(50) DEFAULT 'single_leader',
ADD COLUMN IF NOT EXISTS operational_status VARCHAR(50) DEFAULT 'planning',
ADD COLUMN IF NOT EXISTS budget_allocation DECIMAL(12,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS agent_capacity INTEGER DEFAULT 10,
ADD COLUMN IF NOT EXISTS performance_metrics JSONB DEFAULT '{}';

-- Update departments to ensure proper structure
ALTER TABLE departments ALTER COLUMN department_key TYPE VARCHAR(100);
ALTER TABLE departments ALTER COLUMN department_name TYPE VARCHAR(255);

-- 3. DEPARTMENT LEADERS TABLE (Enhanced with more details)
-- Update existing table with additional fields
ALTER TABLE department_leaders 
ADD COLUMN IF NOT EXISTS leader_key VARCHAR(100),
ADD COLUMN IF NOT EXISTS leader_type VARCHAR(50) DEFAULT 'executive',
ADD COLUMN IF NOT EXISTS leadership_tier VARCHAR(50) DEFAULT 'department',
ADD COLUMN IF NOT EXISTS specialization TEXT,
ADD COLUMN IF NOT EXISTS biblical_archetype VARCHAR(100),
ADD COLUMN IF NOT EXISTS authority_level INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS reports_to_leader_id INTEGER REFERENCES department_leaders(id),
ADD COLUMN IF NOT EXISTS appointment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS leadership_metrics JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS active_status VARCHAR(50) DEFAULT 'active',
ADD COLUMN IF NOT EXISTS contact_methods JSONB DEFAULT '{}';

-- Add unique constraint for leader_key
CREATE UNIQUE INDEX IF NOT EXISTS idx_department_leaders_key ON department_leaders(leader_key) WHERE leader_key IS NOT NULL;

-- 4. DIVISION LEADERSHIP TABLE (Executive oversight of divisions)
CREATE TABLE IF NOT EXISTS division_leadership (
    id SERIAL PRIMARY KEY,
    division_id INTEGER REFERENCES divisions(id) ON DELETE CASCADE,
    leader_id INTEGER REFERENCES department_leaders(id) ON DELETE CASCADE,
    leadership_role VARCHAR(100) NOT NULL, -- 'executive_sponsor', 'division_head', 'strategic_advisor'
    authority_scope JSONB DEFAULT '{}',
    appointed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    appointed_by VARCHAR(255),
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(division_id, leader_id, leadership_role)
);

-- 5. ORGANIZATIONAL HIERARCHY TABLE (Formal reporting structure)
CREATE TABLE IF NOT EXISTS organizational_hierarchy (
    id SERIAL PRIMARY KEY,
    superior_type VARCHAR(50) NOT NULL, -- 'division', 'department', 'leader'
    superior_id VARCHAR(100) NOT NULL, -- ID of the superior entity
    subordinate_type VARCHAR(50) NOT NULL, -- 'division', 'department', 'leader', 'agent'
    subordinate_id VARCHAR(100) NOT NULL, -- ID of the subordinate entity
    relationship_type VARCHAR(50) DEFAULT 'reports_to',
    relationship_strength INTEGER DEFAULT 5, -- 1-10 scale
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(superior_type, superior_id, subordinate_type, subordinate_id, relationship_type)
);

-- 6. LEADERSHIP SUCCESSION PLAN TABLE
CREATE TABLE IF NOT EXISTS leadership_succession (
    id SERIAL PRIMARY KEY,
    current_leader_id INTEGER REFERENCES department_leaders(id) ON DELETE CASCADE,
    successor_leader_id INTEGER REFERENCES department_leaders(id) ON DELETE CASCADE,
    succession_type VARCHAR(50) DEFAULT 'planned', -- 'planned', 'emergency', 'temporary'
    readiness_level INTEGER DEFAULT 1, -- 1-10 scale
    succession_plan TEXT,
    target_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(current_leader_id, successor_leader_id)
);

-- 7. DEPARTMENT CAPABILITIES TABLE (What each department can do)
CREATE TABLE IF NOT EXISTS department_capabilities (
    id SERIAL PRIMARY KEY,
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    capability_name VARCHAR(255) NOT NULL,
    capability_description TEXT,
    capability_type VARCHAR(100), -- 'core', 'supporting', 'specialized', 'strategic'
    proficiency_level INTEGER DEFAULT 5, -- 1-10 scale
    automation_level INTEGER DEFAULT 3, -- 1-10 scale
    required_skills JSONB DEFAULT '[]',
    enabling_tools JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. CROSS-DEPARTMENT COLLABORATION TABLE
CREATE TABLE IF NOT EXISTS department_collaborations (
    id SERIAL PRIMARY KEY,
    primary_department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    collaborating_department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    collaboration_type VARCHAR(100), -- 'workflow', 'project', 'ongoing', 'consultative'
    collaboration_name VARCHAR(255),
    collaboration_description TEXT,
    priority_level INTEGER DEFAULT 5,
    frequency VARCHAR(50), -- 'daily', 'weekly', 'monthly', 'ad_hoc', 'project_based'
    success_metrics JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT true,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(primary_department_id, collaborating_department_id, collaboration_type)
);

-- 9. DEPARTMENT PERFORMANCE METRICS TABLE (Enhanced from department_status)
-- Rename and enhance existing department_status table
ALTER TABLE department_status RENAME TO department_performance;

ALTER TABLE department_performance 
ADD COLUMN IF NOT EXISTS division_id INTEGER REFERENCES divisions(id),
ADD COLUMN IF NOT EXISTS performance_period VARCHAR(50) DEFAULT 'current',
ADD COLUMN IF NOT EXISTS efficiency_score DECIMAL(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS collaboration_score DECIMAL(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS innovation_score DECIMAL(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS customer_satisfaction_score DECIMAL(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS budget_utilization DECIMAL(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS goal_achievement_rate DECIMAL(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS performance_trend VARCHAR(50) DEFAULT 'stable',
ADD COLUMN IF NOT EXISTS risk_factors JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS improvement_areas JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS achievements JSONB DEFAULT '[]';

-- 10. STRATEGIC OBJECTIVES TABLE (Division and department goals)
CREATE TABLE IF NOT EXISTS strategic_objectives (
    id SERIAL PRIMARY KEY,
    objective_type VARCHAR(50) NOT NULL, -- 'division', 'department', 'cross_functional'
    entity_id VARCHAR(100) NOT NULL, -- division_id or department_id
    objective_name VARCHAR(255) NOT NULL,
    objective_description TEXT,
    objective_category VARCHAR(100), -- 'revenue', 'operational', 'strategic', 'innovation'
    priority_level INTEGER DEFAULT 5,
    target_value DECIMAL(15,2),
    current_value DECIMAL(15,2) DEFAULT 0.00,
    unit_of_measure VARCHAR(100),
    target_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'paused', 'cancelled'
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    assigned_to_leader_id INTEGER REFERENCES department_leaders(id),
    supporting_departments JSONB DEFAULT '[]',
    success_criteria TEXT,
    dependencies JSONB DEFAULT '[]',
    risks JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_divisions_priority ON divisions(priority);
CREATE INDEX IF NOT EXISTS idx_divisions_active ON divisions(is_active);

CREATE INDEX IF NOT EXISTS idx_departments_division ON departments(division_id);
CREATE INDEX IF NOT EXISTS idx_departments_operational_status ON departments(operational_status);
CREATE INDEX IF NOT EXISTS idx_departments_parent ON departments(parent_department_id);

CREATE INDEX IF NOT EXISTS idx_department_leaders_tier ON department_leaders(leadership_tier);
CREATE INDEX IF NOT EXISTS idx_department_leaders_type ON department_leaders(leader_type);
CREATE INDEX IF NOT EXISTS idx_department_leaders_active ON department_leaders(active_status);

CREATE INDEX IF NOT EXISTS idx_division_leadership_division ON division_leadership(division_id);
CREATE INDEX IF NOT EXISTS idx_division_leadership_leader ON division_leadership(leader_id);

CREATE INDEX IF NOT EXISTS idx_org_hierarchy_superior ON organizational_hierarchy(superior_type, superior_id);
CREATE INDEX IF NOT EXISTS idx_org_hierarchy_subordinate ON organizational_hierarchy(subordinate_type, subordinate_id);

CREATE INDEX IF NOT EXISTS idx_dept_capabilities_department ON department_capabilities(department_id);
CREATE INDEX IF NOT EXISTS idx_dept_capabilities_type ON department_capabilities(capability_type);

CREATE INDEX IF NOT EXISTS idx_dept_collaborations_primary ON department_collaborations(primary_department_id);
CREATE INDEX IF NOT EXISTS idx_dept_collaborations_active ON department_collaborations(active);

CREATE INDEX IF NOT EXISTS idx_dept_performance_division ON department_performance(division_id);
CREATE INDEX IF NOT EXISTS idx_dept_performance_period ON department_performance(performance_period);

CREATE INDEX IF NOT EXISTS idx_strategic_objectives_type ON strategic_objectives(objective_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_strategic_objectives_status ON strategic_objectives(status);
CREATE INDEX IF NOT EXISTS idx_strategic_objectives_assigned ON strategic_objectives(assigned_to_leader_id);

-- Update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for new tables
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_divisions_updated_at') THEN
        CREATE TRIGGER update_divisions_updated_at BEFORE UPDATE ON divisions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_leadership_succession_updated_at') THEN
        CREATE TRIGGER update_leadership_succession_updated_at BEFORE UPDATE ON leadership_succession FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_department_capabilities_updated_at') THEN
        CREATE TRIGGER update_department_capabilities_updated_at BEFORE UPDATE ON department_capabilities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_strategic_objectives_updated_at') THEN
        CREATE TRIGGER update_strategic_objectives_updated_at BEFORE UPDATE ON strategic_objectives FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Create comprehensive views for easy data access

-- Division Overview View
CREATE OR REPLACE VIEW division_overview AS
SELECT 
    d.id,
    d.division_key,
    d.division_name,
    d.division_description,
    d.division_purpose,
    d.priority,
    d.is_active,
    COUNT(DISTINCT dept.id) as department_count,
    COUNT(DISTINCT dl.id) as leader_count,
    COUNT(DISTINCT ada.agent_id) as assigned_agent_count,
    AVG(dp.health_score) as avg_health_score,
    AVG(dp.productivity_score) as avg_productivity_score,
    AVG(dp.efficiency_score) as avg_efficiency_score
FROM divisions d
LEFT JOIN departments dept ON d.id = dept.division_id
LEFT JOIN department_leaders dl ON dept.id = dl.department_id
LEFT JOIN agent_department_assignments ada ON dept.id = ada.department_id AND ada.assignment_status = 'active'
LEFT JOIN department_performance dp ON dept.id = dp.department_id
GROUP BY d.id, d.division_key, d.division_name, d.division_description, d.division_purpose, d.priority, d.is_active
ORDER BY d.priority, d.division_name;

-- Enhanced Department Overview View
CREATE OR REPLACE VIEW department_overview AS
SELECT 
    dept.id,
    dept.department_key,
    COALESCE(dept.department_name, dept.name) as department_name,
    dept.category,
    COALESCE(dept.description, '') as description,
    dept.department_purpose,
    dept.priority,
    dept.is_active,
    dept.operational_status,
    dept.agent_capacity,
    div.division_name,
    div.division_key,
    COUNT(DISTINCT dl.id) as leaders_count,
    COUNT(DISTINCT dna.id) as native_agent_types_count,
    COUNT(DISTINCT ada.agent_id) as assigned_agents_count,
    COUNT(DISTINCT dc.id) as capabilities_count,
    COALESCE(dp.health_score, 0.0) as health_score,
    COALESCE(dp.productivity_score, 0.0) as productivity_score,
    COALESCE(dp.efficiency_score, 0.0) as efficiency_score,
    dp.performance_trend,
    dp.last_activity
FROM departments dept
LEFT JOIN divisions div ON dept.division_id = div.id
LEFT JOIN department_leaders dl ON dept.id = dl.department_id AND dl.active_status = 'active'
LEFT JOIN department_native_agents dna ON dept.id = dna.department_id
LEFT JOIN agent_department_assignments ada ON dept.id = ada.department_id AND ada.assignment_status = 'active'
LEFT JOIN department_capabilities dc ON dept.id = dc.department_id
LEFT JOIN department_performance dp ON dept.id = dp.department_id
WHERE dept.is_active = true
GROUP BY dept.id, dept.department_key, dept.department_name, dept.name, dept.category, dept.description, 
         dept.department_purpose, dept.priority, dept.is_active, dept.operational_status, dept.agent_capacity,
         div.division_name, div.division_key, dp.health_score, dp.productivity_score, dp.efficiency_score,
         dp.performance_trend, dp.last_activity
ORDER BY dept.priority, dept.department_name;

-- Leadership Hierarchy View
CREATE OR REPLACE VIEW leadership_hierarchy AS
SELECT 
    dl.id as leader_id,
    dl.leader_key,
    dl.name as leader_name,
    dl.title,
    dl.leadership_tier,
    dl.leader_type,
    dl.authority_level,
    dl.active_status,
    dept.department_name,
    dept.department_key,
    div.division_name,
    div.division_key,
    superior.name as reports_to_name,
    superior.title as reports_to_title,
    dl.appointment_date,
    dl.specialization,
    dl.biblical_archetype
FROM department_leaders dl
LEFT JOIN departments dept ON dl.department_id = dept.id
LEFT JOIN divisions div ON dept.division_id = div.id
LEFT JOIN department_leaders superior ON dl.reports_to_leader_id = superior.id
WHERE dl.active_status = 'active'
ORDER BY dl.leadership_tier, dl.authority_level DESC, dl.name;

-- Agent Current Assignments View (Enhanced)
CREATE OR REPLACE VIEW agent_current_assignments AS
SELECT 
    ada.agent_id,
    ada.department_id,
    COALESCE(dept.department_name, dept.name) as department_name,
    dept.category,
    div.division_name,
    div.division_key,
    ada.assignment_type,
    ada.assigned_by,
    ada.assigned_at,
    ada.assignment_status,
    dl.name as department_leader,
    dl.title as leader_title
FROM agent_department_assignments ada
JOIN departments dept ON ada.department_id = dept.id
LEFT JOIN divisions div ON dept.division_id = div.id
LEFT JOIN department_leaders dl ON dept.id = dl.department_id AND dl.is_primary = true
WHERE ada.assignment_status = 'active'
ORDER BY div.priority, dept.priority, ada.assigned_at;

-- Organizational Structure View
CREATE OR REPLACE VIEW organizational_structure AS
SELECT 
    'division' as level_type,
    div.id::text as entity_id,
    div.division_name as entity_name,
    div.division_key as entity_key,
    NULL as parent_id,
    div.priority as sort_order,
    div.is_active as active
FROM divisions div
WHERE div.is_active = true

UNION ALL

SELECT 
    'department' as level_type,
    dept.id::text as entity_id,
    COALESCE(dept.department_name, dept.name) as entity_name,
    dept.department_key as entity_key,
    dept.division_id::text as parent_id,
    dept.priority as sort_order,
    dept.is_active as active
FROM departments dept
JOIN divisions div ON dept.division_id = div.id
WHERE dept.is_active = true

UNION ALL

SELECT 
    'leader' as level_type,
    dl.id::text as entity_id,
    dl.name as entity_name,
    dl.leader_key as entity_key,
    dl.department_id::text as parent_id,
    dl.authority_level as sort_order,
    CASE WHEN dl.active_status = 'active' THEN true ELSE false END as active
FROM department_leaders dl
JOIN departments dept ON dl.department_id = dept.id
WHERE dl.active_status = 'active' AND dept.is_active = true

ORDER BY parent_id NULLS FIRST, sort_order, entity_name;

-- Performance Dashboard View
CREATE OR REPLACE VIEW performance_dashboard AS
SELECT 
    div.division_name,
    div.division_key,
    COUNT(DISTINCT dept.id) as departments_count,
    COUNT(DISTINCT dl.id) as leaders_count,
    COUNT(DISTINCT ada.agent_id) as active_agents_count,
    ROUND(AVG(dp.health_score), 2) as avg_health_score,
    ROUND(AVG(dp.productivity_score), 2) as avg_productivity_score,
    ROUND(AVG(dp.efficiency_score), 2) as avg_efficiency_score,
    COUNT(CASE WHEN dp.performance_trend = 'improving' THEN 1 END) as improving_departments,
    COUNT(CASE WHEN dp.performance_trend = 'declining' THEN 1 END) as declining_departments,
    COUNT(CASE WHEN dept.operational_status = 'operational' THEN 1 END) as operational_departments
FROM divisions div
LEFT JOIN departments dept ON div.id = dept.division_id AND dept.is_active = true
LEFT JOIN department_leaders dl ON dept.id = dl.department_id AND dl.active_status = 'active'
LEFT JOIN agent_department_assignments ada ON dept.id = ada.department_id AND ada.assignment_status = 'active'
LEFT JOIN department_performance dp ON dept.id = dp.department_id
WHERE div.is_active = true
GROUP BY div.id, div.division_name, div.division_key, div.priority
ORDER BY div.priority;

-- Comments for documentation
COMMENT ON TABLE divisions IS 'Top-level organizational divisions (9 major business areas)';
COMMENT ON TABLE department_leaders IS 'Enhanced leadership table with biblical archetypes and authority levels';
COMMENT ON TABLE division_leadership IS 'Executive oversight and strategic leadership of divisions';
COMMENT ON TABLE organizational_hierarchy IS 'Formal reporting structure across all organizational levels';
COMMENT ON TABLE leadership_succession IS 'Succession planning for leadership continuity';
COMMENT ON TABLE department_capabilities IS 'Detailed capabilities and competencies of each department';
COMMENT ON TABLE department_collaborations IS 'Cross-department collaboration patterns and workflows';
COMMENT ON TABLE department_performance IS 'Enhanced performance metrics and KPIs (renamed from department_status)';
COMMENT ON TABLE strategic_objectives IS 'Division and department strategic goals and objectives';

COMMENT ON VIEW division_overview IS 'High-level overview of all divisions with key metrics';
COMMENT ON VIEW department_overview IS 'Comprehensive department view with performance and structure data';
COMMENT ON VIEW leadership_hierarchy IS 'Complete leadership structure with reporting relationships';
COMMENT ON VIEW organizational_structure IS 'Full organizational tree from divisions to leaders';
COMMENT ON VIEW performance_dashboard IS 'Executive dashboard view for organizational performance';