#!/bin/bash
# Start BoarderframeOS

echo "Starting BoarderframeOS..."

# Activate virtual environment
source venv/bin/activate

# Start MCP servers in background
echo "Starting MCP servers..."
python mcp-servers/filesystem_server.py &
MCP_PID=$!

# Wait for servers to start
sleep 2

# Initialize system if needed
if [ ! -f "boarderframe.yaml" ]; then
    echo "Initializing BoarderframeOS..."
    ./boarderctl init
fi

# Show status
./boarderctl status

echo ""
echo "BoarderframeOS is ready!"
echo "Try these commands:"
echo "  ./boarderctl zone create executive"
echo "  ./boarderctl agent create jarvis"
echo "  ./boarderctl agent start jarvis"
echo ""
echo "Press Ctrl+C to stop"

# Keep running
wait $MCP_PID
