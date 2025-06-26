#!/bin/bash
# Quick start script for BoarderframeOS on new machine

echo "🏰 BoarderframeOS Quick Start for New Machine"
echo "============================================="
echo ""

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "👉 Please start Docker Desktop first, then run this script again."
    echo ""
    echo "To start Docker Desktop:"
    echo "1. Open Finder"
    echo "2. Go to Applications"
    echo "3. Double-click Docker"
    echo "4. Wait for the whale icon to appear in menu bar"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start PostgreSQL and Redis containers
echo "🚀 Starting PostgreSQL and Redis containers..."
docker-compose up -d postgresql redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to initialize (30 seconds)..."
sleep 30

# Check if PostgreSQL is responding
echo "🔍 Checking PostgreSQL connection..."
docker exec boarderframeos_postgres psql -U boarderframe -d boarderframeos -c "SELECT version();" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL may still be initializing. Continuing anyway..."
fi

# Activate virtual environment and start BoarderframeOS
echo ""
echo "🏁 Starting BoarderframeOS..."
echo ""

source .venv/bin/activate
python startup.py

echo ""
echo "📌 If startup.py completes successfully:"
echo "   - Corporate HQ UI: http://localhost:8888"
echo "   - Agent Cortex: http://localhost:8889"
echo "   - Check system status: python system_status.py"