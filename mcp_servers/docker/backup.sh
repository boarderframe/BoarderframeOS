#!/bin/bash

# MCP Server Manager Backup and Disaster Recovery Script
# Provides comprehensive backup, restore, and disaster recovery capabilities

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-mcp-server-manager}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Notification function
notify() {
    local message="$1"
    local status="${2:-info}"
    
    log "$message"
    
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        local color="good"
        if [[ "$status" == "error" ]]; then
            color="danger"
        elif [[ "$status" == "warning" ]]; then
            color="warning"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"MCP Backup: $message\"}]}" \
            "$SLACK_WEBHOOK" >/dev/null 2>&1 || true
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    mkdir -p "$BACKUP_DIR"
    
    success "Prerequisites check passed"
}

# Encrypt file if encryption key is provided
encrypt_file() {
    local file="$1"
    
    if [[ -n "$ENCRYPTION_KEY" ]]; then
        log "Encrypting $file..."
        openssl enc -aes-256-cbc -salt -in "$file" -out "${file}.enc" -k "$ENCRYPTION_KEY"
        rm "$file"
        echo "${file}.enc"
    else
        echo "$file"
    fi
}

# Decrypt file if encryption key is provided
decrypt_file() {
    local file="$1"
    
    if [[ "$file" == *.enc ]] && [[ -n "$ENCRYPTION_KEY" ]]; then
        log "Decrypting $file..."
        local decrypted_file="${file%.enc}"
        openssl enc -aes-256-cbc -d -salt -in "$file" -out "$decrypted_file" -k "$ENCRYPTION_KEY"
        echo "$decrypted_file"
    else
        echo "$file"
    fi
}

# Upload to S3 if configured
upload_to_s3() {
    local file="$1"
    
    if [[ -n "$S3_BUCKET" ]] && command -v aws &> /dev/null; then
        log "Uploading $file to S3..."
        aws s3 cp "$file" "s3://$S3_BUCKET/backups/$(basename "$file")"
        success "Uploaded to S3: s3://$S3_BUCKET/backups/$(basename "$file")"
    fi
}

# Create full backup
backup_full() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="full_backup_$timestamp"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    log "Creating full backup: $backup_name"
    mkdir -p "$backup_path"
    
    # Backup Docker volumes
    log "Backing up Docker volumes..."
    local volumes=$(docker volume ls --filter "name=${COMPOSE_PROJECT_NAME}" --format "{{.Name}}")
    
    for volume in $volumes; do
        log "Backing up volume: $volume"
        docker run --rm \
            -v "$volume":/volume \
            -v "$backup_path":/backup \
            alpine tar czf "/backup/${volume}.tar.gz" -C /volume .
    done
    
    # Backup configuration files
    log "Backing up configuration files..."
    tar czf "$backup_path/configs.tar.gz" \
        docker-compose.yml \
        docker-compose.prod.yml \
        docker-compose.dev.yml \
        docker/nginx/nginx.conf \
        docker/monitoring/prometheus/prometheus.yml \
        .env 2>/dev/null || true
    
    # Backup database dump (Redis)
    log "Creating Redis backup..."
    docker exec "${COMPOSE_PROJECT_NAME}_redis_1" redis-cli BGSAVE
    sleep 5  # Wait for background save to complete
    docker cp "${COMPOSE_PROJECT_NAME}_redis_1:/data/dump.rdb" "$backup_path/redis_dump.rdb"
    
    # Create backup manifest
    log "Creating backup manifest..."
    cat > "$backup_path/manifest.json" << EOF
{
    "backup_name": "$backup_name",
    "timestamp": "$timestamp",
    "type": "full",
    "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "volumes": [$(echo "$volumes" | sed 's/.*/"&"/' | paste -sd,)],
    "size": "$(du -sh "$backup_path" | cut -f1)"
}
EOF
    
    # Create archive
    log "Creating backup archive..."
    tar czf "$BACKUP_DIR/${backup_name}.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    rm -rf "$backup_path"
    
    # Encrypt if configured
    local final_backup=$(encrypt_file "$BACKUP_DIR/${backup_name}.tar.gz")
    
    # Upload to S3 if configured
    upload_to_s3 "$final_backup"
    
    success "Full backup completed: $(basename "$final_backup")"
    notify "Full backup completed successfully: $(basename "$final_backup")" "good"
}

