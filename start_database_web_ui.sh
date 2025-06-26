#!/bin/bash
# Start Adminer Web UI for PostgreSQL Database Management

echo "🚀 Starting Adminer Database Web UI..."
echo "=================================================="

# Check if main PostgreSQL is running
if ! docker ps | grep -q boarderframeos_postgres; then
    echo "⚠️  PostgreSQL container is not running!"
    echo "Please start it first with: docker-compose up -d postgresql"
    exit 1
fi

# Start Adminer
docker-compose -f docker-compose.adminer.yml up -d

# Wait for Adminer to start
echo "⏳ Waiting for Adminer to start..."
sleep 3

# Check if Adminer is running
if docker ps | grep -q boarderframeos_adminer; then
    echo "✅ Adminer is running!"
    echo ""
    echo "📊 Database Web UI Access:"
    echo "=================================================="
    echo "🌐 URL: http://localhost:8081"
    echo ""
    echo "🔐 Connection Details:"
    echo "   System:   PostgreSQL"
    echo "   Server:   boarderframeos_postgres"
    echo "   Username: boarderframe"
    echo "   Password: boarderframe_secure_2025"
    echo "   Database: boarderframeos"
    echo "=================================================="
    echo ""
    echo "💡 Tips:"
    echo "   - Leave 'Server' field as: boarderframeos_postgres"
    echo "   - Or use: host.docker.internal:5434 for localhost"
    echo "   - To stop: docker-compose -f docker-compose.adminer.yml down"
    echo ""

    # Try to open in browser (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:8081
    fi
else
    echo "❌ Failed to start Adminer"
    docker logs boarderframeos_adminer
fi
