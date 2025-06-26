#!/usr/bin/env python3
"""
Pre-Migration Verification Script for BoarderframeOS
Ensures source installation is complete before migration
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class PreMigrationChecker:
    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.issues = []
        self.warnings = []
        self.successes = []
        self.critical_missing = []
        
    def log_success(self, message: str):
        self.successes.append(f"✓ {message}")
        print(f"✓ {message}")
        
    def log_warning(self, message: str):
        self.warnings.append(f"⚠ {message}")
        print(f"⚠ {message}")
        
    def log_error(self, message: str):
        self.issues.append(f"✗ {message}")
        print(f"✗ {message}")
        
    def check_core_files(self) -> bool:
        """Check for critical system files"""
        print("\n=== Checking Core System Files ===")
        
        core_files = {
            "startup.py": "Main system startup script",
            "CLAUDE.md": "Claude Code integration documentation",
            "corporate_headquarters.py": "Corporate HQ UI server",
            "system_status.py": "System health monitoring",
            "boarderframe.yaml": "Main configuration file",
            "docker-compose.yml": "Docker services configuration",
            "requirements.txt": "Python dependencies",
            "Makefile": "Build and development commands",
        }
        
        all_present = True
        for file_name, description in core_files.items():
            file_path = self.source_dir / file_name
            if file_path.exists():
                self.log_success(f"Found {file_name} - {description}")
            else:
                self.log_error(f"Missing {file_name} - {description}")
                self.critical_missing.append(file_name)
                all_present = False
                
        return all_present
        
    def check_agent_framework(self) -> bool:
        """Check agent framework components"""
        print("\n=== Checking Agent Framework ===")
        
        framework_files = [
            "core/base_agent.py",
            "core/message_bus.py",
            "core/agent_orchestrator.py",
            "core/llm_client.py",
            "core/cost_management.py",
            "core/hq_metrics_layer.py",
            "core/hq_metrics_integration.py",
            "core/agent_registry.py",
        ]
        
        all_present = True
        for file_path in framework_files:
            full_path = self.source_dir / file_path
            if full_path.exists():
                self.log_success(f"Found {file_path}")
            else:
                self.log_error(f"Missing {file_path}")
                all_present = False
                
        return all_present
        
    def check_agents(self) -> Dict[str, bool]:
        """Check for agent implementations"""
        print("\n=== Checking Agent Implementations ===")
        
        agents = {
            "Solomon": "agents/solomon/solomon.py",
            "David": "agents/david/david.py",
            "Adam": "agents/primordials/adam.py",
            "Eve": "agents/primordials/eve.py",
            "Bezalel": "agents/primordials/bezalel.py",
        }
        
        agent_status = {}
        for agent_name, file_path in agents.items():
            full_path = self.source_dir / file_path
            if full_path.exists():
                self.log_success(f"Found {agent_name} agent at {file_path}")
                agent_status[agent_name] = True
            else:
                self.log_warning(f"Missing {agent_name} agent at {file_path}")
                agent_status[agent_name] = False
                
        return agent_status
        
    def check_mcp_servers(self) -> Dict[str, bool]:
        """Check for MCP server implementations"""
        print("\n=== Checking MCP Servers ===")
        
        mcp_servers = {
            "Registry Server": ("mcp/registry_server.py", 8009),
            "Filesystem Server": ("mcp/filesystem_server.py", 8001),
            "SQLite Database Server": ("mcp/database_server.py", 8004),
            "PostgreSQL Database Server": ("mcp/database_server_postgres.py", 8010),
            "Payment Server": ("mcp/payment_server.py", 8006),
            "Analytics Server": ("mcp/analytics_server.py", 8007),
            "Customer Server": ("mcp/customer_server.py", 8008),
            "Screenshot Server": ("mcp/screenshot_server.py", 8011),
            "LLM Server": ("mcp_stdio/llm_server_stdio.py", 8005),
        }
        
        server_status = {}
        for server_name, (file_path, port) in mcp_servers.items():
            full_path = self.source_dir / file_path
            if full_path.exists():
                self.log_success(f"Found {server_name} at {file_path} (port {port})")
                server_status[server_name] = True
            else:
                self.log_warning(f"Missing {server_name} at {file_path}")
                server_status[server_name] = False
                
        return server_status
        
    def check_database_files(self) -> Dict[str, int]:
        """Check for database files and their sizes"""
        print("\n=== Checking Database Files ===")
        
        db_files = [
            "data/boarderframe.db",
            "data/agent_cortex_config.db",
            "data/agent_cortex_panel.db",
            "data/analytics.db",
            "data/embeddings.db",
            "data/message_bus.db",
            "data/vectors.db",
            "vectors.db",  # Sometimes in root
            "analytics.db",  # Sometimes in root
        ]
        
        db_info = {}
        total_size = 0
        
        for db_path in db_files:
            full_path = self.source_dir / db_path
            if full_path.exists():
                size = full_path.stat().st_size
                size_mb = size / (1024 * 1024)
                self.log_success(f"Found {db_path} ({size_mb:.2f} MB)")
                db_info[db_path] = size
                total_size += size
            else:
                self.log_warning(f"Database not found: {db_path}")
                
        if total_size > 0:
            total_mb = total_size / (1024 * 1024)
            print(f"\nTotal database size: {total_mb:.2f} MB")
            
        return db_info
        
    def check_dependencies(self) -> bool:
        """Check Python and Node.js dependencies"""
        print("\n=== Checking Dependencies ===")
        
        # Check Python dependencies
        req_file = self.source_dir / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                lines = f.readlines()
            dep_count = sum(1 for line in lines if line.strip() and not line.startswith('#'))
            self.log_success(f"Found requirements.txt with {dep_count} dependencies")
        else:
            self.log_error("Missing requirements.txt")
            
        # Check MCP requirements
        mcp_req = self.source_dir / "mcp/requirements.txt"
        if mcp_req.exists():
            self.log_success("Found MCP requirements.txt")
        else:
            self.log_warning("Missing MCP requirements.txt")
            
        # Check UI package.json
        ui_package = self.source_dir / "ui/modern/package.json"
        if ui_package.exists():
            self.log_success("Found UI package.json")
        else:
            self.log_warning("Missing UI package.json")
            
        return req_file.exists()
        
    def check_environment_files(self) -> Dict[str, bool]:
        """Check for environment configuration files"""
        print("\n=== Checking Environment Configuration ===")
        
        env_status = {}
        
        # Check for .env files
        env_file = self.source_dir / ".env"
        env_example = self.source_dir / ".env.example"
        
        if env_file.exists():
            self.log_success("Found .env file")
            env_status['.env'] = True
            
            # Check for critical variables
            with open(env_file, 'r') as f:
                content = f.read()
                if 'ANTHROPIC_API_KEY' in content:
                    if 'YOUR_KEY_HERE' not in content and 'sk-...' not in content:
                        self.log_success("ANTHROPIC_API_KEY appears to be configured")
                    else:
                        self.log_warning("ANTHROPIC_API_KEY needs to be configured")
                else:
                    self.log_warning("ANTHROPIC_API_KEY not found in .env")
        else:
            self.log_warning("No .env file found")
            env_status['.env'] = False
            
        if env_example.exists():
            self.log_success("Found .env.example file")
            env_status['.env.example'] = True
        else:
            self.log_warning("No .env.example file found")
            env_status['.env.example'] = False
            
        return env_status
        
    def check_docker_setup(self) -> bool:
        """Check Docker configuration and availability"""
        print("\n=== Checking Docker Setup ===")
        
        # Check docker-compose.yml
        docker_compose = self.source_dir / "docker-compose.yml"
        if docker_compose.exists():
            self.log_success("Found docker-compose.yml")
        else:
            self.log_error("Missing docker-compose.yml")
            return False
            
        # Check if Docker is installed
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_success(f"Docker installed: {result.stdout.strip()}")
            else:
                self.log_warning("Docker command failed")
        except FileNotFoundError:
            self.log_warning("Docker not found in PATH")
            
        # Check PostgreSQL config
        pg_conf = self.source_dir / "postgres-config/postgresql.conf"
        if pg_conf.exists():
            self.log_success("Found PostgreSQL configuration")
        else:
            self.log_warning("Missing PostgreSQL configuration")
            
        return docker_compose.exists()
        
    def check_ui_components(self) -> bool:
        """Check UI components"""
        print("\n=== Checking UI Components ===")
        
        ui_files = [
            "ui/agent_cortex_panel.py",
            "ui/templates/agent_cortex_panel.html",
            "ui/templates/dashboard.html",
            "ui/modern/package.json",
            "ui/modern/vite.config.ts",
        ]
        
        all_present = True
        for file_path in ui_files:
            full_path = self.source_dir / file_path
            if full_path.exists():
                self.log_success(f"Found {file_path}")
            else:
                self.log_warning(f"Missing {file_path}")
                all_present = False
                
        return all_present
        
    def check_scripts_organization(self) -> Dict[str, int]:
        """Check scripts directory organization"""
        print("\n=== Checking Scripts Organization ===")
        
        script_dirs = [
            "scripts/database",
            "scripts/enhance",
            "scripts/integrate",
            "scripts/launch",
            "scripts/publish",
            "scripts/run",
            "scripts/updates",
            "scripts/utils",
            "scripts/verify",
        ]
        
        script_counts = {}
        for dir_path in script_dirs:
            full_path = self.source_dir / dir_path
            if full_path.exists() and full_path.is_dir():
                py_files = list(full_path.glob("*.py"))
                sh_files = list(full_path.glob("*.sh"))
                total = len(py_files) + len(sh_files)
                self.log_success(f"Found {dir_path} with {total} scripts")
                script_counts[dir_path] = total
            else:
                self.log_warning(f"Missing directory: {dir_path}")
                script_counts[dir_path] = 0
                
        return script_counts
        
    def generate_report(self) -> str:
        """Generate a comprehensive pre-migration report"""
        report = f"""
