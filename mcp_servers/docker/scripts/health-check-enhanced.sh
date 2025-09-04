#!/bin/bash
# Enhanced Health Check Script with Security Validation
# Comprehensive health checking for production containers

set -euo pipefail

# Configuration
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-10}"
MAX_RETRIES="${MAX_RETRIES:-3}"
CHECK_INTERVAL="${CHECK_INTERVAL:-5}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
SECURITY_CHECKS="${SECURITY_CHECKS:-true}"

# Service endpoints
MCP_MANAGER_URL="${MCP_MANAGER_URL:-http://localhost:8080}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"

# Health check results
declare -A health_results
declare -A security_results

# Logging functions
log() {
    local level="$1"
    shift
    if [[ "$LOG_LEVEL" =~ ^(DEBUG|INFO|WARN|ERROR)$ ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" >&2
    fi
}

debug() { [[ "$LOG_LEVEL" == "DEBUG" ]] && log "DEBUG" "$@"; }
info() { log "INFO" "$@"; }
warn() { log "WARN" "$@"; }
error() { log "ERROR" "$@"; }

# Network connectivity check
check_network() {
    local service="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    debug "Checking network connectivity to $service ($url)"
    
    local response
    if response=$(curl -s -w "%{http_code}" -o /dev/null --max-time "$HEALTH_CHECK_TIMEOUT" "$url" 2>/dev/null); then
        if [[ "$response" == "$expected_status" ]]; then
            health_results["$service"]="HEALTHY"
            info "$service is responding correctly (HTTP $response)"
            return 0
        else
            health_results["$service"]="UNHEALTHY"
            warn "$service returned unexpected status: $response"
            return 1
        fi
    else
        health_results["$service"]="UNREACHABLE"
        error "$service is unreachable"
        return 1
    fi
}

# Database connectivity check
check_database() {
    local service="redis"
    
    debug "Checking database connectivity"
    
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; then
            health_results["$service"]="HEALTHY"
            info "Redis database is responding"
            return 0
        else
            health_results["$service"]="UNHEALTHY"
            error "Redis database is not responding"
            return 1
        fi
    else
        # Alternative check using netcat or curl
        local redis_host
        local redis_port
        redis_host=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/\([^:]*\):.*/\1/p')
        redis_port=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/[^:]*:\([0-9]*\).*/\1/p')
        
        if nc -z "$redis_host" "$redis_port" 2>/dev/null; then
            health_results["$service"]="HEALTHY"
            info "Redis database port is accessible"
            return 0
        else
            health_results["$service"]="UNHEALTHY"
            error "Redis database port is not accessible"
            return 1
        fi
    fi
}

# File system health check
check_filesystem() {
    debug "Checking filesystem health"
    
    local issues=0
    
    # Check disk space
    local disk_usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ "$disk_usage" -gt 90 ]]; then
        error "Disk usage is critically high: ${disk_usage}%"
        ((issues++))
    elif [[ "$disk_usage" -gt 80 ]]; then
        warn "Disk usage is high: ${disk_usage}%"
    else
        debug "Disk usage is normal: ${disk_usage}%"
    fi
    
    # Check for required directories
    local required_dirs=("/app" "/app/src" "/app/config")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            error "Required directory missing: $dir"
            ((issues++))
        fi
    done
    
    # Check file permissions
    if [[ -f "/app/.readonly" ]]; then
        debug "Read-only marker found"
    else
        warn "Read-only marker missing"
        ((issues++))
    fi
    
    if [[ "$issues" -eq 0 ]]; then
        health_results["filesystem"]="HEALTHY"
        info "Filesystem checks passed"
        return 0
    else
        health_results["filesystem"]="UNHEALTHY"
        error "Filesystem checks failed with $issues issues"
        return 1
    fi
}

# Memory health check
check_memory() {
    debug "Checking memory usage"
    
    if [[ -f "/proc/meminfo" ]]; then
        local mem_total
        local mem_available
        local mem_usage
        
        mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        mem_usage=$(( (mem_total - mem_available) * 100 / mem_total ))
        
        if [[ "$mem_usage" -gt 90 ]]; then
            health_results["memory"]="CRITICAL"
            error "Memory usage is critically high: ${mem_usage}%"
            return 1
        elif [[ "$mem_usage" -gt 80 ]]; then
            health_results["memory"]="WARNING"
            warn "Memory usage is high: ${mem_usage}%"
        else
            health_results["memory"]="HEALTHY"
            debug "Memory usage is normal: ${mem_usage}%"
        fi
        
        return 0
    else
        health_results["memory"]="UNKNOWN"
        warn "Cannot determine memory usage"
        return 1
    fi
}

# Process health check
check_processes() {
    debug "Checking critical processes"
    
    local required_processes=("node")
    local missing_processes=0
    
    for process in "${required_processes[@]}"; do
        if pgrep -f "$process" >/dev/null; then
            debug "Process $process is running"
        else
            error "Required process $process is not running"
            ((missing_processes++))
        fi
    done
    
    if [[ "$missing_processes" -eq 0 ]]; then
        health_results["processes"]="HEALTHY"
        info "All required processes are running"
        return 0
    else
        health_results["processes"]="UNHEALTHY"
        error "$missing_processes required processes are missing"
        return 1
    fi
}

