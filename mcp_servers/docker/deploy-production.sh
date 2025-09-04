#!/bin/bash

# Production Deployment Script for MCP Server Manager
# Includes comprehensive security validation and monitoring setup
# Version: 1.0.0

set -euo pipefail

# ==============================================
# CONFIGURATION
# ==============================================

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/mcp-deploy.log"
DEPLOY_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment configuration
ENVIRONMENT="${1:-production}"
DRY_RUN="${DRY_RUN:-false}"
FORCE_DEPLOY="${FORCE_DEPLOY:-false}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"

# Security configuration
SECURITY_SCAN_ENABLED="${SECURITY_SCAN_ENABLED:-true}"
VULNERABILITY_THRESHOLD="${VULNERABILITY_THRESHOLD:-HIGH}"
MIN_SECURITY_SCORE="${MIN_SECURITY_SCORE:-80}"

# ==============================================
# LOGGING AND UTILITIES
# ==============================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "${YELLOW}$*${NC}"; }
log_error() { log "ERROR" "${RED}$*${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$*${NC}"; }

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Cleanup function
cleanup() {
    local exit_code=$?
    log_info "Cleaning up temporary files..."
    rm -rf /tmp/mcp-deploy-* 2>/dev/null || true
    
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed with exit code $exit_code"
        # Send failure notification
        send_notification "FAILURE" "MCP deployment failed"
    fi
    
    exit $exit_code
}

trap cleanup EXIT

# ==============================================
# VALIDATION FUNCTIONS
# ==============================================

validate_environment() {
    log_info "Validating deployment environment..."
    
    # Check if running as root (should not be)
    if [[ $EUID -eq 0 ]]; then
        error_exit "This script should not be run as root for security reasons"
    fi
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "curl" "jq" "openssl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error_exit "Required command '$cmd' is not installed"
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running or accessible"
    fi
    
    # Check available disk space (minimum 10GB)
    local available_space=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        error_exit "Insufficient disk space. At least 10GB required"
    fi
    
    # Check memory (minimum 4GB)
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    if [ "$available_memory" -lt 4096 ]; then
        log_warn "Available memory is less than 4GB. Performance may be impacted"
    fi
    
    log_success "Environment validation passed"
}