# BoarderframeOS Pre-Migration Verification Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source Directory: {self.source_dir}

## Summary

- ✓ Successes: {len(self.successes)}
- ⚠ Warnings: {len(self.warnings)}
- ✗ Issues: {len(self.issues)}
- Critical Missing Files: {len(self.critical_missing)}

## Readiness Assessment

"""
        
        if len(self.critical_missing) > 0:
            report += "### ❌ NOT READY FOR MIGRATION\n\n"
            report += "Critical files are missing:\n"
            for file in self.critical_missing:
                report += f"- {file}\n"
            report += "\nPlease ensure these files exist before attempting migration.\n"
        elif len(self.issues) > 5:
            report += "### ⚠️  MIGRATION POSSIBLE WITH RISKS\n\n"
            report += f"Found {len(self.issues)} issues that should be addressed.\n"
            report += "Migration can proceed but some components may not work.\n"
        else:
            report += "### ✅ READY FOR MIGRATION\n\n"
            report += "Source installation appears complete.\n"
            report += f"Found {len(self.warnings)} minor warnings.\n"
            
        report += """
## Detailed Results

### Successes
"""
        for success in self.successes[:20]:  # Show first 20
            report += f"- {success}\n"
        if len(self.successes) > 20:
            report += f"... and {len(self.successes) - 20} more\n"
            
        if self.warnings:
            report += "\n### Warnings\n"
            for warning in self.warnings:
                report += f"- {warning}\n"
                
        if self.issues:
            report += "\n### Issues\n"
            for issue in self.issues:
                report += f"- {issue}\n"
                
        report += """
