#!/bin/bash

# MCP Server Manager Health Check Script
# Comprehensive health monitoring for all services

set -euo pipefail

# Configuration
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-mcp-server-manager}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-30}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Health check results
declare -A HEALTH_STATUS
declare -A HEALTH_DETAILS

# Logging
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

# Send notification
notify() {
    local message="$1"
    local status="${2:-info}"
    
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local color="good"
        local emoji=":white_check_mark:"
        
        if [[ "$status" == "error" ]]; then
            color="danger"
            emoji=":x:"
        elif [[ "$status" == "warning" ]]; then
            color="warning"
            emoji=":warning:"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$emoji MCP Health Check: $message\",\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
    fi
    
    if [[ -n "$EMAIL_RECIPIENT" ]] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "MCP Health Check Alert" "$EMAIL_RECIPIENT" || true
    fi
}

# Check if container is running
check_container() {
    local container_name="$1"
    local display_name="${2:-$container_name}"
    
    log "Checking container: $display_name"
    
    if docker ps --filter "name=$container_name" --filter "status=running" --format "{{.Names}}" | grep -q "$container_name"; then
        HEALTH_STATUS["$display_name"]="healthy"
        HEALTH_DETAILS["$display_name"]="Container is running"
        success "$display_name container is running"
        return 0
    else
        HEALTH_STATUS["$display_name"]="unhealthy"
        HEALTH_DETAILS["$display_name"]="Container is not running"
        error "$display_name container is not running"
        return 1
    fi
}

# Check HTTP endpoint
check_http_endpoint() {
    local url="$1"
    local service_name="$2"
    local expected_status="${3:-200}"
    
    log "Checking HTTP endpoint: $service_name ($url)"
    
    local response_code
    if response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$HEALTH_CHECK_TIMEOUT" "$url" 2>/dev/null); then
        if [[ "$response_code" == "$expected_status" ]]; then
            HEALTH_STATUS["$service_name"]="healthy"
            HEALTH_DETAILS["$service_name"]="HTTP $response_code - OK"
            success "$service_name HTTP endpoint is healthy ($response_code)"
            return 0
        else
            HEALTH_STATUS["$service_name"]="warning"
            HEALTH_DETAILS["$service_name"]="HTTP $response_code - Unexpected status"
            warning "$service_name returned unexpected status: $response_code"
            return 1
        fi
    else
        HEALTH_STATUS["$service_name"]="unhealthy"
        HEALTH_DETAILS["$service_name"]="HTTP endpoint unreachable"
        error "$service_name HTTP endpoint is unreachable"
        return 1
    fi
}

# Check PostgreSQL connection
check_postgres() {
    log "Checking PostgreSQL connection"
    
    local container_name="${COMPOSE_PROJECT_NAME}-postgres"
    
    if docker exec "$container_name" pg_isready -U mcpuser -d mcpdb >/dev/null 2>&1; then
        HEALTH_STATUS["PostgreSQL"]="healthy"
        HEALTH_DETAILS["PostgreSQL"]="Database is ready"
        success "PostgreSQL is responding to connection check"
        
        # Check PostgreSQL stats
        local connection_count
        connection_count=$(docker exec "$container_name" psql -U mcpuser -d mcpdb -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ')
        log "PostgreSQL active connections: $connection_count"
        
        # Check database size
        local db_size
        db_size=$(docker exec "$container_name" psql -U mcpuser -d mcpdb -t -c "SELECT pg_size_pretty(pg_database_size('mcpdb'));" 2>/dev/null | tr -d ' ')
        log "PostgreSQL database size: $db_size"
        
        return 0
    else
        HEALTH_STATUS["PostgreSQL"]="unhealthy"
        HEALTH_DETAILS["PostgreSQL"]="Database not ready"
        error "PostgreSQL is not responding"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    log "Checking disk space"
    
    local usage
    usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ "$usage" -lt 80 ]]; then
        HEALTH_STATUS["Disk Space"]="healthy"
        HEALTH_DETAILS["Disk Space"]="Usage: ${usage}%"
        success "Disk space usage is healthy: ${usage}%"
        return 0
    elif [[ "$usage" -lt 90 ]]; then
        HEALTH_STATUS["Disk Space"]="warning"
        HEALTH_DETAILS["Disk Space"]="Usage: ${usage}% - Warning level"
        warning "Disk space usage is high: ${usage}%"
        return 1
    else
        HEALTH_STATUS["Disk Space"]="unhealthy"
        HEALTH_DETAILS["Disk Space"]="Usage: ${usage}% - Critical level"
        error "Disk space usage is critical: ${usage}%"
        return 1
    fi
}

