#!/bin/bash

# Open WebUI Complete Development Environment Stop Script
# This script stops all services started by start_dev_environment.sh

PROJECT_ROOT="/Users/cosburn/open_webui"
PID_DIR="$PROJECT_ROOT/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ ! -f "$pid_file" ]; then
        print_warning "No PID file found for $service_name"
        return 1
    fi
    
    local pid=$(cat "$pid_file")
    
    if kill -0 $pid 2>/dev/null; then
        print_status "Stopping $service_name (PID: $pid)..."
        kill $pid
        
        # Wait for graceful shutdown
        local attempts=10
        while [ $attempts -gt 0 ] && kill -0 $pid 2>/dev/null; do
            sleep 1
            attempts=$((attempts - 1))
        done
        
        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            print_warning "Force killing $service_name..."
            kill -9 $pid
        fi
        
        print_success "$service_name stopped"
        rm -f "$pid_file"
    else
        print_warning "$service_name was not running"
        rm -f "$pid_file"
    fi
}

print_status "🛑 Stopping Open WebUI Complete Development Environment"
echo ""

# Stop services in reverse order
services=("webui-frontend" "webui-backend" "pipelines" "langgraph" "litellm")

for service in "${services[@]}"; do
    stop_service "$service"
done

# Stop all MCP servers
print_status "Stopping MCP servers..."
if [ -f "$PROJECT_ROOT/mcp_control.sh" ]; then
    "$PROJECT_ROOT/mcp_control.sh" stop
else
    # Fallback to stopping individual MCP servers via PID files
    mcp_services=("mcpo-filesystem" "mcpo-git" "mcpo-github" "mcpo-puppeteer" "mcpo-playwright" "mcpo-postgresql" "mcpo-fetch")
    for service in "${mcp_services[@]}"; do
        if [ -f "$PID_DIR/${service}.pid" ]; then
            stop_service "$service"
        fi
    done
fi

echo ""

# Also kill any remaining processes on known ports
print_status "Cleaning up any remaining processes..."

ports=(5173 8080 9999 8001 8002 8003 8004 8005 8006 8007 8008 9000 4000)
for port in "${ports[@]}"; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        print_status "Killing process on port $port (PID: $pid)"
        kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null
    fi
done

# Note: No Docker containers to stop (Qdrant removed)

echo ""
print_success "🎉 All services stopped successfully!"
echo ""
print_status "📁 Logs are preserved in: $PROJECT_ROOT/logs"