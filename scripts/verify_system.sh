#!/bin/bash
# BoarderframeOS System Verification Script

echo "🔍 BoarderframeOS System Verification"
echo "======================================="

# Check Docker
echo -n "🐳 Docker Desktop: "
if docker info >/dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not running - please start Docker Desktop"
    exit 1
fi

# Check Docker containers
echo -n "🗄️ PostgreSQL Container: "
if docker ps --format "table {{.Names}}" | grep -q boarderframeos_postgres; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

echo -n "🗄️ Redis Container: "
if docker ps --format "table {{.Names}}" | grep -q boarderframeos_redis; then
    echo "✅ Running"
else
    echo "❌ Not running"
fi

# Check PostgreSQL connection
echo -n "🔌 PostgreSQL Connection: "
if docker exec boarderframeos_postgres psql -U boarderframe -d boarderframeos -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "❌ Connection failed"
fi

# Check Redis connection
echo -n "🔌 Redis Connection: "
if docker exec boarderframeos_redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "❌ Connection failed"
fi

# Check key ports
ports=(8000 8001 8004 8005 8006 8007 8008 8009 8888)
echo ""
echo "🔌 Port Status:"
for port in "${ports[@]}"; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "   Port $port: ✅ In use"
    else
        echo "   Port $port: ❌ Available"
    fi
done

# Check Python environment
echo ""
echo -n "🐍 Python Version: "
python_version=$(python --version 2>&1)
echo "$python_version"

if [[ "$python_version" == *"3.13"* ]] || [[ "$python_version" == *"3.12"* ]] || [[ "$python_version" == *"3.11"* ]]; then
    echo "   ✅ Compatible version"
else
    echo "   ⚠️  Recommend Python 3.11+"
fi

# Check system status
echo ""
echo "📊 System Status:"
if python system_status.py 2>/dev/null | grep -q "OPERATIONAL"; then
    echo "   ✅ System operational"
else
    echo "   ⚠️  System status unclear"
fi

# Check BCC accessibility
echo ""
echo -n "🎛️ BCC Dashboard: "
if curl -s http://localhost:8888 >/dev/null 2>&1; then
    echo "✅ Accessible at http://localhost:8888"
else
    echo "❌ Not accessible"
fi

echo ""
echo "======================================="
echo "🏁 Verification complete!"
echo ""
echo "To start the system: python startup.py"
echo "To check status: python system_status.py"
echo "Dashboard: http://localhost:8888"