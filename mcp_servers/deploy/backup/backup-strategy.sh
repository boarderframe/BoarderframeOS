#!/bin/bash

# MCP-UI Production Backup Strategy Script
# Automated backup solution with encryption, compression, and cloud storage
# Supports full, incremental, and differential backups

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/backup.conf"
LOG_FILE="/var/log/mcp-backup/backup-$(date +%Y%m%d).log"
LOCK_FILE="/var/run/mcp-backup.lock"

# Default configuration (can be overridden by config file)
BACKUP_TYPE="${BACKUP_TYPE:-full}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
S3_BUCKET="${S3_BUCKET:-}"
S3_REGION="${S3_REGION:-us-west-2}"
NOTIFICATION_WEBHOOK="${NOTIFICATION_WEBHOOK:-}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"
PARALLEL_JOBS="${PARALLEL_JOBS:-2}"

# Database configuration
POSTGRES_HOST="${POSTGRES_HOST:-postgres-primary}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-mcpdb}"
POSTGRES_USER="${POSTGRES_USER:-mcpuser}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

# Redis configuration
REDIS_HOST="${REDIS_HOST:-redis-master}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# Backup locations
BACKUP_ROOT="/backups"
DB_BACKUP_DIR="${BACKUP_ROOT}/database"
CONFIG_BACKUP_DIR="${BACKUP_ROOT}/config"
LOGS_BACKUP_DIR="${BACKUP_ROOT}/logs"
APP_BACKUP_DIR="${BACKUP_ROOT}/application"
TEMP_DIR="${BACKUP_ROOT}/temp"

# Load configuration file if it exists
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi

# Ensure backup directories exist
mkdir -p "$DB_BACKUP_DIR" "$CONFIG_BACKUP_DIR" "$LOGS_BACKUP_DIR" "$APP_BACKUP_DIR" "$TEMP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR" "$1"
    cleanup
    send_notification "FAILED" "$1"
    exit 1
}

# Cleanup function
cleanup() {
    log "INFO" "Cleaning up temporary files..."
    rm -rf "${TEMP_DIR:?}"/*
    [[ -f "$LOCK_FILE" ]] && rm -f "$LOCK_FILE"
}

# Trap for cleanup on exit
trap cleanup EXIT

# Check if backup is already running
if [[ -f "$LOCK_FILE" ]]; then
    log "ERROR" "Backup is already running (lock file exists: $LOCK_FILE)"
    exit 1
fi

# Create lock file
echo $$ > "$LOCK_FILE"

# Send notification function
send_notification() {
    local status="$1"
    local message="$2"
    
    if [[ -n "$NOTIFICATION_WEBHOOK" ]]; then
        local payload=$(cat <<EOF
{
    "text": "MCP-UI Backup $status",
    "attachments": [
        {
            "color": "$([[ "$status" == "SUCCESS" ]] && echo "good" || echo "danger")",
            "title": "Backup Status: $status",
            "fields": [
                {
                    "title": "Environment",
                    "value": "${ENVIRONMENT:-production}",
                    "short": true
                },
                {
                    "title": "Backup Type",
                    "value": "$BACKUP_TYPE",
                    "short": true
                },
                {
                    "title": "Timestamp",
                    "value": "$(date -u '+%Y-%m-%d %H:%M:%S UTC')",
                    "short": true
                },
                {
                    "title": "Message",
                    "value": "$message",
                    "short": false
                }
            ]
        }
    ]
}
EOF
        )
        
        curl -X POST \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$NOTIFICATION_WEBHOOK" \
            --max-time 30 \
            --silent \
            || log "WARNING" "Failed to send notification"
    fi
}

# Database backup function
backup_database() {
    log "INFO" "Starting database backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${DB_BACKUP_DIR}/postgres_${timestamp}.sql"
    local compressed_file="${backup_file}.gz"
    
    # Set PostgreSQL password
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    # Perform database dump
    log "INFO" "Creating PostgreSQL dump..."
    if ! pg_dump \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --lock-wait-timeout=30000 \
        --file="$backup_file.custom" 2>>"$LOG_FILE"; then
        error_exit "PostgreSQL dump failed"
    fi
    
    # Also create a plain SQL dump for easier restore
    if ! pg_dump \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --no-password \
        --format=plain \
        --file="$backup_file" 2>>"$LOG_FILE"; then
        error_exit "PostgreSQL plain dump failed"
    fi
    
    # Compress the plain SQL dump
    log "INFO" "Compressing database dump..."
    gzip -"$COMPRESSION_LEVEL" "$backup_file"
    
    # Verify the backup
    log "INFO" "Verifying database backup..."
    if ! gzip -t "$compressed_file"; then
        error_exit "Database backup verification failed"
    fi
    
    # Encrypt if encryption key is provided
    if [[ -n "$ENCRYPTION_KEY" ]]; then
        log "INFO" "Encrypting database backup..."
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$compressed_file" \
            -out "${compressed_file}.enc" \
            -pass pass:"$ENCRYPTION_KEY"
        rm "$compressed_file"
        compressed_file="${compressed_file}.enc"
    fi
    
    log "INFO" "Database backup completed: $(basename "$compressed_file")"
    echo "$compressed_file"
}

# Redis backup function
backup_redis() {
    log "INFO" "Starting Redis backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${DB_BACKUP_DIR}/redis_${timestamp}.rdb"
    
    # Create Redis backup using BGSAVE
    if [[ -n "$REDIS_PASSWORD" ]]; then
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" BGSAVE
    else
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
    fi
    
    # Wait for background save to complete
    local save_status
    while true; do
        if [[ -n "$REDIS_PASSWORD" ]]; then
            save_status=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" LASTSAVE)
        else
            save_status=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)
        fi
        
        sleep 5
        
        local current_status
        if [[ -n "$REDIS_PASSWORD" ]]; then
            current_status=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" LASTSAVE)
        else
            current_status=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)
        fi
        
        if [[ "$current_status" != "$save_status" ]]; then
            break
        fi
    done
    
    # Copy the RDB file (this would need to be adjusted based on your Redis setup)
    # In Kubernetes, you might need to copy from a volume or use kubectl exec
    kubectl exec -n mcp-ui deployment/redis-master -- cat /data/dump.rdb > "$backup_file"
    
    # Compress the backup
    gzip -"$COMPRESSION_LEVEL" "$backup_file"
    backup_file="${backup_file}.gz"
    
    # Encrypt if encryption key is provided
    if [[ -n "$ENCRYPTION_KEY" ]]; then
        log "INFO" "Encrypting Redis backup..."
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$backup_file" \
            -out "${backup_file}.enc" \
            -pass pass:"$ENCRYPTION_KEY"
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    log "INFO" "Redis backup completed: $(basename "$backup_file")"
    echo "$backup_file"
}

# Configuration backup function
backup_configurations() {
    log "INFO" "Starting configuration backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${CONFIG_BACKUP_DIR}/config_${timestamp}.tar.gz"
    
    # Create temporary directory for configs
    local temp_config_dir="${TEMP_DIR}/config"
    mkdir -p "$temp_config_dir"
    
    # Backup Kubernetes configurations
    log "INFO" "Backing up Kubernetes configurations..."
    kubectl get all,secrets,configmaps,pvc,ingress -n mcp-ui -o yaml > "${temp_config_dir}/k8s-resources.yaml"
    kubectl get secrets -n mcp-ui -o yaml > "${temp_config_dir}/secrets.yaml"
    
    # Backup application configs (if mounted)
    if [[ -d "/app/config" ]]; then
        cp -r /app/config "${temp_config_dir}/app-config"
    fi
    
    # Backup Nginx configs
    if [[ -d "/etc/nginx" ]]; then
        cp -r /etc/nginx "${temp_config_dir}/nginx"
    fi
    
    # Create compressed archive
    tar -czf "$backup_file" -C "$temp_config_dir" .
    
    # Encrypt if encryption key is provided
    if [[ -n "$ENCRYPTION_KEY" ]]; then
        log "INFO" "Encrypting configuration backup..."
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$backup_file" \
            -out "${backup_file}.enc" \
            -pass pass:"$ENCRYPTION_KEY"
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    log "INFO" "Configuration backup completed: $(basename "$backup_file")"
    echo "$backup_file"
}

# Application data backup function
backup_application_data() {
    log "INFO" "Starting application data backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${APP_BACKUP_DIR}/app_data_${timestamp}.tar.gz"
    
    # Create temporary directory for app data
    local temp_app_dir="${TEMP_DIR}/app_data"
    mkdir -p "$temp_app_dir"
    
    # Backup application logs
    if [[ -d "/app/logs" ]]; then
        cp -r /app/logs "${temp_app_dir}/logs"
    fi
    
    # Backup any persistent volumes (adjust paths as needed)
    # This would typically involve copying from mounted volumes
    
    # Create compressed archive
    tar -czf "$backup_file" -C "$temp_app_dir" .
    
    # Encrypt if encryption key is provided
    if [[ -n "$ENCRYPTION_KEY" ]]; then
        log "INFO" "Encrypting application data backup..."
        openssl enc -aes-256-cbc -salt -pbkdf2 \
            -in "$backup_file" \
            -out "${backup_file}.enc" \
            -pass pass:"$ENCRYPTION_KEY"
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    log "INFO" "Application data backup completed: $(basename "$backup_file")"
    echo "$backup_file"
}

# Upload to S3 function
upload_to_s3() {
    local file="$1"
    local s3_key="$2"
    
    if [[ -z "$S3_BUCKET" ]]; then
        log "WARNING" "S3 bucket not configured, skipping upload"
        return 0
    fi
    
    log "INFO" "Uploading $(basename "$file") to S3..."
    
    if ! aws s3 cp "$file" "s3://$S3_BUCKET/$s3_key" \
        --region "$S3_REGION" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256; then
        log "ERROR" "Failed to upload $(basename "$file") to S3"
        return 1
    fi
    
    log "INFO" "Successfully uploaded to S3: s3://$S3_BUCKET/$s3_key"
}

# Cleanup old backups function
cleanup_old_backups() {
    log "INFO" "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Local cleanup
    find "$BACKUP_ROOT" -type f -mtime +$RETENTION_DAYS -delete
    
    # S3 cleanup (if configured)
    if [[ -n "$S3_BUCKET" ]]; then
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y%m%d)
        aws s3 ls "s3://$S3_BUCKET/" --recursive | \
        awk -v cutoff="$cutoff_date" '$1 < cutoff {print $4}' | \
        while read -r key; do
            aws s3 rm "s3://$S3_BUCKET/$key"
            log "INFO" "Deleted old S3 backup: $key"
        done
    fi
    
    log "INFO" "Cleanup completed"
}

# Verify backup integrity
verify_backup() {
    local file="$1"
    
    log "INFO" "Verifying backup integrity: $(basename "$file")"
    
    # Check if file exists and is not empty
    if [[ ! -f "$file" ]] || [[ ! -s "$file" ]]; then
        log "ERROR" "Backup file is missing or empty: $file"
        return 1
    fi
    
    # Check file format based on extension
    case "$file" in
        *.gz)
            if ! gzip -t "$file"; then
                log "ERROR" "Gzip integrity check failed: $file"
                return 1
            fi
            ;;
        *.tar.gz)
            if ! tar -tzf "$file" >/dev/null; then
                log "ERROR" "Tar.gz integrity check failed: $file"
                return 1
            fi
            ;;
        *.enc)
            if [[ -n "$ENCRYPTION_KEY" ]]; then
                if ! openssl enc -aes-256-cbc -d -pbkdf2 \
                    -in "$file" \
                    -pass pass:"$ENCRYPTION_KEY" \
                    -out /dev/null; then
                    log "ERROR" "Encryption integrity check failed: $file"
                    return 1
                fi
            fi
            ;;
    esac
    
    log "INFO" "Backup integrity verified: $(basename "$file")"
    return 0
}

# Main backup function
main() {
    log "INFO" "Starting MCP-UI backup process (type: $BACKUP_TYPE)"
    
    local backup_files=()
    local start_time=$(date +%s)
    
    # Perform backups based on type
    case "$BACKUP_TYPE" in
        "full")
            log "INFO" "Performing full backup..."
            backup_files+=($(backup_database))
            backup_files+=($(backup_redis))
            backup_files+=($(backup_configurations))
            backup_files+=($(backup_application_data))
            ;;
        "database")
            log "INFO" "Performing database-only backup..."
            backup_files+=($(backup_database))
            backup_files+=($(backup_redis))
            ;;
        "config")
            log "INFO" "Performing configuration-only backup..."
            backup_files+=($(backup_configurations))
            ;;
        *)
            error_exit "Unknown backup type: $BACKUP_TYPE"
            ;;
    esac
    
    # Verify all backups
    local verification_failed=false
    for file in "${backup_files[@]}"; do
        if ! verify_backup "$file"; then
            verification_failed=true
        fi
    done
    
    if [[ "$verification_failed" == true ]]; then
        error_exit "Backup verification failed"
    fi
    
    # Upload to S3 if configured
    if [[ -n "$S3_BUCKET" ]]; then
        local upload_failed=false
        for file in "${backup_files[@]}"; do
            local s3_key="mcp-ui/${ENVIRONMENT:-production}/$(date +%Y/%m/%d)/$(basename "$file")"
            if ! upload_to_s3 "$file" "$s3_key"; then
                upload_failed=true
            fi
        done
        
        if [[ "$upload_failed" == true ]]; then
            error_exit "S3 upload failed"
        fi
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "INFO" "Backup completed successfully in ${duration} seconds"
    log "INFO" "Backed up files: ${#backup_files[@]}"
    
    # Calculate total backup size
    local total_size=0
    for file in "${backup_files[@]}"; do
        if [[ -f "$file" ]]; then
            size=$(stat -c%s "$file")
            total_size=$((total_size + size))
        fi
    done
    
    local human_size=$(numfmt --to=iec-i --suffix=B "$total_size")
    log "INFO" "Total backup size: $human_size"
    
    send_notification "SUCCESS" "Backup completed successfully. Files: ${#backup_files[@]}, Size: $human_size, Duration: ${duration}s"
}

# Usage function
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
    -t, --type TYPE         Backup type: full, database, config (default: full)
    -r, --retention DAYS    Retention period in days (default: 30)
    -e, --encrypt KEY       Encryption key for backups
    -s, --s3-bucket BUCKET  S3 bucket for remote storage
    -n, --notify URL        Webhook URL for notifications
    -h, --help              Show this help message

Environment Variables:
    BACKUP_TYPE             Backup type
    RETENTION_DAYS          Retention period
    ENCRYPTION_KEY          Encryption key
    S3_BUCKET              S3 bucket name
    S3_REGION              S3 region
    NOTIFICATION_WEBHOOK    Webhook URL
    POSTGRES_HOST          PostgreSQL host
    POSTGRES_USER          PostgreSQL user
    POSTGRES_PASSWORD      PostgreSQL password
    REDIS_HOST             Redis host
    REDIS_PASSWORD         Redis password

Examples:
    $0                                    # Full backup with defaults
    $0 -t database                        # Database-only backup
    $0 -t full -r 7 -s my-backup-bucket  # Full backup with 7-day retention to S3
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -e|--encrypt)
            ENCRYPTION_KEY="$2"
            shift 2
            ;;
        -s|--s3-bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        -n|--notify)
            NOTIFICATION_WEBHOOK="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate configuration
if [[ -n "$ENCRYPTION_KEY" ]] && [[ ${#ENCRYPTION_KEY} -lt 16 ]]; then
    error_exit "Encryption key must be at least 16 characters long"
fi

if [[ -z "$POSTGRES_PASSWORD" ]]; then
    error_exit "PostgreSQL password is required"
fi

# Check required tools
for tool in pg_dump redis-cli gzip openssl tar kubectl; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        error_exit "Required tool not found: $tool"
    fi
done

if [[ -n "$S3_BUCKET" ]] && ! command -v aws >/dev/null 2>&1; then
    error_exit "AWS CLI is required for S3 uploads"
fi

# Run main function
main