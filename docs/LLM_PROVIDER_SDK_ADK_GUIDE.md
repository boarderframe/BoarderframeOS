# LLM Provider SDK & Agent Development Kit (ADK) Guide

## Overview

BoarderframeOS now includes a comprehensive **LLM Provider SDK** and **Agent Development Kit (ADK)** that provides:

- **40+ Language Models** from 8+ providers (Anthropic, OpenAI, Google, Groq, Ollama, etc.)
- **LangChain Integration** for advanced agent capabilities
- **Template-Based Agent Creation** with pre-built patterns
- **Swarm Orchestration** for multi-agent collaboration
- **Intelligent Model Routing** based on task requirements
- **Cost Optimization** with real-time pricing calculations

## LLM Provider SDK

### Supported Providers

| Provider | Models | Key Features | Cost |
|----------|--------|--------------|------|
| **Anthropic** | Claude 4 Opus, Sonnet, Haiku | Best reasoning, 200K context | $0.015-$0.075/1K |
| **OpenAI** | GPT-4o, GPT-4-turbo, GPT-4o-mini | Vision, function calling | $0.00015-$0.03/1K |
| **Google** | Gemini 1.5 Pro/Flash | 2M token context! | $0.00035-$0.0105/1K |
| **Groq** | Llama 3.3 70B, Mixtral | Ultra-fast (150-200ms) | $0.00024-$0.00079/1K |
| **Ollama** | Llama 3.2, Mistral, DeepSeek | Local, private, free | $0 |
| **Perplexity** | Sonar models | Internet-connected | $0.001/1K |
| **Cohere** | Command models | Enterprise focused | Varies |
| **Hugging Face** | Open models | Community models | Varies |

### Model Capabilities

```python
from core.llm_provider_sdk import ModelCapability

# Available capabilities
CHAT                # General conversation
CODE_GENERATION     # Writing code
EMBEDDINGS         # Text similarity
VISION             # Image understanding
FUNCTION_CALLING   # Tool use
STREAMING          # Real-time responses
LONG_CONTEXT       # 100K+ tokens
REASONING          # Complex logic
CREATIVE_WRITING   # Creative content
```

### SDK Usage Examples

#### 1. Basic Model Information

```python
from core.llm_provider_sdk import get_llm_sdk

sdk = get_llm_sdk()

# List all providers
providers = sdk.list_providers()
# ['anthropic', 'openai', 'google', 'groq', 'ollama', ...]

# Get specific model info
model = sdk.get_model_info("anthropic", "claude-opus-4-20250514")
print(f"Quality: {model.quality_score}")
print(f"Context: {model.context_window} tokens")
print(f"Cost: ${model.cost_per_1k_input}/1K input")
```

#### 2. Find Best Model for Task

```python
# Get best coding model under $0.01/1K tokens
model = sdk.registry.get_best_model_for_task(
    task_type="coding",
    max_cost_per_1k=0.01,
    max_latency_ms=2000,
    min_quality=0.85
)
# Returns: groq/llama-3.3-70b-versatile (fast & affordable)
```

#### 3. Create Optimized LangChain Model

```python
# Create model with automatic selection
chat_model = await sdk.create_optimized_chain(
    task_type="reasoning",
    required_capabilities=[ModelCapability.REASONING, ModelCapability.LONG_CONTEXT],
    constraints={
        "max_cost_per_1k": 0.05,
        "quality_weight": 0.8,  # Prioritize quality
        "speed_weight": 0.2
    },
    temperature=0.3
)

# Use with LangChain
response = await chat_model.ainvoke("Explain quantum computing")
```

#### 4. Cost Estimation

```python
# Estimate cost for a request
cost = sdk.estimate_cost(
    provider="openai",
    model_name="gpt-4o",
    input_tokens=5000,
    output_tokens=2000
)
print(f"Estimated cost: ${cost:.4f}")
# Output: Estimated cost: $0.0550
```

## Agent Development Kit (ADK)

### Pre-built Agent Templates