# Security validation checks
check_security() {
    if [[ "$SECURITY_CHECKS" != "true" ]]; then
        debug "Security checks disabled"
        return 0
    fi
    
    debug "Performing security validation checks"
    
    local security_issues=0
    
    # Check if running as root
    if [[ "$(id -u)" -eq 0 ]]; then
        error "Security violation: Running as root user"
        security_results["user"]="FAIL"
        ((security_issues++))
    else
        debug "Security check passed: Not running as root"
        security_results["user"]="PASS"
    fi
    
    # Check file permissions
    if [[ -w "/etc/passwd" ]]; then
        error "Security violation: /etc/passwd is writable"
        security_results["permissions"]="FAIL"
        ((security_issues++))
    else
        debug "Security check passed: System files are protected"
        security_results["permissions"]="PASS"
    fi
    
    # Check for suspicious processes
    local suspicious_processes=("nc" "netcat" "telnet" "ftp")
    for proc in "${suspicious_processes[@]}"; do
        if pgrep -f "$proc" >/dev/null; then
            warn "Security warning: Suspicious process detected: $proc"
            security_results["processes"]="WARNING"
        fi
    done
    
    # Check network connections
    if command -v netstat >/dev/null 2>&1; then
        local open_ports
        open_ports=$(netstat -tuln 2>/dev/null | grep -c LISTEN || echo "0")
        if [[ "$open_ports" -gt 10 ]]; then
            warn "Security warning: Many open ports detected: $open_ports"
            security_results["network"]="WARNING"
        else
            debug "Security check passed: Normal number of open ports: $open_ports"
            security_results["network"]="PASS"
        fi
    fi
    
    if [[ "$security_issues" -eq 0 ]]; then
        info "Security validation checks passed"
        return 0
    else
        error "Security validation failed with $security_issues critical issues"
        return 1
    fi
}

# Application-specific health checks
check_application() {
    debug "Checking application-specific health"
    
    # Check MCP Manager
    if check_network "mcp-manager" "$MCP_MANAGER_URL/health"; then
        # Additional application checks
        if curl -s --max-time "$HEALTH_CHECK_TIMEOUT" "$MCP_MANAGER_URL/metrics" >/dev/null 2>&1; then
            debug "MCP Manager metrics endpoint is accessible"
        else
            warn "MCP Manager metrics endpoint is not accessible"
        fi
    fi
    
    # Check Redis
    check_database
    
    # Check monitoring services
    check_network "prometheus" "$PROMETHEUS_URL/-/healthy" || true
    check_network "grafana" "$GRAFANA_URL/api/health" || true
}

# Generate health report
generate_health_report() {
    local overall_status="HEALTHY"
    local critical_issues=0
    local warnings=0
    
    info "=== Health Check Report ==="
    info "Timestamp: $(date -Iseconds)"
    
    # Service health
    info "--- Service Health ---"
    for service in "${!health_results[@]}"; do
        local status="${health_results[$service]}"
        info "$service: $status"
        
        case "$status" in
            "UNHEALTHY"|"UNREACHABLE"|"CRITICAL")
                overall_status="UNHEALTHY"
                ((critical_issues++))
                ;;
            "WARNING")
                ((warnings++))
                if [[ "$overall_status" == "HEALTHY" ]]; then
                    overall_status="WARNING"
                fi
                ;;
        esac
    done
    
    # Security results
    if [[ "${#security_results[@]}" -gt 0 ]]; then
        info "--- Security Checks ---"
        for check in "${!security_results[@]}"; do
            local status="${security_results[$check]}"
            info "$check: $status"
            
            if [[ "$status" == "FAIL" ]]; then
                overall_status="UNHEALTHY"
                ((critical_issues++))
            fi
        done
    fi
    
    info "--- Summary ---"
    info "Overall Status: $overall_status"
    info "Critical Issues: $critical_issues"
    info "Warnings: $warnings"
    
    # Exit with appropriate code
    case "$overall_status" in
        "HEALTHY")
            info "All health checks passed"
            return 0
            ;;
        "WARNING")
            warn "Health checks passed with warnings"
            return 0
            ;;
        "UNHEALTHY")
            error "Health checks failed"
            return 1
            ;;
    esac
}

# Main health check function
main() {
    info "Starting enhanced health check"
    
    local start_time
    start_time=$(date +%s)
    
    # Perform all health checks
    check_filesystem
    check_memory
    check_processes
    check_security
    check_application
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    info "Health check completed in ${duration}s"
    
    # Generate and return report
    generate_health_report
}

# Handle timeouts
timeout_handler() {
    error "Health check timed out after ${HEALTH_CHECK_TIMEOUT}s"
    exit 1
}

trap timeout_handler ALRM

# Run with timeout
(
    sleep "$HEALTH_CHECK_TIMEOUT" && kill $$ 2>/dev/null
) &
timeout_pid=$!

main "$@"
exit_code=$?

# Clean up timeout process
kill $timeout_pid 2>/dev/null || true

exit $exit_code