#!/bin/bash

# MCP Server Manager Deployment Script
# Production-ready deployment with health checks and rollback capability

set -euo pipefail

# Configuration
COMPOSE_PROJECT_NAME="mcp-server-manager"
ENVIRONMENT="${1:-production}"
BACKUP_DIR="./backups"
HEALTH_CHECK_TIMEOUT=60
ROLLBACK_ENABLED=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    if [[ "$ENVIRONMENT" == "production" && ! -f ".env" ]]; then
        error "Production environment file (.env) not found"
        error "Copy .env.example to .env and configure for production"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create backup of current deployment
create_backup() {
    if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
        log "Creating backup of current deployment..."
        
        mkdir -p "$BACKUP_DIR"
        BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
        
        # Backup volumes
        docker-compose ps -q | xargs -r docker inspect | \
            jq -r '.[].Mounts[] | select(.Type == "volume") | .Name' | \
            sort -u > "$BACKUP_DIR/$BACKUP_NAME-volumes.txt"
        
        # Export container configurations
        docker-compose config > "$BACKUP_DIR/$BACKUP_NAME-compose.yml"
        
        success "Backup created: $BACKUP_NAME"
    fi
}

# Health check function
health_check() {
    local service=$1
    local endpoint=$2
    local max_attempts=$3
    
    log "Performing health check for $service..."
    
    for i in $(seq 1 $max_attempts); do
        if curl -f -s "$endpoint" > /dev/null 2>&1; then
            success "$service is healthy"
            return 0
        fi
        
        if [[ $i -lt $max_attempts ]]; then
            warning "$service not ready, attempt $i/$max_attempts. Waiting 5 seconds..."
            sleep 5
        fi
    done
    
    error "$service health check failed after $max_attempts attempts"
    return 1
}

# Deploy application
deploy() {
    log "Starting deployment for environment: $ENVIRONMENT"
    
    # Set compose files based on environment
    local compose_files="-f docker-compose.yml"
    if [[ "$ENVIRONMENT" == "development" ]]; then
        compose_files="$compose_files -f docker-compose.dev.yml"
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        compose_files="$compose_files -f docker-compose.prod.yml"
    fi
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose $compose_files pull
    
    # Build application image
    log "Building application image..."
    docker-compose $compose_files build --no-cache mcp-manager
    
    # Start services
    log "Starting services..."
    docker-compose $compose_files up -d
    
    # Wait for services to start
    sleep 10
    
    # Perform health checks
    local health_checks_passed=true
    
    # Check FastAPI MCP Manager
    if ! health_check "FastAPI MCP Manager" "http://localhost:8000/health" 12; then
        health_checks_passed=false
    fi
    
    # Check Open WebUI
    if ! health_check "Open WebUI" "http://localhost:3000/health" 12; then
        health_checks_passed=false
    fi
    
    # Check PostgreSQL (using pg_isready through docker)
    if docker-compose $compose_files exec -T postgres pg_isready -U mcpuser -d mcpdb >/dev/null 2>&1; then
        success "PostgreSQL is healthy"
    else
        warning "PostgreSQL health check failed, but continuing deployment"
    fi
    
    if [[ "$health_checks_passed" == "true" ]]; then
        success "Deployment completed successfully!"
        
        # Show service status
        log "Service status:"
        docker-compose $compose_files ps
        
        # Show URLs
        log "Access URLs:"
        echo "  - FastAPI MCP Manager API: http://localhost:8000"
        echo "  - Open WebUI: http://localhost:3000"
        echo "  - Grafana: http://localhost:3001"
        echo "  - Prometheus: http://localhost:9090"
        echo "  - PostgreSQL: localhost:5432 (database: mcpdb)"
        
    else
        error "Health checks failed. Deployment may have issues."
        
        if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
            warning "Consider running rollback: ./deploy.sh rollback"
        fi
        
        exit 1
    fi
}

# Rollback function
rollback() {
    log "Starting rollback process..."
    
    # Stop current services
    docker-compose down
    
    # Find latest backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/*-compose.yml 2>/dev/null | head -n1)
    
    if [[ -n "$latest_backup" ]]; then
        log "Rolling back to: $(basename "$latest_backup")"
        
        # Restore from backup
        docker-compose -f "$latest_backup" up -d
        
        success "Rollback completed"
    else
        error "No backup found for rollback"
        exit 1
    fi
}

# Clean up old resources
cleanup() {
    log "Cleaning up old resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove old backups (keep last 5)
    if [[ -d "$BACKUP_DIR" ]]; then
        ls -t "$BACKUP_DIR"/*-compose.yml 2>/dev/null | tail -n +6 | xargs -r rm
    fi
    
    success "Cleanup completed"
}

# Stop services
stop() {
    log "Stopping services..."
    docker-compose down
    success "Services stopped"
}

# Show logs
logs() {
    local service=${1:-}
    if [[ -n "$service" ]]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        check_prerequisites
        create_backup
        deploy
        ;;
    "rollback")
        rollback
        ;;
    "stop")
        stop
        ;;
    "cleanup")
        cleanup
        ;;
    "logs")
        logs "${2:-}"
        ;;
    "status")
        docker-compose ps
        ;;
    "health")
        health_check "FastAPI MCP Manager" "http://localhost:8000/health" 3
        health_check "Open WebUI" "http://localhost:3000/health" 3
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|stop|cleanup|logs|status|health} [environment]"
        echo ""
        echo "Commands:"
        echo "  deploy [dev|production]  - Deploy the application (default: production)"
        echo "  rollback                 - Rollback to previous deployment"
        echo "  stop                     - Stop all services"
        echo "  cleanup                  - Clean up old Docker resources"
        echo "  logs [service]           - Show logs for all services or specific service"
        echo "  status                   - Show service status"
        echo "  health                   - Perform health checks"
        echo ""
        echo "Examples:"
        echo "  $0 deploy production     - Deploy to production"
        echo "  $0 deploy development    - Deploy to development"
        echo "  $0 logs mcp-manager      - Show logs for MCP manager"
        echo "  $0 rollback              - Rollback deployment"
        exit 1
        ;;
esac