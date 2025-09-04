#!/bin/bash
# Production entrypoint script for MCP-UI Backend
# Handles database migrations, health checks, and graceful startup

set -euo pipefail

# Configuration
LOG_LEVEL="${LOG_LEVEL:-info}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"
WORKER_CLASS="${WORKER_CLASS:-uvicorn.workers.UvicornWorker}"
WORKER_CONNECTIONS="${WORKER_CONNECTIONS:-1000}"
MAX_REQUESTS="${MAX_REQUESTS:-1000}"
MAX_REQUESTS_JITTER="${MAX_REQUESTS_JITTER:-100}"
TIMEOUT="${TIMEOUT:-30}"
KEEPALIVE="${KEEPALIVE:-5}"
PRELOAD="${PRELOAD:-true}"
RELOAD="${RELOAD:-false}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ENTRYPOINT] $*"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Wait for service to be available
wait_for_service() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local max_attempts=30
    local attempt=1
    
    log "Waiting for $service_name at $host:$port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            log "$service_name is available!"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: $service_name not yet available, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error_exit "$service_name is not available after $max_attempts attempts"
}

# Parse database URL to extract connection details
parse_database_url() {
    if [[ -z "${DATABASE_URL:-}" ]]; then
        error_exit "DATABASE_URL environment variable is required"
    fi
    
    # Extract components from DATABASE_URL
    # Format: postgresql://user:password@host:port/database
    local db_url="$DATABASE_URL"
    
    # Remove protocol
    db_url="${db_url#postgresql://}"
    
    # Extract user:password
    local user_pass="${db_url%%@*}"
    export DB_USER="${user_pass%%:*}"
    export DB_PASS="${user_pass#*:}"
    
    # Extract host:port/database
    local host_port_db="${db_url#*@}"
    local host_port="${host_port_db%%/*}"
    export DB_HOST="${host_port%%:*}"
    export DB_PORT="${host_port#*:}"
    export DB_NAME="${host_port_db#*/}"
    
    log "Database connection details parsed: $DB_HOST:$DB_PORT/$DB_NAME (user: $DB_USER)"
}

# Check database connectivity
check_database() {
    log "Checking database connectivity..."
    
    parse_database_url
    wait_for_service "$DB_HOST" "$DB_PORT" "PostgreSQL"
    
    # Test actual database connection
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1 || \
        error_exit "Failed to connect to database"
    
    log "Database connectivity verified"
}

# Check Redis connectivity
check_redis() {
    if [[ -n "${REDIS_URL:-}" ]]; then
        log "Checking Redis connectivity..."
        
        # Parse Redis URL
        local redis_url="$REDIS_URL"
        redis_url="${redis_url#redis://}"
        
        local redis_host="${redis_url%%:*}"
        local redis_port="${redis_url#*:}"
        redis_port="${redis_port%%/*}"
        
        wait_for_service "$redis_host" "$redis_port" "Redis"
        
        # Test Redis connection
        redis-cli -h "$redis_host" -p "$redis_port" ping >/dev/null 2>&1 || \
            error_exit "Failed to connect to Redis"
        
        log "Redis connectivity verified"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Check if we should run migrations
    if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
        # Set environment for Alembic
        export PYTHONPATH="/app/src:$PYTHONPATH"
        
        # Run migrations
        if ! alembic upgrade head; then
            error_exit "Database migrations failed"
        fi
        
        log "Database migrations completed successfully"
    else
        log "Database migrations skipped (RUN_MIGRATIONS=false)"
    fi
}

# Pre-start hooks
run_prestart_script() {
    if [[ -f "/app/prestart.sh" ]]; then
        log "Running pre-start script..."
        bash /app/prestart.sh || error_exit "Pre-start script failed"
        log "Pre-start script completed"
    fi
}

# Validate configuration
validate_config() {
    log "Validating configuration..."
    
    # Check required environment variables
    local required_vars=(
        "DATABASE_URL"
        "SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
    done
    
    # Validate numeric values
    if ! [[ "$WORKERS" =~ ^[0-9]+$ ]] || [[ "$WORKERS" -lt 1 ]]; then
        error_exit "WORKERS must be a positive integer"
    fi
    
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [[ "$PORT" -lt 1 ]] || [[ "$PORT" -gt 65535 ]]; then
        error_exit "PORT must be a valid port number (1-65535)"
    fi
    
    log "Configuration validation passed"
}

# Setup signal handlers for graceful shutdown
setup_signal_handlers() {
    # This will be handled by dumb-init, but we can add custom logic here if needed
    trap 'log "Received shutdown signal, terminating gracefully..."' TERM INT
}

# Start the application
start_application() {
    log "Starting MCP-UI Backend Application..."
    log "Configuration:"
    log "  Host: $HOST"
    log "  Port: $PORT"
    log "  Workers: $WORKERS"
    log "  Worker Class: $WORKER_CLASS"
    log "  Log Level: $LOG_LEVEL"
    log "  Environment: ${FASTAPI_ENV:-production}"
    
    # Determine if we should use Gunicorn or Uvicorn directly
    if [[ "$WORKERS" -gt 1 ]] && [[ "$RELOAD" != "true" ]]; then
        # Production mode with multiple workers
        log "Starting with Gunicorn (multi-worker mode)..."
        exec gunicorn app.main:app \
            --bind "$HOST:$PORT" \
            --workers "$WORKERS" \
            --worker-class "$WORKER_CLASS" \
            --worker-connections "$WORKER_CONNECTIONS" \
            --max-requests "$MAX_REQUESTS" \
            --max-requests-jitter "$MAX_REQUESTS_JITTER" \
            --timeout "$TIMEOUT" \
            --keepalive "$KEEPALIVE" \
            --preload="$PRELOAD" \
            --log-level "$LOG_LEVEL" \
            --access-logfile - \
            --error-logfile - \
            --log-config-json /app/logging.json \
            --capture-output \
            --enable-stdio-inheritance
    else
        # Development mode or single worker
        log "Starting with Uvicorn (single-worker mode)..."
        local uvicorn_args=(
            app.main:app
            --host "$HOST"
            --port "$PORT"
            --log-level "$LOG_LEVEL"
        )
        
        if [[ "$RELOAD" == "true" ]]; then
            uvicorn_args+=(--reload)
            log "Auto-reload enabled for development"
        fi
        
        exec uvicorn "${uvicorn_args[@]}"
    fi
}

# Create logging configuration
create_logging_config() {
    cat > /app/logging.json << 'EOF'
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    },
    "loggers": {
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": false
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": false
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": false
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": false
        }
    }
}
EOF
}

# Main execution
main() {
    log "MCP-UI Backend starting up..."
    
    # Setup
    setup_signal_handlers
    validate_config
    create_logging_config
    
    # Health checks
    check_database
    check_redis
    
    # Initialization
    run_prestart_script
    run_migrations
    
    # Start application
    start_application
}

# Run main function
main "$@"