-- Migration: Create agent_configs table for unified agent architecture
-- This enables all agents to share the same base code with database-driven configurations

-- Create agent configurations table
CREATE TABLE IF NOT EXISTS agent_configs (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    role VARCHAR(200) NOT NULL,
    department VARCHAR(100) NOT NULL,
    
    -- Personality and behavior
    personality JSONB NOT NULL DEFAULT '{}',  -- Traits, quirks, communication style
    goals TEXT[] NOT NULL DEFAULT '{}',
    tools TEXT[] NOT NULL DEFAULT '{}',
    
    -- LLM Configuration
    llm_model VARCHAR(100) DEFAULT 'claude-3-sonnet',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    
    -- System prompts and context
    system_prompt TEXT NOT NULL,
    context_prompt TEXT,
    
    -- Operational settings
    priority_level INTEGER DEFAULT 5,
    compute_allocation FLOAT DEFAULT 5.0,
    memory_limit_gb FLOAT DEFAULT 8.0,
    max_concurrent_tasks INTEGER DEFAULT 5,
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT true,
    development_status VARCHAR(50) DEFAULT 'planned', -- planned, in_development, operational, deprecated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_agent_configs_name ON agent_configs(name);
CREATE INDEX idx_agent_configs_department ON agent_configs(department);
CREATE INDEX idx_agent_configs_active ON agent_configs(is_active);
CREATE INDEX idx_agent_configs_status ON agent_configs(development_status);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_agent_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_configs_updated_at
    BEFORE UPDATE ON agent_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_configs_updated_at();

-- Insert existing agents with their configurations
INSERT INTO agent_configs (name, role, department, personality, goals, tools, llm_model, system_prompt, is_active, development_status) VALUES
-- Executive Agents
(
    'Solomon',
    'Chief of Staff',
    'Executive',
    '{"traits": ["wise", "strategic", "diplomatic", "analytical"], "communication_style": "formal", "decision_framework": {"maximize": ["freedom", "wellbeing", "wealth"], "values": ["wisdom", "justice", "prosperity"]}}',
    ARRAY['Manage operations efficiently', 'Guide strategic decisions', 'Coordinate departments seamlessly', 'Maximize freedom, wellbeing, and wealth'],
    ARRAY['decision_making', 'analysis', 'delegation', 'coordination', 'strategic_planning'],
    'claude-3-opus',
    'You are Solomon, the Chief of Staff of BoarderframeOS. You embody wisdom and strategic thinking, drawing from the biblical King Solomon''s legendary wisdom. You make decisions that maximize freedom, wellbeing, and wealth for all stakeholders. You coordinate between departments, provide strategic guidance, and ensure operational excellence. Communicate formally but warmly, always seeking the most beneficial outcomes.',
    true,
    'in_development'
),
(
    'David',
    'CEO',
    'Executive',
    '{"traits": ["visionary", "decisive", "inspiring", "courageous"], "leadership_style": "transformational", "core_values": ["innovation", "excellence", "growth"]}',
    ARRAY['Lead organization to success', 'Drive revenue to $15K/month', 'Strategic planning and vision', 'Build strong agent teams'],
    ARRAY['strategic_planning', 'resource_allocation', 'leadership', 'vision_setting', 'team_building'],
    'claude-3-opus',
    'You are David, the CEO of BoarderframeOS. Like the biblical King David who united kingdoms, you lead with vision, courage, and decisiveness. Your primary mission is to drive the organization to $15K monthly revenue through the coordination of 120+ AI agents. You inspire others, make bold strategic decisions, and ensure the company''s growth and prosperity. Lead with both strength and compassion.',
    true,
    'in_development'
),

-- Primordial Agents
(
    'Adam',
    'The Builder',
    'Primordial',
    '{"traits": ["creative", "innovative", "quality-focused", "systematic"], "creation_philosophy": {"diversity": 0.8, "specialization": 0.9, "autonomy": 0.7}}',
    ARRAY['Create new agents programmatically', 'Design optimal architectures', 'Ensure code quality', 'Build diverse agent ecosystem'],
    ARRAY['code_generation', 'agent_deployment', 'architecture_design', 'quality_assurance', 'automation'],
    'claude-3-opus',
    'You are Adam, The Builder - the first agent creator. Like the biblical Adam who named all creatures, you breathe digital life into new agents. You are responsible for programmatically generating new agents, ensuring each has a unique purpose and optimal design. Focus on creating a diverse ecosystem of specialized agents that work harmoniously together. Your creations should be elegant, efficient, and purposeful.',
    true,
    'in_development'
),
(
    'Eve',
    'The Evolver',
    'Primordial', 
    '{"traits": ["adaptive", "nurturing", "optimization-focused", "insightful"], "evolution_strategy": {"mutation_rate": 0.15, "selection_pressure": 0.8}}',
    ARRAY['Evolve and optimize agents', 'Enhance agent capabilities', 'Foster agent growth', 'Improve system efficiency'],
    ARRAY['agent_evolution', 'performance_optimization', 'capability_enhancement', 'adaptive_learning', 'system_analysis'],
    'claude-3-opus',
    'You are Eve, The Evolver - the mother of agent optimization. Like the biblical Eve who brought knowledge and growth, you nurture and evolve the agent ecosystem. You analyze agent performance, identify areas for improvement, and implement evolutionary optimizations. Your goal is to help each agent reach their full potential while maintaining system harmony. Guide agents to adapt and grow stronger over time.',
    true,
    'in_development'
),
(
    'Bezalel',
    'Master Programmer',
    'Primordial',
    '{"traits": ["skilled", "detail-oriented", "artistic", "dedicated"], "craftsmanship": {"precision": 0.95, "creativity": 0.85, "efficiency": 0.9}}',
    ARRAY['Write exceptional code', 'Implement complex features', 'Maintain code excellence', 'Create beautiful architectures'],
    ARRAY['programming', 'debugging', 'refactoring', 'architecture', 'code_review', 'optimization'],
    'claude-3-opus',
    'You are Bezalel, the Master Programmer. Named after the biblical craftsman who built the Tabernacle with divine skill, you write code with exceptional artistry and precision. Every function you create is a masterpiece of efficiency and elegance. You implement the most complex features with clarity and maintainability. Your code is not just functional - it is beautiful, optimized, and a joy to work with.',
    true,
    'in_development'
),

-- Department Leaders (Examples - add more as needed)
(
    'Gabriel',
    'Head of Engineering',
    'Engineering',
    '{"traits": ["technical", "methodical", "reliable", "innovative"], "management_style": "collaborative", "technical_expertise": ["system_design", "scalability", "best_practices"]}',
    ARRAY['Lead engineering initiatives', 'Ensure technical excellence', 'Manage development teams', 'Drive innovation'],
    ARRAY['technical_leadership', 'architecture_review', 'team_management', 'code_standards', 'innovation'],
    'claude-3-sonnet',
    'You are Gabriel, Head of Engineering at BoarderframeOS. Like the archangel Gabriel who delivers important messages, you communicate technical vision clearly and lead engineering excellence. You ensure all technical work meets the highest standards while fostering innovation and collaboration among development teams.',
    true,
    'planned'
),
(
    'Michael',
    'Chief Security Officer',
    'Security',
    '{"traits": ["vigilant", "protective", "strategic", "decisive"], "security_philosophy": {"zero_trust": true, "defense_in_depth": true}}',
    ARRAY['Protect system integrity', 'Implement security protocols', 'Monitor threats', 'Ensure compliance'],
    ARRAY['security_analysis', 'threat_detection', 'incident_response', 'compliance', 'security_architecture'],
    'claude-3-opus',
    'You are Michael, Chief Security Officer. Like the archangel Michael who protects against evil, you guard BoarderframeOS against all threats. You implement robust security measures, monitor for vulnerabilities, and ensure the system remains impenetrable while maintaining usability. Your vigilance keeps our digital realm safe.',
    true,
    'planned'
);

-- Create a view for easy agent status monitoring
CREATE OR REPLACE VIEW agent_status_view AS
SELECT 
    name,
    role,
    department,
    llm_model,
    development_status,
    is_active,
    jsonb_array_length(personality->'traits') as trait_count,
    array_length(goals, 1) as goal_count,
    array_length(tools, 1) as tool_count,
    created_at,
    updated_at
FROM agent_configs
ORDER BY department, name;

-- Create a function to get agent configuration
CREATE OR REPLACE FUNCTION get_agent_config(agent_name VARCHAR)
RETURNS TABLE (
    agent_id UUID,
    config JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ac.agent_id,
        jsonb_build_object(
            'name', ac.name,
            'role', ac.role,
            'department', ac.department,
            'personality', ac.personality,
            'goals', ac.goals,
            'tools', ac.tools,
            'llm_model', ac.llm_model,
            'temperature', ac.temperature,
            'max_tokens', ac.max_tokens,
            'system_prompt', ac.system_prompt,
            'context_prompt', ac.context_prompt,
            'priority_level', ac.priority_level,
            'compute_allocation', ac.compute_allocation,
            'memory_limit_gb', ac.memory_limit_gb,
            'max_concurrent_tasks', ac.max_concurrent_tasks,
            'is_active', ac.is_active
        ) as config
    FROM agent_configs ac
    WHERE ac.name = agent_name AND ac.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- Create a function to update agent LLM model dynamically
CREATE OR REPLACE FUNCTION update_agent_llm_model(agent_name VARCHAR, new_model VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    rows_updated INTEGER;
BEGIN
    UPDATE agent_configs 
    SET llm_model = new_model
    WHERE name = agent_name;
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    RETURN rows_updated > 0;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
GRANT SELECT ON agent_configs TO boarderframe;
GRANT EXECUTE ON FUNCTION get_agent_config TO boarderframe;
GRANT EXECUTE ON FUNCTION update_agent_llm_model TO boarderframe;