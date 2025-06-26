#!/usr/bin/env python3
"""
Post-migration verification script
Verifies that the BoarderframeOS system is working correctly after migration
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


class PostMigrationVerifier:
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add_result(self, test_name, status, details=""):
        """Add a test result"""
        self.test_results.append(
            {
                "test": test_name,
                "status": status,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if status == "passed":
            self.passed += 1
            print(f"  {GREEN}✓{RESET} {test_name}")
        elif status == "failed":
            self.failed += 1
            print(f"  {RED}✗{RESET} {test_name}")
        else:  # warning
            self.warnings += 1
            print(f"  {YELLOW}⚠{RESET} {test_name}")

        if details:
            print(f"    {details}")

    def verify_file_structure(self):
        """Verify core file structure is intact"""
        print(f"\n{BLUE}Verifying File Structure...{RESET}")

        critical_paths = [
            "startup.py",
            "corporate_headquarters.py",
            "core/base_agent.py",
            "core/message_bus.py",
            "agents/solomon/solomon.py",
            "mcp/server_launcher.py",
            "data/",
            "logs/",
            "configs/",
        ]

        for path in critical_paths:
            if os.path.exists(path):
                self.add_result(f"Path: {path}", "passed")
            else:
                self.add_result(f"Path: {path}", "failed", "File/directory not found")

    def verify_python_imports(self):
        """Verify Python imports work correctly"""
        print(f"\n{BLUE}Verifying Python Imports...{RESET}")

        test_imports = [
            ("core.base_agent", "BaseAgent"),
            ("core.message_bus", "MessageBus"),
            ("core.agent_orchestrator", "AgentOrchestrator"),
            ("core.llm_client", "LLMClient"),
            ("anthropic", "Anthropic"),
        ]

        for module_name, class_name in test_imports:
            try:
                module = __import__(module_name, fromlist=[class_name])
                if hasattr(module, class_name):
                    self.add_result(f"Import: {module_name}.{class_name}", "passed")
                else:
                    self.add_result(
                        f"Import: {module_name}.{class_name}",
                        "failed",
                        f"Class {class_name} not found in module",
                    )
            except ImportError as e:
                self.add_result(
                    f"Import: {module_name}.{class_name}",
                    "failed",
                    f"Import error: {str(e)}",
                )

    def verify_database_connections(self):
        """Verify database connections"""
        print(f"\n{BLUE}Verifying Database Connections...{RESET}")

        # Check PostgreSQL
        try:
            result = subprocess.run(
                [
                    "psql",
                    "-U",
                    "boarderframe",
                    "-h",
                    "localhost",
                    "-p",
                    "5434",
                    "-d",
                    "boarderframeos",
                    "-c",
                    "SELECT COUNT(*) FROM agents;",
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "PGPASSWORD": "boarderframe"},
            )

            if result.returncode == 0:
                # Parse count from output
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip().isdigit():
                        count = int(line.strip())
                        self.add_result(
                            "PostgreSQL connection",
                            "passed",
                            f"Connected successfully - {count} agents in database",
                        )
                        break
            else:
                self.add_result(
                    "PostgreSQL connection", "failed", "Could not connect to PostgreSQL"
                )
        except Exception as e:
            self.add_result(
                "PostgreSQL connection", "failed", f"PostgreSQL test failed: {str(e)}"
            )

        # Check SQLite databases
        sqlite_dbs = ["data/boarderframe.db", "data/analytics.db"]
        for db_path in sqlite_dbs:
            if os.path.exists(db_path):
                try:
                    import sqlite3

                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
                    )
                    result = cursor.fetchone()
                    conn.close()

                    if result:
                        self.add_result(
                            f"SQLite: {db_path}", "passed", "Database accessible"
                        )
                    else:
                        self.add_result(
                            f"SQLite: {db_path}", "warning", "Database empty"
                        )
                except Exception as e:
                    self.add_result(f"SQLite: {db_path}", "failed", f"Error: {str(e)}")
            else:
                self.add_result(
                    f"SQLite: {db_path}", "warning", "Database file not found"
                )

    async def verify_service_endpoints(self):
        """Verify service endpoints are responding"""
        print(f"\n{BLUE}Verifying Service Endpoints...{RESET}")

        endpoints = [
            ("http://localhost:8888/", "Corporate HQ"),
            ("http://localhost:8889/", "Agent Cortex"),
            ("http://localhost:8890/", "Agent Communication Center"),
            ("http://localhost:8000/health", "Registry Server"),
            ("http://localhost:8001/health", "Filesystem Server"),
            ("http://localhost:8010/health", "Database Server"),
            ("http://localhost:8007/health", "Analytics Server"),
            ("http://localhost:8009/health", "Registry Server"),
            ("http://localhost:8006/health", "Payment Server"),
            ("http://localhost:8011/health", "Screenshot Server"),
        ]

        async with aiohttp.ClientSession() as session:
            for url, service_name in endpoints:
                try:
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            self.add_result(
                                f"Service: {service_name}",
                                "passed",
                                f"Responding at {url}",
                            )
                        else:
                            self.add_result(
                                f"Service: {service_name}",
                                "warning",
                                f"Status code: {response.status}",
                            )
                except asyncio.TimeoutError:
                    self.add_result(
                        f"Service: {service_name}",
                        "warning",
                        "Service not responding (timeout)",
                    )
                except Exception as e:
                    self.add_result(
                        f"Service: {service_name}",
                        "warning",
                        f"Service not available: {str(e)}",
                    )

    def verify_docker_containers(self):
        """Verify Docker containers are running"""
        print(f"\n{BLUE}Verifying Docker Containers...{RESET}")

        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\\t{{.Status}}"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                containers = result.stdout.strip().split("\n")
                boarderframe_containers = [
                    c for c in containers if "boarderframe" in c.lower()
                ]

                if boarderframe_containers:
                    for container in boarderframe_containers:
                        parts = container.split("\t")
                        if len(parts) >= 2:
                            name, status = parts[0], parts[1]
                            if "Up" in status:
                                self.add_result(f"Container: {name}", "passed", status)
                            else:
                                self.add_result(f"Container: {name}", "warning", status)
                else:
                    self.add_result(
                        "Docker containers",
                        "warning",
                        "No BoarderframeOS containers found",
                    )
            else:
                self.add_result("Docker", "failed", "Docker command failed")
        except Exception as e:
            self.add_result("Docker", "failed", f"Docker check failed: {str(e)}")

    def verify_agent_functionality(self):
        """Verify basic agent functionality"""
        print(f"\n{BLUE}Verifying Agent Functionality...{RESET}")

        # Test message bus
        try:
            from core.message_bus import MessageBus

            bus = MessageBus()
            self.add_result("Message Bus", "passed", "Initialized successfully")
        except Exception as e:
            self.add_result("Message Bus", "failed", f"Initialization failed: {str(e)}")

        # Test agent import
        try:
            from agents.solomon import solomon

            self.add_result("Solomon Agent", "passed", "Module imported successfully")
        except Exception as e:
            self.add_result("Solomon Agent", "failed", f"Import failed: {str(e)}")

    def verify_configuration_files(self):
        """Verify configuration files"""
        print(f"\n{BLUE}Verifying Configuration Files...{RESET}")

        config_files = [
            (".env", "Environment variables"),
            (".claude/settings.json", "Claude settings"),
            (".mcp.json", "MCP configuration"),
            ("boarderframe.yaml", "System configuration"),
            ("docker-compose.yml", "Docker configuration"),
        ]

        for file_path, description in config_files:
            if os.path.exists(file_path):
                try:
                    # Try to validate JSON files
                    if file_path.endswith(".json"):
                        with open(file_path, "r") as f:
                            json.load(f)
                        self.add_result(
                            f"Config: {description}", "passed", "Valid JSON"
                        )
                    else:
                        self.add_result(
                            f"Config: {description}", "passed", "File exists"
                        )
                except json.JSONDecodeError:
                    self.add_result(
                        f"Config: {description}", "failed", "Invalid JSON format"
                    )
                except Exception as e:
                    self.add_result(
                        f"Config: {description}",
                        "failed",
                        f"Error reading file: {str(e)}",
                    )
            else:
                severity = "warning" if file_path == ".env" else "failed"
                self.add_result(f"Config: {description}", severity, "File not found")

    def test_startup_script(self):
        """Test if startup script works"""
        print(f"\n{BLUE}Testing Startup Script...{RESET}")

        # Just check if startup.py has valid syntax
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", "startup.py"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.add_result("Startup script", "passed", "Valid Python syntax")
            else:
                self.add_result(
                    "Startup script", "failed", f"Syntax error: {result.stderr}"
                )
        except Exception as e:
            self.add_result("Startup script", "failed", f"Test failed: {str(e)}")

    def generate_report(self):
        """Generate verification report"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{BOLD}Post-Migration Verification Report{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        print(f"\n{GREEN}Passed: {self.passed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")

        # Show failed tests
        if self.failed > 0:
            print(f"\n{RED}Failed Tests:{RESET}")
            for result in self.test_results:
                if result["status"] == "failed":
                    print(f"  ✗ {result['test']}")
                    if result["details"]:
                        print(f"    {result['details']}")

        # Show warnings
        if self.warnings > 0:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for result in self.test_results:
                if result["status"] == "warning":
                    print(f"  ⚠ {result['test']}")
                    if result["details"]:
                        print(f"    {result['details']}")

        # Overall status
        if self.failed == 0:
            if self.warnings == 0:
                print(f"\n{GREEN}✅ All tests passed - migration successful!{RESET}")
            else:
                print(f"\n{YELLOW}⚠️  Migration completed with warnings{RESET}")
            return True
        else:
            print(f"\n{RED}❌ Some tests failed - please investigate{RESET}")
            return False

    def save_report(self):
        """Save verification report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.test_results),
                "passed": self.passed,
                "warnings": self.warnings,
                "failed": self.failed,
            },
            "test_results": self.test_results,
        }

        report_path = "post_migration_report.json"
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n{BLUE}Report saved to: {report_path}{RESET}")

    def provide_next_steps(self):
        """Provide next steps based on verification results"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{BOLD}Next Steps{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        if self.failed == 0:
            print(f"\n{GREEN}Your BoarderframeOS migration appears successful!{RESET}")
            print("\nRecommended next steps:")
            print("1. Run 'python startup.py' to start all services")
            print("2. Access Corporate HQ at http://localhost:8888")
            print("3. Verify your agents are functioning properly")
            print("4. Check logs in the logs/ directory for any issues")
        else:
            print(f"\n{YELLOW}Some issues were detected during verification.{RESET}")
            print("\nRecommended actions:")
            print("1. Review the failed tests above")
            print("2. Check Docker containers: 'docker ps'")
            print("3. Verify PostgreSQL is running on port 5434")
            print(
                "4. Ensure all Python dependencies are installed: 'pip install -r requirements.txt'"
            )
            print("5. Review migration logs for any errors")

        print(
            f"\n{CYAN}For additional help, consult BOARDERFRAMEOS_MIGRATION_GUIDE.md{RESET}"
        )


async def main():
    """Run post-migration verification"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}BoarderframeOS Post-Migration Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    # Check if we're in the correct directory
    if not os.path.exists("startup.py"):
        print(
            f"{RED}Error: This script must be run from the BoarderframeOS root directory{RESET}"
        )
        sys.exit(1)

    verifier = PostMigrationVerifier()

    # Run all verification tests
    verifier.verify_file_structure()
    verifier.verify_python_imports()
    verifier.verify_configuration_files()
    verifier.verify_database_connections()
    verifier.verify_docker_containers()
    verifier.test_startup_script()
    verifier.verify_agent_functionality()

    # Run async tests
    await verifier.verify_service_endpoints()

    # Generate report
    success = verifier.generate_report()
    verifier.save_report()
    verifier.provide_next_steps()

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
