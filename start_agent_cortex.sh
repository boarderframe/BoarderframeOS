#!/bin/bash
# Agent Cortex Manual Startup Script
# Created by BoarderframeOS startup system

echo "🧠 Starting Agent Cortex Management UI..."
echo "📍 Working directory: $(pwd)"
echo "🔧 Using Python: $(which python)"

# Set up environment
export PYTHONPATH="/Users/cosburn/BoarderframeOS"
export BOARDERFRAME_STARTUP="0"  # Mark as manual start

# Kill any existing processes
pkill -f "agent_cortex_management.py" 2>/dev/null
pkill -f "agent_cortex_launcher.py" 2>/dev/null
pkill -f "agent_cortex_simple_launcher.py" 2>/dev/null

# Start Agent Cortex using the simple launcher
echo "🚀 Launching Agent Cortex..."
python ui/agent_cortex_simple_launcher.py

echo "✅ Agent Cortex Management UI should now be available at http://localhost:8889"