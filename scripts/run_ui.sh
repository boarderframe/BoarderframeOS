#!/bin/bash
# Persistent Control Center runner that keeps restarting

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🚀 Starting Persistent BoarderframeOS Control Center..."
echo "📍 Control Center will be available at: http://localhost:8501"
echo "🔄 Server will auto-restart if it goes down"
echo ""

# Function to check if server is running
check_server() {
    curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1
    return $?
}

# Kill any existing Streamlit servers
pkill -f "streamlit" 2>/dev/null
sleep 2

# Start the server loop
attempt=1
while true; do
    echo "🚀 Starting Control Center (attempt $attempt)..."

    # Start streamlit in background
    streamlit run boarderframeos_ctl.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &
    SERVER_PID=$!

    # Give it time to start
    sleep 5

    # Check if it's running
    if check_server; then
        echo "✅ Control Center is running on http://localhost:8501"
        echo "🌐 Opening browser..."

        # Open browser (macOS)
        if command -v open >/dev/null 2>&1; then
            open http://localhost:8501
        fi

        # Monitor the server
        while kill -0 $SERVER_PID 2>/dev/null; do
            if ! check_server; then
                echo "⚠️  Control Center stopped responding, restarting..."
                kill $SERVER_PID 2>/dev/null
                break
            fi
            sleep 10
        done
    else
        echo "❌ Control Center failed to start"
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
