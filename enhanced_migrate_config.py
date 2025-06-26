#!/usr/bin/env python3
"""
Enhanced BoarderframeOS Configuration Migration Tool
Comprehensive migration including all components from CLAUDE.md
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


class EnhancedConfigMigrator:
    def __init__(self, source_dir: str, target_dir: str, dry_run: bool = False):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.log_file = (
            self.target_dir
            / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        self.sensitive_files = []
        self.migrated_files = []
        self.skipped_files = []
        self.errors = []
        self.database_files = []

    def log(self, message: str, level: str = "INFO"):
        """Log messages to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)

        if not self.dry_run and self.target_dir.exists():
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")

    def get_config_files(self) -> Dict[str, List[str]]:
        """Define all configuration files to migrate - enhanced from CLAUDE.md"""
        return {
            "environment": [
                ".env", 
                ".env.example", 
                "scripts/.env"
            ],
            "primary_config": [
                "boarderframe.yaml",
                "tools/ctl/boarderframe.yaml",
                "configs/boarderframe.yaml",
                "docker-compose.yml",
                "docker-compose.adminer.yml",
                "CLAUDE.md",  # Critical for Claude Code integration
            ],
            "python_config": [
                "requirements.txt",
                "mcp/requirements.txt",
                "mcp/requirements-optional.txt",
                "pyproject.toml",
                "setup.py",
            ],
            "nodejs_config": [
                "ui/modern/package.json",
                "ui/modern/tailwind.config.js",
                "ui/modern/vite.config.ts",
                "ui/modern/tsconfig.json",  # TypeScript config
                "tools/claude/package.json",
                "tools/claude/package-lock.json",
            ],
            "build_tools": [
                "Makefile", 
                ".pre-commit-config.yaml", 
                ".gitignore",
                ".github/workflows/ci.yml",
                ".github/workflows/release.yml",
                ".github/dependabot.yml",
            ],
            "database_config": [
                "postgres-config/postgresql.conf",
                "postgres-config/pg_hba.conf",
                "redis-config/redis.conf",
            ],
            "migrations": [
                "migrations/001_initial_schema.sql",
                "migrations/002_registry_schema.sql",
                "migrations/003_departments_schema.sql",
                "migrations/004_departments_extension.sql",
                "migrations/005_divisions_departments_restructure.sql",
                "migrations/006_enhanced_registry_tables.sql",
                "migrations/007_add_visual_metadata.sql",
                "migrations/007_llm_cost_tracking.sql",
                "migrations/migrate_departments.py",
                "migrations/migrate_sqlite_to_postgres.py",
                "migrations/populate_divisions_departments.py",
            ],
            "agent_config": [
                "configs/agents/david.json",
                "configs/agents/solomon.json",
                "configs/enhanced_coordination_config.py",
                "configs/__init__.py",
                "departments/boarderframeos-departments.json",
            ],
            "core_system": [
                "startup.py",
                "corporate_headquarters.py",
                "system_status.py",
                "agent_communication_center_enhanced.py",
            ],
            "agent_framework": [
                "core/base_agent.py",
                "core/message_bus.py",
                "core/agent_orchestrator.py",
                "core/llm_client.py",
                "core/cost_management.py",
                "core/hq_metrics_layer.py",
                "core/hq_metrics_integration.py",
                "core/claude_integration.py",
                "core/agent_registry.py",
                "core/__init__.py",
            ],
            "agents": [
                "agents/solomon/solomon.py",
                "agents/david/david.py",
                "agents/primordials/adam.py",
                "agents/primordials/eve.py",
                "agents/primordials/bezalel.py",
                "agents/__init__.py",
            ],
            "mcp_servers": [
                "mcp/registry_server.py",
                "mcp/filesystem_server.py",
                "mcp/database_server.py",
                "mcp/database_server_postgres.py",
                "mcp/payment_server.py",
                "mcp/analytics_server.py",
                "mcp/customer_server.py",
                "mcp/department_server.py",
                "mcp/screenshot_server.py",
                "mcp/server_launcher.py",
                "mcp/llm_server_stdio.py",
                "mcp/__init__.py",
            ],
            "ui_components": [
                "ui/agent_cortex_panel.py",
                "ui/agent_cortex_simple_launcher.py",
                "ui/templates/agent_cortex_panel.html",
                "ui/templates/dashboard.html",
                "ui/templates/agents.html",
                "ui/templates/solomon.html",
                "ui/__init__.py",
            ],
            "scripts": [
                # Database scripts
                "scripts/database/audit_and_fix_agent_status.py",
                "scripts/database/cleanup_duplicate_agents.py",
                "scripts/database/register_all_components.py",
                "scripts/database/populate_visual_metadata.py",
                # Launch scripts
                "scripts/launch/launch_corporate_headquarters.py",
                "scripts/launch/launch_agent_cortex_ui.py",
                # Verification scripts
                "scripts/verify/verify_system_health.py",
                "scripts/verify/verify_complete_integration.py",
                # Utility scripts
                "scripts/utils/cleanup_processes.py",
                "scripts/run/run_tests.sh",
                # Main scripts
                "scripts/start",
                "scripts/start.sh",
                "scripts/status",
                "scripts/db",
                "scripts/db-query",
                "scripts/README.md",
            ],
            "data_files": [
                "data/system_status.json"
            ],
            "test_files": [
                "tests/conftest.py",
                "tests/test_base_agent.py",
                "tests/__init__.py",
                "test_infrastructure.py",
                "test_cost_optimization.py",
                "test_db_connection.py",
            ],
            "tools": [
                "tools/claude/package.json",
                "tools/claude/index.js",
                "tools/claude/README.md",
                "tools/claude/CLAUDE.md",
                "tools/ctl/boarderctl",
                "tools/ctl/claude",
            ],
        }

    def check_sensitive_content(self, file_path: Path) -> bool:
        """Check if file contains sensitive information"""
        sensitive_patterns = [
            "API_KEY",
            "SECRET",
            "PASSWORD",
            "TOKEN",
            "PRIVATE",
            "CREDENTIAL",
            "DATABASE_URL",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "STRIPE_API_KEY",
        ]

        # Check filename
        for pattern in sensitive_patterns:
            if pattern.lower() in str(file_path).lower():
                return True

        # Always mark .env files as sensitive
        if file_path.name.startswith('.env'):
            return True

        # Check content for text files
        if file_path.suffix in [".env", ".yaml", ".yml", ".json", ".conf", ".py"]:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                    for pattern in sensitive_patterns:
                        if pattern in content.upper():
                            return True
            except:
                pass

        return False

    def create_directory_structure(self):
        """Create necessary directories in target location - enhanced"""
        directories = [
            # Core directories
            "configs/agents",
            "core",
            "migrations",
            "postgres-config",
            "redis-config",
            ".github/workflows",
            # UI directories
            "ui/modern",
            "ui/templates",
            # Tools
            "tools/claude",
            "tools/ctl",
            # MCP
            "mcp",
            "mcp_stdio",
            # Scripts organization
            "scripts/database",
            "scripts/enhance",
            "scripts/integrate",
            "scripts/launch",
            "scripts/publish",
            "scripts/run",
            "scripts/updates",
            "scripts/utils",
            "scripts/verify",
            # Data
            "data",
            # Agents
            "agents/solomon",
            "agents/david",
            "agents/primordials",
            # Departments
            "departments",
            # Logs
            "logs/agents",
            "logs/enhanced_agents",
            # Tests
            "tests",
            # Utils
            "utils",
            # Temp directories
            "temp",
            "screenshots",
        ]

        for dir_path in directories:
            target_path = self.target_dir / dir_path
            if not self.dry_run:
                target_path.mkdir(parents=True, exist_ok=True)
            self.log(f"Created directory: {dir_path}")

    def identify_database_files(self):
        """Identify database files that need manual migration"""
        db_patterns = [
            "data/*.db",
            "data/*.sqlite",
            "vectors.db",
            "analytics.db",
        ]
        
        for pattern in db_patterns:
            for db_file in self.source_dir.glob(pattern):
                if db_file.is_file():
                    rel_path = db_file.relative_to(self.source_dir)
                    self.database_files.append(str(rel_path))
                    self.log(f"Found database file: {rel_path}", "WARNING")

    def migrate_file(self, rel_path: str) -> bool:
        """Migrate a single file"""
        source_path = self.source_dir / rel_path
        target_path = self.target_dir / rel_path

        if not source_path.exists():
            self.log(f"Source file not found: {rel_path}", "WARNING")
            self.skipped_files.append(rel_path)
            return False

        # Check if sensitive
        is_sensitive = self.check_sensitive_content(source_path)
        if is_sensitive:
            self.sensitive_files.append(rel_path)
            self.log(f"Sensitive file detected: {rel_path}", "WARNING")

        try:
            # Create parent directory
            if not self.dry_run:
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if rel_path.endswith(".env"):
                    # Special handling for .env files - create template
                    self.create_env_template(source_path, target_path)
                else:
                    shutil.copy2(source_path, target_path)

            self.migrated_files.append(rel_path)
            self.log(f"Migrated: {rel_path}")
            return True

        except Exception as e:
            self.errors.append((rel_path, str(e)))
            self.log(f"Error migrating {rel_path}: {e}", "ERROR")
            return False

    def create_env_template(self, source_path: Path, target_path: Path):
        """Create sanitized .env template with BoarderframeOS-specific variables"""
        with open(source_path, "r") as f:
            lines = f.readlines()

        # Save original with .secret extension
        secret_path = target_path.with_suffix(".env.secret")
        with open(secret_path, "w") as f:
            f.writelines(lines)

        # Create sanitized template
        sanitized_lines = []
        
        # Add header
        sanitized_lines.append("# BoarderframeOS Environment Configuration\n")
        sanitized_lines.append("# Generated by migration tool - Replace placeholders with actual values\n\n")
        
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                key = key.strip()
                
                # Special handling for known BoarderframeOS variables
                if key == "ANTHROPIC_API_KEY":
                    sanitized_lines.append(f"{key}=sk-ant-api11-YOUR_KEY_HERE\n")
                elif key == "POSTGRES_PASSWORD":
                    sanitized_lines.append(f"{key}=boarderframe_secure_2025\n")
                elif key == "POSTGRES_PORT":
                    sanitized_lines.append(f"{key}=5434\n")
                elif key == "REDIS_PORT":
                    sanitized_lines.append(f"{key}=6379\n")
                elif any(
                    sensitive in key.upper()
                    for sensitive in ["KEY", "SECRET", "TOKEN", "PASSWORD"]
                ):
                    sanitized_lines.append(f"{key}=YOUR_{key.strip()}_HERE\n")
                else:
                    sanitized_lines.append(line)
            else:
                sanitized_lines.append(line)

        # Add any missing required variables
        required_vars = {
            "ANTHROPIC_API_KEY": "sk-ant-api11-YOUR_KEY_HERE",
            "POSTGRES_PASSWORD": "boarderframe_secure_2025",
            "POSTGRES_PORT": "5434",
            "REDIS_PORT": "6379",
            "PYTHONPATH": ".",
        }
        
        existing_keys = {line.split("=")[0].strip() for line in lines if "=" in line and not line.startswith("#")}
        
        for key, default_value in required_vars.items():
            if key not in existing_keys:
                sanitized_lines.append(f"\n# Added by migration tool\n")
                sanitized_lines.append(f"{key}={default_value}\n")

        with open(target_path, "w") as f:
            f.writelines(sanitized_lines)

    def migrate_all(self):
        """Perform the complete migration"""
        self.log(f"Starting enhanced migration from {self.source_dir} to {self.target_dir}")
        self.log(f"Dry run: {self.dry_run}")

        # Create directory structure
        if not self.dry_run:
            self.target_dir.mkdir(parents=True, exist_ok=True)
        self.create_directory_structure()

        # Identify database files
        self.identify_database_files()

        # Migrate all configuration files
        config_files = self.get_config_files()
        total_files = sum(len(files) for files in config_files.values())
        migrated_count = 0

        for category, files in config_files.items():
            self.log(f"\nMigrating {category} files...")
            for file_path in files:
                if self.migrate_file(file_path):
                    migrated_count += 1

        # Generate summary
        self.generate_summary(total_files, migrated_count)

        # Create migration guide
        if not self.dry_run:
            self.create_migration_guide()
            self.create_database_migration_script()

    def create_database_migration_script(self):
        """Create a script to help with database migration"""
        script_path = self.target_dir / "migrate_databases.sh"
        
        script_content = """#!/bin/bash
# BoarderframeOS Database Migration Script
# Generated by enhanced migration tool

echo "BoarderframeOS Database Migration"
echo "================================="

SOURCE_DIR="${1:-PLEASE_SPECIFY_SOURCE_DIR}"
TARGET_DIR="$(pwd)"

if [ "$SOURCE_DIR" = "PLEASE_SPECIFY_SOURCE_DIR" ]; then
    echo "Usage: ./migrate_databases.sh /path/to/source/boarderframeos"
    exit 1
fi

echo "Migrating databases from: $SOURCE_DIR"
echo "To: $TARGET_DIR"
echo ""

# Create data directory if it doesn't exist
mkdir -p "$TARGET_DIR/data"

# Database files to migrate
DATABASES=(
"""
        
        # Add each database file
        for db_file in self.database_files:
            script_content += f'    "{db_file}"\n'
            
        script_content += """)

# Copy each database file
for DB in "${DATABASES[@]}"; do
    if [ -f "$SOURCE_DIR/$DB" ]; then
        echo "Copying $DB..."
        cp -v "$SOURCE_DIR/$DB" "$TARGET_DIR/$DB"
    else
        echo "Warning: $DB not found in source directory"
    fi
done

echo ""
echo "Database migration complete!"
echo "Remember to update any database connection strings if paths have changed."
"""
        
        if not self.dry_run:
            with open(script_path, "w") as f:
                f.write(script_content)
            script_path.chmod(0o755)
            self.log(f"Created database migration script: {script_path}")

    def generate_summary(self, total: int, migrated: int):
        """Generate migration summary"""
        self.log("\n" + "=" * 60)
        self.log("ENHANCED MIGRATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Total files to migrate: {total}")
        self.log(f"Successfully migrated: {migrated}")
        self.log(f"Skipped (not found): {len(self.skipped_files)}")
        self.log(f"Errors: {len(self.errors)}")
        self.log(f"Sensitive files: {len(self.sensitive_files)}")
        self.log(f"Database files found: {len(self.database_files)}")

        if self.database_files:
            self.log("\nDATABASE FILES (require manual migration):")
            for f in self.database_files:
                self.log(f"  - {f}")

        if self.sensitive_files:
            self.log("\nSENSITIVE FILES (require manual review):")
            for f in self.sensitive_files[:10]:  # Show first 10
                self.log(f"  - {f}")
            if len(self.sensitive_files) > 10:
                self.log(f"  ... and {len(self.sensitive_files) - 10} more")

        if self.errors:
            self.log("\nERRORS:")
            for file_path, error in self.errors[:10]:  # Show first 10
                self.log(f"  - {file_path}: {error}")
            if len(self.errors) > 10:
                self.log(f"  ... and {len(self.errors) - 10} more")

    def create_migration_guide(self):
        """Create a comprehensive guide for completing the migration"""
        guide_path = self.target_dir / "BOARDERFRAMEOS_MIGRATION_GUIDE.md"

        guide_content = f"""# BoarderframeOS Enhanced Migration Guide

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Migration Summary

- **Total files migrated**: {len(self.migrated_files)}
- **Sensitive files**: {len(self.sensitive_files)}
- **Database files**: {len(self.database_files)}
- **Files not found**: {len(self.skipped_files)}
- **Errors**: {len(self.errors)}

## Critical Post-Migration Steps

### 1. Environment Variables
```bash
# Review and update .env file
cp .env.secret .env  # Start with the original
# Edit .env and replace:
# - ANTHROPIC_API_KEY with your actual key
# - Any other API keys and secrets
# - Database passwords if changed
```

### 2. Database Migration
```bash
# Use the generated script
chmod +x migrate_databases.sh
./migrate_databases.sh /path/to/source/boarderframeos

# Or manually copy database files:
cp -r /source/data/*.db ./data/
```

### 3. Docker Infrastructure Setup
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgresql redis

# Verify containers are running
docker ps

# Check PostgreSQL connection
docker exec boarderframeos_postgres psql -U boarderframe -d boarderframeos -c "SELECT version();"
```

### 4. Database Schema Setup
```bash
# Run all migrations in order
cd migrations
python migrate_departments.py
python populate_divisions_departments.py

# Or use psql directly:
docker exec -i boarderframeos_postgres psql -U boarderframe -d boarderframeos < 001_initial_schema.sql
# ... repeat for all SQL files
```

### 5. Python Environment Setup
```bash
# Create virtual environment (Python 3.13+)
python3.13 -m venv venv
source venv/bin/activate  # or venv\\Scripts\\activate on Windows

# Install all dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r mcp/requirements.txt

# Install development dependencies
make dev-install
```

### 6. Node.js Setup (for UI)
```bash
# Modern UI setup
cd ui/modern
npm install
npm run build

# Claude tools setup
cd ../../tools/claude
npm install
```

### 7. MCP Server Verification
```bash
# Test each MCP server individually
python mcp/registry_server.py --test
python mcp/filesystem_server.py --test
# ... test all 9 servers
```

### 8. System Startup
```bash
# Return to root directory
cd /path/to/new/boarderframeos

# Start the complete system
python startup.py

# In another terminal, verify system status
python system_status.py
```

### 9. Access Points
After successful startup, access:
- Corporate HQ: http://localhost:8888
- Agent Cortex: http://localhost:8889
- Agent Communication Center: http://localhost:8890

### 10. Health Checks
```bash
# Run comprehensive health check
python scripts/verify/verify_system_health.py

# Check MCP server health
curl http://localhost:8000/health  # Registry
curl http://localhost:8001/health  # Filesystem
# ... check all servers
```

## Port Configuration

Default ports (can be changed in .env):
- PostgreSQL: 5434
- Redis: 6379
- MCP Servers: 8000-8011
- Corporate HQ: 8888
- Agent Cortex: 8889
- Agent Communication Center: 8890

## Troubleshooting

### Common Issues:

1. **Port conflicts**: Change ports in .env and docker-compose.yml
2. **Python version**: Ensure Python 3.13+ is used
3. **Docker permissions**: May need sudo on Linux
4. **Database connections**: Check POSTGRES_PORT in .env matches docker-compose.yml
5. **MCP server failures**: Check individual server logs in logs/

### Debug Commands:
```bash
# Check all Python processes
ps aux | grep python

# Check port usage
lsof -i :5434  # PostgreSQL
lsof -i :8888  # Corporate HQ

# View logs
tail -f logs/startup.log
tail -f logs/mcp_servers.log
```

## Sensitive Files Requiring Manual Review

{chr(10).join(f"- {f}" for f in self.sensitive_files[:20])}

## Database Files (Manual Migration Required)

{chr(10).join(f"- {f}" for f in self.database_files)}

## Next Steps

1. Complete all environment variable configurations
2. Migrate database files using the provided script
3. Run the system and verify all components are working
4. Review CLAUDE.md for detailed system documentation

For additional help, see:
- CLAUDE.md - Complete system documentation
- docs/QUICK_START.md - Quick start guide
- docs/INFRASTRUCTURE.md - Infrastructure details

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review log files in the logs/ directory
3. Verify all dependencies are installed
4. Ensure all ports are available

Remember: BoarderframeOS is an AI-Native Operating System with complex dependencies.
Take time to verify each component is properly configured.
"""

        with open(guide_path, "w") as f:
            f.write(guide_content)

        self.log(f"\nEnhanced migration guide created: {guide_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced BoarderframeOS configuration migration tool"
    )
    parser.add_argument(
        "source", help="Source directory (current BoarderframeOS installation)"
    )
    parser.add_argument("target", help="Target directory for migration")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without copying files",
    )

    args = parser.parse_args()

    # Validate source directory
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source directory does not exist: {args.source}")
        sys.exit(1)

    # Check if it's a valid BoarderframeOS installation
    required_files = ["startup.py", "CLAUDE.md", "corporate_headquarters.py"]
    missing_files = []
    for req_file in required_files:
        if not (source_path / req_file).exists():
            missing_files.append(req_file)
    
    if missing_files:
        print(f"Error: Source directory does not appear to be a complete BoarderframeOS installation")
        print(f"Missing required files: {', '.join(missing_files)}")
        sys.exit(1)

    # Run migration
    migrator = EnhancedConfigMigrator(args.source, args.target, args.dry_run)
    migrator.migrate_all()


if __name__ == "__main__":
    main()