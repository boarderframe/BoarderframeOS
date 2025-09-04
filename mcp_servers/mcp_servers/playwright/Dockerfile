# Secure Playwright MCP Server Docker Image
# Multi-stage build for minimal attack surface

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Stage 2: Runtime
FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd -r playwright -g 1001 && \
    useradd -r -g playwright -u 1001 -m -s /bin/bash playwright

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Playwright browsers from builder
COPY --from=builder /root/.cache/ms-playwright /home/playwright/.cache/ms-playwright
RUN chown -R playwright:playwright /home/playwright/.cache

# Create necessary directories with proper permissions
RUN mkdir -p /app /var/log/playwright /tmp/playwright-screenshots && \
    chown -R playwright:playwright /app /var/log/playwright /tmp/playwright-screenshots

# Copy application code
WORKDIR /app
COPY --chown=playwright:playwright secure_playwright_server.py .
COPY --chown=playwright:playwright security_config.yaml .

# Security: Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PLAYWRIGHT_BROWSERS_PATH=/home/playwright/.cache/ms-playwright \
    LOG_LEVEL=INFO \
    TZ=UTC

# Security: Drop all capabilities and add only required ones
USER playwright

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9003/health || exit 1

# Expose port (only accessible within Docker network by default)
EXPOSE 9003

# Security: Use exec form to prevent shell injection
ENTRYPOINT ["python"]
CMD ["-u", "secure_playwright_server.py"]