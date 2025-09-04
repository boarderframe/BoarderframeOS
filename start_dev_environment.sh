#!/bin/bash

# Open WebUI Complete Development Environment Startup Script
# This script starts all services required for the complete AI development environment

set -e  # Exit on any error

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log and pid directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start a service in background
start_service() {
    local service_name=$1
    local port=$2
    local command=$3
    local log_file="$LOG_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if check_port $port; then
        print_warning "$service_name already running on port $port"
        return 0
    fi
    
    print_status "Starting $service_name on port $port..."
    
    # Start the service in background and capture PID
    nohup bash -c "$command" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        print_success "$service_name started successfully (PID: $pid)"
        return 0
    else
        print_error "$service_name failed to start"
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within timeout"
    return 1
}

print_status "🚀 Starting Open WebUI Complete Development Environment"
echo ""

# Check for environment file
if [ ! -f "$PROJECT_ROOT/.env.litellm" ]; then
    print_warning "Environment file .env.litellm not found!"
    print_warning "Cloud models (GPT-5, Claude, etc.) will not work without API keys."
    print_warning "Only local models will be available."
    echo ""
fi

# 0. Prepare MCP Servers (if present)
if [ -d "$PROJECT_ROOT/mcp_servers" ] && [ -f "$PROJECT_ROOT/start_mcp_servers.sh" ]; then
    print_status "0/6 Preparing MCP Servers..."
    "$PROJECT_ROOT/start_mcp_servers.sh"
    echo ""
fi

# 1. Start LiteLLM Proxy Server
print_status "1/5 Starting LiteLLM Proxy Server..."
if [ -f "$PROJECT_ROOT/.env.litellm" ]; then
    start_service "litellm" 4000 "cd '$PROJECT_ROOT' && export \$(cat .env.litellm | grep -v '^#' | xargs) && litellm --config litellm_config.yaml"
else
    start_service "litellm" 4000 "cd '$PROJECT_ROOT' && litellm --config litellm_config.yaml"
fi
wait_for_service "litellm" 4000

# 2. Start LangGraph Multi-Agent Backend
print_status "2/6 Starting LangGraph Multi-Agent Backend..."
start_service "langgraph" 9000 "cd '$PROJECT_ROOT/langgraph_backend' && source langgraph_venv/bin/activate && python multi_agent_system.py"
wait_for_service "langgraph" 9000

# 3. Start MCP Servers (each with individual MCPO proxy)
print_status "3/6 Starting MCP Servers..."

# Use the unified MCP control script to start all servers
if [ -f "$PROJECT_ROOT/mcp_control.sh" ]; then
    "$PROJECT_ROOT/mcp_control.sh" start
else
    # Fallback to individual scripts if control script not found
    print_warning "MCP control script not found, trying individual scripts..."
    
    # Start filesystem MCP server
    if [ -f "$PROJECT_ROOT/start_mcp_filesystem.sh" ]; then
        "$PROJECT_ROOT/start_mcp_filesystem.sh" start
    fi
    
    # Start other MCP servers
    for server in git github puppeteer playwright postgresql fetch; do
        if [ -f "$PROJECT_ROOT/start_mcp_${server}.sh" ]; then
            "$PROJECT_ROOT/start_mcp_${server}.sh" start
        fi
    done
fi

# 4. Start Open WebUI Pipelines Server
print_status "4/6 Starting Open WebUI Pipelines Server..."
start_service "pipelines" 9999 "cd '$PROJECT_ROOT/pipelines' && uvicorn main:app --host 0.0.0.0 --port 9999"
wait_for_service "pipelines" 9999

# 5. Start Open WebUI Backend
print_status "5/6 Starting Open WebUI Backend..."
start_service "webui-backend" 8080 "cd '$PROJECT_ROOT/open-webui/backend' && CORS_ALLOW_ORIGIN='http://localhost:5173' WEBUI_SECRET_KEY=secret DATA_DIR=./data python3.12 -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080"
wait_for_service "webui-backend" 8080

# 6. Start Open WebUI Frontend
print_status "6/6 Starting Open WebUI Frontend..."
start_service "webui-frontend" 5173 "cd '$PROJECT_ROOT/open-webui' && npm run dev"
wait_for_service "webui-frontend" 5173

echo ""
print_success "🎉 All services started successfully!"
echo ""
echo "📋 Service Status:"
echo "  • LiteLLM Proxy:             http://localhost:4000"
echo "  • LangGraph Multi-Agent:     http://localhost:9000"
echo "  • Open WebUI Pipelines:      http://localhost:9999"
echo "  • Open WebUI Backend:        http://localhost:8080"
echo "  • Open WebUI Frontend:       http://localhost:5173"
echo ""
echo "🔌 MCP Servers (each with dedicated MCPO):"
echo "  • Filesystem MCP:            http://localhost:8001 (API Key: filesystem-mcp-key-2024)"
echo "  • GitHub MCP:                http://localhost:8003 (API Key: github-mcp-key-2024)"
echo "  • Puppeteer MCP:             http://localhost:8004 (API Key: puppeteer-mcp-key-2024)"
echo "  • Playwright MCP:            http://localhost:8005 (API Key: playwright-mcp-key-2024)"
echo "  • Fetch MCP:                 http://localhost:8008 (API Key: fetch-mcp-key-2024)"
echo ""
echo "  ⚠️  Note: Git (8002) and SQLite/PostgreSQL (8007) have compatibility issues"

echo ""
echo "🌐 Access Open WebUI at: http://localhost:5173"
echo ""
echo "📁 Logs are available in: $LOG_DIR"
echo "🔧 PIDs are stored in: $PID_DIR"

# Show MCP info if configured  
if [ -f "$PROJECT_ROOT/.mcp.json" ]; then
    echo "🤖 MCP servers configured in: .mcp.json"
fi

echo ""
echo "ℹ️  To stop all services, run: ./stop_dev_environment.sh"