#!/bin/bash

# MCP Servers Stop Script
# Stops all MCP servers gracefully

set -e

cd "$(dirname "$0")"

echo "🛑 STOPPING ALL MCP SERVERS"
echo "==========================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop server by PID file
stop_server_by_pid() {
    local name=$1
    local pid_file="${name// /_}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}🔄 Stopping $name (PID: $pid)...${NC}"
            kill $pid
            sleep 2
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${RED}💀 Force killing $name...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $name was not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file for $name${NC}"
    fi
}

# Function to stop by port (fallback)
stop_server_by_port() {
    local port=$1
    local name=$2
    
    local pid=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}🔄 Stopping process on port $port...${NC}"
        kill $pid 2>/dev/null || true
        sleep 1
        
        # Force kill if still running
        local still_running=$(lsof -ti:$port 2>/dev/null || echo "")
        if [ ! -z "$still_running" ]; then
            echo -e "${RED}💀 Force killing process on port $port...${NC}"
            kill -9 $still_running 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Port $port cleared${NC}"
    else
        echo -e "${GREEN}✅ Port $port already free${NC}"
    fi
}

# Stop servers by PID files first
stop_server_by_pid "Simple Filesystem"
stop_server_by_pid "Advanced Filesystem"
stop_server_by_pid "Playwright Server"
stop_server_by_pid "Kroger MCP Server"

# Stop frontend UI if running
if [ -f "frontend.pid" ]; then
    echo -e "${YELLOW}🖥️  Stopping MCP Client UI...${NC}"
    stop_server_by_pid "Frontend UI"
    
    # Also check port 5173 specifically for Vite dev server
    vite_pid=$(lsof -ti:5173 2>/dev/null || echo "")
    if [ ! -z "$vite_pid" ]; then
        echo -e "${YELLOW}🔄 Stopping Vite dev server (port 5173)...${NC}"
        kill $vite_pid 2>/dev/null || true
        sleep 1
        
        # Force kill if still running
        still_running=$(lsof -ti:5173 2>/dev/null || echo "")
        if [ ! -z "$still_running" ]; then
            kill -9 $still_running 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ MCP Client UI stopped${NC}"
    fi
    
    rm -f "frontend.pid"
fi

echo
echo "🔍 CHECKING PORTS:"
echo "=================="

# Fallback: stop by port if still running
stop_server_by_port 9001 "Simple Filesystem"
stop_server_by_port 9002 "Advanced Filesystem"  
stop_server_by_port 9003 "Playwright Server"
stop_server_by_port 9004 "Kroger MCP Server"
stop_server_by_port 5173 "MCP Client UI"

echo
echo "🧹 CLEANUP:"
echo "==========="

# Clean up log files (optional)
if [ "$1" = "--clean-logs" ]; then
    echo -e "${YELLOW}🗑️  Cleaning log files...${NC}"
    rm -rf logs/*.log
    echo -e "${GREEN}✅ Log files cleaned${NC}"
fi

# Clean up PID files
rm -f *.pid

echo
echo -e "${GREEN}🎉 All MCP servers stopped successfully!${NC}"
echo
echo "💡 To restart: ./start_all_mcp_servers.sh"
echo "💡 To clean logs on next stop: ./stop_all_mcp_servers.sh --clean-logs"