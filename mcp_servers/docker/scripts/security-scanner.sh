#!/bin/bash
# Continuous Security Scanner for Docker Images
# Scans all running containers and images for vulnerabilities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCANNER_CONFIG:-/config/scanner-config.yaml}"
RESULTS_DIR="${RESULTS_DIR:-/results}"
REPORTS_DIR="${REPORTS_DIR:-/reports}"
SCAN_INTERVAL="${SCAN_INTERVAL:-3600}"
VULNERABILITY_THRESHOLD="${VULNERABILITY_THRESHOLD:-HIGH}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

error() {
    log "ERROR: $*"
    exit 1
}

# Initialize directories
mkdir -p "$RESULTS_DIR" "$REPORTS_DIR"

# Scan a single image
scan_image() {
    local image="$1"
    local scan_id="$(date +%s)-$(echo "$image" | tr '/:' '_')"
    local output_file="$RESULTS_DIR/scan-$scan_id.json"
    local report_file="$REPORTS_DIR/report-$scan_id.html"
    
    log "Scanning image: $image"
    
    # Run Trivy scan
    if trivy image \
        --format json \
        --severity "$VULNERABILITY_THRESHOLD,CRITICAL" \
        --ignore-unfixed \
        --no-progress \
        --timeout 10m \
        --output "$output_file" \
        "$image"; then
        
        log "Trivy scan completed for $image"
        
        # Generate SBOM
        local sbom_file="$RESULTS_DIR/sbom-$scan_id.json"
        syft "$image" -o spdx-json --file "$sbom_file" || log "SBOM generation failed for $image"
        
        # Run Grype scan for additional coverage
        local grype_file="$RESULTS_DIR/grype-$scan_id.json"
        grype "$image" -o json --file "$grype_file" || log "Grype scan failed for $image"
        
        # Process results
        process_scan_results "$output_file" "$image" "$scan_id"
        
    else
        log "Trivy scan failed for $image"
        return 1
    fi
}

# Process scan results
process_scan_results() {
    local results_file="$1"
    local image="$2"
    local scan_id="$3"
    
    if [[ ! -f "$results_file" ]]; then
        log "Results file not found: $results_file"
        return 1
    fi
    
    # Count vulnerabilities by severity
    local critical=$(jq -r '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$results_file" 2>/dev/null || echo "0")
    local high=$(jq -r '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' "$results_file" 2>/dev/null || echo "0")
    local medium=$(jq -r '[.Results[]?.Vulnerabilities[]? | select(.Severity == "MEDIUM")] | length' "$results_file" 2>/dev/null || echo "0")
    local total=$((critical + high + medium))
    
    log "Scan results for $image: CRITICAL=$critical, HIGH=$high, MEDIUM=$medium, TOTAL=$total"
    
    # Generate summary report
    generate_summary_report "$image" "$scan_id" "$critical" "$high" "$medium" "$total"
    
    # Send alerts if thresholds exceeded
    if [[ $critical -gt 0 ]] || [[ $high -gt 5 ]]; then
        send_security_alert "$image" "$critical" "$high" "$medium" "$scan_id"
    fi
    
    # Store scan metadata
    store_scan_metadata "$image" "$scan_id" "$critical" "$high" "$medium" "$total"
}

# Generate summary report
generate_summary_report() {
    local image="$1"
    local scan_id="$2"
    local critical="$3"
    local high="$4"
    local medium="$5"
    local total="$6"
    
    local report_file="$REPORTS_DIR/summary-$scan_id.json"
    
    cat > "$report_file" <<EOF
{
  "scan_id": "$scan_id",
  "image": "$image",
  "timestamp": "$(date -Iseconds)",
  "vulnerabilities": {
    "critical": $critical,
    "high": $high,
    "medium": $medium,
    "total": $total
  },
  "status": "$([ $critical -eq 0 ] && [ $high -le 5 ] && echo "PASS" || echo "FAIL")",
  "threshold_exceeded": $([ $critical -gt 0 ] || [ $high -gt 5 ] && echo "true" || echo "false")
}
EOF
    
    log "Summary report generated: $report_file"
}

# Send security alert
send_security_alert() {
    local image="$1"
    local critical="$2"
    local high="$3"
    local medium="$4"
    local scan_id="$5"
    
    local message="🚨 *Security Alert*: Vulnerabilities detected in \`$image\`
    
📊 *Vulnerability Count:*
• Critical: $critical
• High: $high  
• Medium: $medium

🔍 *Scan ID:* $scan_id
⏰ *Time:* $(date)

🔗 *Action Required:* Review and update the image immediately."
    
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK" || log "Failed to send Slack alert"
    fi
    
    log "Security alert sent for $image"
}

# Store scan metadata
store_scan_metadata() {
    local image="$1"
    local scan_id="$2"
    local critical="$3"
    local high="$4"
    local medium="$5"
    local total="$6"
    
    local metadata_file="$RESULTS_DIR/metadata.jsonl"
    
    echo "{\"timestamp\":\"$(date -Iseconds)\",\"image\":\"$image\",\"scan_id\":\"$scan_id\",\"critical\":$critical,\"high\":$high,\"medium\":$medium,\"total\":$total}" >> "$metadata_file"
}

# Get list of images to scan
get_images_to_scan() {
    # Get running container images
    docker ps --format "table {{.Image}}" | tail -n +2 | sort -u
    
    # Get recently built images (last 24 hours)
    docker images --format "table {{.Repository}}:{{.Tag}}" \
        --filter "since=24h" | tail -n +2 | grep -v "<none>" || true
}

# Cleanup old results
cleanup_old_results() {
    log "Cleaning up old scan results..."
    
    # Keep results for 30 days
    find "$RESULTS_DIR" -type f -name "*.json" -mtime +30 -delete || true
    find "$REPORTS_DIR" -type f -name "*.html" -mtime +30 -delete || true
    find "$REPORTS_DIR" -type f -name "*.json" -mtime +30 -delete || true
    
    log "Cleanup completed"
}

# Main scanning loop
main() {
    log "Starting continuous security scanner"
    log "Scan interval: ${SCAN_INTERVAL}s"
    log "Vulnerability threshold: $VULNERABILITY_THRESHOLD"
    
    while true; do
        log "Starting new scan cycle"
        
        # Cleanup old results
        cleanup_old_results
        
        # Get images to scan
        local images
        images=$(get_images_to_scan)
        
        if [[ -z "$images" ]]; then
            log "No images found to scan"
        else
            local image_count
            image_count=$(echo "$images" | wc -l)
            log "Found $image_count images to scan"
            
            # Scan each image
            while IFS= read -r image; do
                if [[ -n "$image" ]]; then
                    scan_image "$image" || log "Failed to scan $image"
                fi
            done <<< "$images"
        fi
        
        log "Scan cycle completed. Sleeping for ${SCAN_INTERVAL}s"
        sleep "$SCAN_INTERVAL"
    done
}

# Handle signals
trap 'log "Received termination signal, shutting down..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"