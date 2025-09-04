#!/bin/bash

# GitHub MCP Server with dedicated MCPO instance
# Provides GitHub API integration

set -e

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
PORT=8003
API_KEY="github-mcp-key-2024"
SERVER_NAME="github"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directories
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

# Check for GitHub token
check_github_token() {
    if [ -z "$GITHUB_TOKEN" ]; then
        if [ -f "$PROJECT_ROOT/.env" ]; then
            source "$PROJECT_ROOT/.env"
        fi
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        print_warning "GITHUB_TOKEN not set. GitHub API features will be limited."
        print_status "Set GITHUB_TOKEN in .env file or environment"
    fi
}

# Function to start MCPO for github
start_github_mcpo() {
    if check_port $PORT; then
        print_warning "GitHub MCP server already running on port $PORT"
        return 0
    fi
    
    check_github_token
    
    print_status "Starting GitHub MCP server on port $PORT..."
    
    # Start MCPO with github server
    GITHUB_TOKEN="${GITHUB_TOKEN:-}" \
    nohup mcpo \
        --host 0.0.0.0 \
        --port $PORT \
        --api-key "$API_KEY" \
        -- \
        npx -y @modelcontextprotocol/server-github \
        > "$LOG_DIR/mcpo-github.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/mcpo-github.pid"
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_success "GitHub MCP server started successfully (PID: $pid)"
        echo ""
        echo "🐙 GitHub MCP Server Configuration:"
        echo "  • URL: http://localhost:$PORT"
        echo "  • API Key: $API_KEY"
        echo "  • OpenAPI Docs: http://localhost:$PORT/docs"
        if [ -n "$GITHUB_TOKEN" ]; then
            echo "  • GitHub Token: Configured ✓"
        else
            echo "  • GitHub Token: Not configured (limited functionality)"
        fi
        return 0
    else
        print_error "GitHub MCP server failed to start"
        cat "$LOG_DIR/mcpo-github.log" | tail -5
        return 1
    fi
}

# Function to stop github MCPO
stop_github_mcpo() {
    if [ -f "$PID_DIR/mcpo-github.pid" ]; then
        pid=$(cat "$PID_DIR/mcpo-github.pid")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping GitHub MCP server (PID: $pid)..."
            kill $pid
            rm "$PID_DIR/mcpo-github.pid"
            print_success "GitHub MCP server stopped"
        else
            print_warning "GitHub MCP server not running (stale PID file removed)"
            rm "$PID_DIR/mcpo-github.pid"
        fi
    else
        print_warning "No GitHub MCP server PID file found"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_github_mcpo
        ;;
    stop)
        stop_github_mcpo
        ;;
    restart)
        stop_github_mcpo
        sleep 2
        start_github_mcpo
        ;;
    status)
        if [ -f "$PID_DIR/mcpo-github.pid" ]; then
            pid=$(cat "$PID_DIR/mcpo-github.pid")
            if kill -0 $pid 2>/dev/null; then
                print_success "GitHub MCP server is running (PID: $pid)"
                echo "URL: http://localhost:$PORT"
            else
                print_warning "GitHub MCP server is not running (stale PID file)"
            fi
        else
            print_status "GitHub MCP server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac