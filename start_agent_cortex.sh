#!/bin/bash
# Agent Cortex Manual Startup Script
# Created by BoarderframeOS startup system

echo "🧠 Starting Agent Cortex Management UI..."
echo "📍 Working directory: $(pwd)"
echo "🔧 Using Python: $(which python)"

# Set up environment
export PYTHONPATH="/Users/cosburn/BoarderframeOS"

# Kill any existing processes
pkill -f "agent_cortex_management.py" 2>/dev/null

# Start Agent Cortex
echo "🚀 Launching Agent Cortex..."
python ui/agent_cortex_management.py

echo "✅ Agent Cortex Management UI should now be available at http://localhost:8889"