| Template | Purpose | Tier | Key Traits |
|----------|---------|------|------------|
| **EXECUTIVE** | High-level strategy & decisions | Executive | Leadership, strategic thinking |
| **DEPARTMENT_HEAD** | Department management | Department | Organization, delegation |
| **SPECIALIST** | Domain expertise | Specialist | Deep knowledge, problem-solving |
| **WORKER** | Task execution | Worker | Efficiency, reliability |
| **RESEARCHER** | Information gathering | Specialist | Curiosity, thoroughness |
| **CODER** | Software development | Specialist | Technical, detail-oriented |
| **ANALYST** | Data analysis | Specialist | Analytical, objective |
| **CREATIVE** | Content creation | Specialist | Creativity, innovation |
| **COORDINATOR** | Workflow management | Department | Communication, organization |
| **MONITOR** | System monitoring | Worker | Vigilance, reporting |

### Creating Agents with ADK

#### 1. From Template

```python
from core.agent_development_kit import get_adk, AgentTemplate, ModelTier

adk = get_adk()

# Create a research agent
researcher = await adk.create_agent_from_template(
    name="market_researcher",
    template=AgentTemplate.RESEARCHER,
    department="Strategy",
    goals=[
        "Research market trends",
        "Analyze competitor strategies",
        "Identify growth opportunities"
    ],
    tier=ModelTier.SPECIALIST
)
```

#### 2. Custom Agent Blueprint

```python
from core.agent_development_kit import AgentBlueprint, ModelCapability

blueprint = AgentBlueprint(
    name="data_scientist",
    role="Senior Data Scientist",
    template=AgentTemplate.ANALYST,
    department="Analytics",
    tier=ModelTier.SPECIALIST,
    goals=[
        "Analyze complex datasets",
        "Build predictive models",
        "Generate insights"
    ],
    tools=["mcp_database", "mcp_analytics"],
    capabilities=[
        ModelCapability.REASONING,
        ModelCapability.CODE_GENERATION
    ],
    personality_traits={
        "analytical": 0.95,
        "creativity": 0.7,
        "communication": 0.8
    },
    knowledge_domains=["statistics", "machine_learning", "data_viz"],
    autonomy_level=0.85
)

agent = await adk.create_custom_agent(blueprint)
```

### Agent Swarms

#### 1. Sequential Swarm (Chain)

```python
# Create agents
pm = await adk.create_agent_from_template("pm", AgentTemplate.COORDINATOR, "Management")
researcher = await adk.create_agent_from_template("researcher", AgentTemplate.RESEARCHER, "Strategy")
developer = await adk.create_agent_from_template("developer", AgentTemplate.CODER, "Engineering")

# Create sequential swarm
adk.create_swarm(
    "project_pipeline",
    agents=["pm", "researcher", "developer"],
    pattern="sequential"
)

# Execute task through swarm
result = await adk.execute_swarm_task(
    "project_pipeline",
    {"task": "Build new feature based on market research"}
)
```

#### 2. Parallel Swarm

```python
# Multiple agents work concurrently
adk.create_swarm(
    "analysis_team",
    agents=["analyst1", "analyst2", "analyst3"],
    pattern="parallel"
)
```

#### 3. Hierarchical Swarm

```python
# Tree structure with delegation
adk.create_swarm(
    "department_hierarchy",
    agents=["ceo", "cto", "dev1", "dev2", "qa"],
    pattern="hierarchical"
)
```

### Enhanced Agent Features

#### 1. Skill Registration

```python
# Add custom skills to agents
async def market_analysis_skill(agent, market_data):
    """Custom market analysis skill"""
    # Perform analysis
    return insights

researcher.register_skill("market_analysis", market_analysis_skill)

# Execute skill
insights = await researcher.execute_skill("market_analysis", market_data)
```

#### 2. LangGraph Workflows

```python
# Agents have built-in LangGraph workflows
state = AgentState(
    messages=[],
    context={"project": "Q4 Planning"},
    current_task="Generate quarterly roadmap",
    next_agent=None,
    results={}
)

# Execute workflow
result = await agent.workflow.ainvoke(state)
```

