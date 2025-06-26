# BoarderframeOS Complete Migration Checklist

This checklist ensures a successful migration of BoarderframeOS to a new environment. Follow each step carefully and check off completed items.

## Pre-Migration Phase

### 1. Verify Source Installation
- [ ] Run pre-migration check: `python pre_migration_check.py /path/to/current/boarderframeos`
- [ ] Review the generated pre-migration report
- [ ] Ensure all critical files are present
- [ ] Note any warnings about optional components
- [ ] Backup current installation (if needed)

### 2. Prepare Target Environment
- [ ] Ensure Python 3.13+ is installed
- [ ] Install Docker Desktop (for PostgreSQL and Redis)
- [ ] Install Node.js 18+ (for UI components)
- [ ] Create target directory for migration
- [ ] Ensure sufficient disk space (at least 2GB free)

### 3. Document Current Configuration
- [ ] Note current API keys from .env file
- [ ] Document any custom port configurations
- [ ] List any custom agents or modifications
- [ ] Save database connection strings
- [ ] Export any important data from databases

## Migration Phase

### 4. Run Migration Script
- [ ] Dry run first: `python enhanced_migrate_config.py /source/path /target/path --dry-run`
- [ ] Review what will be migrated
- [ ] Run actual migration: `python enhanced_migrate_config.py /source/path /target/path`
- [ ] Check migration log for any errors
- [ ] Verify all files were copied successfully

### 5. Migrate Database Files
- [ ] Use generated script: `cd /target/path && ./migrate_databases.sh /source/path`
- [ ] Or manually copy all .db files from source/data/ to target/data/
- [ ] Verify database file sizes match source
- [ ] Check permissions on database files

### 6. Handle Sensitive Files
- [ ] Review .env.secret file
- [ ] Create .env from .env.secret
- [ ] Add actual API keys:
  - [ ] ANTHROPIC_API_KEY
  - [ ] OPENAI_API_KEY (if used)
  - [ ] STRIPE_API_KEY (if used)
  - [ ] Any other service keys
- [ ] Set database passwords if changed
- [ ] Configure ports if defaults conflict

## Post-Migration Phase

### 7. Run Automated Setup
- [ ] Navigate to target directory: `cd /target/path`
- [ ] Run setup script: `python post_migration_setup.py`
- [ ] Or run with auto mode: `python post_migration_setup.py --auto`
- [ ] Follow prompts for each setup phase:
  - [ ] Python virtual environment creation
  - [ ] Python dependencies installation
  - [ ] Node.js dependencies (if npm available)
  - [ ] Docker services startup
  - [ ] Database schema setup
  - [ ] Environment configuration

### 8. Manual Configuration Steps

#### Python Environment
- [ ] Activate virtual environment:
  ```bash
  # Unix/Linux/macOS:
  source venv/bin/activate
  
  # Windows:
  venv\Scripts\activate
  ```
- [ ] Verify Python version: `python --version` (should be 3.13+)
- [ ] Install any missing dependencies: `pip install -r requirements.txt`

#### Docker Services
- [ ] Start Docker Desktop
- [ ] Start services: `docker-compose up -d postgresql redis`
- [ ] Verify containers: `docker ps`
- [ ] Check PostgreSQL: `docker exec boarderframeos_postgres psql -U boarderframe -d boarderframeos -c "SELECT version();"`
- [ ] Check Redis: `docker exec boarderframeos_redis redis-cli ping`

#### Database Migrations
- [ ] Run SQL migrations in order:
  ```bash
  cd migrations
  for sql in *.sql; do
    docker exec -i boarderframeos_postgres psql -U boarderframe -d boarderframeos < $sql
  done
  ```
- [ ] Run Python migrations:
  ```bash
  python migrate_departments.py
  python populate_divisions_departments.py
  ```

#### Node.js Setup (Optional but Recommended)
- [ ] Modern UI setup:
  ```bash
  cd ui/modern
  npm install
  npm run build
  cd ../..
  ```
