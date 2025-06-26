#!/bin/bash
# Launch Enhanced Agent Communication Center

echo "🚀 Starting Enhanced Agent Communication Center..."

# Check if PostgreSQL is running
if ! nc -z localhost 5434 2>/dev/null; then
    echo "❌ PostgreSQL is not running on port 5434"
    echo "   Please start PostgreSQL first: docker-compose up -d postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo "🌟 Launching Enhanced ACC on port 8890..."
python agent_communication_center_enhanced.py