# Create incremental backup (volumes only)
backup_incremental() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="incremental_backup_$timestamp"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    log "Creating incremental backup: $backup_name"
    mkdir -p "$backup_path"
    
    # Backup only data volumes
    local data_volumes=$(docker volume ls --filter "name=${COMPOSE_PROJECT_NAME}" --filter "name=data" --format "{{.Name}}")
    
    for volume in $data_volumes; do
        log "Backing up data volume: $volume"
        docker run --rm \
            -v "$volume":/volume \
            -v "$backup_path":/backup \
            alpine tar czf "/backup/${volume}.tar.gz" -C /volume .
    done
    
    # Create manifest
    cat > "$backup_path/manifest.json" << EOF
{
    "backup_name": "$backup_name",
    "timestamp": "$timestamp",
    "type": "incremental",
    "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "volumes": [$(echo "$data_volumes" | sed 's/.*/"&"/' | paste -sd,)],
    "size": "$(du -sh "$backup_path" | cut -f1)"
}
EOF
    
    # Create archive
    tar czf "$BACKUP_DIR/${backup_name}.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    rm -rf "$backup_path"
    
    # Encrypt if configured
    local final_backup=$(encrypt_file "$BACKUP_DIR/${backup_name}.tar.gz")
    
    # Upload to S3 if configured
    upload_to_s3 "$final_backup"
    
    success "Incremental backup completed: $(basename "$final_backup")"
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log "Restoring from backup: $backup_file"
    
    # Decrypt if needed
    backup_file=$(decrypt_file "$backup_file")
    
    # Extract backup
    local restore_dir=$(mktemp -d)
    tar xzf "$backup_file" -C "$restore_dir"
    
    # Find backup directory
    local backup_dir=$(find "$restore_dir" -type d -name "*backup*" | head -n1)
    
    if [[ ! -d "$backup_dir" ]]; then
        error "Invalid backup structure"
        exit 1
    fi
    
    # Stop services
    log "Stopping services..."
    docker-compose down
    
    # Restore volumes
    log "Restoring volumes..."
    for volume_archive in "$backup_dir"/*.tar.gz; do
        if [[ -f "$volume_archive" ]] && [[ "$(basename "$volume_archive")" != "configs.tar.gz" ]]; then
            local volume_name=$(basename "$volume_archive" .tar.gz)
            log "Restoring volume: $volume_name"
            
            # Remove existing volume
            docker volume rm "$volume_name" 2>/dev/null || true
            
            # Create new volume
            docker volume create "$volume_name"
            
            # Restore data
            docker run --rm \
                -v "$volume_name":/volume \
                -v "$backup_dir":/backup \
                alpine tar xzf "/backup/$(basename "$volume_archive")" -C /volume
        fi
    done
    
    # Restore Redis data if available
    if [[ -f "$backup_dir/redis_dump.rdb" ]]; then
        log "Restoring Redis data..."
        docker-compose up -d redis
        sleep 10
        docker cp "$backup_dir/redis_dump.rdb" "${COMPOSE_PROJECT_NAME}_redis_1:/data/dump.rdb"
        docker-compose restart redis
    fi
    
    # Restore configurations if available
    if [[ -f "$backup_dir/configs.tar.gz" ]]; then
        log "Restoring configurations..."
        tar xzf "$backup_dir/configs.tar.gz" -C .
    fi
    
    # Start services
    log "Starting services..."
    docker-compose up -d
    
    # Clean up
    rm -rf "$restore_dir"
    
    success "Restore completed successfully"
    notify "Restore completed successfully from $(basename "$backup_file")" "good"
}

# List available backups
list_backups() {
    log "Available backups:"
    
    if [[ -d "$BACKUP_DIR" ]]; then
        ls -la "$BACKUP_DIR"/*.tar.gz* 2>/dev/null | while read -r line; do
            echo "  $line"
        done
    else
        warning "No backup directory found"
    fi
    
    # List S3 backups if configured
    if [[ -n "$S3_BUCKET" ]] && command -v aws &> /dev/null; then
        log "S3 backups:"
        aws s3 ls "s3://$S3_BUCKET/backups/" 2>/dev/null | while read -r line; do
            echo "  S3: $line"
        done
    fi
}

# Clean old backups
cleanup_backups() {
    log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    find "$BACKUP_DIR" -name "*.tar.gz*" -type f -mtime +"$RETENTION_DAYS" -delete
    
    success "Cleanup completed"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    log "Verifying backup integrity: $backup_file"
    
    # Decrypt if needed
    backup_file=$(decrypt_file "$backup_file")
    
    # Test archive
    if tar tzf "$backup_file" >/dev/null 2>&1; then
        success "Backup archive is valid"
    else
        error "Backup archive is corrupted"
        exit 1
    fi
    
    # Extract and check manifest
    local temp_dir=$(mktemp -d)
    tar xzf "$backup_file" -C "$temp_dir"
    
    local manifest_file=$(find "$temp_dir" -name "manifest.json" | head -n1)
    if [[ -f "$manifest_file" ]]; then
        log "Backup manifest:"
        cat "$manifest_file" | jq .
    else
        warning "No manifest found in backup"
    fi
    
    rm -rf "$temp_dir"
}

# Main script logic
case "${1:-help}" in
    "full")
        check_prerequisites
        backup_full
        ;;
    "incremental")
        check_prerequisites
        backup_incremental
        ;;
    "restore")
        if [[ -z "${2:-}" ]]; then
            error "Please specify backup file to restore"
            exit 1
        fi
        check_prerequisites
        restore_backup "$2"
        ;;
    "list")
        list_backups
        ;;
    "cleanup")
        cleanup_backups
        ;;
    "verify")
        if [[ -z "${2:-}" ]]; then
            error "Please specify backup file to verify"
            exit 1
        fi
        verify_backup "$2"
        ;;
    "help"|*)
        echo "Usage: $0 {full|incremental|restore|list|cleanup|verify} [backup_file]"
        echo ""
        echo "Commands:"
        echo "  full                    - Create full backup (all volumes + configs)"
        echo "  incremental            - Create incremental backup (data volumes only)"
        echo "  restore <backup_file>  - Restore from backup file"
        echo "  list                   - List available backups"
        echo "  cleanup                - Remove old backups based on retention policy"
        echo "  verify <backup_file>   - Verify backup integrity"
        echo ""
        echo "Environment Variables:"
        echo "  BACKUP_DIR             - Backup directory (default: ./backups)"
        echo "  RETENTION_DAYS         - Backup retention in days (default: 30)"
        echo "  S3_BUCKET             - S3 bucket for remote backups"
        echo "  ENCRYPTION_KEY         - Key for backup encryption"
        echo "  SLACK_WEBHOOK         - Slack webhook for notifications"
        echo ""
        echo "Examples:"
        echo "  $0 full                              - Create full backup"
        echo "  $0 restore backups/backup_20240101.tar.gz - Restore from backup"
        echo "  $0 verify backups/backup_20240101.tar.gz  - Verify backup"
        exit 1
        ;;
esac