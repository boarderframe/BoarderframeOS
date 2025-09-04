# Open WebUI Complete Development Environment

This is a comprehensive AI development environment featuring Open WebUI with memory capabilities, multi-agent systems, and cost-optimized local processing.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Open WebUI    │    │   LiteLLM       │    │   LM Studio     │
│   Frontend      │◄──►│   Proxy         │◄──►│   Local Models  │
│   Port 5173     │    │   Port 4000     │    │   Port 1234     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Open WebUI    │    │   Pipelines     │    │   Cloud APIs    │
│   Backend       │◄──►│   Server        │    │   GPT/Claude    │
│   Port 8080     │    │   Port 9999     │    │   /Gemini       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Qdrant        │    │   LangGraph     │
│   Vector DB     │    │   Multi-Agent   │
│   Port 6333     │    │   Port 9000     │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   MCP Servers   │
│   On-demand     │
│   via Claude    │
└─────────────────┘
```

## 🚀 Quick Start

### Development Environment
```bash
# Start all services
./start_dev_environment.sh

# Stop all services
./stop_dev_environment.sh
```

### Manual Startup (for debugging)
```bash
# 1. Start Qdrant Vector Database
docker run -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage:z qdrant/qdrant

# 2. Start LiteLLM Proxy (with environment variables)
export $(cat .env.litellm | grep -v '^#' | xargs) && litellm --config litellm_config.yaml

# 3. Start LangGraph Multi-Agent Backend
cd langgraph_backend && source langgraph_venv/bin/activate && python multi_agent_system.py

# 4. Start Pipelines Server
cd pipelines && uvicorn main:app --host 0.0.0.0 --port 9999

# 5. Start Open WebUI Backend
cd open-webui/backend && WEBUI_SECRET_KEY=secret DATA_DIR=./data python3.12 -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080

# 6. Start Open WebUI Frontend
cd open-webui && npm run dev
```

## 🧠 Memory System Configuration

### Mem0 Memory Pipeline
- **Type**: Filter Pipeline (processes all conversations)
- **Storage**: Qdrant Vector Database
- **Processing Model**: gpt-oss-20b (local, cost-free)
- **Embeddings**: OpenAI text-embedding-3-large (minimal API cost)
- **Memory Cycle**: Stores memories every 5 messages
- **Configuration**: `/pipelines/pipelines/mem0_memory_filter.py`

### Memory Features
- **Long-term conversation memory** across sessions
- **Context-aware retrieval** based on conversation relevance
- **User-specific memory storage** with unique user IDs
- **Cost optimization** using local models for processing

## 🔌 MCP (Model Context Protocol) Servers

### Overview
MCP servers extend Claude's capabilities with custom tools and integrations. They run on-demand when Claude needs them.

### Available MCP Servers
- **filesystem** (Port 8001): Full access to /Users/cosburn home directory
  - Read, write, delete, move, copy files
  - List directories and search with glob patterns
  - Get detailed file information
- **git** (Port 8002): Git repository operations (Note: Schema compatibility issues)
- **github** (Port 8003): GitHub API integration
  - Repository management, issues, pull requests
  - Requires GITHUB_TOKEN environment variable
- **puppeteer** (Port 8004): Browser automation (headless mode)
  - Web scraping, screenshots, automated testing
- **playwright** (Port 8005): Cross-browser automation (headless mode)
  - Multi-browser support, testing, screenshots
- **postgresql** (Port 8007): PostgreSQL database operations
  - SQL queries, schema management, data operations
  - Requires database connection configuration
- **fetch** (Port 8008): Web content fetching and API testing
  - HTTP/HTTPS requests, HTML to Markdown conversion

### Configuration
MCP servers are configured in `.mcp.json` at the project root. This file is committed to the repository for team sharing.

### Adding New MCP Servers
1. Create a new directory in `mcp_servers/`
2. Implement the MCP server (TypeScript or Python)
3. Add configuration to `.mcp.json`
4. Run `./start_mcp_servers.sh` to build

### Usage with Claude Code
When using Claude Code in this project directory, it will automatically detect and use the configured MCP servers. You can interact with them seamlessly in the same conversation as WebUI development.

### Usage with Open WebUI
MCP servers are exposed to Open WebUI via MCPO (MCP-to-OpenAPI proxy) with each server running on its own port (8001-8008).
Each server has its own API key for authentication.
See [MCP_WEBUI_SETUP.md](MCP_WEBUI_SETUP.md) for complete configuration instructions.

## 🤖 Multi-Agent System

### LangGraph Configuration
- **Backend**: `/langgraph_backend/multi_agent_system.py`
- **Pipeline**: `/pipelines/pipelines/langgraph_stream_pipeline.py`
- **Available Agents**:
  - Multi-Agent System (general purpose)
  - Code Review Agents (specialized for development)
  - Writing Agents (content creation)

### Agent Capabilities
- **Collaborative reasoning** between multiple AI models
- **Streaming responses** with real-time updates
- **Tool integration** for enhanced functionality
- **Cost optimization** using LiteLLM proxy

## 💰 Cost Optimization

### Local Processing
- **Primary Model**: gpt-oss-20b via LM Studio (free)
- **Memory Processing**: Local model for all memory operations
- **Tagging**: Local model for conversation tagging
- **Title Generation**: Local model for chat titles

### API Usage (Minimal)
- **Embeddings**: OpenAI text-embedding-3-large (small cost)
- **Cloud Models**: Only when explicitly selected by user
- **Estimated Cost**: <$1/month for typical usage

## 🔧 Configuration

### API Keys (.env.litellm)
```bash
# Environment file contains all API keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
XAI_API_KEY=xai-...
```

### LiteLLM Models (litellm_config.yaml)
```yaml
# Local Models
- model_name: gpt-oss-20b
  litellm_params:
    model: gpt-oss-20b
    api_base: http://localhost:1234/v1
    api_key: lm-studio

# Cloud Models
- model_name: gpt-5
- model_name: claude-sonnet-4
- model_name: gemini-2-5-pro

# Embedding Models
- model_name: text-embedding-3-large
```

### Open WebUI Settings
1. **OpenAI API Configuration**:
   - API Base URL: `http://localhost:4000`
   - API Key: `litellm-master-key-2024`

2. **Pipeline Configuration**:
   - Pipeline URL: `http://localhost:9999`
   - Enable Pipelines: ON

3. **Task Model Configuration**:
   - Task Model: `gpt-oss-20b`
   - Task Model External: `gpt-oss-20b`
   - Enable Tags Generation: ON
   - Enable Title Generation: ON

## 📁 Project Structure

```
/Users/cosburn/open_webui/
├── open-webui/                 # Main Open WebUI application
│   ├── backend/               # Python backend
│   └── frontend/              # Svelte frontend
├── pipelines/                 # Pipeline server and filters
│   ├── main.py               # Pipeline server
│   └── pipelines/            # Individual pipeline modules
│       ├── mem0_memory_filter.py
│       └── langgraph_stream_pipeline.py
├── langgraph_backend/         # Multi-agent system
│   ├── multi_agent_system.py # Main LangGraph application
│   └── langgraph_venv/       # Virtual environment
├── mcp_servers/               # MCP servers
│   └── filesystem/           # Filesystem MCP server
│       ├── src/             # TypeScript source
│       ├── dist/            # Compiled JavaScript
│       └── package.json     # Dependencies
├── .mcp.json                 # MCP configuration
├── litellm_config.yaml       # LiteLLM configuration
├── start_dev_environment.sh  # Development startup script
├── start_mcp_servers.sh     # MCP preparation script
├── stop_dev_environment.sh   # Development stop script
└── CLAUDE.md                 # This documentation
```

## 🛠️ Development Commands

### Service Status
```bash
# Check all ports
lsof -i :6333,4000,9000,9999,8080,5173

# View logs
tail -f logs/qdrant.log
tail -f logs/litellm.log
tail -f logs/langgraph.log
tail -f logs/pipelines.log
tail -f logs/webui-backend.log
tail -f logs/webui-frontend.log
```

### Common Tasks
```bash
# Restart just the pipelines server
kill $(cat pids/pipelines.pid)
cd pipelines && uvicorn main:app --host 0.0.0.0 --port 9999 &

# Update memory pipeline configuration
# Edit: pipelines/pipelines/mem0_memory_filter.py
# Then restart pipelines server

# Test LiteLLM proxy
curl -H "Authorization: Bearer litellm-master-key-2024" http://localhost:4000/v1/models

# Test pipeline server
curl http://localhost:9999

# Test LangGraph backend
curl -X POST http://localhost:9000/stream -H "Content-Type: application/json" -d '{"test": true}'
```

## 🔍 Troubleshooting

### Common Issues

1. **Models not showing in Open WebUI**:
   - Check LiteLLM proxy is running on port 4000
   - Verify OpenAI API settings in Open WebUI admin panel
   - Ensure API key is `litellm-master-key-2024`

2. **Cloud models (GPT-5, Claude) not working**:
   - Verify `.env.litellm` file exists with proper API keys
   - Check LiteLLM logs: `tail -f logs/litellm.log`
   - Restart LiteLLM with environment: `export $(cat .env.litellm | grep -v '^#' | xargs) && litellm --config litellm_config.yaml`

3. **Memory system not working**:
   - Check Qdrant is running on port 6333
   - Verify pipelines server is running on port 9999
   - Check pipeline configuration in Open WebUI admin panel

4. **LangGraph agents not available**:
   - Ensure LangGraph backend is running on port 9000
   - Check LangGraph pipeline is loaded in pipelines server
   - Verify virtual environment dependencies

5. **Backend startup issues**:
   - Use Python 3.12 for compatibility
   - Install requirements: `pip install -r open-webui/backend/requirements.txt`
   - Check environment variables are set correctly

6. **Authentication errors in LiteLLM**:
   - Ensure `.env.litellm` contains valid API keys
   - Check API key format: OpenAI keys start with `sk-`
   - Verify API quotas and billing status

### Log Locations
- **Service Logs**: `/Users/cosburn/open_webui/logs/`
- **Process IDs**: `/Users/cosburn/open_webui/pids/`
- **Qdrant Data**: Docker volume `qdrant_storage`
- **Open WebUI Data**: `open-webui/backend/data/`

## 📊 Performance Monitoring

### Resource Usage
- **Memory**: ~4GB for all services
- **CPU**: Moderate usage, spikes during AI processing
- **Storage**: Vector embeddings in Qdrant, conversation data in SQLite
- **Network**: Local traffic only, minimal external API calls

### Optimization Tips
- Use local gpt-oss-20b for all auxiliary tasks (tagging, titles)
- Enable memory system for conversation continuity
- Monitor LiteLLM proxy logs for API usage patterns
- Regularly check Qdrant storage size

## 🚦 Service Dependencies

**Startup Order** (handled automatically by start_dev_environment.sh):
1. Qdrant Vector Database
2. LiteLLM Proxy Server  
3. LangGraph Multi-Agent Backend
4. Open WebUI Pipelines Server
5. Open WebUI Backend
6. Open WebUI Frontend

**Critical Dependencies**:
- LM Studio must be running with gpt-oss-20b model
- Docker must be available for Qdrant
- Python 3.12 for Open WebUI backend compatibility
- Node.js for Open WebUI frontend

## 📝 Notes for Development

- All services run in background for development
- Logs are preserved across restarts
- PID files track running processes
- Scripts handle graceful startup/shutdown
- Port conflicts are automatically detected
- Services can be started individually for debugging

## 🔮 Future Enhancements

- [ ] Add health check endpoints for all services
- [ ] Implement service auto-restart on failure
- [ ] Add configuration validation
- [ ] Create Docker Compose alternative
- [ ] Add performance metrics dashboard
- [ ] Implement backup/restore for Qdrant data