- [ ] Claude tools setup:
  ```bash
  cd tools/claude
  npm install
  cd ../..
  ```

### 9. Verification Phase
- [ ] Run verification script: `python migration_verification_enhanced.py .`
- [ ] Review verification report
- [ ] Address any missing files
- [ ] Fix any invalid configurations
- [ ] Resolve all critical issues

### 10. System Testing

#### Basic Tests
- [ ] Test system status: `python system_status.py`
- [ ] Test imports:
  ```python
  python -c "from core.message_bus import message_bus; print('✓ Message bus')"
  python -c "from core.base_agent import BaseAgent; print('✓ Base agent')"
  python -c "import anthropic; print('✓ Anthropic client')"
  ```

#### Start System
- [ ] Start BoarderframeOS: `python startup.py`
- [ ] Monitor startup logs
- [ ] Wait for all services to initialize
- [ ] Check for any startup errors

#### Access Web Interfaces
- [ ] Corporate HQ: http://localhost:8888
  - [ ] Verify dashboard loads
  - [ ] Check metrics display
  - [ ] Test agent registry
- [ ] Agent Cortex: http://localhost:8889
  - [ ] Verify UI loads
  - [ ] Test agent interactions
- [ ] Agent Communication Center: http://localhost:8890
  - [ ] Verify chat interface
  - [ ] Test agent communication

#### Test MCP Servers
- [ ] Check health endpoints:
  ```bash
  curl http://localhost:8009/health  # Registry
  curl http://localhost:8001/health  # Filesystem
  curl http://localhost:8010/health  # PostgreSQL
  curl http://localhost:8007/health  # Analytics
  curl http://localhost:8006/health  # Payment
  curl http://localhost:8008/health  # Customer
  curl http://localhost:8011/health  # Screenshot
  ```

### 11. Final Validation
- [ ] Test agent interactions through Corporate HQ
- [ ] Verify message bus is functioning
- [ ] Check database connectivity
- [ ] Ensure cost management is active
- [ ] Verify metrics are being collected
- [ ] Test a simple agent task

## Troubleshooting Checklist

### Common Issues
- [ ] **Port conflicts**: Change ports in .env and docker-compose.yml
- [ ] **Import errors**: Ensure virtual environment is activated
- [ ] **Docker errors**: Ensure Docker Desktop is running
- [ ] **Database connection**: Check POSTGRES_PORT matches docker-compose.yml
- [ ] **Missing modules**: Run `pip install -r requirements.txt` again
- [ ] **API errors**: Verify ANTHROPIC_API_KEY is set correctly

### Log Locations
- [ ] Check startup logs: `logs/startup.log`
- [ ] Check MCP server logs: `logs/mcp_servers.log`
- [ ] Check agent logs: `logs/agents/*.log`
- [ ] Check Docker logs: `docker logs boarderframeos_postgres`

### Recovery Steps
- [ ] If startup fails, check all logs
- [ ] If database errors, verify migrations ran successfully
- [ ] If API errors, double-check .env configuration
- [ ] If UI doesn't load, check port availability
- [ ] If agents don't respond, verify message bus is running

## Migration Complete!

Once all items are checked:
1. Your BoarderframeOS installation is ready for use
2. Save this checklist for future reference
3. Review CLAUDE.md for system documentation
4. Start building with your AI-Native Operating System!

## Quick Reference Commands

```bash
# Start system
./start.sh  # or start.bat on Windows

# Stop system
docker-compose down
pkill -f "python.*startup.py"

# View logs
tail -f logs/startup.log

# System status
python system_status.py

# Database access
docker exec -it boarderframeos_postgres psql -U boarderframe -d boarderframeos
```

## Support Resources

- CLAUDE.md - Complete system documentation
- docs/QUICK_START.md - Quick start guide
- docs/INFRASTRUCTURE.md - Infrastructure details
- Corporate HQ (http://localhost:8888) - System dashboard
- Migration reports in target directory

Remember: BoarderframeOS is a complex AI-Native Operating System. Take time to verify each component is properly configured for optimal performance.