## Web Interface Features

### Enhanced Agent Cortex Panel

Access at: **http://localhost:8890**

#### 1. SDK Providers View
- Browse all 40+ models with detailed specs
- See capabilities, costs, and performance metrics
- Filter by provider or capability

#### 2. Model Explorer
- Find models by capability (vision, coding, etc.)
- Compare quality scores and pricing
- Test model connections

#### 3. AI Recommendations
- Input your task requirements
- Get best model recommendation
- Consider cost, quality, and speed constraints

#### 4. Agent Factory
- Create agents from templates
- Configure goals and departments
- Assign optimal LLMs automatically

#### 5. Swarm Builder
- Visual swarm creation
- Drag-and-drop agent selection
- Preview collaboration patterns

#### 6. Cost Calculator
- Real-time cost estimation
- Compare providers
- Budget planning tools

## Best Practices

### 1. Model Selection

```python
# For high-stakes decisions
executive_model = "anthropic/claude-opus-4-20250514"

# For fast, efficient tasks
worker_model = "groq/mixtral-8x7b-32768"

# For local/private data
local_model = "ollama/llama3.2"

# For internet research
search_model = "perplexity/llama-3.1-sonar-large-128k-online"
```

### 2. Cost Optimization

```python
# Use tiered approach
if task.complexity == "high":
    model = "claude-opus-4"
elif task.requires_speed:
    model = "groq/llama-3.3-70b"
else:
    model = "gpt-4o-mini"
```

### 3. Agent Collaboration

```python
# Specialized teams
research_team = ["market_analyst", "competitor_analyst", "trend_spotter"]
dev_team = ["architect", "backend_dev", "frontend_dev", "qa"]

# Cross-functional swarms
product_swarm = research_team + ["product_manager"] + dev_team
```

## Integration Examples

### 1. With Existing BoarderframeOS Agents

```python
# Enhance existing David agent
david_config = {
    "provider": "anthropic",
    "model": "claude-opus-4-20250514",
    "temperature": 0.7,
    "max_tokens": 4000
}

await panel._update_agent_llm("david", david_config)
```

### 2. With Message Bus

```python
# Agents automatically integrate with message bus
from core.message_bus import send_task_request

await send_task_request(
    from_agent="coordinator",
    to_agent="researcher",
    task={"type": "research", "topic": "AI market trends"}
)
```

### 3. With MCP Tools

```python
# Tools are automatically converted to LangChain format
agent = await adk.create_agent_from_template(
    name="file_manager",
    template=AgentTemplate.WORKER,
    department="Operations",
    tools=["mcp_filesystem", "mcp_database"]
)
```

## Troubleshooting

### Common Issues

1. **LangChain not installed**
   ```bash
   pip install -r requirements.txt
   ```

2. **API keys not set**
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   export OPENAI_API_KEY="your-key"
   export GOOGLE_API_KEY="your-key"
   export GROQ_API_KEY="your-key"
   ```

3. **Model not available**
   - Check provider status in SDK Providers view
   - Verify API key is valid
   - Try alternative model

4. **High costs**
   - Use Model Recommendations for budget options
   - Consider Groq for ultra-fast, affordable inference
   - Use Ollama for free local models

## Future Enhancements

- **Fine-tuning Integration** - Custom models for specific domains
- **Model A/B Testing** - Automatic performance comparison
- **Advanced Swarm Patterns** - Dynamic, self-organizing swarms
- **Visual Workflow Builder** - Drag-and-drop agent workflows
- **Model Marketplace** - Share and discover custom agents
- **Performance Analytics** - Detailed agent/model metrics

## Conclusion

The LLM Provider SDK and Agent Development Kit transform BoarderframeOS into a comprehensive platform for building sophisticated AI agent systems. With support for 40+ models, template-based agent creation, and advanced swarm orchestration, you can build anything from simple chatbots to complex multi-agent enterprises.

For questions or support, consult the main BoarderframeOS documentation or explore the enhanced Agent Cortex Panel at http://localhost:8890.