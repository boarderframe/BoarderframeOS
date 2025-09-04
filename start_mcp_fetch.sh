#!/bin/bash

# Fetch MCP Server with dedicated MCPO instance
# Provides web content fetching, API testing, and web scraping

set -e

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
PORT=8008
API_KEY="fetch-mcp-key-2024"
SERVER_NAME="fetch"

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

# Function to start MCPO for Fetch
start_fetch_mcpo() {
    if check_port $PORT; then
        print_warning "Fetch MCP server already running on port $PORT"
        return 0
    fi
    
    print_status "Starting Fetch MCP server on port $PORT..."
    
    # Start MCPO with MCP Fetch server (using TypeScript version)
    nohup mcpo \
        --host 0.0.0.0 \
        --port $PORT \
        --api-key "$API_KEY" \
        -- \
        npx -y mcp-server-fetch-typescript \
        > "$LOG_DIR/mcpo-fetch.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/mcpo-fetch.pid"
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_success "Fetch MCP server started successfully (PID: $pid)"
        echo ""
        echo "🌐 Fetch MCP Server Configuration:"
        echo "  • URL: http://localhost:$PORT"
        echo "  • API Key: $API_KEY"
        echo "  • OpenAPI Docs: http://localhost:$PORT/docs"
        echo "  • Capabilities: Web content fetching, API testing, HTML to Markdown conversion"
        echo "  • Features: HTTP/HTTPS requests, content extraction, web scraping"
        return 0
    else
        print_error "Fetch MCP server failed to start"
        cat "$LOG_DIR/mcpo-fetch.log" | tail -5
        return 1
    fi
}

# Function to stop Fetch MCPO
stop_fetch_mcpo() {
    if [ -f "$PID_DIR/mcpo-fetch.pid" ]; then
        pid=$(cat "$PID_DIR/mcpo-fetch.pid")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping Fetch MCP server (PID: $pid)..."
            kill $pid
            rm "$PID_DIR/mcpo-fetch.pid"
            print_success "Fetch MCP server stopped"
        else
            print_warning "Fetch MCP server not running (stale PID file removed)"
            rm "$PID_DIR/mcpo-fetch.pid"
        fi
    else
        print_warning "No Fetch MCP server PID file found"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_fetch_mcpo
        ;;
    stop)
        stop_fetch_mcpo
        ;;
    restart)
        stop_fetch_mcpo
        sleep 2
        start_fetch_mcpo
        ;;
    status)
        if [ -f "$PID_DIR/mcpo-fetch.pid" ]; then
            pid=$(cat "$PID_DIR/mcpo-fetch.pid")
            if kill -0 $pid 2>/dev/null; then
                print_success "Fetch MCP server is running (PID: $pid)"
                echo "URL: http://localhost:$PORT"
            else
                print_warning "Fetch MCP server is not running (stale PID file)"
            fi
        else
            print_status "Fetch MCP server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac