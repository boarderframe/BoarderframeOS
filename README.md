# BoarderframeOS - AI-Powered Agentic Company Platform

BoarderframeOS is an AI-powered platform for building autonomous AI agents that work together as a virtual company. Built on Open WebUI with enhanced memory capabilities, multi-agent systems, and cost-optimized processing.

**Version:** 0.1.0  
**Repository:** https://github.com/boarderframe/BoarderframeOS

## 🚀 Quick Start

```bash
# Start the complete development environment
./start_dev_environment.sh

# Check service status
./check_services.sh

# Stop all services
./stop_dev_environment.sh
```

## 🌐 Access Points

- **Open WebUI**: http://localhost:5173
- **LiteLLM Proxy**: http://localhost:4000
- **Pipelines Server**: http://localhost:9999
- **LangGraph Backend**: http://localhost:9000

## 📜 Available Scripts

| Script | Purpose | Usage |
|--------|---------|--------|
| `start_dev_environment.sh` | Start all services in background | `./start_dev_environment.sh` |
| `stop_dev_environment.sh` | Stop all services gracefully | `./stop_dev_environment.sh` |
| `check_services.sh` | Check status of all services | `./check_services.sh` |

## 🛠️ Development Features

### ✅ Multi-Agent System  
- **LangGraph integration** with multiple specialized agents
- **Real-time streaming** responses
- **Cost-optimized** via LiteLLM proxy

### ✅ Local Processing
- **Primary model**: gpt-oss-20b via LM Studio
- **Memory processing**: Local model (free)
- **Tagging & titles**: Local model (free)
- **Minimal API costs**: Only for embeddings

### ✅ Model Management
- **Unified access** to local and cloud models
- **Automatic routing** via LiteLLM
- **Hot-swappable** model configurations

## 📁 Key Files

- `CLAUDE.md` - Complete documentation and architecture
- `litellm_config.yaml` - Model configuration
- `langgraph_backend/multi_agent_system.py` - Multi-agent backend

## 🔧 Configuration

### First-Time Setup in Open WebUI:
1. **Models**: Configure LiteLLM connection
   - API Base URL: `http://localhost:4000`
   - API Key: `litellm-master-key-2024`

2. **Pipelines**: Enable pipeline server
   - Pipeline URL: `http://localhost:9999`

3. **Task Models**: Set local model for auxiliary tasks
   - Task Model: `gpt-oss-20b`

## 🚦 Service Architecture

```
Frontend (5173) → Backend (8080) → LiteLLM (4000) → Models
     ↓               ↓                              
Pipelines (9999)                                   
     ↓                                             
LangGraph (9000)                                   
```

## 📊 Resource Usage

- **Memory**: ~4GB total
- **Cost**: <$1/month (mostly local processing)
- **Performance**: Optimized for development

## 📝 Development Notes

- All services run in background during development
- Logs are preserved in `logs/` directory
- Process IDs tracked in `pids/` directory
- Graceful startup/shutdown with dependency management
- Port conflict detection and resolution

For detailed information, see `CLAUDE.md`.