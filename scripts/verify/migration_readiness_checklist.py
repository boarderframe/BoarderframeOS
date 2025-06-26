#!/usr/bin/env python3
"""
Interactive checklist to verify system readiness for migration
Ensures all prerequisites are met before starting the migration process
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


class MigrationChecklist:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add_check(self, name, result, message="", severity="critical"):
        """Add a check result"""
        self.checks.append(
            {
                "name": name,
                "result": result,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if result == "passed":
            self.passed += 1
        elif result == "failed":
            self.failed += 1
        elif result == "warning":
            self.warnings += 1

    def check_command(self, command, description):
        """Check if a command is available"""
        try:
            result = subprocess.run(["which", command], capture_output=True)
            if result.returncode == 0:
                self.add_check(
                    f"Command: {command}",
                    "passed",
                    f"{command} is available at {result.stdout.decode().strip()}",
                )
                return True
            else:
                self.add_check(
                    f"Command: {command}",
                    "failed",
                    f"{command} not found - {description}",
                )
                return False
        except Exception as e:
            self.add_check(
                f"Command: {command}", "failed", f"Error checking {command}: {str(e)}"
            )
            return False

    def check_docker_status(self):
        """Check Docker daemon status"""
        print(f"\n{BLUE}Checking Docker Status...{RESET}")

        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                self.add_check("Docker daemon", "passed", "Docker is running")

                # Check for BoarderframeOS containers
                result = subprocess.run(
                    ["docker", "ps", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                )
                containers = result.stdout.strip().split("\n") if result.stdout else []
                boarderframe_containers = [
                    c for c in containers if "boarderframe" in c.lower()
                ]

                if boarderframe_containers:
                    self.add_check(
                        "BoarderframeOS containers",
                        "passed",
                        f"Found {len(boarderframe_containers)} running containers: {', '.join(boarderframe_containers)}",
                    )
                else:
                    self.add_check(
                        "BoarderframeOS containers",
                        "warning",
                        "No BoarderframeOS containers are running",
                        severity="warning",
                    )

                return True
            else:
                self.add_check("Docker daemon", "failed", "Docker is not running")
                return False
        except Exception as e:
            self.add_check(
                "Docker daemon", "failed", f"Error checking Docker: {str(e)}"
            )
            return False

    def check_disk_space(self):
        """Check available disk space"""
        print(f"\n{BLUE}Checking Disk Space...{RESET}")

        try:
            result = subprocess.run(["df", "-h", "."], capture_output=True, text=True)
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                # Parse df output
                parts = lines[1].split()
                if len(parts) >= 4:
                    available = parts[3]
                    # Try to parse the available space
                    if "G" in available:
                        gb = float(available.replace("G", ""))
                        if gb > 10:
                            self.add_check(
                                "Disk space",
                                "passed",
                                f"{available} available (recommended: >10GB)",
                            )
                        else:
                            self.add_check(
                                "Disk space",
                                "warning",
                                f"Only {available} available - consider freeing up space",
                                severity="warning",
                            )
                    else:
                        self.add_check(
                            "Disk space",
                            "warning",
                            f"{available} available - please verify sufficient space",
                            severity="warning",
                        )
                    return True
        except Exception as e:
            self.add_check(
                "Disk space", "failed", f"Error checking disk space: {str(e)}"
            )
            return False

    def check_python_environment(self):
        """Check Python environment"""
        print(f"\n{BLUE}Checking Python Environment...{RESET}")

        # Check Python version
        try:
            import sys

            version = sys.version_info
            if version.major == 3 and version.minor >= 11:
                self.add_check(
                    "Python version",
                    "passed",
                    f"Python {version.major}.{version.minor}.{version.micro}",
                )
            else:
                self.add_check(
                    "Python version",
                    "warning",
                    f"Python {version.major}.{version.minor}.{version.micro} - recommended 3.11+",
                    severity="warning",
                )
        except:
            self.add_check(
                "Python version", "failed", "Could not determine Python version"
            )

        # Check virtual environment
        if hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            venv_path = sys.prefix
            self.add_check("Virtual environment", "passed", f"Active at {venv_path}")
        else:
            self.add_check(
                "Virtual environment",
                "warning",
                "Not in a virtual environment - recommended for isolation",
                severity="warning",
            )

        # Check key packages
        key_packages = ["anthropic", "aiohttp", "asyncpg", "redis", "click", "pydantic"]
        try:
            import pkg_resources

            installed = {pkg.key for pkg in pkg_resources.working_set}

            for package in key_packages:
                if package in installed:
                    self.add_check(f"Package: {package}", "passed", "Installed")
                else:
                    self.add_check(
                        f"Package: {package}",
                        "warning",
                        "Not installed - run 'pip install -r requirements.txt'",
                        severity="warning",
                    )
        except:
            self.add_check(
                "Python packages",
                "warning",
                "Could not check installed packages",
                severity="warning",
            )

    def check_services_running(self):
        """Check if critical services are running"""
        print(f"\n{BLUE}Checking Running Services...{RESET}")

        # Check critical ports
        ports_to_check = [
            (5434, "PostgreSQL"),
            (6379, "Redis"),
            (8888, "Corporate HQ"),
            (8889, "Agent Cortex"),
            (8890, "Agent Communication Center"),
            (8000, "Registry Server"),
            (8001, "Filesystem Server"),
            (8010, "Database Server"),
        ]

        for port, service in ports_to_check:
            try:
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True,
                    stderr=subprocess.DEVNULL,
                )
                if result.returncode == 0:
                    self.add_check(f"Port {port}", "passed", f"{service} is running")
                else:
                    severity = "critical" if port in [5434, 6379] else "warning"
                    self.add_check(
                        f"Port {port}",
                        "warning" if severity == "warning" else "failed",
                        f"{service} is not running",
                        severity=severity,
                    )
            except:
                self.add_check(
                    f"Port {port}",
                    "warning",
                    f"Could not check {service}",
                    severity="warning",
                )

    def check_data_integrity(self):
        """Check data integrity"""
        print(f"\n{BLUE}Checking Data Integrity...{RESET}")

        # Check if data directory exists
        if os.path.exists("data"):
            db_files = [f for f in os.listdir("data") if f.endswith(".db")]
            if db_files:
                self.add_check(
                    "SQLite databases",
                    "passed",
                    f"Found {len(db_files)} database files",
                )

                # Check database sizes
                for db_file in db_files:
                    db_path = os.path.join("data", db_file)
                    size_mb = os.path.getsize(db_path) / (1024 * 1024)
                    if size_mb > 0:
                        self.add_check(
                            f"Database: {db_file}", "passed", f"Size: {size_mb:.2f} MB"
                        )
                    else:
                        self.add_check(
                            f"Database: {db_file}",
                            "warning",
                            "Database is empty",
                            severity="warning",
                        )
            else:
                self.add_check(
                    "SQLite databases",
                    "warning",
                    "No database files found",
                    severity="warning",
                )
        else:
            self.add_check("Data directory", "failed", "Data directory not found")

    def check_git_status(self):
        """Check git repository status"""
        print(f"\n{BLUE}Checking Git Status...{RESET}")

        try:
            # Check if it's a git repo
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True
            )
            if result.returncode == 0:
                self.add_check("Git repository", "passed", "Git repository found")

                # Check for uncommitted changes
                result = subprocess.run(
                    ["git", "status", "--porcelain"], capture_output=True, text=True
                )
                if result.stdout:
                    changes = len(result.stdout.strip().split("\n"))
                    self.add_check(
                        "Git status",
                        "warning",
                        f"{changes} uncommitted changes - consider committing",
                        severity="warning",
                    )
                else:
                    self.add_check("Git status", "passed", "No uncommitted changes")

                # Check remote
                result = subprocess.run(
                    ["git", "remote", "-v"], capture_output=True, text=True
                )
                if "origin" in result.stdout:
                    self.add_check("Git remote", "passed", "Remote 'origin' configured")
                else:
                    self.add_check(
                        "Git remote",
                        "warning",
                        "No remote configured",
                        severity="warning",
                    )
            else:
                self.add_check(
                    "Git repository",
                    "warning",
                    "Not a git repository",
                    severity="warning",
                )
        except:
            self.add_check("Git", "warning", "Git not available", severity="warning")

    def interactive_confirmation(self):
        """Interactive confirmation prompts"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Interactive Confirmation{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        confirmations = [
            (
                "Have you reviewed the migration guide?",
                "Review BOARDERFRAMEOS_MIGRATION_GUIDE.md",
            ),
            (
                "Do you have a recent backup of your data?",
                "Create a backup before proceeding",
            ),
            (
                "Is your target machine ready?",
                "Ensure target has required dependencies",
            ),
            (
                "Have you noted any custom configurations?",
                "Document any non-standard settings",
            ),
            ("Are you ready to proceed with migration?", "This is your final check"),
        ]

        all_confirmed = True

        for question, note in confirmations:
            print(f"\n{CYAN}{question}{RESET}")
            print(f"  {YELLOW}Note: {note}{RESET}")

            while True:
                response = input(f"  {BOLD}[Y/n]:{RESET} ").strip().lower()
                if response in ["", "y", "yes"]:
                    print(f"  {GREEN}✓ Confirmed{RESET}")
                    break
                elif response in ["n", "no"]:
                    print(f"  {RED}✗ Not confirmed{RESET}")
                    all_confirmed = False
                    break

        return all_confirmed

    def generate_report(self):
        """Generate final checklist report"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Migration Readiness Report{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        print(f"\n{GREEN}Passed: {self.passed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")

        # Show failed checks
        if self.failed > 0:
            print(f"\n{RED}Failed Checks:{RESET}")
            for check in self.checks:
                if check["result"] == "failed":
                    print(f"  ✗ {check['name']}: {check['message']}")

        # Show warnings
        if self.warnings > 0:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for check in self.checks:
                if check["result"] == "warning":
                    print(f"  ⚠ {check['name']}: {check['message']}")

        # Overall status
        if self.failed == 0:
            if self.warnings == 0:
                print(
                    f"\n{GREEN}✅ All checks passed - system is ready for migration!{RESET}"
                )
            else:
                print(
                    f"\n{YELLOW}⚠️  System is ready with warnings - review before proceeding{RESET}"
                )
            return True
        else:
            print(
                f"\n{RED}❌ Critical issues found - please resolve before migration{RESET}"
            )
            return False

    def save_report(self):
        """Save checklist report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": self.passed,
                "warnings": self.warnings,
                "failed": self.failed,
            },
            "checks": self.checks,
        }

        report_path = "migration_readiness_report.json"
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n{BLUE}Report saved to: {report_path}{RESET}")


