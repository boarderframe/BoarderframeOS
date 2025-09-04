#!/bin/bash

# Playwright MCP Server with dedicated MCPO instance
# Provides browser automation with Playwright

set -e

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
PORT=8005
API_KEY="playwright-mcp-key-2024"
SERVER_NAME="playwright"

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

# Function to start MCPO for playwright
start_playwright_mcpo() {
    if check_port $PORT; then
        print_warning "Playwright MCP server already running on port $PORT"
        return 0
    fi
    
    print_status "Installing Playwright browsers if needed..."
    npx playwright install chromium 2>/dev/null || true
    
    print_status "Starting Playwright MCP server on port $PORT..."
    
    # Start MCPO with playwright server in headless mode
    nohup mcpo \
        --host 0.0.0.0 \
        --port $PORT \
        --api-key "$API_KEY" \
        -- \
        npx -y @playwright/mcp --headless \
        > "$LOG_DIR/mcpo-playwright.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/mcpo-playwright.pid"
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_success "Playwright MCP server started successfully (PID: $pid)"
        echo ""
        echo "🎬 Playwright MCP Server Configuration:"
        echo "  • URL: http://localhost:$PORT"
        echo "  • API Key: $API_KEY"
        echo "  • OpenAPI Docs: http://localhost:$PORT/docs"
        echo "  • Capabilities: Cross-browser automation, testing, screenshots"
        return 0
    else
        print_error "Playwright MCP server failed to start"
        cat "$LOG_DIR/mcpo-playwright.log" | tail -5
        return 1
    fi
}

# Function to stop playwright MCPO
stop_playwright_mcpo() {
    if [ -f "$PID_DIR/mcpo-playwright.pid" ]; then
        pid=$(cat "$PID_DIR/mcpo-playwright.pid")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping Playwright MCP server (PID: $pid)..."
            kill $pid
            rm "$PID_DIR/mcpo-playwright.pid"
            print_success "Playwright MCP server stopped"
        else
            print_warning "Playwright MCP server not running (stale PID file removed)"
            rm "$PID_DIR/mcpo-playwright.pid"
        fi
    else
        print_warning "No Playwright MCP server PID file found"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_playwright_mcpo
        ;;
    stop)
        stop_playwright_mcpo
        ;;
    restart)
        stop_playwright_mcpo
        sleep 2
        start_playwright_mcpo
        ;;
    status)
        if [ -f "$PID_DIR/mcpo-playwright.pid" ]; then
            pid=$(cat "$PID_DIR/mcpo-playwright.pid")
            if kill -0 $pid 2>/dev/null; then
                print_success "Playwright MCP server is running (PID: $pid)"
                echo "URL: http://localhost:$PORT"
            else
                print_warning "Playwright MCP server is not running (stale PID file)"
            fi
        else
            print_status "Playwright MCP server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac