#!/usr/bin/env python3
"""
Enhanced BoarderframeOS Migration Verification Tool
Comprehensive validation of migrated installation
"""

import os
import json
import yaml
import subprocess
import requests
import time
from pathlib import Path
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class EnhancedMigrationVerifier:
    def __init__(self, installation_dir: str):
        self.installation_dir = Path(installation_dir)
        self.missing_files = []
        self.invalid_files = []
        self.warnings = []
        self.successes = []
        self.server_status = {}
        self.test_results = {}
        
    def check_file_exists(self, rel_path: str, required: bool = True) -> bool:
        """Check if a file exists"""
        file_path = self.installation_dir / rel_path
        exists = file_path.exists()
        
        if exists:
            self.successes.append(f"✓ Found: {rel_path}")
        elif required:
            self.missing_files.append(f"✗ Missing: {rel_path}")
        else:
            self.warnings.append(f"⚠ Optional file missing: {rel_path}")
            
        return exists
    
    def check_json_valid(self, rel_path: str) -> bool:
        """Check if JSON file is valid"""
        file_path = self.installation_dir / rel_path
        if not file_path.exists():
            return False
            
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            return True
        except Exception as e:
            self.invalid_files.append(f"✗ Invalid JSON in {rel_path}: {e}")
            return False
    
    def check_yaml_valid(self, rel_path: str) -> bool:
        """Check if YAML file is valid"""
        file_path = self.installation_dir / rel_path
        if not file_path.exists():
            return False
            
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            return True
        except Exception as e:
            self.invalid_files.append(f"✗ Invalid YAML in {rel_path}: {e}")
            return False
            
    def check_core_components(self) -> bool:
        """Check all core BoarderframeOS components"""
        print("\n=== Checking Core Components ===")
        
        # Core system files
        core_files = [
            "startup.py",
            "corporate_headquarters.py",
            "system_status.py",
            "agent_communication_center_enhanced.py",
            "CLAUDE.md",
            "boarderframe.yaml",
            "docker-compose.yml",
            "requirements.txt",
            "Makefile",
        ]
        
        all_present = True
        for file_path in core_files:
            if not self.check_file_exists(file_path):
                all_present = False
                
        return all_present
        
    def check_agent_framework(self) -> Dict[str, bool]:
        """Check agent framework components"""
        print("\n=== Checking Agent Framework ===")
        
        framework_components = {
            "Base Agent": "core/base_agent.py",
            "Message Bus": "core/message_bus.py",
            "Agent Orchestrator": "core/agent_orchestrator.py",
            "LLM Client": "core/llm_client.py",
            "Cost Management": "core/cost_management.py",
            "HQ Metrics Layer": "core/hq_metrics_layer.py",
            "HQ Metrics Integration": "core/hq_metrics_integration.py",
            "Claude Integration": "core/claude_integration.py",
            "Agent Registry": "core/agent_registry.py",
        }
        
        status = {}
        for component, file_path in framework_components.items():
            exists = self.check_file_exists(file_path)
            status[component] = exists
            
        return status
        
    def check_agents(self) -> Dict[str, Dict[str, bool]]:
        """Check agent implementations"""
        print("\n=== Checking Agent Implementations ===")
        
        agents = {
            "Solomon (Chief of Staff)": {
                "main": "agents/solomon/solomon.py",
                "enhanced": "agents/solomon/enhanced_solomon.py",
            },
            "David (CEO)": {
                "main": "agents/david/david.py",
                "enhanced": "agents/david/enhanced_david.py",
            },
            "Adam (Agent Creator)": {
                "main": "agents/primordials/adam.py",
                "enhanced": "agents/primordials/enhanced_adam.py",
            },
            "Eve (Agent Evolver)": {
                "main": "agents/primordials/eve.py",
                "enhanced": "agents/primordials/enhanced_eve.py",
            },
            "Bezalel (Master Programmer)": {
                "main": "agents/primordials/bezalel.py",
                "enhanced": "agents/primordials/enhanced_bezalel.py",
            },
        }
        
        agent_status = {}
        for agent_name, files in agents.items():
            status = {}
            for file_type, file_path in files.items():
                exists = self.check_file_exists(file_path, required=(file_type == "main"))
                status[file_type] = exists
            agent_status[agent_name] = status
            
        return agent_status
        
    def check_mcp_servers(self) -> Dict[str, Dict[str, any]]:
        """Check MCP server components and configurations"""
        print("\n=== Checking MCP Servers ===")
        
        mcp_servers = {
            "PostgreSQL Database Server": {
                "file": "mcp/database_server_postgres.py",
                "port": 8010,
                "priority": "Enterprise",
            },
            "Filesystem Server": {
                "file": "mcp/filesystem_server.py",
                "port": 8001,
                "priority": "Enterprise",
            },
            "Analytics Server": {
                "file": "mcp/analytics_server.py",
                "port": 8007,
                "priority": "Enterprise",
            },
            "Registry Server": {
                "file": "mcp/registry_server.py",
                "port": 8009,
                "priority": "Standard",
            },
            "Payment Server": {
                "file": "mcp/payment_server.py",
                "port": 8006,
                "priority": "Standard",
            },
            "LLM Server": {
                "file": "mcp_stdio/llm_server_stdio.py",
                "port": 8005,
                "priority": "Standard",
            },
            "SQLite Database Server": {
                "file": "mcp/database_server.py",
                "port": 8004,
                "priority": "Advanced",
            },
            "Customer Server": {
                "file": "mcp/customer_server.py",
                "port": 8008,
                "priority": "Standard",
            },
            "Screenshot Server": {
                "file": "mcp/screenshot_server.py",
                "port": 8011,
                "priority": "Advanced",
            },
        }
        
        server_status = {}
        for server_name, config in mcp_servers.items():
            status = {
                "file_exists": self.check_file_exists(config["file"]),
                "port": config["port"],
                "priority": config["priority"],
                "health_check": None
            }
            server_status[server_name] = status
            
        return server_status
        
    def check_ui_components(self) -> Dict[str, bool]:
        """Check UI components"""
        print("\n=== Checking UI Components ===")
        
        ui_components = {
            "Agent Cortex Panel": "ui/agent_cortex_panel.py",
            "Agent Cortex Launcher": "ui/agent_cortex_simple_launcher.py",
            "Agent Cortex Template": "ui/templates/agent_cortex_panel.html",
            "Dashboard Template": "ui/templates/dashboard.html",
            "Agents Template": "ui/templates/agents.html",
            "Solomon Template": "ui/templates/solomon.html",
            "Modern UI Package": "ui/modern/package.json",
            "Modern UI Vite Config": "ui/modern/vite.config.ts",
            "Modern UI Tailwind": "ui/modern/tailwind.config.js",
        }
        
        status = {}
        for component, file_path in ui_components.items():
            exists = self.check_file_exists(file_path)
            status[component] = exists
            
        return status
        
    def check_database_setup(self) -> Dict[str, any]:
        """Check database configuration and files"""
        print("\n=== Checking Database Setup ===")
        
        db_status = {
            "config_files": {},
            "database_files": {},
            "docker_services": {}
        }
        
        # Check configuration files
        config_files = [
            "postgres-config/postgresql.conf",
            "postgres-config/pg_hba.conf",
            "redis-config/redis.conf",
        ]
        
        for config_file in config_files:
            exists = self.check_file_exists(config_file, required=False)
            db_status["config_files"][config_file] = exists
            
        # Check database files
        db_files = [
            "data/boarderframe.db",
            "data/agent_cortex_config.db",
            "data/analytics.db",
            "data/vectors.db",
            "data/system_status.json",
        ]
        
        for db_file in db_files:
            file_path = self.installation_dir / db_file
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                db_status["database_files"][db_file] = {
                    "exists": True,
                    "size_mb": round(size_mb, 2)
                }
                self.successes.append(f"✓ Database: {db_file} ({size_mb:.2f} MB)")
            else:
                db_status["database_files"][db_file] = {
                    "exists": False,
                    "size_mb": 0
                }
                self.warnings.append(f"⚠ Database not found: {db_file}")
                
        return db_status
        
    def check_scripts_organization(self) -> Dict[str, int]:
        """Check scripts directory organization"""
        print("\n=== Checking Scripts Organization ===")
        
        script_categories = {
            "database": "Database management scripts",
            "enhance": "Enhancement scripts",
            "integrate": "Integration scripts",
            "launch": "Launch scripts",
            "publish": "Publishing scripts",
            "run": "Execution scripts",
            "updates": "Update scripts",
            "utils": "Utility scripts",
            "verify": "Verification scripts",
        }
        
        script_counts = {}
        for category, description in script_categories.items():
            dir_path = self.installation_dir / "scripts" / category
            if dir_path.exists() and dir_path.is_dir():
                scripts = list(dir_path.glob("*.py")) + list(dir_path.glob("*.sh"))
                count = len(scripts)
                script_counts[category] = count
                self.successes.append(f"✓ Scripts/{category}: {count} scripts - {description}")
            else:
                script_counts[category] = 0
                self.warnings.append(f"⚠ Missing scripts/{category} - {description}")
                
        return script_counts
        
    def check_environment_config(self) -> Dict[str, any]:
        """Check environment configuration"""
        print("\n=== Checking Environment Configuration ===")
        
        env_status = {
            "env_file": False,
            "env_example": False,
            "env_secret": False,
            "api_keys": {},
            "ports": {}
        }
        
        # Check .env files
        env_file = self.installation_dir / ".env"
        env_example = self.installation_dir / ".env.example"
        env_secret = self.installation_dir / ".env.secret"
        
        env_status["env_file"] = env_file.exists()
        env_status["env_example"] = env_example.exists()
        env_status["env_secret"] = env_secret.exists()
        
        if env_file.exists():
            self.successes.append("✓ Found .env file")
            
            # Parse environment variables
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Check API keys
                        if 'API_KEY' in key:
                            if value and not any(placeholder in value for placeholder in ['YOUR_KEY_HERE', 'sk-...', '']):
                                env_status["api_keys"][key] = "configured"
                                self.successes.append(f"✓ {key} is configured")
                            else:
                                env_status["api_keys"][key] = "not_configured"
                                self.warnings.append(f"⚠ {key} needs configuration")
                                
                        # Check ports
                        if 'PORT' in key:
                            env_status["ports"][key] = value
                            
        else:
            self.warnings.append("⚠ No .env file found")
            
        return env_status
        
    def test_docker_services(self) -> Dict[str, bool]:
        """Test Docker services availability"""
        print("\n=== Testing Docker Services ===")
        
        docker_status = {
            "docker_installed": False,
            "docker_compose_installed": False,
            "postgresql_running": False,
            "redis_running": False
        }
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                docker_status["docker_installed"] = True
                self.successes.append(f"✓ Docker installed: {result.stdout.strip()}")
        except FileNotFoundError:
            self.warnings.append("⚠ Docker not installed")
            
        # Check docker-compose
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                docker_status["docker_compose_installed"] = True
                self.successes.append("✓ docker-compose installed")
        except FileNotFoundError:
            # Try newer syntax
            try:
                result = subprocess.run(['docker', 'compose', 'version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    docker_status["docker_compose_installed"] = True
                    self.successes.append("✓ docker compose installed")
            except:
                self.warnings.append("⚠ docker-compose not installed")
                
        # Check running containers
        if docker_status["docker_installed"]:
            try:
                result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    running_containers = result.stdout
                    if 'boarderframeos_postgres' in running_containers:
                        docker_status["postgresql_running"] = True
                        self.successes.append("✓ PostgreSQL container is running")
                    else:
                        self.warnings.append("⚠ PostgreSQL container not running")
                        
                    if 'boarderframeos_redis' in running_containers:
                        docker_status["redis_running"] = True
                        self.successes.append("✓ Redis container is running")
                    else:
                        self.warnings.append("⚠ Redis container not running")
            except:
                pass
                
        return docker_status
        
    def test_python_environment(self) -> Dict[str, bool]:
        """Test Python environment setup"""
        print("\n=== Testing Python Environment ===")
        
        py_status = {
            "python_version": "",
            "venv_exists": False,
            "requirements_installed": False,
            "key_imports": {}
        }
        
        # Check Python version
        result = subprocess.run([sys.executable, '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            py_status["python_version"] = result.stdout.strip()
            self.successes.append(f"✓ Python version: {py_status['python_version']}")
            
        # Check virtual environment
        venv_path = self.installation_dir / "venv"
        if venv_path.exists():
            py_status["venv_exists"] = True
            self.successes.append("✓ Virtual environment exists")
        else:
            self.warnings.append("⚠ No virtual environment found")
            
        # Test key imports
        test_imports = {
            "anthropic": "Anthropic API client",
            "aiohttp": "Async HTTP client",
            "asyncio": "Async support",
            "redis": "Redis client",
            "psycopg2": "PostgreSQL client",
        }
        
        for module, description in test_imports.items():
            try:
                __import__(module)
                py_status["key_imports"][module] = True
                self.successes.append(f"✓ Can import {module} - {description}")
            except ImportError:
                py_status["key_imports"][module] = False
                self.warnings.append(f"⚠ Cannot import {module} - {description}")
                
        return py_status
        
    def test_server_endpoints(self) -> Dict[str, Dict[str, any]]:
        """Test server endpoints if services are running"""
        print("\n=== Testing Server Endpoints ===")
        
        endpoints = {
            "Corporate HQ": {"url": "http://localhost:8888", "expected_status": 200},
            "Agent Cortex": {"url": "http://localhost:8889", "expected_status": 200},
            "Agent Communication Center": {"url": "http://localhost:8890", "expected_status": 200},
            "Registry Server Health": {"url": "http://localhost:8009/health", "expected_status": 200},
            "Filesystem Server Health": {"url": "http://localhost:8001/health", "expected_status": 200},
            "Database Server Health": {"url": "http://localhost:8010/health", "expected_status": 200},
        }
        
        endpoint_status = {}
        for name, config in endpoints.items():
            try:
                response = requests.get(config["url"], timeout=2)
                status = {
                    "reachable": True,
                    "status_code": response.status_code,
                    "healthy": response.status_code == config["expected_status"]
                }
                if status["healthy"]:
                    self.successes.append(f"✓ {name} is accessible at {config['url']}")
                else:
                    self.warnings.append(f"⚠ {name} returned status {response.status_code}")
            except requests.exceptions.RequestException:
                status = {
                    "reachable": False,
                    "status_code": None,
                    "healthy": False
                }
                # This is expected if services aren't running yet
                
            endpoint_status[name] = status
            
        return endpoint_status
        
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        report = f"""# BoarderframeOS Migration Verification Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Installation Directory: {self.installation_dir}

## Summary

- ✓ Successes: {len(self.successes)}
- ⚠ Warnings: {len(self.warnings)}
- ✗ Missing Files: {len(self.missing_files)}
- ✗ Invalid Files: {len(self.invalid_files)}

## Migration Status

"""
        
        # Determine overall status
        critical_issues = len(self.missing_files) + len(self.invalid_files)
        
        if critical_issues == 0:
            if len(self.warnings) == 0:
                report += "### ✅ MIGRATION SUCCESSFUL - FULLY VERIFIED\n\n"
                report += "All components are present and properly configured.\n"
            else:
                report += "### ✅ MIGRATION SUCCESSFUL - WITH WARNINGS\n\n"
                report += f"Migration completed successfully with {len(self.warnings)} warnings to review.\n"
        else:
            report += "### ❌ MIGRATION INCOMPLETE\n\n"
            report += f"Found {critical_issues} critical issues that need attention.\n"
            
        # Add test results
        report += "\n## Component Status\n\n"
        
        # Format test results
        if hasattr(self, 'component_results'):
            for component, status in self.component_results.items():
                if isinstance(status, dict):
                    report += f"### {component}\n"
                    for key, value in status.items():
                        report += f"- {key}: {value}\n"
                    report += "\n"
                    
        # Add detailed results
        report += "\n## Detailed Results\n\n"
        
        if self.successes:
            report += "### Successes\n"
            for success in self.successes[:50]:  # First 50
                report += f"{success}\n"
            if len(self.successes) > 50:
                report += f"... and {len(self.successes) - 50} more\n"
                
        if self.warnings:
            report += "\n### Warnings\n"
            for warning in self.warnings:
                report += f"{warning}\n"
                
        if self.missing_files:
            report += "\n### Missing Files\n"
            for missing in self.missing_files:
                report += f"{missing}\n"
                
        if self.invalid_files:
            report += "\n### Invalid Files\n"
            for invalid in self.invalid_files:
                report += f"{invalid}\n"
                
        # Add recommendations
        report += """
## Recommendations

1. **Address Missing Files**: Any missing critical files should be migrated manually
2. **Review Warnings**: Check each warning to ensure optional components are intentionally excluded
3. **Configure Environment**: Ensure all API keys are properly set in .env file
4. **Start Services**: Use `docker-compose up -d` to start PostgreSQL and Redis
5. **Run Setup**: Execute `python post_migration_setup.py` for automated configuration

## Next Steps

1. Review this report for any critical issues
2. Address any missing files or invalid configurations
3. Run the post-migration setup script
4. Start the system with `python startup.py`
5. Access Corporate HQ at http://localhost:8888

For detailed documentation, see CLAUDE.md in the project root.
"""
        
        return report
        
    def verify_all(self) -> bool:
        """Run all verification checks"""
        print(f"Verifying BoarderframeOS installation at: {self.installation_dir}\n")
        
        # Store results for report
        self.component_results = {}
        
        # Run all checks
        checks = [
            ("Core Components", self.check_core_components),
            ("Agent Framework", self.check_agent_framework),
            ("Agents", self.check_agents),
            ("MCP Servers", self.check_mcp_servers),
            ("UI Components", self.check_ui_components),
            ("Database Setup", self.check_database_setup),
            ("Scripts Organization", self.check_scripts_organization),
            ("Environment Config", self.check_environment_config),
            ("Docker Services", self.test_docker_services),
            ("Python Environment", self.test_python_environment),
            ("Server Endpoints", self.test_server_endpoints),
        ]
        
        for check_name, check_func in checks:
            print(f"\n{'='*60}")
            result = check_func()
            self.component_results[check_name] = result
            
        # Generate and save report
        report = self.generate_report()
        report_path = self.installation_dir / f"migration_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, "w") as f:
            f.write(report)
            
        # Print summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print(f"✓ Successes: {len(self.successes)}")
        print(f"⚠ Warnings: {len(self.warnings)}")
        print(f"✗ Missing Files: {len(self.missing_files)}")
        print(f"✗ Invalid Files: {len(self.invalid_files)}")
        print(f"\nDetailed report saved to: {report_path}")
        print("="*60)
        
        # Return True if no critical issues
        return len(self.missing_files) == 0 and len(self.invalid_files) == 0


def main():
    if len(sys.argv) != 2:
        print("Usage: python migration_verification_enhanced.py <installation_directory>")
        sys.exit(1)
    
    installation_dir = sys.argv[1]
    
    # Check if directory exists
    if not Path(installation_dir).exists():
        print(f"Error: Directory does not exist: {installation_dir}")
        sys.exit(1)
    
    # Run verification
    verifier = EnhancedMigrationVerifier(installation_dir)
    success = verifier.verify_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()