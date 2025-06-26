#!/usr/bin/env python3
"""
BoarderframeOS Configuration Migration Tool
Safely migrates all configuration files to a new environment
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


class ConfigMigrator:
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

    def log(self, message: str, level: str = "INFO"):
        """Log messages to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)

        if not self.dry_run and self.target_dir.exists():
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")

    def get_config_files(self) -> Dict[str, List[str]]:
        """Define all configuration files to migrate"""
        return {
            "environment": [".env", ".env.example", "scripts/.env"],
            "primary_config": [
                "boarderframe.yaml",
                "tools/ctl/boarderframe.yaml",
                "configs/boarderframe.yaml",
                "docker-compose.yml",
                "docker-compose.adminer.yml",
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
                "tools/claude/package.json",
                "tools/claude/package-lock.json",
            ],
            "build_tools": ["Makefile", ".pre-commit-config.yaml", ".gitignore"],
            "database_config": [
                "postgres-config/postgresql.conf",
                "postgres-config/pg_hba.conf",
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
            "cicd_config": [
                ".github/workflows/ci.yml",
                ".github/workflows/release.yml",
                ".github/dependabot.yml",
            ],
            "agent_config": [
                "configs/agents/david.json",
                "configs/agents/solomon.json",
                "configs/enhanced_coordination_config.py",
                "configs/__init__.py",
            ],
            "data_files": ["data/system_status.json"],
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
            ".env",
        ]

        # Check filename
        for pattern in sensitive_patterns:
            if pattern.lower() in str(file_path).lower():
                return True

        # Check content for text files
        if file_path.suffix in [".env", ".yaml", ".yml", ".json", ".conf"]:
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
        """Create necessary directories in target location"""
        directories = [
            "configs/agents",
            "migrations",
            "postgres-config",
            ".github/workflows",
            "ui/modern",
            "tools/claude",
            "tools/ctl",
            "mcp",
            "scripts",
            "data",
        ]

        for dir_path in directories:
            target_path = self.target_dir / dir_path
            if not self.dry_run:
                target_path.mkdir(parents=True, exist_ok=True)
            self.log(f"Created directory: {dir_path}")

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
        """Create sanitized .env template"""
        with open(source_path, "r") as f:
            lines = f.readlines()

        # Save original with .secret extension
        secret_path = target_path.with_suffix(".env.secret")
        with open(secret_path, "w") as f:
            f.writelines(lines)

        # Create sanitized template
        sanitized_lines = []
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                if any(
                    sensitive in key.upper()
                    for sensitive in ["KEY", "SECRET", "TOKEN", "PASSWORD"]
                ):
                    sanitized_lines.append(f"{key}=YOUR_{key.strip()}_HERE\n")
                else:
                    sanitized_lines.append(line)
            else:
                sanitized_lines.append(line)

        with open(target_path, "w") as f:
            f.writelines(sanitized_lines)

    def migrate_all(self):
        """Perform the complete migration"""
        self.log(f"Starting migration from {self.source_dir} to {self.target_dir}")
        self.log(f"Dry run: {self.dry_run}")

        # Create directory structure
        if not self.dry_run:
            self.target_dir.mkdir(parents=True, exist_ok=True)
        self.create_directory_structure()

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

    def generate_summary(self, total: int, migrated: int):
        """Generate migration summary"""
        self.log("\n" + "=" * 60)
        self.log("MIGRATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Total files to migrate: {total}")
        self.log(f"Successfully migrated: {migrated}")
        self.log(f"Skipped (not found): {len(self.skipped_files)}")
        self.log(f"Errors: {len(self.errors)}")
        self.log(f"Sensitive files: {len(self.sensitive_files)}")

        if self.sensitive_files:
            self.log("\nSENSITIVE FILES (require manual review):")
            for f in self.sensitive_files:
                self.log(f"  - {f}")

        if self.errors:
            self.log("\nERRORS:")
            for file_path, error in self.errors:
                self.log(f"  - {file_path}: {error}")

    def create_migration_guide(self):
        """Create a guide for completing the migration"""
        guide_path = self.target_dir / "MIGRATION_GUIDE.md"

        guide_content = f"""# BoarderframeOS Migration Guide

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Migration Summary

- **Total files migrated**: {len(self.migrated_files)}
- **Sensitive files**: {len(self.sensitive_files)}
- **Files not found**: {len(self.skipped_files)}
- **Errors**: {len(self.errors)}

## Post-Migration Steps

### 1. Environment Variables
- Review and update `.env` files with your actual API keys
- Check `.env.secret` files for original values (delete after updating)

### 2. Database Configuration
- Update PostgreSQL connection settings in `docker-compose.yml`
- Adjust port mappings if needed (default: 5434)
- Update Redis connection if needed (default: 6379)

### 3. Path Updates
Update any absolute paths in:
- `boarderframe.yaml`
- `docker-compose.yml`
- Agent configuration files

### 4. Docker Setup
```bash
# Start infrastructure
docker-compose up -d postgresql redis

# Verify containers
docker ps
```

### 5. Database Migration
```bash
# Run migrations
python migrations/migrate_departments.py
python migrations/populate_divisions_departments.py
```

### 6. Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\\Scripts\\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r mcp/requirements.txt
```

### 7. Node.js Setup
```bash
# UI setup
cd ui/modern
npm install

# Claude tools setup
cd tools/claude
npm install
```

### 8. Verify Installation
```bash
# Start the system
python startup.py

# Check system status
python system_status.py
```

## Sensitive Files Requiring Manual Review

{chr(10).join(f"- {f}" for f in self.sensitive_files)}

## Additional Notes

- MCP servers run on ports 8000-8011
- Corporate HQ runs on port 8888
- Agent Cortex runs on port 8889
- Agent Communication Center runs on port 8890

For more information, see CLAUDE.md in the project root.
"""

        with open(guide_path, "w") as f:
            f.write(guide_content)

        self.log(f"\nMigration guide created: {guide_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate BoarderframeOS configuration files"
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
    if not (source_path / "startup.py").exists():
        print(
            f"Error: Source directory does not appear to be a BoarderframeOS installation"
        )
        print(f"(startup.py not found)")
        sys.exit(1)

    # Run migration
    migrator = ConfigMigrator(args.source, args.target, args.dry_run)
    migrator.migrate_all()


if __name__ == "__main__":
    main()