validate_configuration() {
    log_info "Validating configuration files..."
    
    # Check if environment file exists
    local env_file="$SCRIPT_DIR/.env.$ENVIRONMENT"
    if [ ! -f "$env_file" ]; then
        error_exit "Environment file $env_file not found. Copy from .env.production.template"
    fi
    
    # Load and validate environment variables
    source "$env_file"
    
    # Check critical security variables
    local required_vars=("WEBUI_SECRET_KEY" "GRAFANA_ADMIN_PASSWORD" "JWT_SECRET")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ] || [ "${!var}" = "CHANGE_THIS_TO_RANDOM_32_CHAR_HEX_STRING" ]; then
            error_exit "Security variable $var is not set or using default value"
        fi
    done
    
    # Validate secret strength
    if [ ${#WEBUI_SECRET_KEY} -lt 32 ]; then
        error_exit "WEBUI_SECRET_KEY must be at least 32 characters long"
    fi
    
    # Check SSL configuration
    if [ "${SSL_ENABLED:-false}" = "true" ]; then
        if [ ! -f "${SSL_CERT_PATH:-}" ] || [ ! -f "${SSL_KEY_PATH:-}" ]; then
            error_exit "SSL is enabled but certificate files are missing"
        fi
    fi
    
    log_success "Configuration validation passed"
}

validate_network_security() {
    log_info "Validating network security configuration..."
    
    # Check for exposed dangerous ports
    local dangerous_ports=(22 23 135 139 445 1433 3306 5432)
    for port in "${dangerous_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            log_warn "Dangerous port $port is exposed on the host"
        fi
    done
    
    # Check firewall status
    if command -v ufw &> /dev/null; then
        if ! ufw status | grep -q "Status: active"; then
            log_warn "UFW firewall is not active"
        fi
    fi
    
    log_success "Network security validation completed"
}

# ==============================================
# SECURITY SCANNING FUNCTIONS
# ==============================================

run_security_scan() {
    if [ "$SECURITY_SCAN_ENABLED" != "true" ]; then
        log_info "Security scanning is disabled, skipping..."
        return 0
    fi
    
    log_info "Running comprehensive security scan..."
    
    local scan_results_dir="/tmp/mcp-security-scan-$DEPLOY_TIMESTAMP"
    mkdir -p "$scan_results_dir"
    
    # Build images first
    log_info "Building images for security scanning..."
    docker-compose -f docker-compose.yml build --no-cache
    
    # Scan with Trivy
    if command -v trivy &> /dev/null; then
        log_info "Running Trivy vulnerability scan..."
        trivy image --severity "$VULNERABILITY_THRESHOLD" --format json \
            --output "$scan_results_dir/trivy-scan.json" \
            mcp-server-manager:latest || {
            log_error "Trivy scan failed or found vulnerabilities"
            if [ "$FORCE_DEPLOY" != "true" ]; then
                return 1
            fi
        }
    fi
    
    # Scan with Hadolint (Dockerfile best practices)
    if command -v hadolint &> /dev/null; then
        log_info "Running Hadolint Dockerfile scan..."
        hadolint "$SCRIPT_DIR/Dockerfile" --format json \
            > "$scan_results_dir/hadolint-scan.json" 2>&1 || {
            log_warn "Hadolint found issues in Dockerfile"
        }
    fi
    
    # Custom security checks
    run_custom_security_checks "$scan_results_dir"
    
    # Generate security report
    generate_security_report "$scan_results_dir"
    
    log_success "Security scan completed"
}

run_custom_security_checks() {
    local scan_dir="$1"
    log_info "Running custom security checks..."
    
    # Check for secrets in environment files
    local secrets_found=false
    while IFS= read -r line; do
        if echo "$line" | grep -iE "(password|secret|key|token).*=" | grep -v "CHANGE_THIS" | grep -v "_ENABLED" | grep -v "_PATH" | grep -v "_URL"; then
            log_warn "Potential secret found: $line"
            secrets_found=true
        fi
    done < "$SCRIPT_DIR/.env.$ENVIRONMENT"
    
    # Check Docker daemon configuration
    local docker_info=$(docker info --format '{{json .}}')
    
    # Check if Docker daemon is running in rootless mode
    if echo "$docker_info" | jq -r '.SecurityOptions[]' | grep -q "rootless"; then
        log_success "Docker is running in rootless mode"
    else
        log_warn "Docker is not running in rootless mode"
    fi
    
    # Check for insecure registries
    if echo "$docker_info" | jq -r '.InsecureRegistries[]?' 2>/dev/null | grep -q .; then
        log_warn "Insecure registries are configured"
    fi
    
    # Save custom check results
    {
        echo "{"
        echo "  \"secrets_found\": $secrets_found,"
        echo "  \"timestamp\": \"$(date -Iseconds)\","
        echo "  \"docker_security\": $(echo "$docker_info" | jq '.SecurityOptions')"
        echo "}"
    } > "$scan_dir/custom-checks.json"
}

generate_security_report() {
    local scan_dir="$1"
    local report_file="$scan_dir/security-report.html"
    
    log_info "Generating security report..."
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>MCP Security Scan Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .critical { color: #d32f2f; }
        .warning { color: #f57c00; }
        .success { color: #388e3c; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>MCP Server Manager Security Scan Report</h1>
        <p>Generated: $(date)</p>
        <p>Environment: $ENVIRONMENT</p>
    </div>
    
    <div class="section">
        <h2>Scan Summary</h2>
        <p>Security scanning completed for MCP Server Manager deployment.</p>
    </div>
    
    <div class="section">
        <h2>Vulnerability Scan Results</h2>
        <p>Check individual JSON reports for detailed vulnerability information.</p>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            <li>Regularly update base images and dependencies</li>
            <li>Monitor security advisories for used components</li>
            <li>Implement runtime security monitoring</li>
            <li>Regular security audits and penetration testing</li>
        </ul>
    </div>
</body>
</html>
EOF
    
    log_success "Security report generated: $report_file"
}

# ==============================================
# DEPLOYMENT FUNCTIONS
# ==============================================

backup_data() {
    if [ "$BACKUP_BEFORE_DEPLOY" != "true" ]; then
        log_info "Backup disabled, skipping..."
        return 0
    fi
    
    log_info "Creating backup before deployment..."
    
    local backup_dir="/var/backups/mcp-$DEPLOY_TIMESTAMP"
    mkdir -p "$backup_dir"
    
    # Backup Docker volumes
    docker run --rm \
        -v mcp_redis_data:/source:ro \
        -v "$backup_dir":/backup \
        alpine tar czf "/backup/redis_data.tar.gz" -C /source .
    
    docker run --rm \
        -v mcp_grafana_data:/source:ro \
        -v "$backup_dir":/backup \
        alpine tar czf "/backup/grafana_data.tar.gz" -C /source .
    
    # Backup configuration
    cp -r "$SCRIPT_DIR/config" "$backup_dir/" 2>/dev/null || true
    cp "$SCRIPT_DIR/.env.$ENVIRONMENT" "$backup_dir/" 2>/dev/null || true
    
    log_success "Backup created: $backup_dir"
}

deploy_services() {
    log_info "Deploying MCP Server Manager services..."
    
    cd "$SCRIPT_DIR"
    
    if [ "$DRY_RUN" = "true" ]; then
        log_info "DRY RUN: Would execute deployment commands"
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml config
        return 0
    fi
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
    
    # Build custom images
    log_info "Building custom images..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
    
    # Start services with zero-downtime deployment
    log_info "Starting services..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    wait_for_services
    
    log_success "Services deployed successfully"
}

wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_wait=300  # 5 minutes
    local wait_time=0
    local interval=10
    
    local services=("mcp-manager" "redis" "prometheus" "grafana")
    
    while [ $wait_time -lt $max_wait ]; do
        local all_healthy=true
        
        for service in "${services[@]}"; do
            local health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unhealthy")
            if [ "$health" != "healthy" ]; then
                all_healthy=false
                break
            fi
        done
        
        if [ "$all_healthy" = "true" ]; then
            log_success "All services are healthy"
            return 0
        fi
        
        log_info "Waiting for services... ($wait_time/$max_wait seconds)"
        sleep $interval
        wait_time=$((wait_time + interval))
    done
    
    error_exit "Services failed to become healthy within $max_wait seconds"
}

# ==============================================
# POST-DEPLOYMENT VALIDATION
# ==============================================

validate_deployment() {
    log_info "Validating deployment..."
    
    # Check service endpoints
    local endpoints=(
        "http://localhost:8080/health"
        "http://localhost:9090/-/healthy"
        "http://localhost:3001/api/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -sf "$endpoint" >/dev/null 2>&1; then
            log_success "Endpoint $endpoint is responding"
        else
            log_error "Endpoint $endpoint is not responding"
        fi
    done
    
    # Check container resource usage
    log_info "Checking container resource usage..."
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" || true
    
    # Run smoke tests
    run_smoke_tests
    
    log_success "Deployment validation completed"
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test MCP Manager API
    local api_response=$(curl -sf "http://localhost:8080/api/health" 2>/dev/null || echo "")
    if echo "$api_response" | jq -e '.status == "healthy"' >/dev/null 2>&1; then
        log_success "MCP Manager API is healthy"
    else
        log_error "MCP Manager API health check failed"
    fi
    
    # Test Redis connection
    if docker exec mcp-redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis is responding"
    else
        log_error "Redis connection failed"
    fi
    
    # Test Prometheus metrics
    if curl -sf "http://localhost:9090/api/v1/query?query=up" | jq -e '.status == "success"' >/dev/null 2>&1; then
        log_success "Prometheus is collecting metrics"
    else
        log_error "Prometheus metrics collection failed"
    fi
    
    log_success "Smoke tests completed"
}

# ==============================================
# NOTIFICATION FUNCTIONS
# ==============================================

send_notification() {
    local status="$1"
    local message="$2"
    
    # Slack notification
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        local color="good"
        [ "$status" = "FAILURE" ] && color="danger"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"MCP Deployment $status\",
                    \"text\": \"$message\",
                    \"fields\": [{
                        \"title\": \"Environment\",
                        \"value\": \"$ENVIRONMENT\",
                        \"short\": true
                    }, {
                        \"title\": \"Timestamp\",
                        \"value\": \"$(date)\",
                        \"short\": true
                    }]
                }]
            }" \
            "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
    fi
    
    # Email notification (if configured)
    if [ -n "${EMAIL_RECIPIENT:-}" ]; then
        echo "$message" | mail -s "MCP Deployment $status" "$EMAIL_RECIPIENT" 2>/dev/null || true
    fi
}

# ==============================================
# MAIN EXECUTION
# ==============================================

main() {
    log_info "Starting MCP Server Manager deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Dry run: $DRY_RUN"
    log_info "Force deploy: $FORCE_DEPLOY"
    
    # Pre-deployment validation
    validate_environment
    validate_configuration
    validate_network_security
    
    # Security scanning
    run_security_scan
    
    # Backup existing data
    backup_data
    
    # Deploy services
    deploy_services
    
    # Post-deployment validation
    validate_deployment
    
    # Send success notification
    send_notification "SUCCESS" "MCP Server Manager deployed successfully to $ENVIRONMENT"
    
    log_success "Deployment completed successfully!"
    log_info "Services are available at:"
    log_info "  - MCP Manager: http://localhost:8080"
    log_info "  - Open WebUI: http://localhost:3000"
    log_info "  - Grafana: http://localhost:3001"
    log_info "  - Prometheus: http://localhost:9090"
}

# ==============================================
# SCRIPT ENTRY POINT
# ==============================================

# Display usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <environment> [options]"
    echo ""
    echo "Environments:"
    echo "  production    Deploy to production environment"
    echo "  staging       Deploy to staging environment"
    echo ""
    echo "Options:"
    echo "  DRY_RUN=true                 Perform a dry run without actual deployment"
    echo "  FORCE_DEPLOY=true           Force deployment even if security scans fail"
    echo "  BACKUP_BEFORE_DEPLOY=false  Skip backup before deployment"
    echo "  SECURITY_SCAN_ENABLED=false Skip security scanning"
    echo ""
    echo "Example:"
    echo "  $0 production"
    echo "  DRY_RUN=true $0 staging"
    exit 1
fi

# Validate environment argument
case "$ENVIRONMENT" in
    production|staging)
        ;;
    *)
        error_exit "Invalid environment: $ENVIRONMENT. Use 'production' or 'staging'"
        ;;
esac

# Run main deployment
main "$@"