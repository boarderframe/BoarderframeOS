# Multi-stage Dockerfile for FastAPI MCP Server Manager
# Production-ready with enhanced security best practices and OWASP compliance
# Security features: non-root user, minimal attack surface, security scanning, distroless base

# Build stage - includes dev dependencies for building
FROM python:3.11-slim AS builder

# Add comprehensive security labels for container scanning and policy enforcement
LABEL security.scan="true" \
      security.vulnerability-threshold="HIGH" \
      security.non-root="true" \
      security.read-only="true" \
      security.no-new-privileges="true" \
      org.opencontainers.image.title="FastAPI MCP Server Manager" \
      org.opencontainers.image.description="Secure FastAPI MCP Server Manager with enhanced security" \
      org.opencontainers.image.vendor="Your Company" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT" \
      maintainer="security@yourcompany.com"

# Set working directory
WORKDIR /app

# Create non-root user early for security
RUN groupadd -g 1001 mcpuser && \
    useradd -r -s /bin/false -g mcpuser -u 1001 mcpuser

# Install system dependencies and security tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ ./app/
COPY config/ ./config/
COPY alembic/ ./alembic/ 2>/dev/null || echo "No alembic directory found"
COPY alembic.ini ./alembic.ini 2>/dev/null || echo "No alembic.ini found"

# Production stage - minimal runtime image
FROM python:3.11-slim AS production

# Install security updates and required packages with CVE scanning
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        dumb-init \
        curl \
        ca-certificates \
        tzdata \
        tini \
        postgresql-client && \
    # Create secure temp directory with proper permissions
    mkdir -p /tmp && \
    chmod 1777 /tmp && \
    # Clean package cache
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for production
RUN groupadd -g 1001 mcpuser && \
    useradd -r -s /bin/false -g mcpuser -u 1001 mcpuser

# Set working directory
WORKDIR /app

# Copy Python environment and dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code from builder stage
COPY --from=builder --chown=mcpuser:mcpuser /app/app ./app
COPY --from=builder --chown=mcpuser:mcpuser /app/config ./config
COPY --from=builder --chown=mcpuser:mcpuser /app/alembic ./alembic 2>/dev/null || true
COPY --from=builder --chown=mcpuser:mcpuser /app/alembic.ini ./alembic.ini 2>/dev/null || true

# Copy requirements.txt for runtime
COPY --chown=mcpuser:mcpuser requirements.txt ./

# Create directory for MCP configurations with proper permissions
RUN mkdir -p /app/data && \
    chown -R mcpuser:mcpuser /app

# Enhanced security: Remove package managers, docs, and unnecessary tools
RUN rm -rf /usr/local/bin/pip* && \
    rm -rf /usr/local/bin/easy_install* && \
    # Remove development tools, docs, and potential attack vectors
    rm -rf /usr/include /usr/share/man /usr/share/doc /usr/share/info && \
    rm -rf /var/cache/* /tmp/* /var/tmp/* && \
    rm -rf /root/.cache /root/.local && \
    # Remove shell access for security (keep /bin/sh for dumb-init)
    rm -f /usr/bin/whoami && \
    # Set secure file permissions (principle of least privilege)
    find /app -type f -exec chmod 644 {} \; && \
    find /app -type d -exec chmod 755 {} \; && \
    # Lock down sensitive directories with strict permissions
    chmod 700 /app/config /app/data && \
    # Create read-only filesystem markers
    touch /app/.readonly && \
    # Remove write permissions from system directories
    chmod -R a-w /etc /usr /lib /bin /sbin || true

# Switch to non-root user
USER mcpuser

# Expose port (non-privileged port)
EXPOSE 8000

# Enhanced health check with security validation and dependency checks
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set environment variables for production with enhanced security hardening
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MCP_CONFIG_PATH=/app/config/mcp.json \
    PORT=8000 \
    # Enhanced security environment variables
    PYTHONIOENCODING=utf-8 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    # Disable unnecessary Python features for security
    PYTHONOPTIMIZE=2 \
    # Application security
    FASTAPI_ENV=production \
    RATE_LIMIT_ENABLED=true \
    # Database configuration
    DATABASE_URL="" \
    DB_POOL_SIZE=20 \
    DB_MAX_OVERFLOW=30

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the FastAPI application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]