#!/usr/bin/env python3
"""
Final Comprehensive Migration Verification for BoarderframeOS
This script performs an exhaustive check of everything that needs to be migrated.
"""

import hashlib
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
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_subheader(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}=== {text} ==={Colors.ENDC}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.MAGENTA}ℹ {text}{Colors.ENDC}")


class ComprehensiveMigrationChecker:
    def __init__(self):
        self.project_root = Path.cwd()
        self.home_dir = Path.home()
        self.findings = {
            "boarderframeos": {},
            "docker": {},
            "development": {},
            "system": {},
            "other_projects": [],
            "recommendations": [],
        }

    def check_boarderframeos_complete(self):
        """Complete BoarderframeOS check"""
        print_header("BoarderframeOS Project Check")

        # Core files
        print_subheader("Core Files")
        core_files = {
            ".env": "API keys and configuration",
            "docker-compose.yml": "Docker orchestration",
            "startup.py": "System startup script",
            "requirements.txt": "Python dependencies",
            "CLAUDE.md": "Project documentation",
        }

        for file, desc in core_files.items():
            path = self.project_root / file
            if path.exists():
                size = path.stat().st_size
                print_success(f"{file} ({self._format_size(size)}) - {desc}")
                self.findings["boarderframeos"][file] = {"exists": True, "size": size}
            else:
                print_error(f"{file} - {desc}")
                self.findings["boarderframeos"][file] = {"exists": False}

        # Databases with transaction files
        print_subheader("Database Files")
        db_dir = self.project_root / "data"
        if db_dir.exists():
            for db_file in db_dir.glob("*.db*"):
                size = db_file.stat().st_size
                print_success(f"{db_file.name} ({self._format_size(size)})")

        # Check for uncommitted changes
        print_subheader("Git Status")
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.stdout.strip():
                print_warning("Uncommitted changes detected:")
                for line in result.stdout.strip().split("\n")[:5]:
                    print(f"  {line}")
                if len(result.stdout.strip().split("\n")) > 5:
                    print(
                        f"  ... and {len(result.stdout.strip().split('\n')) - 5} more files"
                    )
                self.findings["boarderframeos"]["git_clean"] = False
            else:
                print_success("Git repository is clean")
                self.findings["boarderframeos"]["git_clean"] = True
        except:
            print_warning("Could not check git status")

    def check_docker_comprehensive(self):
        """Comprehensive Docker check"""
        print_header("Docker Environment Check")

        try:
            # Check Docker daemon
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if result.returncode == 0:
                print_success("Docker daemon is running")
            else:
                print_error("Docker daemon not running")
                return

            # List ALL containers (not just BoarderframeOS)
            print_subheader("All Docker Containers")
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--format",
                    "table {{.Names}}\t{{.Status}}\t{{.Size}}",
                ],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                print(result.stdout)

            # List ALL volumes
            print_subheader("All Docker Volumes")
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "table {{.Name}}\t{{.Driver}}"],
                capture_output=True,
                text=True,
            )
            if result.stdout.strip():
                print(result.stdout)

            # Docker disk usage
            print_subheader("Docker Disk Usage")
            result = subprocess.run(
                ["docker", "system", "df"], capture_output=True, text=True
            )
            if result.stdout:
                print(result.stdout)

            # Docker.raw size on macOS
            docker_raw = (
                Path.home()
                / "Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
            )
            if docker_raw.exists():
                size = docker_raw.stat().st_size
                print_info(f"Docker.raw size: {self._format_size(size)}")
                self.findings["docker"]["docker_raw_size"] = size

        except Exception as e:
            print_error(f"Docker check failed: {e}")

    def check_development_environment(self):
        """Check complete development environment"""
        print_header("Development Environment Check")

        # SSH Keys
        print_subheader("SSH Keys")
        ssh_dir = self.home_dir / ".ssh"
        if ssh_dir.exists():
            key_files = list(ssh_dir.glob("id_*"))
            print_success(f"Found {len(key_files)} SSH key files")
            for key in key_files:
                if not key.name.endswith(".pub"):
                    print_info(f"  - {key.name}")
        else:
            print_warning("No .ssh directory found")

        # Git configuration
        print_subheader("Git Configuration")
        try:
            email = subprocess.run(
                ["git", "config", "--global", "user.email"],
                capture_output=True,
                text=True,
            ).stdout.strip()
            name = subprocess.run(
                ["git", "config", "--global", "user.name"],
                capture_output=True,
                text=True,
            ).stdout.strip()
            print_success(f"Git user: {name} <{email}>")
        except:
            print_warning("Could not read git configuration")

        # Shell configuration
        print_subheader("Shell Configuration")
        shell_files = [".zshrc", ".bashrc", ".zprofile", ".bash_profile"]
        for file in shell_files:
            path = self.home_dir / file
            if path.exists():
                size = path.stat().st_size
                print_success(f"{file} ({self._format_size(size)})")

        # Homebrew
        print_subheader("Homebrew Packages")
        try:
            result = subprocess.run(
                ["brew", "list", "--formula"], capture_output=True, text=True
            )
            if result.returncode == 0:
                packages = result.stdout.strip().split("\n")
                print_success(f"Found {len(packages)} Homebrew formulae")
                # Show first 10
                for pkg in packages[:10]:
                    print(f"  - {pkg}")
                if len(packages) > 10:
                    print(f"  ... and {len(packages) - 10} more")
        except:
            print_warning("Homebrew not found or not accessible")

        # Node.js global packages
        print_subheader("Global npm Packages")
        try:
            result = subprocess.run(
                ["npm", "list", "-g", "--depth=0"], capture_output=True, text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip first line
                print_success(f"Found {len(lines)} global npm packages")
        except:
            print_warning("npm not found")

        # Python environments
        print_subheader("Python Environments")

        # Check for pyenv
        pyenv_dir = self.home_dir / ".pyenv/versions"
        if pyenv_dir.exists():
            versions = list(pyenv_dir.iterdir())
            print_success(f"pyenv: {len(versions)} Python versions")

        # Check for conda
        conda_dir = self.home_dir / "anaconda3/envs"
        if not conda_dir.exists():
            conda_dir = self.home_dir / "miniconda3/envs"
        if conda_dir.exists():
            envs = list(conda_dir.iterdir())
            print_success(f"conda: {len(envs)} environments")

    def check_other_projects(self):
        """Find other git repositories"""
        print_header("Other Git Repositories")

        search_dirs = [
            self.home_dir / "Documents",
            self.home_dir / "Desktop",
            self.home_dir / "Developer",
            self.home_dir / "Projects",
            self.home_dir / "Code",
            self.home_dir / "repos",
        ]

        repos = []
        for search_dir in search_dirs:
            if search_dir.exists():
                try:
                    # Use find command for efficiency
                    cmd = f'find "{search_dir}" -name ".git" -type d -maxdepth 4 2>/dev/null'
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True
                    )
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            repo_path = Path(line).parent
                            repos.append(repo_path)
                except:
                    pass

        print_info(f"Found {len(repos)} git repositories")

        # Check for uncommitted changes
        repos_with_changes = []
        for repo in repos[:20]:  # Check first 20 to avoid taking too long
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    cwd=repo,
                )
                if result.stdout.strip():
                    repos_with_changes.append(repo)
            except:
                pass

        if repos_with_changes:
            print_warning(
                f"{len(repos_with_changes)} repositories have uncommitted changes:"
            )
            for repo in repos_with_changes[:5]:
                print(f"  - {repo}")
            if len(repos_with_changes) > 5:
                print(f"  ... and {len(repos_with_changes) - 5} more")

        self.findings["other_projects"] = {
            "total": len(repos),
            "with_changes": len(repos_with_changes),
        }

    def check_cloud_configurations(self):
        """Check cloud CLI configurations"""
        print_header("Cloud Service Configurations")

        cloud_configs = {
            "AWS CLI": self.home_dir / ".aws",
            "Google Cloud": self.home_dir / ".config/gcloud",
            "Azure CLI": self.home_dir / ".azure",
            "Heroku": self.home_dir / ".netrc",
            "Vercel": self.home_dir / ".vercel",
            "Netlify": self.home_dir / ".netlify",
        }

        for service, path in cloud_configs.items():
            if path.exists():
                print_success(f"{service}: Configuration found at {path}")
            else:
                print_info(f"{service}: No configuration found")

    def check_applications(self):
        """Check installed applications and their data"""
        print_header("Application Data")

        # VS Code
        print_subheader("VS Code")
        vscode_settings = (
            self.home_dir / "Library/Application Support/Code/User/settings.json"
        )
        if vscode_settings.exists():
            print_success("VS Code settings found")
            try:
                result = subprocess.run(
                    ["code", "--list-extensions"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    extensions = result.stdout.strip().split("\n")
                    print_success(f"VS Code: {len(extensions)} extensions installed")
            except:
                print_info("Could not list VS Code extensions")

        # Check for other IDEs
        ide_paths = {
            "Cursor": self.home_dir / "Library/Application Support/Cursor",
            "IntelliJ IDEA": self.home_dir / "Library/Application Support/JetBrains",
            "Sublime Text": self.home_dir / "Library/Application Support/Sublime Text",
        }

        for ide, path in ide_paths.items():
            if path.exists():
                print_success(f"{ide}: Configuration found")

    def check_system_configuration(self):
        """Check system-level configurations"""
        print_header("System Configuration")

        # LaunchAgents
        print_subheader("Launch Agents")
        launch_agents = self.home_dir / "Library/LaunchAgents"
        if launch_agents.exists():
            agents = list(launch_agents.glob("*.plist"))
            if agents:
                print_warning(f"Found {len(agents)} LaunchAgents:")
                for agent in agents:
                    print(f"  - {agent.name}")
            else:
                print_success("No custom LaunchAgents found")

        # Cron jobs
        print_subheader("Cron Jobs")
        try:
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                print_warning("Active cron jobs found:")
                print(result.stdout)
            else:
                print_success("No cron jobs configured")
        except:
            print_info("Could not check cron jobs")

    def estimate_total_size(self):
        """Estimate total migration size"""
        print_header("Migration Size Estimate")

        total_size = 0

        # BoarderframeOS project
        project_size = sum(
            f.stat().st_size for f in self.project_root.rglob("*") if f.is_file()
        )
        total_size += project_size
        print_info(f"BoarderframeOS project: {self._format_size(project_size)}")

        # Docker estimate (from docker_raw if found)
        if "docker_raw_size" in self.findings.get("docker", {}):
            docker_size = self.findings["docker"]["docker_raw_size"]
            total_size += docker_size
            print_info(f"Docker data: {self._format_size(docker_size)}")
        else:
            # Estimate
            docker_estimate = 10 * 1024**3  # 10GB estimate
            total_size += docker_estimate
            print_info(f"Docker data (estimate): {self._format_size(docker_estimate)}")

        # Development tools estimate
        dev_estimate = 5 * 1024**3  # 5GB for IDEs, tools, etc.
        total_size += dev_estimate
        print_info(f"Development tools (estimate): {self._format_size(dev_estimate)}")

        print(
            f"\n{Colors.BOLD}Total estimated size: {self._format_size(total_size)}{Colors.ENDC}"
        )

        return total_size

    def generate_recommendations(self):
        """Generate migration recommendations"""
        print_header("Migration Recommendations")

        recommendations = []

        # Based on findings
        if not self.findings["boarderframeos"].get("git_clean", True):
            recommendations.append(
                "⚠️  Commit or stash changes in BoarderframeOS before migration"
            )

        if self.findings.get("other_projects", {}).get("with_changes", 0) > 0:
            recommendations.append(
                "⚠️  Review and commit changes in other git repositories"
            )

        # Always recommend
        recommendations.extend(
            [
                "✓ Use the enhanced migration guide: BOARDERFRAMEOS_MIGRATION_GUIDE_ENHANCED.md",
                "✓ Run pre-migration verification: python scripts/verify/pre_migration_verification.py",
                "✓ Create a Time Machine backup as additional safety",
                "✓ Document any custom system configurations",
                "✓ Export browser bookmarks and passwords",
                "✓ Note down any licensed software serial numbers",
            ]
        )

        for rec in recommendations:
            print(rec)

        self.findings["recommendations"] = recommendations

    def _format_size(self, bytes):
        """Format bytes to human readable"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} PB"

    def save_report(self):
        """Save detailed report"""
        report_path = self.project_root / "final_migration_report.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "hostname": subprocess.run(
                    ["hostname"], capture_output=True, text=True
                ).stdout.strip(),
                "user": os.environ.get("USER", "unknown"),
            },
            "findings": self.findings,
            "estimated_size": self.estimate_total_size(),
        }

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n{Colors.GREEN}Report saved to: {report_path}{Colors.ENDC}")

    def run_complete_check(self):
        """Run all checks"""
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'FINAL MIGRATION VERIFICATION':^60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.check_boarderframeos_complete()
        self.check_docker_comprehensive()
        self.check_development_environment()
        self.check_other_projects()
        self.check_cloud_configurations()
        self.check_applications()
        self.check_system_configuration()

        self.estimate_total_size()
        self.generate_recommendations()
        self.save_report()

        print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.GREEN}{Colors.BOLD}{'VERIFICATION COMPLETE':^60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")

        print("\nNext Steps:")
        print("1. Review the recommendations above")
        print("2. Address any warnings or issues")
        print("3. Run the backup process from the migration guide")
        print("4. Use the migration dashboard to track progress")


def main():
    checker = ComprehensiveMigrationChecker()
    checker.run_complete_check()


if __name__ == "__main__":
    main()