def main():
    """Run migration readiness checklist"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}BoarderframeOS Migration Readiness Checklist{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    # Check if we're in the correct directory
    if not os.path.exists("startup.py"):
        print(
            f"{RED}Error: This script must be run from the BoarderframeOS root directory{RESET}"
        )
        sys.exit(1)

    checklist = MigrationChecklist()

    # Run all checks
    print(f"\n{BOLD}Running system checks...{RESET}")

    # Check required commands
    print(f"\n{BLUE}Checking Required Commands...{RESET}")
    checklist.check_command("git", "Required for version control")
    checklist.check_command("docker", "Required for containers")
    checklist.check_command("rsync", "Required for file synchronization")
    checklist.check_command("pg_dump", "Required for PostgreSQL backup")
    checklist.check_command("python3", "Required for running BoarderframeOS")

    # Run other checks
    checklist.check_docker_status()
    checklist.check_disk_space()
    checklist.check_python_environment()
    checklist.check_services_running()
    checklist.check_data_integrity()
    checklist.check_git_status()

    # Generate initial report
    ready = checklist.generate_report()

    # Interactive confirmation
    if ready:
        print(f"\n{BOLD}System checks complete. Proceeding to confirmation...{RESET}")
        confirmed = checklist.interactive_confirmation()

        if confirmed:
            print(
                f"\n{GREEN}✅ All confirmations received - ready to proceed with migration!{RESET}"
            )
        else:
            print(
                f"\n{YELLOW}⚠️  Some items not confirmed - please complete preparations{RESET}"
            )
            ready = False

    # Save report
    checklist.save_report()

    return ready


if __name__ == "__main__":
    ready = main()
    sys.exit(0 if ready else 1)
