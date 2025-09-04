#!/bin/bash

# MCP Server Startup Script - Open WebUI Compatible
# Starts OpenAPI-compatible MCP servers for Open WebUI integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/cosburn/MCP Servers"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Create directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Check if port is in use
check_port() {
    local port=$1
    lsof -ti:$port > /dev/null 2>&1
}

# Start a server
start_server() {
    local name=$1
    local cmd=$2
    local port=$3
    local desc=$4
    
    echo -e "${BLUE}Starting $desc (port $port)...${NC}"
    
    if check_port $port; then
        echo -e "${YELLOW}Port $port already in use, skipping $name${NC}"
        return 1
    fi
    
    cd "$PROJECT_DIR"
    nohup python -m uvicorn $cmd > "$LOG_DIR/$name.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/$name.pid"
    
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✓ $desc started (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start $name${NC}"
        return 1
    fi
}

# Stop a server
stop_server() {
    local name=$1
    local pidfile="$PID_DIR/$name.pid"
    
    if [[ -f "$pidfile" ]]; then
        local pid=$(cat "$pidfile")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping $name...${NC}"
            kill $pid
            rm "$pidfile"
            echo -e "${GREEN}✓ Stopped $name${NC}"
        else
            rm "$pidfile"
        fi
    fi
}

# Show status
show_status() {
    echo -e "${BLUE}=== Open WebUI MCP Server Status ===${NC}"
    echo
    
    # Check main server (port 8000)
    if check_port 8000; then
        echo -e "Main Server (8000):     ${GREEN}RUNNING${NC}"
    else
        echo -e "Main Server (8000):     ${RED}STOPPED${NC}"
    fi
    
    # Check simple filesystem server (port 9001)
    if check_port 9001; then
        echo -e "Filesystem (9001):      ${GREEN}RUNNING${NC}"
    else
        echo -e "Filesystem (9001):      ${RED}STOPPED${NC}"
    fi
    
    # Check simple playwright server (port 9002)
    if check_port 9002; then
        echo -e "Playwright (9002):      ${GREEN}RUNNING${NC}"
    else
        echo -e "Playwright (9002):      ${RED}STOPPED${NC}"
    fi
    
    echo
    echo -e "${BLUE}Open WebUI Integration URLs:${NC}"
    echo "  📁 Filesystem Tools: http://localhost:9001"
    echo "  🌐 Playwright Web Tools: http://localhost:9002"
    echo "  📋 OpenAPI Schemas: http://localhost:9001/openapi.json | http://localhost:9002/openapi.json"
    echo
    echo -e "${BLUE}Management:${NC}"
    echo "  🎛️  Dashboard: http://localhost:3001"
    echo "  🔧 API: http://localhost:8000"
    echo
    echo -e "${BLUE}Available Tools:${NC}"
    echo "  📁 File Operations: read, write, list, search"
    echo "  🌐 Web Navigation & Search"
    echo "  📰 Enhanced News Search"
    echo "  📸 Screenshots & Automation"
    echo "  🔧 Form Interaction"
}

# Start all servers
start_all() {
    echo -e "${BLUE}=== Starting Open WebUI MCP Servers ===${NC}"
    
    # Start main server
    if ! check_port 8000; then
        cd "$PROJECT_DIR/src"
        nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/main.log" 2>&1 &
        echo $! > "$PID_DIR/main.pid"
        echo -e "${GREEN}✓ Main server started (port 8000)${NC}"
    else
        echo -e "${YELLOW}Main server already running (port 8000)${NC}"
    fi
    
    # Start simple filesystem server (Open WebUI compatible)
    if ! check_port 9001; then
        cd "$PROJECT_DIR"
        nohup python -m uvicorn simple_filesystem_server:app --host 0.0.0.0 --port 9001 --reload > "$LOG_DIR/filesystem.log" 2>&1 &
        echo $! > "$PID_DIR/filesystem.pid"
        echo -e "${GREEN}✓ Filesystem Tools started (port 9001)${NC}"
    else
        echo -e "${YELLOW}Filesystem server already running (port 9001)${NC}"
    fi
    
    # Start simple playwright server (Open WebUI compatible)
    if ! check_port 9002; then
        cd "$PROJECT_DIR"
        nohup python -m uvicorn simple_playwright_server:app --host 0.0.0.0 --port 9002 --reload > "$LOG_DIR/playwright.log" 2>&1 &
        echo $! > "$PID_DIR/playwright.pid"
        echo -e "${GREEN}✓ Playwright Web Tools started (port 9002)${NC}"
    else
        echo -e "${YELLOW}Playwright server already running (port 9002)${NC}"
    fi
    
    echo
    show_status
}

# Stop all servers
stop_all() {
    echo -e "${BLUE}=== Stopping MCP Servers ===${NC}"
    
    stop_server "main"
    stop_server "filesystem"
    stop_server "playwright"
    
    # Kill any remaining processes
    for port in 8000 9001 9002; do
        if check_port $port; then
            echo -e "${YELLOW}Killing remaining process on port $port${NC}"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
}

# Show logs
show_logs() {
    echo -e "${BLUE}=== Recent Logs ===${NC}"
    for log in main filesystem playwright; do
        if [[ -f "$LOG_DIR/$log.log" ]]; then
            echo -e "\n${YELLOW}--- $log ---${NC}"
            tail -5 "$LOG_DIR/$log.log"
        fi
    done
}

# Help
show_help() {
    echo -e "${BLUE}Open WebUI MCP Server Management${NC}"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start     Start all Open WebUI compatible MCP servers"
    echo "  stop      Stop all MCP servers"
    echo "  restart   Restart all MCP servers"
    echo "  status    Show server status and integration URLs"
    echo "  logs      Show recent logs"
    echo "  help      Show this help"
    echo
    echo -e "${BLUE}Open WebUI Integration:${NC}"
    echo "  Add these URLs to Open WebUI function settings:"
    echo "  📁 Filesystem: http://localhost:9001"
    echo "  🌐 Playwright: http://localhost:9002"
}

# Main logic
case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        stop_all
        sleep 3
        start_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac