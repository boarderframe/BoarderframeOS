#!/bin/bash
# Persistent UI runner that keeps restarting

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Persistent BoarderframeOS UI..."
echo "📍 Dashboard will be available at: http://localhost:8888"
echo "🔄 Server will auto-restart if it goes down"
echo ""

# Function to check if server is running
check_server() {
    curl -s http://localhost:8888/health > /dev/null 2>&1
    return $?
}

# Kill any existing Python servers on port 8888
pkill -f "python.*8888" 2>/dev/null
pkill -f "stable_ui.py" 2>/dev/null
sleep 2

# Start the server loop
attempt=1
while true; do
    echo "🚀 Starting UI server (attempt $attempt)..."
    
    # Start server in background
    python stable_ui.py &
    SERVER_PID=$!
    
    # Give it time to start
    sleep 3
    
    # Check if it's running
    if check_server; then
        echo "✅ Server is running on http://localhost:8888"
        echo "🌐 Opening browser..."
        
        # Open browser (macOS)
        if command -v open >/dev/null 2>&1; then
            open http://localhost:8888
        fi
        
        # Monitor the server
        while kill -0 $SERVER_PID 2>/dev/null; do
            if ! check_server; then
                echo "⚠️  Server stopped responding, restarting..."
                kill $SERVER_PID 2>/dev/null
                break
            fi
            sleep 10
        done
    else
        echo "❌ Server failed to start"
        kill $SERVER_PID 2>/dev/null
    fi
    
    attempt=$((attempt + 1))
    
    if [ $attempt -gt 5 ]; then
        echo "❌ Failed to start after 5 attempts. Exiting."
        exit 1
    fi
    
    echo "🔄 Restarting in 3 seconds..."
    sleep 3
done