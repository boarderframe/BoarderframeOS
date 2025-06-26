#!/bin/bash
# Comprehensive ACC and Agent Startup Script

echo "🚀 BoarderframeOS ACC Communication System Startup"
echo "=================================================="

# Function to check if process is running
check_process() {
    if pgrep -f "$1" > /dev/null; then
        echo "✅ $2 is running"
        return 0
    else
        echo "❌ $2 is not running"
        return 1
    fi
}

# Function to stop all related processes
stop_all() {
    echo ""
    echo "🛑 Stopping all ACC-related processes..."
    
    # Kill ACC
    pkill -f "agent_communication_center" 2>/dev/null
    
    # Kill agents
    pkill -f "solomon_acc.py" 2>/dev/null
    pkill -f "david_acc.py" 2>/dev/null
    pkill -f "agents/solomon/solomon.py" 2>/dev/null
    pkill -f "agents/david/david.py" 2>/dev/null
    
    sleep 2
    echo "✅ All processes stopped"
}

# Stop everything first
stop_all

# Create logs directory if it doesn't exist
mkdir -p logs/agents

# Start ACC
echo ""
echo "🌐 Starting Agent Communication Center..."
python agent_communication_center_enhanced.py > logs/acc_startup.log 2>&1 &
ACC_PID=$!

# Wait for ACC to start
echo "⏳ Waiting for ACC to initialize..."
sleep 3

# Check if ACC is running
if curl -s http://localhost:8890/health > /dev/null 2>&1; then
    echo "✅ ACC is running at http://localhost:8890"
else
    echo "❌ ACC failed to start! Check logs/acc_startup.log"
    exit 1
fi

# Start agents with ACC integration
echo ""
echo "🤖 Starting Agents with ACC Integration..."

# Start Solomon
echo "Starting Solomon..."
cd agents/solomon
python solomon_acc.py > ../../logs/solomon_acc_startup.log 2>&1 &
SOLOMON_PID=$!
cd ../..

# Start David
echo "Starting David..."
cd agents/david
python david_acc.py > ../../logs/david_acc_startup.log 2>&1 &
DAVID_PID=$!
cd ../..

# Wait for agents to connect
echo "⏳ Waiting for agents to connect..."
sleep 3

# Check agent status
echo ""
echo "📊 System Status:"
echo "-----------------"

# Check ACC
if check_process "agent_communication_center" "ACC"; then
    echo "   URL: http://localhost:8890"
fi

# Check agents
check_process "solomon_acc.py" "Solomon (ACC)"
check_process "david_acc.py" "David (ACC)"

# Show WebSocket connections
echo ""
echo "🔌 Checking ACC connections..."
curl -s http://localhost:8890/health 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'   WebSocket connections: {data.get(\"websocket_connections\", 0)}')
    print(f'   Database connected: {data.get(\"database_connected\", False)}')
except:
    print('   Could not get ACC status')
"

# Test agent availability
echo ""
echo "🧪 Testing agent availability..."
curl -s http://localhost:8890/api/agents 2>/dev/null | python3 -c "
import sys, json
try:
    agents = json.load(sys.stdin)
    online = [a for a in agents if a.get('status') == 'online']
    print(f'   Online agents: {[a[\"name\"] for a in online]}')
except:
    print('   Could not get agent status')
"

echo ""
echo "✅ Startup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Open ACC UI: http://localhost:8890"
echo "2. Click on Solomon or David to start a chat"
echo "3. Send a message - you should see responses!"
echo ""
echo "📝 Logs available at:"
echo "   - logs/acc_startup.log"
echo "   - logs/solomon_acc_startup.log"
echo "   - logs/david_acc_startup.log"