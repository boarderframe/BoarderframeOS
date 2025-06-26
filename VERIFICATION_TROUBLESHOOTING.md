# BoarderframeOS Verification Troubleshooting Guide

## Common Issues and Solutions

### 1. Missing Python Dependencies

**Error**: `ModuleNotFoundError: No module named 'psycopg2'` (or aiohttp, httpx, websockets)

**Solution**:
```bash
# Quick fix - install all verification dependencies
pip install -r requirements-verification.txt

# Or install individually
pip install psycopg2-binary aiohttp httpx websockets psutil redis
```

### 2. Docker Not Running

**Error**: Docker services verification fails

**Solution**:
1. Start Docker Desktop (macOS/Windows) or Docker daemon (Linux)
2. Verify Docker is running:
   ```bash
   docker ps
   ```
3. Start required services:
   ```bash
   docker-compose up -d postgresql redis
   ```

### 3. AgentMessage Type Error

**Error**: `AgentMessage.__init__() missing 1 required positional argument: 'message_type'`

**Solution**: This has been fixed in the updated `verify_message_bus.py`. The AgentMessage class now includes the required `message_type` parameter.

### 4. PostgreSQL Connection Issues

**Error**: Cannot connect to PostgreSQL on port 5434

**Solution**:
```bash
# Check if PostgreSQL container is running
docker ps | grep postgres

# If not running, start it
docker-compose up -d postgresql

# Verify connection
docker exec boarderframeos_postgres psql -U boarderframe -d boarderframeos -c "SELECT 1;"
```

### 5. MCP Servers Not Running

**Error**: All MCP servers show as offline

**Solution**:
```bash
# Start MCP servers using the generated script
./start_offline_mcp_servers.sh

# Or start individually
python mcp/registry_server.py --port 8009 &
python mcp/filesystem_server.py --port 8001 &
# ... etc
```

## Quick Setup Commands

### Option 1: Automated Setup
```bash
# Run the setup script
python setup_verification_environment.py

# Or use the quick fix
python fix_verification_issues.py
```

### Option 2: Manual Setup
```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# 2. Install dependencies
pip install -r requirements-verification.txt

# 3. Start Docker services
docker-compose up -d postgresql redis

# 4. Run verification
python run_all_verifications.py
```

## Verification Process

### Phase 1: Infrastructure Only
If you just want to test the basic infrastructure:
```bash
python verify_docker_services.py
python verify_mcp_servers.py
python verify_message_bus.py
```

### Phase 2: With Running System
If BoarderframeOS is running:
```bash
# Start the system
python startup.py

# Then run full verification
python run_all_verifications.py
```

### Phase 3: Individual Component Testing
Test specific components:
```bash
# Test Corporate HQ (must be running on port 8888)
python verify_corporate_hq.py

# Test agents
python verify_agents.py

# Test performance
python analyze_performance.py
```

## Expected Results

### Healthy System
- Docker Services: ✅ Running
- MCP Servers: 9/9 healthy
- Message Bus: Functional with good throughput
- Agents: 5/5 loaded and functional
- UI Components: All accessible

### Minimal Working System
- Docker Services: ✅ Running
- At least 3 MCP servers online (Registry, Database, Analytics)
- Message Bus: Basic functionality
- At least 1 agent functional
- Corporate HQ accessible

## Interpreting Results

### Success Rate
- **90-100%**: Excellent - system fully operational
- **70-89%**: Good - core functionality working
- **50-69%**: Fair - basic functionality available
- **Below 50%**: Poor - significant issues need addressing

### Critical Components
These must be working for basic functionality:
1. Docker Services (PostgreSQL + Redis)
2. Message Bus
3. At least one MCP server
4. Corporate HQ

### Non-Critical Components
These enhance functionality but aren't required:
- All agents functional
- All UI components
- Performance optimization
- Monitoring setup

## Getting Help

1. Check the detailed reports:
   - `verification_report.html` - Visual summary
   - `master_verification_report.json` - Detailed JSON data
   - Individual `*_report.json` files for each component

2. Review logs:
   - Check Docker logs: `docker-compose logs`
   - Check Python output for specific errors

3. Common fixes:
   - Restart Docker
   - Reinstall dependencies
   - Check port availability (8888, 8889, 8890, 8000-8011)
   - Ensure sufficient system resources