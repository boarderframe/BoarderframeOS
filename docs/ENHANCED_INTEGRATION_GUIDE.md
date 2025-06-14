# BoarderframeOS Enhanced Integration Guide

This guide demonstrates how to use the new enhanced frameworks while maintaining full compatibility with existing BoarderframeOS components.

## Table of Contents
1. [Overview](#overview)
2. [Enhanced Agent Framework](#enhanced-agent-framework)
3. [LangGraph Workflows](#langgraph-workflows)
4. [CrewAI-Style Teams](#crewai-style-teams)
5. [Modern UI Integration](#modern-ui-integration)
6. [Voice Capabilities](#voice-capabilities)
7. [Migration Strategy](#migration-strategy)

## Overview

The enhanced BoarderframeOS maintains 100% backward compatibility while adding:
- **LangChain** integration for advanced reasoning
- **LangGraph** for stateful workflows
- **CrewAI** patterns for team collaboration
- **React + FastAPI** modern UI option
- **Voice integration** with Whisper and TTS
- **Enhanced orchestration** with Kubernetes support

## Enhanced Agent Framework

### Creating an Enhanced Agent

```python
from core.enhanced_agent_base import EnhancedAgentConfig, create_enhanced_agent

# Create an enhanced agent with LangChain
agent = create_enhanced_agent(
    name="market_analyst",
    role="Market Intelligence Specialist",
    goals=[
        "Analyze market trends",
        "Provide competitive intelligence",
        "Generate revenue insights"
    ],
    # Enhanced features
    use_langchain=True,
    enable_reasoning_chain=True,
    enable_self_reflection=True,
    team_role="specialist",
    skills=["analytics", "research", "forecasting"]
)
```

### Backward Compatible Usage

Existing agents continue to work without modification:

```python
from core.base_agent import BaseAgent, AgentConfig

# Traditional agent still works
config = AgentConfig(
    name="legacy_agent",
    role="Traditional Agent",
    goals=["Maintain compatibility"]
)
agent = BaseAgent(config)
```

## LangGraph Workflows

### Define a Workflow

```python
from core.agent_workflows import WorkflowConfig, workflow_orchestrator

# Create a customer onboarding workflow
config = WorkflowConfig(
    name="enhanced_onboarding",
    description="AI-powered customer onboarding",
    agents=["solomon", "david", "support_agent"],
    steps=[
        {
            "name": "gather_requirements",
            "type": "analyze",
            "description": "Understand customer needs"
        },
        {
            "name": "create_proposal",
            "type": "plan",
            "description": "Design solution"
        },
        {
            "name": "setup_services",
            "type": "execute",
            "description": "Implement solution"
        },
        {
            "name": "quality_check",
            "type": "review",
            "description": "Verify everything works",
            "conditions": [
                {"result": "success", "next_step": "complete"},
                {"result": "issues", "next_step": "remediate"}
            ]
        }
    ]
)

# Create and run workflow
workflow = workflow_orchestrator.create_workflow(config)
result = await workflow_orchestrator.run_workflow(
    workflow.workflow_id,
    {"customer_id": "12345", "package": "enterprise"},
    "solomon"  # Starting agent
)
```

### Using Pre-defined Templates

```python
from core.agent_workflows import WORKFLOW_TEMPLATES

# Use agent creation template
workflow = workflow_orchestrator.create_workflow(
    WORKFLOW_TEMPLATES["agent_creation"]
)

await workflow_orchestrator.run_workflow(
    workflow.workflow_id,
    {
        "agent_type": "customer_support",
        "department": "operations",
        "capabilities": ["chat", "ticket_handling"]
    },
    "adam"  # Adam creates agents
)
```

## CrewAI-Style Teams

### Dynamic Team Formation

```python
from core.agent_teams import team_formation, TeamRole

# Register available agents
team_formation.register_agent("analyst_1", ["data_analysis", "reporting"])
team_formation.register_agent("developer_1", ["python", "api_development"])
team_formation.register_agent("designer_1", ["ui_design", "user_research"])

# Form a product team
team = await team_formation.form_team(
    goal="Develop customer analytics dashboard",
    required_skills=["data_analysis", "python", "ui_design"],
    team_size=5
)

# Assign tasks to team
task_id = await team.assign_task(
    "Design dashboard mockups",
    requirements=["ui_design", "user_research"],
    priority=MessagePriority.HIGH
)

# Collaborate on tasks
collaborators = await team.collaborate_on_task(
    task_id,
    requesting_member="developer_1",
    required_skills=["data_analysis"]
)
```

### Team Templates

```python
from core.agent_teams import TEAM_TEMPLATES

# Use revenue optimization template
team = await team_formation.form_team(
    **TEAM_TEMPLATES["revenue_optimization"]
)
```

## Modern UI Integration

### Starting the Modern Stack

```bash
# Start FastAPI backend
python api/modern_api.py

# Start React frontend (in another terminal)
cd ui/modern
npm install
npm run dev
```

### Using the Modern API

```python
import httpx

# REST API
async with httpx.AsyncClient() as client:
    # Get agents
    response = await client.get("http://localhost:8890/api/v1/agents")
    agents = response.json()

    # Create task
    response = await client.post(
        "http://localhost:8890/api/v1/tasks",
        json={
            "description": "Analyze Q4 revenue",
            "agent_id": "solomon",
            "priority": "high"
        }
    )
```

### GraphQL Queries

```graphql
# Query agents and teams
query SystemStatus {
  agents {
    id
    name
    status
    currentTasks
    performanceMetrics
  }

  teams {
    id
    name
    goal
    members {
      name
      role
    }
    health
  }
}

# Start a workflow
mutation StartWorkflow {
  startWorkflow(
    workflowType: "customer_onboarding",
    context: {customerId: "123"},
    startingAgent: "solomon"
  ) {
    id
    status
    currentStep
  }
}
```

### WebSocket Real-time Updates

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8890/ws/client123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};

// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  topics: ['agent_status', 'task_updates']
}));
```

## Voice Capabilities

### Initialize Voice Integration

```python
from core.voice_integration import VoiceConfig, initialize_voice, TTSProvider

# Configure voice
config = VoiceConfig(
    whisper_model="base",
    tts_provider=TTSProvider.ELEVENLABS,
    enable_wake_word=True,
    wake_word="hey boarderframe"
)

voice = initialize_voice(config)
```

### Process Voice Commands

```python
# Process audio file
result = await voice.process_voice_command(audio_bytes)

print(f"Transcription: {result['transcription']}")
print(f"Response: {result['response_text']}")

# Play audio response if available
if result.get('response_audio'):
    audio_data = base64.b64decode(result['response_audio'])
    # Play audio...
```

### Voice-Enabled Agents

```python
# Enhanced agent with voice
class VoiceEnabledAgent(EnhancedBaseAgent):
    async def handle_voice_command(self, command):
        # Process voice command
        response = await self.think({"voice_command": command})

        # Synthesize response
        audio = await voice_integration.synthesize_speech(
            response,
            self.voice_profile
        )

        return {
            "text": response,
            "audio": audio
        }
```

## Migration Strategy

### Phase 1: Add Enhanced Components (No Breaking Changes)

```python
# Existing agents continue to work
existing_agent = Solomon(config)  # Still works

# New agents use enhanced features
enhanced_agent = EnhancedSolomon(enhanced_config)  # New capabilities
```

### Phase 2: Gradual Enhancement

```python
# Enhance existing agents one by one
class Solomon(EnhancedBaseAgent):  # Changed base class
    def __init__(self, config):
        # Convert to enhanced config if needed
        if not isinstance(config, EnhancedAgentConfig):
            config = EnhancedAgentConfig(**config.__dict__)
        super().__init__(config)

        # Rest of implementation stays the same
```

### Phase 3: Modern UI Adoption

```javascript
// Use new React components alongside existing UI
import { AgentDashboard } from '@/components/AgentDashboard';
import { TeamManager } from '@/components/TeamManager';
import { WorkflowDesigner } from '@/components/WorkflowDesigner';

// Embed in existing pages or use standalone
```

### Phase 4: Full Integration

1. All agents using enhanced framework
2. Complex workflows managed by LangGraph
3. Teams dynamically formed for tasks
4. Voice commands integrated throughout
5. Modern UI as primary interface
6. Legacy UI available for compatibility

## Best Practices

### 1. Incremental Adoption
- Start with one enhanced agent
- Test thoroughly before expanding
- Keep legacy systems running in parallel

### 2. Feature Flags
```python
if config.use_enhanced_features:
    agent = EnhancedAgent(config)
else:
    agent = BaseAgent(config)
```

### 3. Monitoring
```python
# Track enhanced vs legacy performance
metrics = {
    "enhanced_agents": enhanced_count,
    "legacy_agents": legacy_count,
    "langchain_success_rate": langchain_metrics,
    "team_efficiency": team_metrics
}
```

### 4. Graceful Degradation
```python
try:
    # Try enhanced features
    result = await enhanced_agent.langchain_think(context)
except Exception:
    # Fall back to basic reasoning
    result = await enhanced_agent.basic_think(context)
```

## Example: Complete Enhanced System

```python
async def run_enhanced_system():
    # 1. Initialize voice
    voice = initialize_voice(VoiceConfig())

    # 2. Create enhanced agents
    solomon = create_enhanced_agent(
        name="solomon",
        role="Chief of Staff",
        goals=["Strategic planning", "Team coordination"],
        use_langchain=True,
        team_role=TeamRole.MANAGER
    )

    # 3. Form a team
    team = await team_formation.form_team(
        "Revenue optimization",
        ["analytics", "sales", "marketing"],
        5
    )

    # 4. Create workflow
    workflow = workflow_orchestrator.create_workflow(
        WORKFLOW_TEMPLATES["revenue_optimization"]
    )

    # 5. Start with voice command
    command = await voice.transcribe_audio(audio_input)

    # 6. Process through enhanced system
    if "optimize revenue" in command.text:
        await workflow_orchestrator.run_workflow(
            workflow.workflow_id,
            {"command": command.text},
            "solomon"
        )

    # 7. Monitor via modern UI
    # Access at http://localhost:3000
```

## Conclusion

The enhanced BoarderframeOS provides a smooth migration path from the current system to a state-of-the-art AI agent platform. All enhancements are additive, ensuring existing functionality continues to work while new capabilities are gradually adopted.

Key benefits:
- **No breaking changes** - Existing code continues to work
- **Gradual adoption** - Enhance at your own pace
- **Best-in-class tools** - LangChain, LangGraph, React, FastAPI
- **Production ready** - Monitoring, scaling, error handling
- **Future proof** - Modern architecture ready for growth
