#!/bin/bash

# Open WebUI Development Environment Status Checker

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ $service_name${NC} - Running on port $port"
        if [ ! -z "$url" ]; then
            echo -e "     🌐 $url"
        fi
        return 0
    else
        echo -e "  ${RED}❌ $service_name${NC} - Not running on port $port"
        return 1
    fi
}

echo -e "${BLUE}🔍 Open WebUI Development Environment Status${NC}"
echo ""

total_services=5
running_services=0

# Check each service
if check_service "LiteLLM Proxy Server" 4000 "http://localhost:4000"; then
    ((running_services++))
fi

if check_service "LangGraph Multi-Agent Backend" 9000 "http://localhost:9000"; then
    ((running_services++))
fi

if check_service "Open WebUI Pipelines" 9999 "http://localhost:9999"; then
    ((running_services++))
fi

if check_service "Open WebUI Backend" 8080 "http://localhost:8080"; then
    ((running_services++))
fi

if check_service "Open WebUI Frontend" 5173 "http://localhost:5173"; then
    ((running_services++))
fi

echo ""
echo -e "${BLUE}📊 Summary: $running_services/$total_services services running${NC}"

if [ $running_services -eq $total_services ]; then
    echo -e "${GREEN}🎉 All services are running! Environment is ready.${NC}"
    echo -e "${GREEN}🌐 Access Open WebUI at: http://localhost:5173${NC}"
elif [ $running_services -eq 0 ]; then
    echo -e "${RED}❌ No services are running. Run ./start_dev_environment.sh to start.${NC}"
else
    echo -e "${YELLOW}⚠️  Some services are not running. Check logs or restart environment.${NC}"
fi

echo ""
echo -e "${BLUE}🛠️  Commands:${NC}"
echo "  Start all:  ./start_dev_environment.sh"
echo "  Stop all:   ./stop_dev_environment.sh"
echo "  Check logs: tail -f logs/[service].log"