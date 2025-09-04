#!/bin/bash

# SQLite MCP Server with dedicated MCPO instance
# Provides SQLite database operations for WebUI database

set -e

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
PORT=8007
API_KEY="sqlite-mcp-key-2024"
SERVER_NAME="sqlite"

# SQLite database path (WebUI's database)
DB_PATH="${SQLITE_DB_PATH:-$PROJECT_ROOT/open-webui/backend/data/webui.db}"

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

# Function to start MCPO for SQLite
start_sqlite_mcpo() {
    if check_port $PORT; then
        print_warning "SQLite MCP server already running on port $PORT"
        return 0
    fi
    
    if [ ! -f "$DB_PATH" ]; then
        print_warning "SQLite database not found at $DB_PATH"
        print_status "Creating new database..."
    fi
    
    print_status "Starting SQLite MCP server on port $PORT..."
    
    # Start MCPO with SQLite server
    DATABASE_PATH="$DB_PATH" \
    nohup mcpo \
        --host 0.0.0.0 \
        --port $PORT \
        --api-key "$API_KEY" \
        -- \
        npx -y sqlite-mcp-server \
        > "$LOG_DIR/mcpo-sqlite.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/mcpo-sqlite.pid"
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_success "SQLite MCP server started successfully (PID: $pid)"
        echo ""
        echo "🗄️  SQLite MCP Server Configuration:"
        echo "  • URL: http://localhost:$PORT"
        echo "  • API Key: $API_KEY"
        echo "  • OpenAPI Docs: http://localhost:$PORT/docs"
        echo "  • Database: $DB_PATH"
        echo "  • Capabilities: SQL queries, schema inspection, WebUI data access"
        echo ""
        echo "  📊 WebUI Tables Available:"
        echo "     • user, chat, message, model, prompt, document"
        echo "     • knowledge, memory, function, tool, and more..."
        return 0
    else
        print_error "SQLite MCP server failed to start"
        cat "$LOG_DIR/mcpo-sqlite.log" | tail -5
        return 1
    fi
}

# Function to stop SQLite MCPO
stop_sqlite_mcpo() {
    if [ -f "$PID_DIR/mcpo-sqlite.pid" ]; then
        pid=$(cat "$PID_DIR/mcpo-sqlite.pid")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping SQLite MCP server (PID: $pid)..."
            kill $pid
            rm "$PID_DIR/mcpo-sqlite.pid"
            print_success "SQLite MCP server stopped"
        else
            print_warning "SQLite MCP server not running (stale PID file removed)"
            rm "$PID_DIR/mcpo-sqlite.pid"
        fi
    else
        print_warning "No SQLite MCP server PID file found"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_sqlite_mcpo
        ;;
    stop)
        stop_sqlite_mcpo
        ;;
    restart)
        stop_sqlite_mcpo
        sleep 2
        start_sqlite_mcpo
        ;;
    status)
        if [ -f "$PID_DIR/mcpo-sqlite.pid" ]; then
            pid=$(cat "$PID_DIR/mcpo-sqlite.pid")
            if kill -0 $pid 2>/dev/null; then
                print_success "SQLite MCP server is running (PID: $pid)"
                echo "URL: http://localhost:$PORT"
                echo "Database: $DB_PATH"
            else
                print_warning "SQLite MCP server is not running (stale PID file)"
            fi
        else
            print_status "SQLite MCP server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac