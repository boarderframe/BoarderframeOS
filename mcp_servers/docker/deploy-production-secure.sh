#!/bin/bash

# Production Deployment Script for MCP Server Manager
# Enhanced with security hardening, monitoring, and rollback capabilities
# Author: Security Team
# Version: 2.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="mcp-server-manager"
DOCKER_COMPOSE_FILES=(
    "docker-compose.yml"
    "docker-compose.prod.yml"
    "docker-compose.security.yml"
)
LOG_FILE="/var/log/mcp-deployment.log"
BACKUP_DIR="/opt/mcp-backups"
MAX_ROLLBACK_ATTEMPTS=3
HEALTH_CHECK_TIMEOUT=300
SECURITY_SCAN_ENABLED=${SECURITY_SCAN_ENABLED:-true}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() { log "INFO" "${BLUE}$*${NC}"; }
warn() { log "WARN" "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}"; }
success() { log "SUCCESS" "${GREEN}$*${NC}"; }

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Deployment failed with exit code $exit_code"
        warn "Check logs at $LOG_FILE for details"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check if running as root or with sudo
    if [[ $EUID -eq 0 ]]; then
        warn "Running as root. Consider using a dedicated deployment user."
    fi
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "openssl" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command '$cmd' not found"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running or accessible"
        exit 1
    fi
    
    # Check Docker Compose version
    local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    local required_version="1.27.0"
    if ! printf '%s\n%s\n' "$required_version" "$compose_version" | sort -V -C; then
        error "Docker Compose version $compose_version is too old. Required: $required_version+"
        exit 1
    fi
    
    # Check available disk space (require at least 10GB)
    local available_space=$(df "$SCRIPT_DIR" | awk 'NR==2{print $4}')
    local required_space=10485760  # 10GB in KB
    if [[ $available_space -lt $required_space ]]; then
        error "Insufficient disk space. Required: 10GB, Available: $(($available_space/1024/1024))GB"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f "$SCRIPT_DIR/.env.prod" ]]; then
        error "Production environment file '.env.prod' not found"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Security pre-flight checks
security_checks() {
    info "Running security pre-flight checks..."
    
    # Check for default passwords
    local env_file="$SCRIPT_DIR/.env.prod"
    local default_passwords=("changeme" "password" "admin" "123456")
    
    for password in "${default_passwords[@]}"; do
        if grep -q "$password" "$env_file"; then
            error "Default password '$password' found in environment file"
            exit 1
        fi
    done
    
    # Check SSL certificates
    local ssl_cert="$SCRIPT_DIR/nginx/ssl/cert.pem"
    local ssl_key="$SCRIPT_DIR/nginx/ssl/key.pem"
    
    if [[ ! -f "$ssl_cert" ]] || [[ ! -f "$ssl_key" ]]; then
        warn "SSL certificates not found. Generating self-signed certificates..."
        mkdir -p "$SCRIPT_DIR/nginx/ssl"
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$ssl_key" \
            -out "$ssl_cert" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
            &> /dev/null
        chmod 600 "$ssl_key"
        chmod 644 "$ssl_cert"
    fi
    
    # Validate SSL certificate
    if ! openssl x509 -in "$ssl_cert" -text -noout &> /dev/null; then
        error "Invalid SSL certificate"
        exit 1
    fi
    
    # Check certificate expiration (warn if expires in less than 30 days)
    local cert_expiry=$(openssl x509 -in "$ssl_cert" -noout -dates | grep "notAfter" | cut -d= -f2)
    local expiry_timestamp=$(date -d "$cert_expiry" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
    
    if [[ $days_until_expiry -lt 30 ]]; then
        warn "SSL certificate expires in $days_until_expiry days"
    fi
    
    # Check Docker socket permissions
    if [[ -S /var/run/docker.sock ]]; then
        local socket_perms=$(stat -c "%a" /var/run/docker.sock)
        if [[ "$socket_perms" != "660" ]] && [[ "$socket_perms" != "600" ]]; then
            warn "Docker socket has permissive permissions: $socket_perms"
        fi
    fi
    
    success "Security checks passed"
}

# Image security scanning
scan_images() {
    if [[ "$SECURITY_SCAN_ENABLED" != "true" ]]; then
        info "Security scanning disabled, skipping..."
        return 0
    fi
    
    info "Scanning Docker images for vulnerabilities..."
    
    # Build images first
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                   build --no-cache
    
    # Get list of built images
    local images=($(docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                                   config | grep "image:" | awk '{print $2}' | sort -u))
    
    # Scan each image with Trivy (if available)
    if command -v trivy &> /dev/null; then
        for image in "${images[@]}"; do
            info "Scanning image: $image"
            if ! trivy image --severity HIGH,CRITICAL --exit-code 1 "$image"; then
                error "High/Critical vulnerabilities found in $image"
                exit 1
            fi
        done
    else
        warn "Trivy not available, skipping vulnerability scanning"
    fi
    
    success "Image security scanning completed"
}

# Create backup before deployment
create_backup() {
    info "Creating backup before deployment..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="$BACKUP_DIR/mcp_backup_$backup_timestamp"
    
    # Stop services gracefully
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                   down --timeout 30 || true
    
    # Backup volumes
    docker run --rm \
        -v mcp_redis_data:/source/redis_data:ro \
        -v mcp_prometheus_data:/source/prometheus_data:ro \
        -v mcp_grafana_data:/source/grafana_data:ro \
        -v "$backup_path:/backup" \
        alpine:latest \
        sh -c "cd /source && tar czf /backup/volumes_$backup_timestamp.tar.gz ."
    
    # Backup configuration
    tar czf "$backup_path/config_$backup_timestamp.tar.gz" \
        -C "$SCRIPT_DIR" \
        --exclude='*.log' \
        --exclude='.git' \
        .
    
    # Store backup metadata
    cat > "$backup_path/metadata.json" <<EOF
{
    "timestamp": "$backup_timestamp",
    "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "deployment_user": "$(whoami)",
    "hostname": "$(hostname)"
}
EOF
    
    echo "$backup_path" > "$SCRIPT_DIR/.last_backup"
    success "Backup created at $backup_path"
}

# Deploy application
deploy() {
    info "Starting deployment..."
    
    # Pull latest images
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                   pull
    
    # Start core services first
    info "Starting core services..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                   up -d redis prometheus grafana
    
    # Wait for core services
    sleep 10
    
    # Start application services
    info "Starting application services..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                   up -d mcp-manager open-webui ollama nginx
    
    # Start security monitoring (if enabled)
    if [[ "$SECURITY_SCAN_ENABLED" == "true" ]]; then
        info "Starting security monitoring..."
        docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                       -f "$SCRIPT_DIR/docker-compose.security.yml" \
                       up -d falco cadvisor node-exporter
    fi
    
    success "Deployment completed"
}

# Health checks
run_health_checks() {
    info "Running health checks..."
    
    local services=("mcp-manager:8080" "open-webui:8080" "prometheus:9090" "grafana:3000")
    local start_time=$(date +%s)
    local timeout=$HEALTH_CHECK_TIMEOUT
    
    for service in "${services[@]}"; do
        local service_name=$(echo "$service" | cut -d: -f1)
        local service_port=$(echo "$service" | cut -d: -f2)
        
        info "Checking health of $service_name..."
        
        local ready=false
        while [[ $ready == false ]]; do
            local current_time=$(date +%s)
            local elapsed=$((current_time - start_time))
            
            if [[ $elapsed -gt $timeout ]]; then
                error "Health check timeout for $service_name"
                return 1
            fi
            
            if docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                              -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                              exec -T "$service_name" \
                              curl -f "http://localhost:$service_port/health" &> /dev/null; then
                success "$service_name is healthy"
                ready=true
            else
                warn "$service_name not ready, waiting..."
                sleep 5
            fi
        done
    done
    
    # Test external connectivity
    info "Testing external connectivity..."
    if curl -f -k "https://localhost/health" &> /dev/null; then
        success "External connectivity test passed"
    else
        error "External connectivity test failed"
        return 1
    fi
    
    success "All health checks passed"
}

# Rollback function
rollback() {
    error "Rolling back deployment..."
    
    if [[ ! -f "$SCRIPT_DIR/.last_backup" ]]; then
        error "No backup found for rollback"
        exit 1
    fi
    
    local backup_path=$(cat "$SCRIPT_DIR/.last_backup")
    
    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found: $backup_path"
        exit 1
    fi
    
    # Stop current services
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                   down --timeout 30
    
    # Restore volumes
    if [[ -f "$backup_path/volumes_*.tar.gz" ]]; then
        docker run --rm \
            -v mcp_redis_data:/target/redis_data \
            -v mcp_prometheus_data:/target/prometheus_data \
            -v mcp_grafana_data:/target/grafana_data \
            -v "$backup_path:/backup" \
            alpine:latest \
            sh -c "cd /target && tar xzf /backup/volumes_*.tar.gz"
    fi
    
    # Restore configuration
    if [[ -f "$backup_path/config_*.tar.gz" ]]; then
        tar xzf "$backup_path/config_*.tar.gz" -C "$SCRIPT_DIR"
    fi
    
    # Restart services
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" \
                   -f "$SCRIPT_DIR/docker-compose.prod.yml" \
                   up -d
    
    success "Rollback completed"
}

# Main deployment function
main() {
    info "Starting production deployment of $PROJECT_NAME"
    info "Deployment started by $(whoami) at $(date)"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Load environment variables
    if [[ -f ".env.prod" ]]; then
        set -a
        source .env.prod
        set +a
    fi
    
    # Run pre-deployment checks
    check_prerequisites
    security_checks
    
    # Create backup
    create_backup
    
    # Scan images for vulnerabilities
    scan_images
    
    # Deploy application
    if ! deploy; then
        error "Deployment failed"
        rollback
        exit 1
    fi
    
    # Run health checks
    if ! run_health_checks; then
        error "Health checks failed"
        rollback
        exit 1
    fi
    
    # Final verification
    info "Running final verification..."
    sleep 30
    if ! run_health_checks; then
        error "Final verification failed"
        rollback
        exit 1
    fi
    
    success "Production deployment completed successfully!"
    info "Services are available at:"
    info "  - Main Application: https://localhost"
    info "  - Grafana: https://localhost/monitoring/grafana"
    info "  - Prometheus: https://localhost/monitoring/prometheus"
    
    if [[ "$SECURITY_SCAN_ENABLED" == "true" ]]; then
        info "  - Falco UI: http://localhost:2802"
        info "  - Kibana: http://localhost:5601"
    fi
    
    info "Logs available at: $LOG_FILE"
    info "Backup created at: $(cat "$SCRIPT_DIR/.last_backup")"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "health-check")
        run_health_checks
        ;;
    "backup")
        create_backup
        ;;
    "scan")
        scan_images
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|health-check|backup|scan]"
        exit 1
        ;;
esac