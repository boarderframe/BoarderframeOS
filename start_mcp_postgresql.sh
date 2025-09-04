#!/bin/bash

# PostgreSQL MCP Server with dedicated MCPO instance
# Provides database management and SQL operations

set -e

PROJECT_ROOT="/Users/cosburn/open_webui"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"
PORT=8007
API_KEY="postgresql-mcp-key-2024"
SERVER_NAME="postgresql"

# PostgreSQL connection settings (customize these)
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-postgres}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-}"

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

# Function to start MCPO for PostgreSQL
start_postgresql_mcpo() {
    if check_port $PORT; then
        print_warning "PostgreSQL MCP server already running on port $PORT"
        return 0
    fi
    
    print_status "Starting PostgreSQL MCP server on port $PORT..."
    
    # Build connection string
    CONNECTION_STRING="postgresql://${DB_USER}"
    if [ -n "$DB_PASSWORD" ]; then
        CONNECTION_STRING="${CONNECTION_STRING}:${DB_PASSWORD}"
    fi
    CONNECTION_STRING="${CONNECTION_STRING}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    
    # Start MCPO with PostgreSQL server (pass connection string as argument)
    nohup mcpo \
        --host 0.0.0.0 \
        --port $PORT \
        --api-key "$API_KEY" \
        -- \
        npx -y @ahmetkca/mcp-server-postgres "$CONNECTION_STRING" \
        > "$LOG_DIR/mcpo-postgresql.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/mcpo-postgresql.pid"
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_success "PostgreSQL MCP server started successfully (PID: $pid)"
        echo ""
        echo "🐘 PostgreSQL MCP Server Configuration:"
        echo "  • URL: http://localhost:$PORT"
        echo "  • API Key: $API_KEY"
        echo "  • OpenAPI Docs: http://localhost:$PORT/docs"
        echo "  • Database: $DB_NAME@$DB_HOST:$DB_PORT"
        echo "  • Capabilities: SQL queries, schema management, data operations"
        return 0
    else
        print_error "PostgreSQL MCP server failed to start"
        cat "$LOG_DIR/mcpo-postgresql.log" | tail -5
        return 1
    fi
}

# Function to stop PostgreSQL MCPO
stop_postgresql_mcpo() {
    if [ -f "$PID_DIR/mcpo-postgresql.pid" ]; then
        pid=$(cat "$PID_DIR/mcpo-postgresql.pid")
        if kill -0 $pid 2>/dev/null; then
            print_status "Stopping PostgreSQL MCP server (PID: $pid)..."
            kill $pid
            rm "$PID_DIR/mcpo-postgresql.pid"
            print_success "PostgreSQL MCP server stopped"
        else
            print_warning "PostgreSQL MCP server not running (stale PID file removed)"
            rm "$PID_DIR/mcpo-postgresql.pid"
        fi
    else
        print_warning "No PostgreSQL MCP server PID file found"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        start_postgresql_mcpo
        ;;
    stop)
        stop_postgresql_mcpo
        ;;
    restart)
        stop_postgresql_mcpo
        sleep 2
        start_postgresql_mcpo
        ;;
    status)
        if [ -f "$PID_DIR/mcpo-postgresql.pid" ]; then
            pid=$(cat "$PID_DIR/mcpo-postgresql.pid")
            if kill -0 $pid 2>/dev/null; then
                print_success "PostgreSQL MCP server is running (PID: $pid)"
                echo "URL: http://localhost:$PORT"
            else
                print_warning "PostgreSQL MCP server is not running (stale PID file)"
            fi
        else
            print_status "PostgreSQL MCP server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac