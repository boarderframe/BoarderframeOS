#!/bin/bash

# MCP Servers Status Script
# Check the status and health of all MCP servers

set -e

cd "$(dirname "$0")"

echo "📊 MCP SERVERS STATUS CHECK"
echo "============================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check server status
check_server() {
    local name=$1
    local port=$2
    local expected_tools=$3
    
    echo -e "${BLUE}🔍 Checking $name (port $port)...${NC}"
    
    # Check if port is listening
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}  ❌ Not running (port $port not listening)${NC}"
        return 1
    fi
    
    # Check health endpoint
    local health_response=$(curl -s --max-time 5 "http://localhost:$port/health" 2>/dev/null || echo "")
    
    if [ -z "$health_response" ]; then
        echo -e "${RED}  ❌ No health response${NC}"
        return 1
    fi
    
    # Parse health response
    local status=$(echo "$health_response" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('status','unknown'))" 2>/dev/null || echo "unknown")
    
    if [ "$status" = "healthy" ]; then
        echo -e "${GREEN}  ✅ Running and healthy${NC}"
        
        # Show additional info if available
        local tools=$(echo "$health_response" | python3 -c "import json,sys;d=json.load(sys.stdin);print(len(d.get('tools',[])) if 'tools' in d else 'N/A')" 2>/dev/null || echo "N/A")
        echo -e "     📦 Tools available: $tools"
        
        # Show version if available
        local version=$(echo "$health_response" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('version','N/A'))" 2>/dev/null || echo "N/A")
        if [ "$version" != "N/A" ]; then
            echo -e "     🏷️  Version: $version"
        fi
        
    else
        echo -e "${YELLOW}  ⚠️  Running but status: $status${NC}"
    fi
    
    echo
}

# Function to show process info
show_process_info() {
    echo -e "${BLUE}📋 PROCESS INFORMATION:${NC}"
    echo "======================="
    
    for port in 9001 9002 9003 9004; do
        local pid=$(lsof -ti:$port 2>/dev/null || echo "")
        if [ ! -z "$pid" ]; then
            local cmd=$(ps -p $pid -o cmd= 2>/dev/null || echo "Unknown")
            local memory=$(ps -p $pid -o rss= 2>/dev/null || echo "0")
            local memory_mb=$((memory / 1024))
            echo -e "Port $port: PID $pid, Memory: ${memory_mb}MB"
            echo -e "  Command: $cmd"
        else
            echo -e "Port $port: ${RED}No process${NC}"
        fi
    done
    echo
}

# Function to show log tails
show_recent_logs() {
    echo -e "${BLUE}📜 RECENT LOG ENTRIES:${NC}"
    echo "======================"
    
    if [ -d "logs" ]; then
        for log_file in logs/*.log; do
            if [ -f "$log_file" ]; then
                local server_name=$(basename "$log_file" .log)
                echo -e "${YELLOW}--- $server_name ---${NC}"
                tail -3 "$log_file" 2>/dev/null || echo "No recent entries"
                echo
            fi
        done
    else
        echo "No log directory found"
    fi
}

# Main status checks
echo "Checking all MCP servers..."
echo

check_server "Simple Filesystem" 9001 "file operations"
check_server "Advanced Filesystem" 9002 "enhanced file operations"
check_server "Playwright Server" 9003 "browser automation"
check_server "Kroger MCP Server" 9004 "grocery shopping"

# Check frontend UI (different approach since it's not an API)
echo -e "${BLUE}🔍 Checking MCP Client UI (port 5173)...${NC}"
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    if curl -s --max-time 3 "http://localhost:5173" >/dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Running and accessible${NC}"
        echo -e "     🌐 URL: http://localhost:5173"
    else
        echo -e "${YELLOW}  ⚠️  Port listening but not responding (may be starting)${NC}"
    fi
else
    echo -e "${RED}  ❌ Not running${NC}"
fi
echo

show_process_info

# Show logs if requested
if [ "$1" = "--logs" ]; then
    show_recent_logs
fi

echo -e "${BLUE}🌐 QUICK LINKS:${NC}"
echo "==============="
echo "🗂️  Simple Filesystem:    http://localhost:9001/docs"
echo "🔧 Advanced Filesystem:   http://localhost:9002/docs" 
echo "🎭 Playwright Server:     http://localhost:9003/docs"
echo "🛒 Kroger MCP Server:     http://localhost:9004/docs"
echo
echo "💡 Use '--logs' flag to see recent log entries"
echo "💡 Start servers: ./start_all_mcp_servers.sh"
echo "💡 Stop servers: ./stop_all_mcp_servers.sh"