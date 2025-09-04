#!/bin/bash

# MCP Servers Startup Script
# Starts all MCP servers in the background for development

set -e

cd "$(dirname "$0")"

echo "🚀 STARTING ALL MCP SERVERS"
echo "=========================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start server if not running
start_server() {
    local name=$1
    local port=$2
    local script=$3
    local log_file=$4
    
    if check_port $port; then
        echo -e "${YELLOW}⚠️  $name (port $port) already running${NC}"
    else
        echo -e "${GREEN}▶️  Starting $name on port $port...${NC}"
        nohup python3 $script > $log_file 2>&1 &
        local pid=$!
        echo $pid > "${name// /_}.pid"
        sleep 2
        
        # Verify it started
        if check_port $port; then
            echo -e "${GREEN}✅ $name started successfully (PID: $pid)${NC}"
        else
            echo -e "${RED}❌ $name failed to start${NC}"
        fi
    fi
}

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting MCP servers..."
echo

# Start all servers
start_server "Simple Filesystem" 9001 "simple_filesystem_server.py" "logs/simple_filesystem.log"
start_server "Advanced Filesystem" 9002 "advanced_filesystem_server.py" "logs/advanced_filesystem.log"
start_server "Playwright Server" 9003 "simple_playwright_server.py" "logs/playwright.log"
start_server "Kroger MCP Server" 9004 "kroger_mcp_server.py" "logs/kroger_mcp.log"

echo
echo "🔍 HEALTH CHECK:"
echo "==============="

# Health check all servers
sleep 3

for port in 9001 9002 9003 9004; do
    if curl -s --max-time 3 "http://localhost:$port/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Port $port: Healthy${NC}"
    else
        echo -e "${RED}❌ Port $port: Not responding${NC}"
    fi
done

echo
echo "📋 SERVER SUMMARY:"
echo "=================="
echo "🗂️  Simple Filesystem:    http://localhost:9001"
echo "🔧 Advanced Filesystem:   http://localhost:9002"
echo "🎭 Playwright Server:     http://localhost:9003"
echo "🛒 Kroger MCP Server:     http://localhost:9004"
echo
echo "📁 Log files in: ./logs/"
echo "🔧 Stop all servers: ./stop_all_mcp_servers.sh"
echo "🚀 STARTING MCP CLIENT UI:"
echo "========================="

# Check if frontend directory exists
if [ -d "frontend" ]; then
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    echo -e "${GREEN}🌐 Starting MCP Client UI on http://localhost:5173...${NC}"
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    local ui_pid=$!
    echo $ui_pid > "../frontend.pid"
    
    cd ..
    
    # Wait a moment for UI to start
    sleep 3
    
    # Check if frontend is running
    if curl -s --max-time 3 "http://localhost:5173" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ MCP Client UI started successfully (PID: $ui_pid)${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP Client UI starting... (may take a moment)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Frontend directory not found - skipping UI startup${NC}"
fi

echo
echo "🎉 All MCP servers and UI are ready!"
echo
echo "🌐 QUICK ACCESS:"
echo "================"
echo "🖥️  MCP Client UI:         http://localhost:5173"
echo "🗂️  Simple Filesystem:    http://localhost:9001/docs"
echo "🔧 Advanced Filesystem:   http://localhost:9002/docs"
echo "🎭 Playwright Server:     http://localhost:9003/docs"
echo "🛒 Kroger MCP Server:     http://localhost:9004/docs"