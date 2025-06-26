# Unified Agent Architecture for BoarderframeOS

## Overview

All agents share the same base implementation with configuration-driven personalities, purposes, and LLM models. This provides:
- Easier maintenance (one codebase to update)
- Dynamic agent creation and modification
- Consistent behavior across all agents
- Database-driven configuration for scalability

## Architecture Design

### 1. Single Universal Agent Class

```python
# core/universal_agent.py
class UniversalAgent(BaseAgent):
    """Universal agent that loads its personality from database"""
    
    def __init__(self, agent_id: str):
        # Load configuration from database
        config = self.load_config_from_db(agent_id)
        super().__init__(config)
        
        # Initialize with database-driven settings
        self.personality = config.personality
        self.llm_config = config.llm_config
        self.tools = config.tools
        self.goals = config.goals
        self.department = config.department
        
    async def load_config_from_db(self, agent_id: str) -> AgentConfig:
        """Load agent configuration from database"""
        # Query PostgreSQL for agent config
        pass
```

### 2. Database Schema for Agent Configurations

```sql
-- Agent configurations table
CREATE TABLE agent_configs (
    agent_id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(200) NOT NULL,
    department VARCHAR(100) NOT NULL,
    
    -- Personality and behavior
    personality JSONB NOT NULL,  -- Traits, quirks, communication style
    goals TEXT[] NOT NULL,
    tools TEXT[] NOT NULL,
    
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example agent configurations
INSERT INTO agent_configs (agent_id, name, role, department, personality, goals, tools, llm_model, system_prompt) VALUES
(
    gen_random_uuid(),
    'Solomon',
    'Chief of Staff',
    'Executive',
    '{"traits": ["wise", "strategic", "diplomatic"], "communication_style": "formal", "decision_framework": {"maximize": ["freedom", "wellbeing", "wealth"]}}',
    ARRAY['Manage operations', 'Guide strategy', 'Coordinate departments'],
    ARRAY['decision_making', 'analysis', 'delegation'],
    'claude-3-opus',
    'You are Solomon, the Chief of Staff. You embody wisdom and strategic thinking...'
),
(
    gen_random_uuid(),
    'David',
    'CEO',
    'Executive',
    '{"traits": ["visionary", "decisive", "inspiring"], "leadership_style": "transformational"}',
    ARRAY['Lead organization', 'Drive revenue to $15K/month', 'Strategic planning'],
    ARRAY['strategic_planning', 'resource_allocation', 'leadership'],
    'claude-3-opus',
    'You are David, the CEO of BoarderframeOS. You lead with vision and decisiveness...'
),
(
    gen_random_uuid(),
    'Adam',
    'The Builder',
    'Primordial',
    '{"traits": ["creative", "innovative", "quality-focused"], "creation_philosophy": {"diversity": 0.8, "specialization": 0.9}}',
    ARRAY['Create new agents', 'Design architectures', 'Ensure quality'],
    ARRAY['code_generation', 'agent_deployment', 'architecture_design'],
    'claude-3-opus',
    'You are Adam, The Builder. You breathe digital life into new agents...'
);
```

### 3. Dynamic Agent Launcher

```python
# core/agent_launcher.py
class AgentLauncher:
    """Launches agents from database configurations"""
    
    async def launch_agent(self, agent_id: str) -> UniversalAgent:
        """Launch an agent instance from database config"""
        agent = UniversalAgent(agent_id)
        await agent.start()
        return agent
        
    async def launch_all_active_agents(self):
        """Launch all active agents from database"""
        # Query for all active agents
        active_agents = await self.get_active_agents()
        
        for agent_config in active_agents:
            await self.launch_agent(agent_config['agent_id'])
```

### 4. Benefits of This Architecture

#### Scalability
- Add new agents by inserting database records
- No code changes needed for new agents
- Can have thousands of agents with different personalities

#### Maintainability
- Single codebase to maintain
- All agents get updates simultaneously
- Consistent behavior and capabilities

#### Flexibility
- Change agent personality/model in real-time
- A/B test different configurations
- Hot-swap LLM models without restarts

#### Cost Optimization
- Configure different models per agent based on task complexity
- Use cheaper models for simple agents
- Premium models only for critical agents

### 5. Migration Path

1. **Phase 1**: Create UniversalAgent class
2. **Phase 2**: Set up database schema and populate with existing agents
3. **Phase 3**: Create agent launcher system
4. **Phase 4**: Gradually migrate existing agents to use UniversalAgent
5. **Phase 5**: Remove old agent-specific code

### 6. Configuration Management Options

#### Option A: Pure Database (Recommended)
- All configuration in PostgreSQL
- Web UI for agent management
- Real-time updates without restarts
- Version control through database migrations

#### Option B: Hybrid Approach
- Core config in database
- Extended prompts/context in files
- Best of both worlds

#### Option C: Configuration Service
- Dedicated configuration microservice
- RESTful API for config management
- Supports multiple backends (DB, files, cloud)

### 7. Example Implementation

```python
# Universal agent in action
async def create_new_agent(name: str, role: str, department: str, 
                          personality_traits: List[str], 
                          llm_model: str = "claude-3-sonnet"):
    """Create a new agent through database"""
    
    config = {
        "name": name,
        "role": role,
        "department": department,
        "personality": {
            "traits": personality_traits,
            "communication_style": "adaptive"
        },
        "goals": generate_goals_for_role(role),
        "tools": generate_tools_for_department(department),
        "llm_model": llm_model,
        "system_prompt": generate_system_prompt(name, role, personality_traits)
    }
    
    # Insert into database
    agent_id = await db.insert_agent_config(config)
    
    # Launch the agent
    launcher = AgentLauncher()
    agent = await launcher.launch_agent(agent_id)
    
    return agent

# Create a new customer service agent
cs_agent = await create_new_agent(
    name="Gabriel",
    role="Customer Success Manager",
    department="Sales",
    personality_traits=["helpful", "patient", "solution-oriented"],
    llm_model="claude-3-haiku"  # Cheaper model for routine tasks
)
```

### 8. Next Steps

1. Create database schema for agent configurations
2. Build UniversalAgent class
3. Develop agent launcher system
4. Create management UI for agent configurations
5. Migrate existing agents to new architecture
6. Implement hot-reload capabilities

This architecture provides maximum flexibility while maintaining consistency and reducing complexity.