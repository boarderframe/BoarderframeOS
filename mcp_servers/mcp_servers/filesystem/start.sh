#!/bin/bash

# File System MCP Server Startup Script

# Set the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT/.venv/lib/python3.13/site-packages:$PYTHONPATH"

# Start the MCP server
echo "Starting File System MCP Server..."
echo "Server directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"

cd "$SCRIPT_DIR"
python main.py