## Recommendations

1. Address any critical missing files before migration
2. Review warnings to understand what might need manual setup
3. Ensure all database files are backed up before migration
4. Have API keys ready for the new environment
5. Verify Docker is installed on the target system

## Next Steps

If ready for migration:
```bash
python enhanced_migrate_config.py {source_dir} /path/to/target
```
"""
        
        return report
        
    def run_all_checks(self):
        """Run all verification checks"""
        print("=" * 60)
        print("BoarderframeOS Pre-Migration Verification")
        print("=" * 60)
        
        # Run all checks
        self.check_core_files()
        self.check_agent_framework()
        self.check_agents()
        self.check_mcp_servers()
        self.check_database_files()
        self.check_dependencies()
        self.check_environment_files()
        self.check_docker_setup()
        self.check_ui_components()
        self.check_scripts_organization()
        
        # Generate and save report
        report = self.generate_report()
        report_path = self.source_dir / f"pre_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, 'w') as f:
            f.write(report)
            
        print("\n" + "=" * 60)
        print(f"Report saved to: {report_path}")
        print("=" * 60)
        
        # Print summary
        print(report.split("## Detailed Results")[0])
        
        # Return whether migration should proceed
        return len(self.critical_missing) == 0


def main():
    if len(sys.argv) != 2:
        print("Usage: python pre_migration_check.py /path/to/boarderframeos")
        sys.exit(1)
        
    source_dir = sys.argv[1]
    
    if not Path(source_dir).exists():
        print(f"Error: Directory does not exist: {source_dir}")
        sys.exit(1)
        
    checker = PreMigrationChecker(source_dir)
    ready = checker.run_all_checks()
    
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()