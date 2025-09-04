#!/bin/bash

# Template for Individual MCP Server with dedicated MCPO instance
# Copy this file and modify the variables below for each new MCP server

# === CONFIGURATION - MODIFY THESE ===
PORT=8002                                    # Change to unique port (8002, 8003, etc.)
API_KEY="my-server-mcp-key-2024"            # Change to unique API key
SERVER_NAME="my-server"                      # Change to your server name
SERVER_COMMAND="node"                        # Command to run server
SERVER_ARGS="/path/to/your/server.js"       # Path to your server executable
# === END CONFIGURATION ===

set -e

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

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

# Function to start MCPO for this server
start_server_mcpo() {
    if check_port $PORT; then
        print_warning "$SERVER_NAME MCP server already running on port $PORT"
        return 0
    fi
    
    print_status "Starting $SERVER_NAME MCP server on port $PORT..."
    
    # Start MCPO with this server
    nohup mcpo \
        --host 0.0.0.0 \
        --port $PORT \
        --api-key "$API_KEY" \
        -- \
        $SERVER_COMMAND $SERVER_ARGS \
        > "$LOG_DIR/mcpo-$SERVER_NAME.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/mcpo-$SERVER_NAME.pid"
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_success "$SERVER_NAME MCP server started successfully (PID: $pid)"
        echo ""
        echo "🔧 $SERVER_NAME MCP Server Configuration:"
        echo "  • URL: http://localhost:$PORT"
        echo "  • API Key: $API_KEY"
        echo "  • OpenAPI Docs: http://localhost:$PORT/docs"
        echo ""
        echo "📝 Open WebUI Configuration:"
        echo "  1. Go to Settings → Admin Settings → Tools"
        echo "  2. Add Tool Server with:"
        echo "     - URL: http://localhost:$PORT"
        echo "     - API Key: $API_KEY"
        return 0
    else
        print_error "$SERVER_NAME MCP server failed to start"
        cat "$LOG_DIR/mcpo-$SERVER_NAME.log" | tail -5
        return 1
    fi
}

# Function to stop this server's MCPO
stop_server_mcpo() {
    if [ -f "$PID_DIR/mcpo-$SERVER_NAME.pid" ]; then
        local pid=$(cat "$PID_DIR/mcpo-$SERVER_NAME.pid")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping $SERVER_NAME MCP server (PID: $pid)..."
            kill $pid
            rm "$PID_DIR/mcpo-$SERVER_NAME.pid"
            print_success "$SERVER_NAME MCP server stopped"
        else
            print_warning "$SERVER_NAME MCP server not running (stale PID file removed)"
            rm "$PID_DIR/mcpo-$SERVER_NAME.pid"
        fi
    else
        print_warning "No $SERVER_NAME MCP server PID file found"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_server_mcpo
        ;;
    stop)
        stop_server_mcpo
        ;;
    restart)
        stop_server_mcpo
        sleep 2
        start_server_mcpo
        ;;
    status)
        if [ -f "$PID_DIR/mcpo-$SERVER_NAME.pid" ]; then
            local pid=$(cat "$PID_DIR/mcpo-$SERVER_NAME.pid")
            if kill -0 $pid 2>/dev/null; then
                print_success "$SERVER_NAME MCP server is running (PID: $pid)"
                echo "URL: http://localhost:$PORT"
            else
                print_warning "$SERVER_NAME MCP server is not running (stale PID file)"
            fi
        else
            print_status "$SERVER_NAME MCP server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac