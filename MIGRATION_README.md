# BoarderframeOS Configuration Migration

This directory contains tools to help migrate BoarderframeOS configuration files to a new environment.

## Quick Start

### 1. Migration Script

```bash
# Dry run to see what will be migrated
python migrate_config.py /path/to/current/boarderframeos /path/to/new/location --dry-run

# Perform actual migration
python migrate_config.py /path/to/current/boarderframeos /path/to/new/location
```

### 2. Verify Migration

```bash
# Verify the new installation
python verify_migration.py /path/to/new/location
```

## What Gets Migrated

The migration script handles:

1. **Environment Files** (.env, .env.example)
2. **Configuration Files** (boarderframe.yaml, docker-compose.yml)
3. **Python Dependencies** (requirements.txt, setup.py, pyproject.toml)
4. **Node.js Configuration** (package.json files)
5. **Build Tools** (Makefile, .gitignore, .pre-commit-config.yaml)
6. **Database Configuration** (PostgreSQL configs, migration scripts)
7. **CI/CD Files** (GitHub Actions workflows)
8. **Agent Configurations** (JSON files in configs/agents/)
9. **System Data** (system_status.json)

## Security Note

The migration script:
- Detects sensitive files (containing API keys, secrets, etc.)
- Creates sanitized templates for .env files
- Saves original .env files with `.secret` extension
- Logs all sensitive files requiring manual review

## Post-Migration Steps

After migration, you'll need to:

1. **Update .env files** with actual API keys
2. **Adjust paths** in configuration files if needed
3. **Update database connections** in docker-compose.yml
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   cd ui/modern && npm install
   ```
5. **Run database migrations**
6. **Start the system**: `python startup.py`

## Files Created

- `migration_log_[timestamp].txt` - Detailed migration log
- `MIGRATION_GUIDE.md` - Customized post-migration instructions
- `.env.secret` files - Original environment files (delete after setup)

## Important Notes

- Database files (*.db) are NOT migrated automatically
- You may need to export/import database data separately
- Port configurations may need adjustment in the new environment
- Docker volumes paths may need updating

For more details, see the generated MIGRATION_GUIDE.md after running the migration.
