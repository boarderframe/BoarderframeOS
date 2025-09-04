#!/bin/bash

# Unified MCP Server Control Script
# Manages all MCPO-wrapped MCP servers for Open WebUI integration

set -e

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# MCP Servers Configuration (using simple arrays for compatibility)
# Note: git and sqlite have compatibility issues with MCPO
MCP_SERVERS="filesystem github puppeteer playwright fetch"
MCP_PORTS="8001 8003 8004 8005 8008"
MCP_KEYS="filesystem-mcp-key-2024 github-mcp-key-2024 puppeteer-mcp-key-2024 playwright-mcp-key-2024 fetch-mcp-key-2024"
MCP_ICONS="📁 🐙 🎭 🎬 🌐"

# Helper function to get server info
get_server_info() {
    local server=$1
    local index=1
    for s in $MCP_SERVERS; do
        if [ "$s" = "$server" ]; then
            echo "$index"
            return
        fi
        index=$((index + 1))
    done
    echo "0"
}

get_port() {
    local index=$1
    echo "$MCP_PORTS" | cut -d' ' -f$index
}

get_key() {
    local index=$1
    echo "$MCP_KEYS" | cut -d' ' -f$index
}

get_icon() {
    local index=$1
    echo "$MCP_ICONS" | cut -d' ' -f$index
}

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

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Function to check if MCPO is installed
check_mcpo() {
    if ! command -v mcpo &> /dev/null; then
        print_error "MCPO is not installed"
        echo "Install with: pipx install mcp-to-openapi"
        exit 1
    fi
}

# Function to start a specific server
start_server() {
    local server=$1
    local script="$PROJECT_ROOT/start_mcp_${server}.sh"
    
    if [ ! -f "$script" ]; then
        print_error "Start script not found: $script"
        return 1
    fi
    
    chmod +x "$script"
    "$script" start
}

# Function to stop a specific server
stop_server() {
    local server=$1
    local script="$PROJECT_ROOT/start_mcp_${server}.sh"
    
    if [ ! -f "$script" ]; then
        print_error "Start script not found: $script"
        return 1
    fi
    
    chmod +x "$script"
    "$script" stop
}

# Function to get server status
status_server() {
    local server=$1
    local script="$PROJECT_ROOT/start_mcp_${server}.sh"
    
    if [ ! -f "$script" ]; then
        print_error "Start script not found: $script"
        return 1
    fi
    
    chmod +x "$script"
    "$script" status
}

# Function to start all servers
start_all() {
    print_header "Starting All MCP Servers"
    
    local index=1
    for server in $MCP_SERVERS; do
        local icon=$(get_icon $index)
        echo -e "\n${icon} Starting $server server..."
        start_server "$server"
        index=$((index + 1))
    done
    
    echo ""
    print_success "All MCP servers started"
    show_urls
}

# Function to stop all servers
stop_all() {
    print_header "Stopping All MCP Servers"
    
    local index=1
    for server in $MCP_SERVERS; do
        local icon=$(get_icon $index)
        echo -e "\n${icon} Stopping $server server..."
        stop_server "$server"
        index=$((index + 1))
    done
    
    echo ""
    print_success "All MCP servers stopped"
}

# Function to show status of all servers
status_all() {
    print_header "MCP Server Status"
    
    local index=1
    for server in $MCP_SERVERS; do
        local icon=$(get_icon $index)
        echo -e "\n${icon} $server server:"
        status_server "$server"
        index=$((index + 1))
    done
}

# Function to show all server URLs
show_urls() {
    print_header "MCP Server URLs for Open WebUI Configuration"
    
    echo -e "${MAGENTA}Add these to Open WebUI > Admin > Settings > Functions:${NC}\n"
    
    local index=1
    for server in $MCP_SERVERS; do
        local port=$(get_port $index)
        local api_key=$(get_key $index)
        local icon=$(get_icon $index)
        echo -e "${icon} ${GREEN}$server${NC}:"
        echo "  • URL: http://localhost:$port"
        echo "  • API Key: $api_key"
        echo "  • OpenAPI: http://localhost:$port/docs"
        echo ""
        index=$((index + 1))
    done
    
    echo -e "${YELLOW}Note: Make sure to enable 'Tools & Functions' in Open WebUI settings${NC}"
}

# Function to tail logs for a specific server
tail_logs() {
    local server=$1
    local log_file="$LOG_DIR/mcpo-${server}.log"
    
    if [ ! -f "$log_file" ]; then
        print_error "Log file not found: $log_file"
        return 1
    fi
    
    print_status "Tailing logs for $server server (Ctrl+C to stop)..."
    tail -f "$log_file"
}

# Function to show help
show_help() {
    cat << EOF
${CYAN}MCP Server Control Script${NC}

${GREEN}Usage:${NC}
  $0 [command] [options]

${GREEN}Commands:${NC}
  start [server]     Start MCP server(s)
  stop [server]      Stop MCP server(s)
  restart [server]   Restart MCP server(s)
  status [server]    Show status of MCP server(s)
  urls               Show all server URLs for configuration
  logs <server>      Tail logs for a specific server
  help               Show this help message

${GREEN}Working Servers:${NC}
  filesystem         File system operations (port 8001)
  github            GitHub API integration (port 8003)
  puppeteer         Browser automation with Puppeteer (port 8004)
  playwright        Browser automation with Playwright (port 8005)
  fetch             Web content fetching & API testing (port 8008)

${YELLOW}Servers with Issues (not included):${NC}
  git               Schema compatibility issue with MCPO (port 8002)
  sqlite/postgresql Database connection issues (port 8007)

${GREEN}Examples:${NC}
  $0 start           # Start all servers
  $0 start git       # Start only git server
  $0 stop            # Stop all servers
  $0 status          # Show status of all servers
  $0 logs filesystem # Tail filesystem server logs
  $0 urls            # Show configuration URLs

${YELLOW}Note:${NC} Requires MCPO to be installed (pipx install mcp-to-openapi)
EOF
}

# Main execution
check_mcpo

case "${1:-help}" in
    start)
        if [ -z "$2" ]; then
            start_all
        else
            start_server "$2"
        fi
        ;;
    stop)
        if [ -z "$2" ]; then
            stop_all
        else
            stop_server "$2"
        fi
        ;;
    restart)
        if [ -z "$2" ]; then
            stop_all
            sleep 2
            start_all
        else
            stop_server "$2"
            sleep 2
            start_server "$2"
        fi
        ;;
    status)
        if [ -z "$2" ]; then
            status_all
        else
            status_server "$2"
        fi
        ;;
    urls)
        show_urls
        ;;
    logs)
        if [ -z "$2" ]; then
            print_error "Please specify a server name"
            echo "Usage: $0 logs <server>"
            exit 1
        else
            tail_logs "$2"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac