#!/usr/bin/env python3
"""
Pre-Migration Verification Script for BoarderframeOS
Ensures everything is ready for a safe migration.
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}=== {text} ==={Colors.ENDC}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


class PreMigrationChecker:
    def __init__(self):
        self.project_root = Path.cwd()
        self.issues = []
        self.warnings = []
        self.critical_files = []
        self.total_size = 0

    def check_running_services(self):
        """Check if any services are still running"""
        print_header("Checking Running Services")

        # Check Docker containers
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
            )
            containers = result.stdout.strip().split("\n")
            boarderframe_containers = [
                c for c in containers if "boarderframe" in c.lower()
            ]

            if boarderframe_containers:
                self.warnings.append(
                    f"Docker containers still running: {', '.join(boarderframe_containers)}"
                )
                print_warning(
                    f"Found {len(boarderframe_containers)} running BoarderframeOS containers"
                )
            else:
                print_success("No BoarderframeOS Docker containers running")
        except:
            print_warning("Could not check Docker status")

        # Check Python processes
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            processes = result.stdout.lower()

            services = ["corporate_headquarters", "agent_cortex", "mcp", "startup.py"]
            running = []
            for service in services:
                if service in processes:
                    running.append(service)

            if running:
                self.warnings.append(
                    f"Python services still running: {', '.join(running)}"
                )
                print_warning(f"Found running services: {', '.join(running)}")
            else:
                print_success("No BoarderframeOS Python services running")
        except:
            print_warning("Could not check process status")

    def check_critical_files(self):
        """Verify all critical files exist"""
        print_header("Checking Critical Files")

        critical_paths = [
            # Core files
            ".env",
            "startup.py",
            "docker-compose.yml",
            "requirements.txt",
            # Core framework
            "core/base_agent.py",
            "core/message_bus.py",
            "core/agent_orchestrator.py",
            # Implemented agents
            "agents/solomon/solomon.py",
            "agents/david/david.py",
            "agents/primordials/adam.py",
            "agents/primordials/eve.py",
            "agents/primordials/bezalel.py",
            # MCP servers
            "mcp/registry_server.py",
            "mcp/filesystem_server.py",
            "mcp/database_server_postgres.py",
            # Databases
            "data/boarderframe.db",
            "data/analytics.db",
            "data/vectors.db",
            # Configuration
            "postgres-config/postgresql.conf",
            "postgres-config/pg_hba.conf",
        ]

        missing = []
        for path in critical_paths:
            full_path = self.project_root / path
            if full_path.exists():
                self.critical_files.append(str(path))
                size = full_path.stat().st_size if full_path.is_file() else 0
                self.total_size += size
            else:
                missing.append(path)

        if missing:
            self.issues.append(f"Missing critical files: {', '.join(missing)}")
            for file in missing:
                print_error(f"Missing: {file}")
        else:
            print_success(f"All {len(critical_paths)} critical files found")

    def check_docker_volumes(self):
        """Check Docker volumes exist and get sizes"""
        print_header("Checking Docker Volumes")

        volumes = [
            "boarderframeos_postgres_data",
            "boarderframeos_redis_data",
            "boarderframeos_pgadmin_data",
        ]

        try:
            for volume in volumes:
                result = subprocess.run(
                    ["docker", "volume", "inspect", volume],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    print_success(f"Volume exists: {volume}")
                else:
                    self.issues.append(f"Docker volume missing: {volume}")
                    print_error(f"Volume missing: {volume}")
        except:
            self.issues.append("Could not check Docker volumes - is Docker running?")
            print_error("Could not check Docker volumes")

    def check_database_integrity(self):
        """Check SQLite database integrity"""
        print_header("Checking Database Integrity")

        db_files = [
            "data/boarderframe.db",
            "data/analytics.db",
            "data/vectors.db",
            "data/agent_cortex_config.db",
            "data/embeddings.db",
        ]

        for db_file in db_files:
            db_path = self.project_root / db_file
            if db_path.exists():
                try:
                    conn = sqlite3.connect(str(db_path))
                    result = conn.execute("PRAGMA integrity_check").fetchone()
                    conn.close()

                    if result[0] == "ok":
                        print_success(f"{db_file}: Integrity OK")
                    else:
                        self.issues.append(f"{db_file}: Integrity check failed")
                        print_error(f"{db_file}: Integrity check failed")
                except Exception as e:
                    self.warnings.append(f"{db_file}: Could not check ({str(e)})")
                    print_warning(f"{db_file}: Could not check")

    def check_disk_space(self):
        """Check available disk space"""
        print_header("Checking Disk Space")

        try:
            stat = shutil.disk_usage(str(self.project_root))
            free_gb = stat.free / (1024**3)
            total_gb = stat.total / (1024**3)
            used_percent = (stat.used / stat.total) * 100

            print(
                f"Free space: {free_gb:.1f} GB / {total_gb:.1f} GB ({used_percent:.1f}% used)"
            )

            if free_gb < 50:
                self.warnings.append(f"Low disk space: only {free_gb:.1f} GB free")
                print_warning("Less than 50GB free - backup may require more space")
            else:
                print_success("Sufficient disk space available")
        except:
            self.warnings.append("Could not check disk space")
            print_warning("Could not check disk space")

    def check_environment_variables(self):
        """Check critical environment variables"""
        print_header("Checking Environment Variables")

        env_file = self.project_root / ".env"
        if env_file.exists():
            with open(env_file, "r") as f:
                content = f.read()

            if "ANTHROPIC_API_KEY" in content:
                print_success(".env file contains ANTHROPIC_API_KEY")
            else:
                self.warnings.append(".env file missing ANTHROPIC_API_KEY")
                print_warning(".env file missing ANTHROPIC_API_KEY")

            # Check file permissions
            stat = env_file.stat()
            if stat.st_mode & 0o077:
                self.warnings.append(".env file has loose permissions")
                print_warning(".env file should have 600 permissions")
            else:
                print_success(".env file permissions OK")
        else:
            self.issues.append(".env file not found")
            print_error(".env file not found")

    def estimate_backup_size(self):
        """Estimate total backup size"""
        print_header("Estimating Backup Size")

        # Project files
        project_size = sum(
            f.stat().st_size for f in self.project_root.rglob("*") if f.is_file()
        )
        project_gb = project_size / (1024**3)

        # Docker volumes (estimate)
        docker_estimate = 5  # GB estimate for Docker volumes

        total_estimate = project_gb + docker_estimate

        print(f"Project files: {project_gb:.2f} GB")
        print(f"Docker volumes (estimate): {docker_estimate} GB")
        print(f"Total estimated backup size: {total_estimate:.2f} GB")

        return total_estimate

    def generate_report(self):
        """Generate pre-migration report"""
        print_header("Pre-Migration Report")

        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "critical_issues": len(self.issues),
            "warnings": len(self.warnings),
            "issues": self.issues,
            "warning_list": self.warnings,
            "critical_files_found": len(self.critical_files),
            "estimated_backup_gb": self.estimate_backup_size(),
        }

        # Save report
        report_path = self.project_root / "pre_migration_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\nReport saved to: {report_path}")

        # Summary
        if self.issues:
            print(
                f"\n{Colors.RED}CRITICAL ISSUES FOUND: {len(self.issues)}{Colors.ENDC}"
            )
            for issue in self.issues:
                print(f"  - {issue}")
            print("\n⚠️  RESOLVE THESE ISSUES BEFORE MIGRATING!")
        else:
            print(f"\n{Colors.GREEN}✓ No critical issues found{Colors.ENDC}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  - {warning}")

        return len(self.issues) == 0

    def run_all_checks(self):
        """Run all pre-migration checks"""
        print(f"{Colors.BOLD}BoarderframeOS Pre-Migration Verification{Colors.ENDC}")
        print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.check_running_services()
        self.check_critical_files()
        self.check_docker_volumes()
        self.check_database_integrity()
        self.check_disk_space()
        self.check_environment_variables()

        ready = self.generate_report()

        if ready:
            print(
                f"\n{Colors.GREEN}{Colors.BOLD}✓ SYSTEM READY FOR MIGRATION{Colors.ENDC}"
            )
            print("\nNext steps:")
            print("1. Review any warnings above")
            print("2. Run the backup commands from the migration guide")
            print("3. Verify backups before transferring")
        else:
            print(
                f"\n{Colors.RED}{Colors.BOLD}✗ SYSTEM NOT READY FOR MIGRATION{Colors.ENDC}"
            )
            print("\nFix all critical issues before proceeding!")

        return ready


def main():
    checker = PreMigrationChecker()
    ready = checker.run_all_checks()
    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    main()
