#!/bin/bash

# MCPO Server Startup Script
# This script starts the MCP-to-OpenAPI proxy server

set -e  # Exit on any error

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
MCPO_PORT=8001
API_KEY="webui-mcp-key-2024"

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

# Function to start MCPO server
start_mcpo() {
    if check_port $MCPO_PORT; then
        print_warning "MCPO server already running on port $MCPO_PORT"
        return 0
    fi
    
    print_status "Starting MCPO server on port $MCPO_PORT..."
    
    # Start MCPO with configuration file
    nohup mcpo \
        --host 0.0.0.0 \
        --port $MCPO_PORT \
        --api-key "$API_KEY" \
        --config "$PROJECT_ROOT/mcpo_config.json" \
        > "$LOG_DIR/mcpo.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/mcpo.pid"
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_success "MCPO server started successfully (PID: $pid)"
        print_status "MCP tools available at:"
        echo "  • Filesystem: http://localhost:$MCPO_PORT/filesystem"
        echo ""
        echo "📝 API Key: $API_KEY"
        echo ""
        echo "🔗 OpenAPI docs: http://localhost:$MCPO_PORT/docs"
        return 0
    else
        print_error "MCPO server failed to start"
        return 1
    fi
}

# Function to stop MCPO server
stop_mcpo() {
    if [ -f "$PID_DIR/mcpo.pid" ]; then
        local pid=$(cat "$PID_DIR/mcpo.pid")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping MCPO server (PID: $pid)..."
            kill $pid
            rm "$PID_DIR/mcpo.pid"
            print_success "MCPO server stopped"
        else
            print_warning "MCPO server not running (stale PID file removed)"
            rm "$PID_DIR/mcpo.pid"
        fi
    else
        print_warning "No MCPO server PID file found"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_mcpo
        ;;
    stop)
        stop_mcpo
        ;;
    restart)
        stop_mcpo
        sleep 2
        start_mcpo
        ;;
    status)
        if [ -f "$PID_DIR/mcpo.pid" ]; then
            pid=$(cat "$PID_DIR/mcpo.pid")
            if kill -0 "$pid" 2>/dev/null; then
                print_success "MCPO server is running (PID: $pid)"
                echo "URL: http://localhost:$MCPO_PORT"
            else
                print_warning "MCPO server is not running (stale PID file)"
            fi
        else
            print_status "MCPO server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac