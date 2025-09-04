#!/bin/bash

# MCP Setup Verification Script
# Checks if all components are ready for startup

set -e

cd "$(dirname "$0")"

echo "🔍 MCP SETUP VERIFICATION"
echo "=========================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track issues
issues=0

# Function to check file exists
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $description: $file${NC}"
    else
        echo -e "${RED}❌ Missing: $description ($file)${NC}"
        ((issues++))
    fi
}

# Function to check directory exists
check_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $description: $dir${NC}"
    else
        echo -e "${RED}❌ Missing: $description ($dir)${NC}"
        ((issues++))
    fi
}

# Function to check Python dependencies
check_python_deps() {
    echo -e "${BLUE}📦 Checking Python dependencies...${NC}"
    
    if python3 -c "import fastapi, uvicorn, httpx, pydantic" 2>/dev/null; then
        echo -e "${GREEN}✅ Core Python dependencies available${NC}"
    else
        echo -e "${RED}❌ Missing Python dependencies - run: pip install -r requirements.txt${NC}"
        ((issues++))
    fi
    
    if python3 -c "import playwright" 2>/dev/null; then
        echo -e "${GREEN}✅ Playwright dependency available${NC}"
    else
        echo -e "${YELLOW}⚠️  Playwright not installed - some features may not work${NC}"
    fi
}

# Function to check Node.js setup
check_node_setup() {
    echo -e "${BLUE}📦 Checking Node.js setup...${NC}"
    
    if command -v node >/dev/null 2>&1; then
        node_version=$(node --version)
        echo -e "${GREEN}✅ Node.js available: $node_version${NC}"
    else
        echo -e "${RED}❌ Node.js not found - required for frontend UI${NC}"
        ((issues++))
    fi
    
    if command -v npm >/dev/null 2>&1; then
        npm_version=$(npm --version)
        echo -e "${GREEN}✅ npm available: $npm_version${NC}"
    else
        echo -e "${RED}❌ npm not found - required for frontend UI${NC}"
        ((issues++))
    fi
    
    if [ -d "frontend" ]; then
        if [ -f "frontend/package.json" ]; then
            echo -e "${GREEN}✅ Frontend package.json exists${NC}"
        else
            echo -e "${RED}❌ frontend/package.json missing${NC}"
            ((issues++))
        fi
    fi
}

echo -e "${BLUE}🗂️  Checking MCP server files...${NC}"
check_file "simple_filesystem_server.py" "Simple Filesystem Server"
check_file "advanced_filesystem_server.py" "Advanced Filesystem Server"  
check_file "simple_playwright_server.py" "Playwright Server"
check_file "kroger_mcp_server.py" "Kroger MCP Server"

echo
echo -e "${BLUE}⚙️  Checking configuration files...${NC}"
check_file ".env" "Environment configuration"
check_file "requirements.txt" "Python requirements"

echo
echo -e "${BLUE}📁 Checking directories...${NC}"
check_directory "frontend" "Frontend UI directory"

echo
echo -e "${BLUE}🔧 Checking management scripts...${NC}"
check_file "start_all_mcp_servers.sh" "Startup script"
check_file "stop_all_mcp_servers.sh" "Stop script"
check_file "status_mcp_servers.sh" "Status script"

echo
check_python_deps

echo
check_node_setup

echo
echo -e "${BLUE}🔍 Checking for running processes on target ports...${NC}"
for port in 5173 9001 9002 9003 9004; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        pid=$(lsof -ti:$port)
        echo -e "${YELLOW}⚠️  Port $port already in use (PID: $pid)${NC}"
    else
        echo -e "${GREEN}✅ Port $port available${NC}"
    fi
done

echo
echo "=========================="
if [ $issues -eq 0 ]; then
    echo -e "${GREEN}🎉 SETUP VERIFICATION PASSED!${NC}"
    echo -e "${GREEN}   All components are ready for startup${NC}"
    echo
    echo -e "${BLUE}🚀 Ready to start:${NC}"
    echo "   ./start_all_mcp_servers.sh"
    exit 0
else
    echo -e "${RED}❌ SETUP VERIFICATION FAILED!${NC}"
    echo -e "${RED}   Found $issues issue(s) that need to be resolved${NC}"
    echo
    echo -e "${BLUE}💡 Next steps:${NC}"
    if [ $issues -gt 0 ]; then
        echo "   1. Fix the issues listed above"
        echo "   2. Run this script again"
        echo "   3. Use ./start_all_mcp_servers.sh when ready"
    fi
    exit 1
fi