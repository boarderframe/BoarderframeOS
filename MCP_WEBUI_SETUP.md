# MCP Server Integration with Open WebUI

## 🎯 Overview
MCP (Model Context Protocol) servers are now integrated with Open WebUI through individual MCPO (MCP-to-OpenAPI proxy) instances, allowing each MCP server to run independently on its own port.

## 🚀 Quick Start

### 1. Start the Environment
```bash
./start_dev_environment.sh
```
This automatically starts:
- All Open WebUI services
- Individual MCPO proxy for each MCP server
- Each MCP server on its own dedicated port

### 2. Configure Open WebUI

#### Step 1: Access Open WebUI
Navigate to: http://localhost:5173

#### Step 2: Add MCP Tools to Open WebUI
1. Go to **Settings** (gear icon)
2. Navigate to **Admin Settings** → **Tools**
3. Click **Add Tool Server**
4. Enter the following for each MCP server:

##### Filesystem Server
- **URL**: `http://localhost:8001`
- **API Key**: `filesystem-mcp-key-2024`
- **Name**: Filesystem Tools (optional)

#### Step 3: Verify Connection
Once connected, you'll see:
- ✅ Green checkmark indicating successful connection
- 🧩 Tool icon appears below the message input box
- Available tools listed in the tool selector

## 📦 Available MCP Servers

### 1. Filesystem Server
- **URL**: `http://localhost:8001`
- **API Key**: `filesystem-mcp-key-2024`
- **Port**: 8001
- **OpenAPI Docs**: http://localhost:8001/docs

**Available Tools**:
- `read_file` - Read contents of any file
- `write_file` - Write content to files
- `list_directory` - List directory contents
- `create_directory` - Create new directories
- `delete_file` - Delete files or directories
- `move_file` - Move or rename files
- `copy_file` - Copy files
- `search_files` - Search with glob patterns
- `get_file_info` - Get detailed file information

**Access**: Full read/write access to `/Users/cosburn` home directory

### 2. Git Server
- **URL**: `http://localhost:8002`
- **API Key**: `git-mcp-key-2024`
- **Port**: 8002
- **OpenAPI Docs**: http://localhost:8002/docs

**Available Tools**:
- Git version control operations
- Repository management
- Commit, branch, and merge operations
- Git history and diff viewing

### 3. GitHub Server
- **URL**: `http://localhost:8003`
- **API Key**: `github-mcp-key-2024`
- **Port**: 8003
- **OpenAPI Docs**: http://localhost:8003/docs

**Available Tools**:
- GitHub API integration
- Repository management
- Issues and pull requests
- **Note**: Requires `GITHUB_TOKEN` environment variable

### 4. Puppeteer Server
- **URL**: `http://localhost:8004`
- **API Key**: `puppeteer-mcp-key-2024`
- **Port**: 8004
- **OpenAPI Docs**: http://localhost:8004/docs

**Available Tools**:
- Browser automation with Puppeteer
- Web scraping
- Screenshot generation
- Page interaction and testing

### 5. Playwright Server
- **URL**: `http://localhost:8005`
- **API Key**: `playwright-mcp-key-2024`
- **Port**: 8005
- **OpenAPI Docs**: http://localhost:8005/docs

**Available Tools**:
- Cross-browser automation
- Advanced testing features
- Multi-browser support (Chrome, Firefox, Safari)
- Network interception

## 🔧 Individual MCP Server Architecture

### New Architecture
Each MCP server runs with its own MCPO proxy instance:
```
Open WebUI ← HTTP/OpenAPI → Individual MCPO → MCP Server
   (5173)                    (unique port)     (stdio)

Example:
- Filesystem: Port 8001
- Memory: Port 8002 (when added)
- Time: Port 8003 (when added)
```

### Benefits
- **Independent Management**: Start/stop each server individually
- **Unique API Keys**: Each server has its own API key for security
- **Clean URLs**: Direct access without subpaths (e.g., `http://localhost:8001` not `/filesystem`)
- **Better Isolation**: Each server runs in its own process
- **Easy Debugging**: Separate logs for each server

## 🛠️ Service Management

### Individual Server Control

#### Unified Control Script
```bash
# Control all servers with one script
./mcp_control.sh [command] [server]

# Examples:
./mcp_control.sh start          # Start all MCP servers
./mcp_control.sh stop           # Stop all MCP servers
./mcp_control.sh status         # Show status of all servers
./mcp_control.sh urls           # Display all server URLs
./mcp_control.sh logs git       # Tail git server logs
```

