#!/bin/bash

# MCP Server Manager - Startup Script
# This script helps you start the MCP Server Manager with the appropriate configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 MCP Server Manager Deployment Script${NC}"
echo "======================================"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

# Change to docker directory
cd "$SCRIPT_DIR"

# Check for environment file
if [[ ! -f .env ]]; then
    print_warning "No .env file found. Creating from template..."
    cp .env.template .env
    print_warning "Please edit .env file with your configuration before running in production!"
fi

# Parse command line arguments
ENVIRONMENT="development"
BUILD=false
CLEAN=false
DETACH=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -f|--foreground)
            DETACH=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --env ENVIRONMENT    Environment to deploy (development|production) [default: development]"
            echo "  -b, --build             Force rebuild of Docker images"
            echo "  -c, --clean             Clean up containers and volumes before starting"
            echo "  -f, --foreground        Run in foreground (don't detach)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Start in development mode"
            echo "  $0 -e production -b                  # Start in production mode with rebuild"
            echo "  $0 -c -e development                 # Clean start in development"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information."
            exit 1
            ;;
    esac
done

print_status "Starting MCP Server Manager in $ENVIRONMENT mode..."

# Compose file selection
COMPOSE_FILES="-f docker-compose.yml"
if [[ "$ENVIRONMENT" == "production" ]]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.prod.yml"
elif [[ "$ENVIRONMENT" == "development" ]]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.dev.yml"
fi

# Clean up if requested
if [[ "$CLEAN" == true ]]; then
    print_status "Cleaning up existing containers and volumes..."
    docker-compose $COMPOSE_FILES down -v --remove-orphans 2>/dev/null || true
fi

# Build if requested
if [[ "$BUILD" == true ]]; then
    print_status "Building Docker images..."
    docker-compose $COMPOSE_FILES build --no-cache
fi

# Start services
print_status "Starting services..."
if [[ "$DETACH" == true ]]; then
    docker-compose $COMPOSE_FILES up -d
else
    docker-compose $COMPOSE_FILES up
fi

if [[ "$DETACH" == true ]]; then
    echo ""
    print_status "Services started successfully!"
    echo ""
    echo "Service URLs:"
    echo "  📊 MCP Manager:    http://localhost:8080"
    echo "  💬 Open WebUI:     http://localhost:3000"
    echo "  🤖 Ollama API:     http://localhost:11434"
    echo "  📈 Prometheus:     http://localhost:9090"
    echo "  📊 Grafana:        http://localhost:3001"
    echo "  🗄️  Redis:          localhost:6379"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        echo "  🌐 Load Balancer:  http://localhost:80"
    fi
    
    echo ""
    echo "To view logs: docker-compose $COMPOSE_FILES logs -f"
    echo "To stop:      docker-compose $COMPOSE_FILES down"
    echo ""
    
    # Show service status
    print_status "Service Status:"
    docker-compose $COMPOSE_FILES ps
fi