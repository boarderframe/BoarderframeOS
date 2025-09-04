#!/bin/bash

# MCP Servers Management Script
# This script manages MCP servers for the Open WebUI project

set -e  # Exit on any error

PROJECT_ROOT="/Users/cosburn/open_webui"
MCP_DIR="$PROJECT_ROOT/mcp_servers"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

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

# Function to build an MCP server
build_mcp_server() {
    local server_name=$1
    local server_path="$MCP_DIR/$server_name"
    
    if [ ! -d "$server_path" ]; then
        print_warning "MCP server '$server_name' not found at $server_path"
        return 1
    fi
    
    print_status "Building MCP server: $server_name"
    
    # Check if package.json exists
    if [ ! -f "$server_path/package.json" ]; then
        print_warning "No package.json found for $server_name, skipping..."
        return 0
    fi
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "$server_path/node_modules" ]; then
        print_status "Installing dependencies for $server_name..."
        (cd "$server_path" && npm install) || {
            print_error "Failed to install dependencies for $server_name"
            return 1
        }
    fi
    
    # Build if TypeScript project
    if [ -f "$server_path/tsconfig.json" ]; then
        print_status "Building TypeScript for $server_name..."
        (cd "$server_path" && npm run build) || {
            print_error "Failed to build $server_name"
            return 1
        }
    fi
    
    print_success "$server_name built successfully"
    return 0
}

# Function to start all MCP servers
start_mcp_servers() {
    print_status "🤖 Starting MCP Servers..."
    
    # Build and prepare all MCP servers
    for server_dir in "$MCP_DIR"/*; do
        if [ -d "$server_dir" ]; then
            server_name=$(basename "$server_dir")
            build_mcp_server "$server_name"
        fi
    done
    
    print_success "All MCP servers prepared"
    
    # Note: MCP servers are started on-demand by Claude Code when needed
    # The .mcp.json configuration file tells Claude Code how to start them
    
    if [ -f "$PROJECT_ROOT/.mcp.json" ]; then
        print_success "MCP configuration found at .mcp.json"
        print_status "MCP servers will be started on-demand by Claude Code"
    else
        print_warning "No .mcp.json configuration found"
    fi
}

# Main execution
if [ "$1" == "stop" ]; then
    print_status "MCP servers are managed by Claude Code and will stop automatically"
else
    start_mcp_servers
fi