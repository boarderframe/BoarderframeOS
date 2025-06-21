# BoarderframeOS Migration Guide

This guide provides comprehensive instructions for migrating your BoarderframeOS installation from one MacBook Pro to another. Follow these steps carefully to ensure all components, data, and configurations are properly transferred.

## Table of Contents
1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [What to Migrate](#what-to-migrate)
3. [Backup Process](#backup-process)
4. [Migration Steps](#migration-steps)
5. [Post-Migration Setup](#post-migration-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Pre-Migration Checklist

### On the New MacBook Pro, install:
- [ ] Docker Desktop for Mac (latest version)
- [ ] Python 3.13 or higher
- [ ] Node.js 18+ and npm
- [ ] Git
- [ ] Command Line Tools: `xcode-select --install`
- [ ] Homebrew (optional but recommended)

### Verify installations:
```bash
docker --version
python3 --version
node --version
npm --version
git --version
```

## What to Migrate

### 1. Project Files
**Location**: `/Users/cosburn/BoarderframeOS/`

The entire BoarderframeOS directory contains:
- Source code for all agents and core systems
- Configuration files
- Scripts and utilities
- UI components
- Documentation

### 2. Docker Volumes
**Volumes to backup**:
- `boarderframeos_postgres_data` - PostgreSQL database
- `boarderframeos_redis_data` - Redis cache data
- `boarderframeos_pgadmin_data` - pgAdmin configuration

### 3. Local Databases
**Location**: `/Users/cosburn/BoarderframeOS/data/`
- `boarderframe.db` - SQLite message bus database
- `agent_cortex_config.db` - Agent Cortex configuration
- `analytics.db` - Analytics data
- `vectors.db` - Vector embeddings
- Other .db files

### 4. Configuration Files
- **Environment Variables**: `.env` (contains API keys - handle securely!)
- **System Config**: `boarderframe.yaml`
- **Docker Config**: `docker-compose.yml`
- **PostgreSQL Config**: `postgres-config/`

### 5. Dependencies
- Python packages: `requirements.txt`
- Node packages: `ui/modern/package.json`, `tools/claude/package.json`

## Backup Process

### Step 1: Stop All Services
```bash
cd /Users/cosburn/BoarderframeOS
# Stop all running services
docker-compose down
# Kill any remaining Python processes
./scripts/utils/kill_all_processes.py
```

### Step 2: Backup Docker Volumes
```bash
# Create backup directory
mkdir -p ~/boarderframeos-backup/docker-volumes

# Backup PostgreSQL data
docker run --rm -v boarderframeos_postgres_data:/source -v ~/boarderframeos-backup/docker-volumes:/backup alpine tar czf /backup/postgres_data.tar.gz -C /source .

# Backup Redis data
docker run --rm -v boarderframeos_redis_data:/source -v ~/boarderframeos-backup/docker-volumes:/backup alpine tar czf /backup/redis_data.tar.gz -C /source .

# Backup pgAdmin data
docker run --rm -v boarderframeos_pgadmin_data:/source -v ~/boarderframeos-backup/docker-volumes:/backup alpine tar czf /backup/pgadmin_data.tar.gz -C /source .
```

### Step 3: Backup Project Files
```bash
# Create project backup (excluding large/temporary files)
cd /Users/cosburn
tar --exclude='BoarderframeOS/node_modules' \
    --exclude='BoarderframeOS/.mypy_cache' \
    --exclude='BoarderframeOS/__pycache__' \
    --exclude='BoarderframeOS/venv' \
    --exclude='BoarderframeOS/env' \
    --exclude='BoarderframeOS/logs/*.log' \
    --exclude='BoarderframeOS/temp' \
    -czf ~/boarderframeos-backup/boarderframeos-project.tar.gz BoarderframeOS/
```

### Step 4: Secure .env File
```bash
# Copy .env file separately (contains API keys!)
cp /Users/cosburn/BoarderframeOS/.env ~/boarderframeos-backup/env-backup
# Also backup example for reference
cp /Users/cosburn/BoarderframeOS/.env.example ~/boarderframeos-backup/
```

## Migration Steps

### On the Old MacBook:
1. Complete all backup steps above
2. Copy the `~/boarderframeos-backup` folder to the new MacBook via:
   - AirDrop
   - External drive
   - Network transfer
   - Cloud storage (encrypt sensitive files first!)

### On the New MacBook:

#### Step 1: Restore Project Files
```bash
# Extract project files
cd /Users/[your-username]
tar -xzf ~/boarderframeos-backup/boarderframeos-project.tar.gz

# Navigate to project
cd BoarderframeOS
```

#### Step 2: Restore Environment File
```bash
# Restore .env file (contains API keys!)
cp ~/boarderframeos-backup/env-backup .env
chmod 600 .env  # Secure the file
```

#### Step 3: Create Python Virtual Environment
```bash
# Create fresh virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Install Node Dependencies
```bash
# Install Node packages for modern UI
cd ui/modern
npm install
cd ../..

# Install Node packages for Claude tools
cd tools/claude
npm install
cd ../..
```

#### Step 5: Restore Docker Volumes
```bash
# Create volumes first
docker volume create boarderframeos_postgres_data
docker volume create boarderframeos_redis_data
docker volume create boarderframeos_pgadmin_data

# Restore PostgreSQL data
docker run --rm -v boarderframeos_postgres_data:/target -v ~/boarderframeos-backup/docker-volumes:/backup alpine tar xzf /backup/postgres_data.tar.gz -C /target

# Restore Redis data
docker run --rm -v boarderframeos_redis_data:/target -v ~/boarderframeos-backup/docker-volumes:/backup alpine tar xzf /backup/redis_data.tar.gz -C /target

# Restore pgAdmin data
docker run --rm -v boarderframeos_pgadmin_data:/target -v ~/boarderframeos-backup/docker-volumes:/backup alpine tar xzf /backup/pgadmin_data.tar.gz -C /target
```

## Post-Migration Setup

### Step 1: Start Docker Services
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgresql redis

# Verify services are running
docker ps
```

### Step 2: Run Database Migrations (if needed)
```bash
# Check if any new migrations need to be applied
python migrations/migrate_sqlite_to_postgres.py
```

### Step 3: Start the System
```bash
# Use the enhanced startup script
python startup.py
```

This will:
- Start all Docker services
- Initialize the database
- Launch MCP servers
- Start Agent Orchestrator
- Launch Corporate Headquarters UI
- Start Agent Cortex

### Step 4: Access Web Interfaces
- Corporate Headquarters: http://localhost:8888
- Agent Cortex: http://localhost:8889
- Agent Communication Center: http://localhost:8890
- pgAdmin (if needed): http://localhost:8080

## Verification

### System Health Check
```bash
# Run comprehensive system status check
python system_status.py

# Check individual components
python check_startup_health.py
```

### Verify Key Components:
1. **Docker Services**: All containers should be running
   ```bash
   docker ps
   ```

2. **MCP Servers**: Should show as online in Corporate HQ
   - Registry Server (8009)
   - Filesystem Server (8001)
   - Database Server (8010)
   - Analytics Server (8007)
   - Others...

3. **Agent Status**: Check in Corporate HQ Metrics tab
   - Solomon (Chief of Staff)
   - David (CEO)
   - Adam, Eve, Bezalel (Primordials)

4. **Database Connectivity**:
   ```bash
   python test_db_connection.py
   ```

## Troubleshooting

### Common Issues:

1. **Port Conflicts**
   - PostgreSQL uses port 5434 (not default 5432)
   - Check for conflicts: `lsof -i :5434`

2. **Missing Dependencies**
   ```bash
   # Reinstall Python packages
   pip install -r requirements.txt

   # For MCP servers
   pip install -r mcp/requirements.txt
   ```

3. **Docker Volume Permissions**
   ```bash
   # Fix PostgreSQL permissions if needed
   docker-compose down
   docker volume rm boarderframeos_postgres_data
   # Then restore volume again
   ```

4. **API Key Issues**
   - Verify `.env` file contains valid ANTHROPIC_API_KEY
   - Check file permissions: `ls -la .env`

5. **MCP Server Failures**
   - Check individual server logs in `logs/`
   - Restart specific server: `python mcp/[server_name].py`

### Emergency Recovery
If the system won't start:
```bash
# Clean start (preserves data)
docker-compose down
./scripts/utils/kill_all_processes.py
python startup.py

# Full reset (last resort - loses Docker data!)
docker-compose down -v
python startup.py
```

## Security Notes

1. **API Keys**: The `.env` file contains sensitive API keys. Never commit this to Git or share publicly.

2. **Database Passwords**: Default passwords are in docker-compose.yml. Change these in production.

3. **File Permissions**: Ensure proper permissions on sensitive files:
   ```bash
   chmod 600 .env
   chmod 600 configs/agents/*.json
   ```

## Additional Resources

- **Documentation**: See `CLAUDE.md` for system overview
- **Quick Start**: `docs/QUICK_START.md`
- **Development Guide**: `docs/DEVELOPMENT.md`
- **Troubleshooting**: `docs/summaries/` for specific component guides

## Migration Checklist Summary

- [ ] Install required software on new MacBook
- [ ] Stop all services on old MacBook
- [ ] Backup Docker volumes
- [ ] Backup project files
- [ ] Secure .env file
- [ ] Transfer backup to new MacBook
- [ ] Restore project files
- [ ] Restore .env file
- [ ] Setup Python virtual environment
- [ ] Install Python dependencies
- [ ] Install Node dependencies
- [ ] Restore Docker volumes
- [ ] Start Docker services
- [ ] Run startup.py
- [ ] Verify system health
- [ ] Test web interfaces

Once all steps are complete, your BoarderframeOS should be fully operational on the new MacBook Pro!
