# Agent Cortex Management Panel

## Overview

The Agent Cortex Management Panel is a comprehensive web interface for managing all LLM (Large Language Model) configurations in BoarderframeOS. It provides centralized control over:

- **LLM Provider Management** - Configure cloud and local providers (Anthropic, OpenAI, Ollama, Local)
- **Individual Agent LLM Assignment** - Assign specific models to each agent with custom settings
- **Tier-based Defaults** - Set default models for Executive, Department, Specialist, and Worker tiers
- **Real-time Testing** - Test LLM connections and verify configurations
- **Performance Tracking** - Monitor model usage, costs, and response times

## Quick Start

### Launch the Panel

```bash
# From the BoarderframeOS root directory
python launch_agent_cortex_panel.py
```

Then open your browser to: **http://localhost:8890**

### First Time Setup

1. **Configure LLM Providers**
   - Navigate to "LLM Providers" section
   - Add your API keys for Anthropic/OpenAI
   - Test connections to ensure they work

2. **Assign Agent LLMs**
   - Go to "Agent LLMs" section
   - Click "Configure" for each agent
   - Select provider, model, and settings

3. **Set Tier Defaults**
   - Visit "Tier Defaults" section
   - Configure default models for each tier
   - These apply to new agents automatically

## Features

### 1. Dashboard Overview
- Total agents in the system
- Active LLM providers
- Department count
- Model assignment statistics

### 2. LLM Providers
Configure multiple providers:
- **Anthropic** - Claude models (Opus, Sonnet, Haiku)
- **OpenAI** - GPT models (GPT-4o, GPT-4o-mini)
- **Ollama** - Local models (Llama, Mistral, Phi)
- **Local** - Custom inference servers

Each provider can have:
- API keys or base URLs
- Multiple models
- Active/inactive status

### 3. Agent LLM Configuration
For each agent, configure:
- **Provider** - Which LLM provider to use
- **Model** - Specific model from that provider
- **Temperature** - Creativity level (0.0-2.0)
- **Max Tokens** - Response length limit
- **Fallback Provider** - Backup if primary fails

### 4. Tier Defaults
Set defaults for agent tiers:
- **Executive** - Solomon, David (High-end models)
- **Department** - Department heads (Balanced models)
- **Specialist** - Technical experts (Efficient models)
- **Worker** - Task agents (Cost-effective models)

Each tier has:
- Default provider/model
- Budget alternative
- Local model option
- Cost and quality thresholds

### 5. Testing & Validation
- Test any provider/model combination
- Verify API keys work correctly
- Check response quality
- Monitor connection status

## Technical Details

### Architecture

The panel consists of:
- **Backend** (`ui/agent_cortex_panel.py`) - Flask server with SQLite persistence
- **Frontend** (`ui/templates/agent_cortex_panel.html`) - Modern responsive UI
- **Database** (`data/agent_cortex_panel.db`) - Configuration storage

### Database Schema

```sql
-- LLM Provider configurations
llm_providers (
    provider_name TEXT UNIQUE,
    provider_type TEXT,
    base_url TEXT,
    api_key TEXT,
    models TEXT (JSON),
    is_active BOOLEAN
)

-- Agent LLM assignments
agent_llm_assignments (
    agent_name TEXT UNIQUE,
    agent_tier TEXT,
    department TEXT,
    provider TEXT,
    model TEXT,
    temperature REAL,
    max_tokens INTEGER,
    fallback_provider TEXT,
    fallback_model TEXT
)

-- Model performance tracking
model_performance (
    agent_name TEXT,
    provider TEXT,
    model TEXT,
    request_count INTEGER,
    total_tokens INTEGER,
    total_cost REAL,
    avg_response_time REAL,
    success_rate REAL
)

-- Tier default configurations
tier_defaults (
    tier TEXT UNIQUE,
    default_provider TEXT,
    default_model TEXT,
    budget_provider TEXT,
    budget_model TEXT,
    local_provider TEXT,
    local_model TEXT,
    max_cost_per_request REAL,
    quality_threshold REAL
)
```

### Integration with BoarderframeOS

The panel integrates with:
- **Agent Cortex** (`core/agent_cortex.py`) - Intelligent model selection
- **LLM Client** (`core/llm_client.py`) - Provider implementations
- **Base Agent** (`core/base_agent.py`) - Agent framework
- **Department Structure** - Biblical organization hierarchy

### API Endpoints

- `GET /api/cortex/overview` - System statistics
- `GET /api/cortex/providers` - List all providers
- `GET /api/cortex/agents` - List all agents with LLM configs
- `PUT /api/cortex/agents/<name>/llm` - Update agent LLM
- `GET /api/cortex/tiers` - Get tier defaults
- `POST /api/cortex/test-llm` - Test LLM connection

## Configuration Examples

### High-Performance Executive Agent
```json
{
    "provider": "anthropic",
    "model": "claude-opus-4-20250514",
    "temperature": 0.3,
    "max_tokens": 4000,
    "fallback_provider": "anthropic",
    "fallback_model": "claude-4-sonnet-20250514"
}
```

### Cost-Effective Worker Agent
```json
{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 1000,
    "fallback_provider": "ollama",
    "fallback_model": "llama3.2"
}
```

### Local Development Agent
```json
{
    "provider": "ollama",
    "model": "llama3.2",
    "temperature": 0.8,
    "max_tokens": 2000
}
```

## Troubleshooting

### Panel won't start
- Check port 8890 is available: `lsof -i :8890`
- Ensure Python dependencies installed: `pip install -r requirements.txt`
- Verify BoarderframeOS path is correct

### LLM connections fail
- Verify API keys are set correctly
- Check provider URLs (especially for local models)
- Test with curl: `curl http://localhost:11434/api/tags` (for Ollama)

### Agents not showing
- Ensure department structure file exists: `departments/boarderframeos-departments.json`
- Check agent config files in `configs/agents/`
- Run integration script: `python integrate_agent_cortex_configs.py`

## Future Enhancements

- Real-time performance graphs
- Cost tracking and budgets
- A/B testing for models
- Automatic failover handling
- Model fine-tuning integration
- Batch configuration updates
- Export/import configurations

## Support

For issues or questions:
1. Check the logs in the terminal where the panel is running
2. Review the database at `data/agent_cortex_panel.db`
3. Consult the main BoarderframeOS documentation
4. Check agent configurations in `configs/agents/`
