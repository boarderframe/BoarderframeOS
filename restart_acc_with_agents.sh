#!/bin/bash
# Restart ACC with agents to test the response flow fix

echo "🔄 Restarting ACC and Agents..."
echo "================================"

# Kill existing processes
echo "Stopping existing processes..."
pkill -f "agent_communication_center_enhanced.py" 2>/dev/null || true
pkill -f "solomon_acc.py" 2>/dev/null || true
pkill -f "david_acc.py" 2>/dev/null || true

sleep 2

# Start ACC
echo -e "\n1️⃣ Starting ACC server..."
python agent_communication_center_enhanced.py > /tmp/acc_server.log 2>&1 &
ACC_PID=$!
echo "   ACC PID: $ACC_PID"

# Wait for ACC to start
echo "   Waiting for ACC to initialize..."
sleep 5

# Check if ACC is running
if curl -s http://localhost:8890/health > /dev/null; then
    echo "   ✅ ACC is running!"
else
    echo "   ❌ ACC failed to start. Check /tmp/acc_server.log"
    exit 1
fi

# Start agents
echo -e "\n2️⃣ Starting agents..."
cd agents/solomon && python solomon_acc.py > /tmp/solomon_acc.log 2>&1 &
SOLOMON_PID=$!
echo "   Solomon PID: $SOLOMON_PID"

cd ../david && python david_acc.py > /tmp/david_acc.log 2>&1 &
DAVID_PID=$!
echo "   David PID: $DAVID_PID"

cd ../..

# Wait for agents to connect
echo -e "\n3️⃣ Waiting for agents to connect..."
sleep 3

# Check agent status
echo -e "\n4️⃣ Checking agent status..."
curl -s http://localhost:8890/api/agents/solomon/presence | python -m json.tool
curl -s http://localhost:8890/api/agents/david/presence | python -m json.tool

echo -e "\n✅ ACC and agents are running!"
echo "================================"
echo "ACC UI: http://localhost:8890"
echo ""
echo "Logs:"
echo "  ACC: tail -f /tmp/acc_server.log"
echo "  Solomon: tail -f /tmp/solomon_acc.log"
echo "  David: tail -f /tmp/david_acc.log"
echo ""
echo "PIDs:"
echo "  ACC: $ACC_PID"
echo "  Solomon: $SOLOMON_PID"
echo "  David: $DAVID_PID"