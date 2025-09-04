#!/bin/bash

# MCP Server Manager Quick Start Script
# Demonstrates deployment options with the enhanced Docker setup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create environment file if it doesn't exist
setup_environment() {
    log "Setting up environment configuration..."
    
    if [[ ! -f .env ]]; then
        log "Creating .env file from template..."
        cp .env.example .env
        
        # Generate secure secrets
        WEBUI_SECRET=$(openssl rand -hex 32)
        GRAFANA_PASSWORD=$(openssl rand -base64 16)
        
        # Update .env with generated secrets
        sed -i.bak "s/your-webui-secret-key-change-this/$WEBUI_SECRET/" .env
        sed -i.bak "s/your-grafana-admin-password/$GRAFANA_PASSWORD/" .env
        
        warning "Please review and update the .env file with your specific configuration"
        success "Environment file created with secure defaults"
    else
        log "Environment file already exists"
    fi
}

# Development deployment
deploy_development() {
    log "Starting development deployment..."
    
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    success "Development environment started!"
    echo ""
    echo "Services available at:"
    echo "  - MCP Manager:    http://localhost:8080"
    echo "  - Open WebUI:     http://localhost:3000"
    echo "  - Prometheus:     http://localhost:9090"
    echo "  - Grafana:        http://localhost:3001"
    echo "  - Redis:          localhost:6379"
}

# Production deployment
deploy_production() {
    log "Starting production deployment..."
    
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    success "Production environment started!"
    echo ""
    echo "Services available at:"
    echo "  - Load Balancer:  http://localhost:80 (https://localhost:443 if SSL configured)"
    echo "  - MCP Manager:    http://localhost:8080"
    echo "  - Open WebUI:     http://localhost:3000"
    echo "  - Prometheus:     http://localhost:9090"
    echo "  - Grafana:        http://localhost:3001"
}

# Start with backup service
deploy_with_backup() {
    log "Starting deployment with backup service..."
    
    docker-compose --profile backup -f docker-compose.yml up -d
    
    success "Environment with backup service started!"
    echo ""
    echo "Backup service is running with schedule: ${BACKUP_SCHEDULE:-0 2 * * *}"
    echo "To run manual backup: docker exec mcp-backup-service /backup.sh full"
}

# Start with monitoring
deploy_with_monitoring() {
    log "Starting deployment with health monitoring..."
    
    docker-compose --profile monitoring -f docker-compose.yml up -d
    
    success "Environment with health monitoring started!"
    echo ""
    echo "Health monitoring is running with interval: ${HEALTH_CHECK_INTERVAL:-300}s"
    echo "Check logs: docker logs mcp-health-monitor"
}

# Complete deployment (all services)
deploy_complete() {
    log "Starting complete deployment with all services..."
    
    docker-compose --profile backup --profile monitoring -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    success "Complete environment started!"
    echo ""
    echo "All services are running:"
    echo "  - Main application stack"
    echo "  - Automated backups"
    echo "  - Health monitoring"
    echo "  - Production optimizations"
}

# Show running services
show_status() {
    log "Checking service status..."
    
    echo ""
    echo "Container Status:"
    docker-compose ps
    
    echo ""
    echo "Health Check Status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(mcp-|NAMES)"
    
    echo ""
    echo "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Run health check
run_health_check() {
    log "Running comprehensive health check..."
    
    if docker ps --filter "name=mcp-health-monitor" --filter "status=running" --format "{{.Names}}" | grep -q mcp-health-monitor; then
        docker exec mcp-health-monitor /scripts/health-monitor.sh
    else
        ./health-check.sh check
    fi
}

# Stop all services
stop_services() {
    log "Stopping all services..."
    
    docker-compose --profile backup --profile monitoring -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.dev.yml down --remove-orphans
    
    success "All services stopped"
}

# Clean up (including volumes)
cleanup() {
    log "Cleaning up all resources..."
    
    warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose --profile backup --profile monitoring -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.dev.yml down --volumes --remove-orphans
        docker system prune -f
        success "Cleanup completed"
    else
        log "Cleanup cancelled"
    fi
}

# Show usage
show_usage() {
    echo "MCP Server Manager Deployment Script"
    echo ""
    echo "Usage: $0 {command}"
    echo ""
    echo "Commands:"
    echo "  dev          - Start development environment"
    echo "  prod         - Start production environment"
    echo "  backup       - Start with backup service"
    echo "  monitoring   - Start with health monitoring"
    echo "  complete     - Start complete environment (all services)"
    echo "  status       - Show service status"
    echo "  health       - Run health check"
    echo "  stop         - Stop all services"
    echo "  cleanup      - Remove all containers and volumes"
    echo "  help         - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Start development environment"
    echo "  $0 prod                   # Start production environment"
    echo "  $0 complete               # Start all services"
    echo "  $0 health                 # Run health check"
    echo ""
    echo "Environment variables can be set in .env file"
}

# Main script logic
main() {
    check_prerequisites
    setup_environment
    
    case "${1:-help}" in
        "dev"|"development")
            deploy_development
            ;;
        "prod"|"production")
            deploy_production
            ;;
        "backup")
            deploy_with_backup
            ;;
        "monitoring")
            deploy_with_monitoring
            ;;
        "complete"|"all")
            deploy_complete
            ;;
        "status")
            show_status
            ;;
        "health")
            run_health_check
            ;;
        "stop")
            stop_services
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|*)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"