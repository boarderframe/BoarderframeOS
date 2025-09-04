# BoarderframeOS Complete Restoration Guide

This guide will help you restore BoarderframeOS from a fresh git clone to a fully operational system.

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows with WSL2
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 20GB free space
- **CPU**: 4+ cores recommended

### Required Software
- **Git**: 2.25+
- **Node.js**: 18.x or 20.x
- **Python**: 3.11 or 3.12
- **Docker**: (Optional, for Qdrant vector database)

## Step 1: Clone the Repository

```bash
git clone https://github.com/boarderframe/BoarderframeOS.git
cd BoarderframeOS
```

## Step 2: Install Dependencies

### Backend Dependencies (Python)

```bash
# Create virtual environment for LiteLLM
python3 -m venv litellm_venv
source litellm_venv/bin/activate  # On Windows: litellm_venv\Scripts\activate
pip install litellm

# Create virtual environment for Pipelines
cd pipelines
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Create virtual environment for LangGraph
cd langgraph_backend
python3 -m venv langgraph_venv
source langgraph_venv/bin/activate  # On Windows: langgraph_venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Install Open WebUI backend dependencies
cd open-webui/backend
pip install -r requirements.txt
cd ../..
```

### Frontend Dependencies (Node.js)

```bash
cd open-webui
npm install --legacy-peer-deps
cd ..
```

### MCP Servers (Optional)

```bash
# Filesystem MCP server
cd mcp_servers/filesystem
npm install
cd ../..

# Other MCP servers as needed
```

## Step 3: Configure Environment Variables

```bash
# Copy environment examples
cp .env.example .env
cp .env.litellm.example .env.litellm

# Edit .env.litellm with your API keys:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=AIza...
```

## Step 4: Install LM Studio (for Local Models)

1. Download LM Studio from https://lmstudio.ai/
2. Install and launch LM Studio
3. Download model: `gpt-oss-20b` or similar
4. Start the local server on port 1234

## Step 5: Start Services

### Option A: Use the All-in-One Script (Recommended)

```bash
./start_dev_environment.sh
```

This will start all services in the correct order:
1. Qdrant Vector Database (if Docker is available)
2. LiteLLM Proxy Server
3. LangGraph Multi-Agent Backend
4. Pipelines Server
5. Open WebUI Backend
6. Open WebUI Frontend

### Option B: Start Services Manually

```bash
# 1. Start Qdrant (optional, requires Docker)
docker run -d -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage:z \
  --name qdrant \
  qdrant/qdrant

# 2. Start LiteLLM Proxy
source litellm_venv/bin/activate
export $(cat .env.litellm | grep -v '^#' | xargs)
litellm --config litellm_config.yaml &

# 3. Start LangGraph Backend
cd langgraph_backend
source langgraph_venv/bin/activate
python multi_agent_system.py &
cd ..

# 4. Start Pipelines Server
cd pipelines
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 9999 &
cd ..

# 5. Start Open WebUI Backend
cd open-webui/backend
WEBUI_SECRET_KEY=secret DATA_DIR=./data \
python3 -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 &
cd ../..

# 6. Start Open WebUI Frontend
cd open-webui
npm run dev &
cd ..
```

## Step 6: Initial Configuration

1. **Access Open WebUI**: http://localhost:5173
2. **Create Admin Account**: First user becomes admin
3. **Configure Models**:
   - Go to Settings → Admin → Connections
   - OpenAI API Base URL: `http://localhost:4000`
   - API Key: `litellm-master-key-2024`
4. **Enable Pipelines**:
   - Go to Settings → Admin → Pipelines
   - Pipeline URL: `http://localhost:9999`
   - Enable Pipelines: ON
5. **Set Task Models**:
   - Go to Settings → Admin → Models
   - Task Model: `gpt-oss-20b`
   - Enable Tags/Title Generation: ON

## Step 7: Verify Installation

```bash
# Check all services are running
./check_services.sh

# Or manually check ports
lsof -i :5173,6333,4000,9000,9999,8080

# Test endpoints
curl http://localhost:4000/v1/models  # LiteLLM
curl http://localhost:9999             # Pipelines
curl http://localhost:8080/api/health  # Backend
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find and kill process on port
   lsof -i :PORT
   kill -9 PID
   ```

2. **Module Not Found Errors**
   - Ensure you're in the correct virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **Frontend Won't Start**
   ```bash
   cd open-webui
   rm -rf node_modules
   npm install --legacy-peer-deps
   npm run dev
   ```

4. **Memory/Qdrant Not Working**
   - Ensure Docker is running
   - Start Qdrant container
   - Check pipelines configuration

5. **Models Not Available**
   - Verify LiteLLM is running
   - Check API keys in .env.litellm
   - Ensure LM Studio is running with model loaded

### Log Files

Check logs for debugging:
- `logs/webui-backend.log`
- `logs/litellm.log`
- `logs/pipelines.log`
- `logs/langgraph.log`

## Stopping Services

```bash
./stop_dev_environment.sh
```

## Additional Resources

- **Main Documentation**: CLAUDE.md
- **MCP Setup**: MCP_WEBUI_SETUP.md
- **Contributing**: CONTRIBUTING.md
- **Issues**: https://github.com/boarderframe/BoarderframeOS/issues

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files
3. Open an issue on GitHub with:
   - Error messages
   - Log outputs
   - Steps to reproduce

---
BoarderframeOS v0.1.0 - Built with Open WebUI