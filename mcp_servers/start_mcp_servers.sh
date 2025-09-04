#!/bin/bash

# MCP Server Startup Script
# Starts all MCP servers in the background and provides management commands

set -e

# Check if running on macOS and adjust accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS doesn't support associative arrays in older bash versions
    echo "macOS detected - using simplified server management"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/cosburn/MCP Servers"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Server configurations
declare -A SERVERS=(
    ["main"]="src.app.main:app --host 0.0.0.0 --port 8000 --reload"
    ["filesystem"]="minimal_webui_server:app --host 0.0.0.0 --port 9001"
    ["playwright"]="playwright_server:app --host 0.0.0.0 --port 9002"
)

declare -A PORTS=(
    ["main"]="8000"
    ["filesystem"]="9001" 
    ["playwright"]="9002"
)

declare -A DESCRIPTIONS=(
    ["main"]="Main MCP Management Server"
    ["filesystem"]="File System Operations Server"
    ["playwright"]="Web Automation & Scraping Server"
)

# Function to check if a port is in use
check_port() {
    local port=$1
    lsof -ti:$port > /dev/null 2>&1
}

# Function to start a server
start_server() {
    local name=$1
    local cmd=${SERVERS[$name]}
    local port=${PORTS[$name]}
    local desc=${DESCRIPTIONS[$name]}
    
    echo -e "${BLUE}Starting $desc (port $port)...${NC}"
    
    if check_port $port; then
        echo -e "${YELLOW}Port $port already in use, skipping $name${NC}"
        return 1
    fi
    
    cd "$PROJECT_DIR"
    nohup python -m uvicorn $cmd > "$LOG_DIR/$name.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_DIR/$name.pid"
    
    # Wait a moment and check if process is still running
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✓ $desc started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start $name${NC}"
        return 1
    fi
}

# Function to stop a server
stop_server() {
    local name=$1
    local pidfile="$PID_DIR/$name.pid"
    
    if [[ -f "$pidfile" ]]; then
        local pid=$(cat "$pidfile")
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping ${DESCRIPTIONS[$name]}...${NC}"
            kill $pid
            rm "$pidfile"
            echo -e "${GREEN}✓ Stopped $name${NC}"
        else
            echo -e "${YELLOW}Process $name not running, removing stale PID file${NC}"
            rm "$pidfile"
        fi
    else
        echo -e "${YELLOW}No PID file found for $name${NC}"
    fi
}

# Function to show server status
show_status() {
    echo -e "${BLUE}=== MCP Server Status ===${NC}"
    printf "%-12s %-8s %-10s %-40s\n" "SERVER" "PORT" "STATUS" "DESCRIPTION"
    echo "----------------------------------------------------------------"
    
    for server in "${!SERVERS[@]}"; do
        local port=${PORTS[$server]}
        local desc=${DESCRIPTIONS[$server]}
        local pidfile="$PID_DIR/$server.pid"
        local status="STOPPED"
        local status_color=$RED
        
        if [[ -f "$pidfile" ]]; then
            local pid=$(cat "$pidfile")
            if kill -0 $pid 2>/dev/null; then
                status="RUNNING"
                status_color=$GREEN
            fi
        fi
        
        printf "%-12s %-8s ${status_color}%-10s${NC} %-40s\n" "$server" "$port" "$status" "$desc"
    done
    
    echo ""
    echo -e "${BLUE}Open WebUI URLs:${NC}"
    echo "  Filesystem Tools: http://localhost:9001/openapi.json"
    echo "  Playwright Tools: http://localhost:9002/openapi.json"
    echo ""
    echo -e "${BLUE}Management UI:${NC}"
    echo "  Main Dashboard: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/api/v1/docs"
}

# Function to start all servers
start_all() {
    echo -e "${BLUE}=== Starting All MCP Servers ===${NC}"
    local success_count=0
    local total_count=${#SERVERS[@]}
    
    for server in "${!SERVERS[@]}"; do
        if start_server "$server"; then
            ((success_count++))
        fi
    done
    
    echo ""
    echo -e "${GREEN}Started $success_count/$total_count servers successfully${NC}"
    echo ""
    show_status
}

# Function to stop all servers
stop_all() {
    echo -e "${BLUE}=== Stopping All MCP Servers ===${NC}"
    
    for server in "${!SERVERS[@]}"; do
        stop_server "$server"
    done
    
    # Clean up any remaining processes on our ports
    for port in "${PORTS[@]}"; do
        if check_port $port; then
            echo -e "${YELLOW}Killing remaining process on port $port${NC}"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✓ All servers stopped${NC}"
}

# Function to restart all servers
restart_all() {
    echo -e "${BLUE}=== Restarting All MCP Servers ===${NC}"
    stop_all
    sleep 3
    start_all
}

# Function to show logs
show_logs() {
    local server=${1:-"all"}
    
    if [[ "$server" == "all" ]]; then
        echo -e "${BLUE}=== Recent logs from all servers ===${NC}"
        for s in "${!SERVERS[@]}"; do
            echo -e "\n${YELLOW}--- $s (${DESCRIPTIONS[$s]}) ---${NC}"
            if [[ -f "$LOG_DIR/$s.log" ]]; then
                tail -10 "$LOG_DIR/$s.log"
            else
                echo "No log file found"
            fi
        done
    else
        if [[ -f "$LOG_DIR/$server.log" ]]; then
            echo -e "${BLUE}=== Logs for $server ===${NC}"
            tail -20 "$LOG_DIR/$server.log"
        else
            echo -e "${RED}No log file found for $server${NC}"
        fi
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}MCP Server Management Script${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start all MCP servers"
    echo "  stop      Stop all MCP servers"  
    echo "  restart   Restart all MCP servers"
    echo "  status    Show server status"
    echo "  logs      Show recent logs from all servers"
    echo "  logs <server>  Show logs for specific server"
    echo "  help      Show this help message"
    echo ""
    echo "Available servers: ${!SERVERS[*]}"
}

# Main script logic
case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
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