# Check memory usage
check_memory() {
    log "Checking system memory"
    
    local memory_info
    memory_info=$(free | grep Mem)
    local total=$(echo "$memory_info" | awk '{print $2}')
    local used=$(echo "$memory_info" | awk '{print $3}')
    local usage=$((used * 100 / total))
    
    if [[ "$usage" -lt 80 ]]; then
        HEALTH_STATUS["Memory"]="healthy"
        HEALTH_DETAILS["Memory"]="Usage: ${usage}%"
        success "Memory usage is healthy: ${usage}%"
        return 0
    elif [[ "$usage" -lt 90 ]]; then
        HEALTH_STATUS["Memory"]="warning"
        HEALTH_DETAILS["Memory"]="Usage: ${usage}% - Warning level"
        warning "Memory usage is high: ${usage}%"
        return 1
    else
        HEALTH_STATUS["Memory"]="unhealthy"
        HEALTH_DETAILS["Memory"]="Usage: ${usage}% - Critical level"
        error "Memory usage is critical: ${usage}%"
        return 1
    fi
}

# Check Docker daemon
check_docker() {
    log "Checking Docker daemon"
    
    if docker info >/dev/null 2>&1; then
        HEALTH_STATUS["Docker"]="healthy"
        HEALTH_DETAILS["Docker"]="Daemon is running"
        success "Docker daemon is healthy"
        return 0
    else
        HEALTH_STATUS["Docker"]="unhealthy"
        HEALTH_DETAILS["Docker"]="Daemon is not responding"
        error "Docker daemon is not responding"
        return 1
    fi
}

# Check SSL certificate (if HTTPS is enabled)
check_ssl_certificate() {
    local domain="${1:-localhost}"
    local port="${2:-443}"
    
    log "Checking SSL certificate for $domain:$port"
    
    if ! command -v openssl &> /dev/null; then
        HEALTH_STATUS["SSL Certificate"]="skipped"
        HEALTH_DETAILS["SSL Certificate"]="OpenSSL not available"
        warning "OpenSSL not available, skipping SSL check"
        return 0
    fi
    
    local expiry_date
    if expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2); then
        local expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ "$days_until_expiry" -gt 30 ]]; then
            HEALTH_STATUS["SSL Certificate"]="healthy"
            HEALTH_DETAILS["SSL Certificate"]="Valid for $days_until_expiry days"
            success "SSL certificate is valid for $days_until_expiry days"
            return 0
        elif [[ "$days_until_expiry" -gt 7 ]]; then
            HEALTH_STATUS["SSL Certificate"]="warning"
            HEALTH_DETAILS["SSL Certificate"]="Expires in $days_until_expiry days"
            warning "SSL certificate expires in $days_until_expiry days"
            return 1
        else
            HEALTH_STATUS["SSL Certificate"]="unhealthy"
            HEALTH_DETAILS["SSL Certificate"]="Expires in $days_until_expiry days - Critical"
            error "SSL certificate expires in $days_until_expiry days"
            return 1
        fi
    else
        HEALTH_STATUS["SSL Certificate"]="unhealthy"
        HEALTH_DETAILS["SSL Certificate"]="Cannot retrieve certificate"
        error "Cannot retrieve SSL certificate"
        return 1
    fi
}

# Run all health checks
run_health_checks() {
    log "Starting comprehensive health check..."
    
    local overall_status="healthy"
    local failed_checks=0
    local warning_checks=0
    
    # System checks
    check_docker || ((failed_checks++))
    check_disk_space || { 
        if [[ "${HEALTH_STATUS["Disk Space"]}" == "warning" ]]; then
            ((warning_checks++))
        else
            ((failed_checks++))
        fi
    }
    check_memory || {
        if [[ "${HEALTH_STATUS["Memory"]}" == "warning" ]]; then
            ((warning_checks++))
        else
            ((failed_checks++))
        fi
    }
    
    # Container checks
    check_container "fastapi-mcp-manager" "FastAPI MCP Manager" || ((failed_checks++))
    check_container "mcp-postgres" "PostgreSQL" || ((failed_checks++))
    check_container "mcp-open-webui" "Open WebUI" || ((failed_checks++))
    check_container "mcp-ollama" "Ollama" || ((failed_checks++))
    check_container "mcp-prometheus" "Prometheus" || ((failed_checks++))
    check_container "mcp-grafana" "Grafana" || ((failed_checks++))
    
    # Service checks
    check_http_endpoint "http://localhost:8000/health" "FastAPI MCP Manager API" || ((failed_checks++))
    check_http_endpoint "http://localhost:3000/health" "Open WebUI" || ((failed_checks++))
    check_http_endpoint "http://localhost:9090/-/healthy" "Prometheus" || ((failed_checks++))
    check_http_endpoint "http://localhost:3001/api/health" "Grafana" || ((failed_checks++))
    check_postgres || ((failed_checks++))
    
    # Optional SSL check
    if [[ "${SSL_ENABLED:-false}" == "true" ]]; then
        check_ssl_certificate "${SSL_DOMAIN:-localhost}" "${SSL_PORT:-443}" || {
            if [[ "${HEALTH_STATUS["SSL Certificate"]}" == "warning" ]]; then
                ((warning_checks++))
            else
                ((failed_checks++))
            fi
        }
    fi
    
    # Determine overall status
    if [[ "$failed_checks" -gt 0 ]]; then
        overall_status="unhealthy"
    elif [[ "$warning_checks" -gt 0 ]]; then
        overall_status="warning"
    fi
    
    # Generate report
    generate_report "$overall_status" "$failed_checks" "$warning_checks"
}

