#!/bin/bash

# MCP Server Management Interface Startup Script

echo "🔧 Starting MCP Server Management Interface..."
echo "=========================================="

# Check if we're in the right directory
if [[ ! -f "mcp_manager.py" ]]; then
    echo "❌ Error: mcp_manager.py not found. Please run this script from the management directory."
    exit 1
fi

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python3 -c "import fastapi, uvicorn, psutil" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "❌ Missing dependencies. Installing..."
    pip3 install fastapi uvicorn psutil
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p ../logs

# Make the API server executable
chmod +x api_server.py

echo "🚀 Starting FastAPI server..."
echo "📊 Dashboard: http://localhost:8090"
echo "📡 API: http://localhost:8090/api/"
echo "❤️  Health: http://localhost:8090/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="

# Start the server
python3 api_server.py