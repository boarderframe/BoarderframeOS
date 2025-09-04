#!/bin/bash
# Enhanced Production Deployment Script with Security Validation
# Deploys MCP Server Manager with comprehensive security checks and monitoring

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="${PROJECT_NAME:-mcp-server-manager}"
ENVIRONMENT="${ENVIRONMENT:-production}"
DRY_RUN="${DRY_RUN:-false}"
SKIP_SECURITY_CHECKS="${SKIP_SECURITY_CHECKS:-false}"
DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-300}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    exit 1
}

# Pre-deployment security checks
check_environment_security() {
    log "Performing pre-deployment security checks..."
    
    local security_issues=0
    
    # Check if running as root
    if [[ "$(id -u)" -eq 0 ]]; then
        warning "Running deployment as root user (not recommended for production)"
    fi
    
    # Check Docker daemon security
    if ! docker info --format '{{.SecurityOptions}}' | grep -q "name=seccomp"; then
        error "Docker daemon does not have seccomp enabled"
        ((security_issues++))
    fi
    
    # Check for Docker content trust
    if [[ "${DOCKER_CONTENT_TRUST:-}" != "1" ]]; then
        warning "Docker Content Trust is not enabled"
    fi
    
    # Check environment file permissions
    local env_files=(".env" ".env.production" ".env.prod")
    for env_file in "${env_files[@]}"; do
        if [[ -f "$env_file" ]]; then
            local perms
            perms=$(stat -c %a "$env_file" 2>/dev/null || stat -f %A "$env_file" 2>/dev/null || echo "unknown")
            if [[ "$perms" != "600" ]] && [[ "$perms" != "400" ]]; then
                warning "Environment file $env_file has insecure permissions: $perms"
            fi
        fi
    done
    
    # Check for secrets in environment variables
    if env | grep -i -E "(password|secret|key|token)" | grep -v -E "(SKIP_|CHECK_|_ENABLED)" >/dev/null; then
        warning "Potential secrets detected in environment variables"
    fi
    
    if [[ "$security_issues" -gt 0 ]]; then
        error "Security checks failed with $security_issues critical issues"
    fi
    
    success "Pre-deployment security checks passed"
}

# Validate configuration files
validate_configuration() {
    log "Validating configuration files..."
    
    # Check required files
    local required_files=(
        "docker-compose.yml"
        "docker-compose.prod.yml"
        "Dockerfile"
        ".env.production.template"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file missing: $file"
        fi
    done
    
    # Validate Docker Compose files
    if ! docker-compose -f docker-compose.yml -f docker-compose.prod.yml config >/dev/null 2>&1; then
        error "Invalid Docker Compose configuration"
    fi
    
    # Check for production environment file
    if [[ ! -f ".env.production" ]] && [[ ! -f ".env.prod" ]]; then
        warning "Production environment file not found. Using template values."
        if [[ -f ".env.production.template" ]]; then
            log "Copying template to .env.production"
            cp .env.production.template .env.production
            warning "Please configure .env.production with actual values before production use"
        fi
    fi
    
    # Validate environment variables
    local required_env_vars=(
        "WEBUI_SECRET_KEY"
        "GRAFANA_ADMIN_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET"
    )
    
    for var in "${required_env_vars[@]}"; do
        if ! grep -q "^${var}=" .env.production 2>/dev/null; then
            error "Required environment variable $var not found in .env.production"
        fi
        
        # Check if using template values
        if grep -q "^${var}=CHANGE_THIS" .env.production 2>/dev/null; then
            error "Environment variable $var still contains template value"
        fi
    done
    
    success "Configuration validation completed"
}

# Security scan images
security_scan_images() {
    if [[ "$SKIP_SECURITY_CHECKS" == "true" ]]; then
        warning "Security scanning skipped"
        return 0
    fi
    
    log "Performing security scan on Docker images..."
    
    # Build images first for scanning
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
    
    # Get list of images to scan
    local images
    images=$(docker-compose -f docker-compose.yml -f docker-compose.prod.yml config | grep "image:" | awk '{print $2}' | sort -u)
    
    local scan_failures=0
    
    while IFS= read -r image; do
        if [[ -n "$image" ]]; then
            log "Scanning image: $image"
            
            # Check if Trivy is available
            if command -v trivy >/dev/null 2>&1; then
                if ! trivy image --severity HIGH,CRITICAL --exit-code 1 "$image"; then
                    error "Security vulnerabilities found in $image"
                    ((scan_failures++))
                fi
            else
                warning "Trivy not available, skipping vulnerability scan"
            fi
        fi
    done <<< "$images"
    
    if [[ "$scan_failures" -gt 0 ]]; then
        error "Security scan failed for $scan_failures images"
    fi
    
    success "Security scan completed successfully"
}

# Setup monitoring and logging
setup_monitoring() {
    log "Setting up monitoring and logging..."
    
    # Create monitoring directories
    local monitoring_dirs=(
        "monitoring/prometheus/data"
        "monitoring/grafana/data"
        "logs"
        "backups"
    )
    
    for dir in "${monitoring_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
    
    # Set proper permissions for monitoring data
    if command -v chown >/dev/null 2>&1; then
        # Prometheus runs as user 65534
        chown -R 65534:65534 monitoring/prometheus/data 2>/dev/null || true
        # Grafana runs as user 472
        chown -R 472:472 monitoring/grafana/data 2>/dev/null || true
    fi
    
    success "Monitoring setup completed"
}

# Deploy services with health checks
deploy_services() {
    log "Deploying services..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would execute deployment commands"
        return 0
    fi
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
    
    # Deploy core services first
    log "Deploying core services (Redis, MCP Manager)..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d redis mcp-manager
    
    # Wait for core services to be healthy
    log "Waiting for core services to be healthy..."
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps | grep -E "(redis|mcp-manager)" | grep -q "Up"; then
            break
        fi
        
        ((attempt++))
        log "Waiting for core services... ($attempt/$max_attempts)"
        sleep 10
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "Core services failed to start within timeout"
    fi
    
    # Deploy remaining services
    log "Deploying remaining services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    success "Service deployment completed"
}

# Verify deployment health
verify_deployment() {
    log "Verifying deployment health..."
    
    local services=(
        "mcp-manager:8080:/health"
        "prometheus:9090:/-/healthy"
        "grafana:3000:/api/health"
    )
    
    local failed_services=0
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service port path <<< "$service_info"
        
        log "Checking $service health..."
        
        local max_attempts=20
        local attempt=0
        local service_healthy=false
        
        while [[ $attempt -lt $max_attempts ]]; do
            if curl -s -f "http://localhost:$port$path" >/dev/null 2>&1; then
                success "$service is healthy"
                service_healthy=true
                break
            fi
            
            ((attempt++))
            sleep 5
        done
        
        if [[ "$service_healthy" != "true" ]]; then
            error "$service failed health check"
            ((failed_services++))
        fi
    done
    
    if [[ "$failed_services" -gt 0 ]]; then
        error "Deployment verification failed for $failed_services services"
    fi
    
    success "Deployment verification completed"
}

# Setup automated backups
setup_backups() {
    log "Setting up automated backups..."
    
    # Create backup script
    cat > backup-production.sh <<'EOF'
#!/bin/bash
# Automated backup script for production data

set -euo pipefail

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_NAME="mcp-server-manager"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Redis data
echo "Backing up Redis data..."
docker-compose exec -T redis redis-cli SAVE
docker cp "${PROJECT_NAME}_redis_1:/data/dump.rdb" "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"

# Backup Grafana data
echo "Backing up Grafana data..."
docker-compose exec -T grafana tar czf - /var/lib/grafana > "$BACKUP_DIR/grafana_${TIMESTAMP}.tar.gz"

# Backup Prometheus data
echo "Backing up Prometheus data..."
docker-compose exec -T prometheus tar czf - /prometheus > "$BACKUP_DIR/prometheus_${TIMESTAMP}.tar.gz"

# Backup configuration
echo "Backing up configuration..."
tar czf "$BACKUP_DIR/config_${TIMESTAMP}.tar.gz" \
    docker-compose*.yml \
    .env.production \
    monitoring/ \
    nginx/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.rdb" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
EOF
    
    chmod +x backup-production.sh
    
    success "Backup setup completed"
}

# Generate deployment report
generate_deployment_report() {
    local report_file="deployment-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== MCP Server Manager Deployment Report ==="
        echo "Timestamp: $(date -Iseconds)"
        echo "Environment: $ENVIRONMENT"
        echo "Project: $PROJECT_NAME"
        echo ""
        
        echo "=== Services Status ==="
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
        echo ""
        
        echo "=== Container Resources ==="
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
        echo ""
        
        echo "=== Disk Usage ==="
        df -h
        echo ""
        
        echo "=== Docker Images ==="
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        echo ""
        
        echo "=== Network Configuration ==="
        docker network ls
        echo ""
        
        echo "=== Volume Information ==="
        docker volume ls
        
    } > "$report_file"
    
    log "Deployment report generated: $report_file"
}

# Cleanup function
cleanup() {
    log "Performing cleanup..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    success "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting enhanced production deployment for $PROJECT_NAME"
    log "Environment: $ENVIRONMENT"
    log "Dry run: $DRY_RUN"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Perform all deployment steps
    check_environment_security
    validate_configuration
    security_scan_images
    setup_monitoring
    deploy_services
    verify_deployment
    setup_backups
    generate_deployment_report
    cleanup
    
    success "Enhanced production deployment completed successfully!"
    
    log ""
    log "=== Next Steps ==="
    log "1. Access the application at: https://localhost"
    log "2. Monitor metrics at: https://localhost/monitoring/grafana"
    log "3. Check Prometheus at: https://localhost/monitoring/prometheus"
    log "4. Review logs: docker-compose logs -f"
    log "5. Run backups: ./backup-production.sh"
    log ""
    log "=== Security Reminders ==="
    log "- Change default passwords in .env.production"
    log "- Configure SSL certificates for production use"
    log "- Review and adjust firewall rules"
    log "- Set up log monitoring and alerting"
    log "- Schedule regular security scans"
}

# Handle script arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --skip-security)
            SKIP_SECURITY_CHECKS="true"
            shift
            ;;
        --environment=*)
            ENVIRONMENT="${1#*=}"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run           Perform a dry run without making changes"
            echo "  --skip-security     Skip security checks (not recommended)"
            echo "  --environment=ENV   Set deployment environment (default: production)"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Handle signals
trap 'error "Deployment interrupted"' SIGINT SIGTERM

# Run main function
main "$@"