# Generate health check report
generate_report() {
    local overall_status="$1"
    local failed_checks="$2"
    local warning_checks="$3"
    
    echo ""
    echo "========================================="
    echo "MCP Server Manager Health Check Report"
    echo "========================================="
    echo "Timestamp: $(date)"
    echo "Overall Status: $overall_status"
    echo "Failed Checks: $failed_checks"
    echo "Warning Checks: $warning_checks"
    echo ""
    
    # Detailed results
    for service in "${!HEALTH_STATUS[@]}"; do
        local status="${HEALTH_STATUS[$service]}"
        local details="${HEALTH_DETAILS[$service]}"
        
        case "$status" in
            "healthy")
                echo -e "${GREEN}✓${NC} $service: $details"
                ;;
            "warning")
                echo -e "${YELLOW}⚠${NC} $service: $details"
                ;;
            "unhealthy")
                echo -e "${RED}✗${NC} $service: $details"
                ;;
            "skipped")
                echo -e "${BLUE}-${NC} $service: $details"
                ;;
        esac
    done
    
    echo ""
    
    # Save report to file
    local report_file="$HOME/mcp-health-$(date +%Y%m%d_%H%M%S).txt"
    {
        echo "MCP Server Manager Health Check Report"
        echo "Timestamp: $(date)"
        echo "Overall Status: $overall_status"
        echo ""
        for service in "${!HEALTH_STATUS[@]}"; do
            echo "$service: ${HEALTH_STATUS[$service]} - ${HEALTH_DETAILS[$service]}"
        done
    } > "$report_file"
    
    log "Health check report saved to: $report_file"
    
    # Send notifications if there are issues
    if [[ "$overall_status" == "unhealthy" ]]; then
        notify "Health check FAILED: $failed_checks critical issues detected" "error"
    elif [[ "$overall_status" == "warning" ]]; then
        notify "Health check WARNING: $warning_checks issues need attention" "warning"
    fi
    
    # Exit with appropriate code
    if [[ "$overall_status" == "unhealthy" ]]; then
        exit 1
    elif [[ "$overall_status" == "warning" ]]; then
        exit 2
    else
        exit 0
    fi
}

# Main script logic
case "${1:-check}" in
    "check")
        run_health_checks
        ;;
    "containers")
        check_container "fastapi-mcp-manager" "FastAPI MCP Manager"
        check_container "mcp-postgres" "PostgreSQL"
        check_container "mcp-open-webui" "Open WebUI"
        check_container "mcp-ollama" "Ollama"
        check_container "mcp-prometheus" "Prometheus"
        check_container "mcp-grafana" "Grafana"
        ;;
    "services")
        check_http_endpoint "http://localhost:8000/health" "FastAPI MCP Manager API"
        check_http_endpoint "http://localhost:3000/health" "Open WebUI"
        check_http_endpoint "http://localhost:9090/-/healthy" "Prometheus"
        check_http_endpoint "http://localhost:3001/api/health" "Grafana"
        check_postgres
        ;;
    "system")
        check_docker
        check_disk_space
        check_memory
        ;;
    "help"|*)
        echo "Usage: $0 {check|containers|services|system}"
        echo ""
        echo "Commands:"
        echo "  check       - Run all health checks (default)"
        echo "  containers  - Check only container status"
        echo "  services    - Check only service endpoints"
        echo "  system      - Check only system resources"
        echo ""
        echo "Environment Variables:"
        echo "  HEALTH_CHECK_TIMEOUT  - Timeout for HTTP checks (default: 30s)"
        echo "  SLACK_WEBHOOK        - Slack webhook for notifications"
        echo "  EMAIL_RECIPIENT      - Email address for alerts"
        echo "  SSL_ENABLED          - Enable SSL certificate checks (true/false)"
        echo "  SSL_DOMAIN          - Domain for SSL checks (default: localhost)"
        echo "  SSL_PORT            - Port for SSL checks (default: 443)"
        echo ""
        echo "Exit Codes:"
        echo "  0 - All checks passed"
        echo "  1 - Critical issues found"
        echo "  2 - Warning issues found"
        exit 1
        ;;
esac