#### Individual Server Scripts
```bash
# Each server also has its own control script
./start_mcp_filesystem.sh start|stop|restart|status
./start_mcp_git.sh start|stop|restart|status
./start_mcp_github.sh start|stop|restart|status
./start_mcp_puppeteer.sh start|stop|restart|status
./start_mcp_playwright.sh start|stop|restart|status
```

#### View Server Logs
```bash
# All server logs are in the logs/ directory
tail -f logs/mcpo-filesystem.log
tail -f logs/mcpo-git.log
tail -f logs/mcpo-github.log
tail -f logs/mcpo-puppeteer.log
tail -f logs/mcpo-playwright.log
```

### All Services Control
```bash
# Start everything
./start_dev_environment.sh

# Stop everything
./stop_dev_environment.sh
```

## 🆕 Adding New MCP Servers

### 1. Create Your MCP Server
```bash
mkdir mcp_servers/my-server
cd mcp_servers/my-server
npm init -y
# Implement your MCP server
npm run build
```

### 2. Create Startup Script
```bash
# Copy the template
cp mcp_servers/MCP_SERVER_TEMPLATE.sh start_mcp_myserver.sh

# Edit the configuration at the top of the file:
PORT=8002                              # Use next available port
API_KEY="myserver-mcp-key-2024"       # Unique API key
SERVER_NAME="myserver"                 # Your server name
SERVER_COMMAND="node"                  # Command to run
SERVER_ARGS="/path/to/server.js"      # Path to server

# Make it executable
chmod +x start_mcp_myserver.sh
```

### 3. Update Main Startup Script
Edit `start_dev_environment.sh` and add:
```bash
# In the MCP Servers section
if [ -f "$PROJECT_ROOT/start_mcp_myserver.sh" ]; then
    "$PROJECT_ROOT/start_mcp_myserver.sh" start
fi

# In the status display section
echo "  • MyServer MCP:              http://localhost:8002 (API Key: myserver-mcp-key-2024)"
```

### 4. Update Stop Script
Edit `stop_dev_environment.sh` and add:
```bash
# In the services array
services=("webui-frontend" "webui-backend" "pipelines" "mcpo-filesystem" "mcpo-myserver" "langgraph" "litellm")

# In the ports array
ports=(5173 8080 9999 8001 8002 9000 4000)
```

### 5. Configure in Open WebUI
- **URL**: `http://localhost:8002`
- **API Key**: `myserver-mcp-key-2024`

## 📊 Port Allocation Guide

| Service | Port | Purpose |
|---------|------|---------|
| LiteLLM Proxy | 4000 | LLM routing |
| Open WebUI Frontend | 5173 | Web interface |
| Open WebUI Backend | 8080 | API backend |
| LangGraph | 9000 | Multi-agent system |
| Pipelines | 9999 | Pipeline processing |
| **MCP Servers** | **8001-8099** | **Reserved for MCP** |
| Filesystem MCP | 8001 | File operations |
| Git MCP | 8002 | Version control |
| GitHub MCP | 8003 | GitHub API integration |
| Puppeteer MCP | 8004 | Browser automation |
| Playwright MCP | 8005 | Cross-browser testing |
| Custom MCP | 8007+ | Your custom servers |

## 🔍 Troubleshooting

### MCP Server Not Working in Open WebUI
1. **Check server is running**: `./start_mcp_filesystem.sh status`
2. **Test API directly**: `curl http://localhost:8001/openapi.json`
3. **Verify API key**: Make sure you're using the correct key for each server
4. **Check logs**: `tail -f logs/mcpo-filesystem.log`
5. **Port conflicts**: Ensure ports are free before starting

### Enable Tool Calling in Open WebUI
1. Go to **Settings → Admin Settings → Models**
2. Enable **"Function/Tool Calling"** for your models
3. Make sure you're using a model that supports tools (GPT-4, etc.)

### Testing Tools
```bash
# Test filesystem list directory
curl -X POST http://localhost:8001/list_directory \
  -H "Authorization: Bearer filesystem-mcp-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"path": "/Users/cosburn"}'
```

## 📚 Additional Resources
- [MCP Documentation](https://modelcontextprotocol.io)
- [MCPO GitHub](https://github.com/open-webui/mcpo)
- [Open WebUI Tools Docs](https://docs.openwebui.com/features/tools)