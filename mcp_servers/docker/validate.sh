#!/bin/bash

# MCP Server Manager - Configuration Validation Script
# Validates Docker setup and configuration files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🔍 MCP Server Manager Configuration Validator${NC}"
echo "=============================================="

# Function to print colored output
print_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

ERRORS=0
WARNINGS=0

# Check Docker installation
echo -e "\n${BLUE}🐳 Docker Environment${NC}"
echo "===================="

if command -v docker >/dev/null 2>&1; then
    print_ok "Docker is installed ($(docker --version | cut -d' ' -f3 | cut -d',' -f1))"
else
    print_error "Docker is not installed"
    ((ERRORS++))
fi

if command -v docker-compose >/dev/null 2>&1; then
    print_ok "Docker Compose is installed ($(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1))"
else
    print_error "Docker Compose is not installed"
    ((ERRORS++))
fi

if docker info >/dev/null 2>&1; then
    print_ok "Docker daemon is running"
else
    print_error "Docker daemon is not running"
    ((ERRORS++))
fi

# Check file structure
echo -e "\n${BLUE}📁 File Structure${NC}"
echo "=================="

cd "$SCRIPT_DIR"

# Required files
required_files=(
    "Dockerfile"
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "docker-compose.dev.yml"
    ".env.template"
    "start.sh"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        print_ok "$file exists"
    else
        print_error "$file is missing"
        ((ERRORS++))
    fi
done

# Check if .env exists
if [[ -f ".env" ]]; then
    print_ok ".env file exists"
    
    # Check for default values that should be changed in production
    if grep -q "your-secret-key-change-this" .env 2>/dev/null; then
        print_warning ".env contains default secret keys - change these for production!"
        ((WARNINGS++))
    fi
    
    if grep -q "admin-change-this-password" .env 2>/dev/null; then
        print_warning ".env contains default admin password - change this for production!"
        ((WARNINGS++))
    fi
else
    print_warning ".env file not found - will use .env.template defaults"
    ((WARNINGS++))
fi

# Check directories
required_dirs=(
    "monitoring/prometheus"
    "monitoring/grafana"
    "nginx"
)

for dir in "${required_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
        print_ok "$dir directory exists"
    else
        print_warning "$dir directory is missing - will be created by Docker"
        ((WARNINGS++))
    fi
done

# Validate Docker Compose files
echo -e "\n${BLUE}🔧 Docker Compose Validation${NC}"
echo "============================="

compose_files=(
    "docker-compose.yml"
    "docker-compose.prod.yml" 
    "docker-compose.dev.yml"
)

for file in "${compose_files[@]}"; do
    if docker-compose -f "$file" config >/dev/null 2>&1; then
        print_ok "$file syntax is valid"
    else
        print_error "$file has syntax errors"
        ((ERRORS++))
    fi
done

# Check for port conflicts
echo -e "\n${BLUE}🔌 Port Availability${NC}"
echo "===================="

ports=(8080 3000 6379 9090 3001 11434)

for port in "${ports[@]}"; do
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i ":$port" >/dev/null 2>&1; then
            print_warning "Port $port is already in use"
            ((WARNINGS++))
        else
            print_ok "Port $port is available"
        fi
    else
        print_warning "Cannot check port $port (lsof not available)"
        ((WARNINGS++))
    fi
done

# Check disk space
echo -e "\n${BLUE}💾 System Resources${NC}"
echo "==================="

if command -v df >/dev/null 2>&1; then
    available_space=$(df -h . | awk 'NR==2 {print $4}' | sed 's/[^0-9.]//g')
    if [[ $(echo "$available_space > 5" | bc 2>/dev/null || echo "0") -eq 1 ]]; then
        print_ok "Sufficient disk space available"
    else
        print_warning "Low disk space - ensure at least 5GB free for Docker images and volumes"
        ((WARNINGS++))
    fi
fi

# Check for Docker images
echo -e "\n${BLUE}📦 Docker Images${NC}"
echo "================="

base_images=(
    "node:18-alpine"
    "redis:7-alpine" 
    "nginx:alpine"
    "prom/prometheus:latest"
    "grafana/grafana:latest"
)

for image in "${base_images[@]}"; do
    if docker image inspect "$image" >/dev/null 2>&1; then
        print_ok "$image is available locally"
    else
        print_warning "$image will be downloaded on first run"
        ((WARNINGS++))
    fi
done

# Security checks
echo -e "\n${BLUE}🔒 Security Configuration${NC}"
echo "=========================="

if [[ -f "Dockerfile" ]]; then
    if grep -q "USER mcpuser" Dockerfile; then
        print_ok "Dockerfile uses non-root user"
    else
        print_error "Dockerfile should specify non-root user"
        ((ERRORS++))
    fi
    
    if grep -q "no-new-privileges" docker-compose*.yml; then
        print_ok "Security options configured in compose files"
    else
        print_warning "Consider adding security options to compose files"
        ((WARNINGS++))
    fi
fi

# Summary
echo -e "\n${BLUE}📊 Validation Summary${NC}"
echo "===================="

if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
    print_ok "All checks passed! Your setup is ready to deploy."
elif [[ $ERRORS -eq 0 ]]; then
    echo -e "${YELLOW}Setup is functional with $WARNINGS warning(s).${NC}"
    echo "Consider addressing warnings before production deployment."
else
    echo -e "${RED}Setup has $ERRORS error(s) and $WARNINGS warning(s).${NC}"
    echo "Please fix errors before deployment."
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Run: ./start.sh -e development  (for development)"
echo "3. Run: ./start.sh -e production  (for production)"
echo ""