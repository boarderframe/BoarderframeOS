#!/usr/bin/env python3
"""
Post-Migration Automated Setup Script for BoarderframeOS
Automates environment configuration after migration
"""

import os
import sys
import subprocess
import shutil
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class PostMigrationSetup:
    def __init__(self, target_dir: str, auto_mode: bool = False):
        self.target_dir = Path(target_dir)
        self.auto_mode = auto_mode
        self.venv_path = self.target_dir / "venv"
        self.errors = []
        self.successes = []
        self.warnings = []
        
    def log_success(self, message: str):
        self.successes.append(message)
        print(f"✓ {message}")
        
    def log_warning(self, message: str):
        self.warnings.append(message)
        print(f"⚠ {message}")
        
    def log_error(self, message: str):
        self.errors.append(message)
        print(f"✗ {message}")
        
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, 
                   check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result"""
        try:
            if cwd is None:
                cwd = self.target_dir
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, 
                                  text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            self.log_error(f"Command failed: {' '.join(cmd)}")
            self.log_error(f"Error: {e.stderr}")
            raise
        except FileNotFoundError:
            self.log_error(f"Command not found: {cmd[0]}")
            raise
            
    def check_python_version(self) -> bool:
        """Verify Python version is 3.13+"""
        print("\n=== Checking Python Version ===")
        
        result = self.run_command([sys.executable, "--version"], check=False)
        if result.returncode == 0:
            version_str = result.stdout.strip()
            self.log_success(f"Python version: {version_str}")
            
            # Parse version
            import re
            match = re.search(r'Python (\d+)\.(\d+)', version_str)
            if match:
                major, minor = int(match.group(1)), int(match.group(2))
                if major >= 3 and minor >= 13:
                    self.log_success("Python 3.13+ confirmed")
                    return True
                else:
                    self.log_error(f"Python 3.13+ required, found {major}.{minor}")
                    return False
        
        self.log_error("Could not determine Python version")
        return False
        
    def setup_python_environment(self) -> bool:
        """Set up Python virtual environment"""
        print("\n=== Setting Up Python Environment ===")
        
        # Create virtual environment
        if not self.venv_path.exists():
            self.log_success("Creating virtual environment...")
            try:
                self.run_command([sys.executable, "-m", "venv", "venv"])
                self.log_success("Virtual environment created")
            except Exception as e:
                self.log_error(f"Failed to create virtual environment: {e}")
                return False
        else:
            self.log_success("Virtual environment already exists")
            
        # Determine pip path based on OS
        if sys.platform == "win32":
            pip_path = self.venv_path / "Scripts" / "pip"
            python_path = self.venv_path / "Scripts" / "python"
        else:
            pip_path = self.venv_path / "bin" / "pip"
            python_path = self.venv_path / "bin" / "python"
            
        # Upgrade pip
        self.log_success("Upgrading pip...")
        try:
            self.run_command([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])
        except Exception:
            self.log_warning("Could not upgrade pip")
            
        # Install main requirements
        req_file = self.target_dir / "requirements.txt"
        if req_file.exists():
            self.log_success("Installing main requirements...")
            try:
                self.run_command([str(pip_path), "install", "-r", "requirements.txt"])
                self.log_success("Main requirements installed")
            except Exception as e:
                self.log_error(f"Failed to install requirements: {e}")
                return False
        else:
            self.log_error("requirements.txt not found")
            return False
            
        # Install MCP requirements
        mcp_req = self.target_dir / "mcp" / "requirements.txt"
        if mcp_req.exists():
            self.log_success("Installing MCP requirements...")
            try:
                self.run_command([str(pip_path), "install", "-r", str(mcp_req)])
                self.log_success("MCP requirements installed")
            except Exception:
                self.log_warning("Some MCP requirements failed to install")
                
        # Install development tools
        if self.auto_mode or self.prompt_user("Install development tools (pre-commit, pytest, etc)?"):
            try:
                self.run_command([str(pip_path), "install", "pre-commit", "pytest", 
                                "pytest-cov", "black", "isort", "flake8", "mypy", "bandit"])
                self.log_success("Development tools installed")
                
                # Set up pre-commit hooks
                if (self.target_dir / ".pre-commit-config.yaml").exists():
                    self.run_command([str(pip_path), "install", "pre-commit"])
                    self.run_command(["pre-commit", "install"])
                    self.log_success("Pre-commit hooks installed")
            except Exception:
                self.log_warning("Some development tools failed to install")
                
        return True
        
    def setup_nodejs_environment(self) -> bool:
        """Set up Node.js environments"""
        print("\n=== Setting Up Node.js Environment ===")
        
        # Check if npm is available
        npm_check = self.run_command(["npm", "--version"], check=False)
        if npm_check.returncode != 0:
            self.log_warning("npm not found - skipping Node.js setup")
            self.log_warning("Install Node.js manually for UI components")
            return True  # Not critical for basic operation
            
        # Setup modern UI
        ui_path = self.target_dir / "ui" / "modern"
        if (ui_path / "package.json").exists():
            self.log_success("Installing UI dependencies...")
            try:
                self.run_command(["npm", "install"], cwd=ui_path)
                self.log_success("UI dependencies installed")
                
                # Build UI
                if self.auto_mode or self.prompt_user("Build UI for production?"):
                    self.run_command(["npm", "run", "build"], cwd=ui_path)
                    self.log_success("UI built for production")
            except Exception as e:
                self.log_warning(f"UI setup failed: {e}")
                
        # Setup Claude tools
        claude_path = self.target_dir / "tools" / "claude"
        if (claude_path / "package.json").exists():
            self.log_success("Installing Claude tools dependencies...")
            try:
                self.run_command(["npm", "install"], cwd=claude_path)
                self.log_success("Claude tools dependencies installed")
            except Exception as e:
                self.log_warning(f"Claude tools setup failed: {e}")
                
        return True
        
    def setup_docker_services(self) -> bool:
        """Set up Docker services"""
        print("\n=== Setting Up Docker Services ===")
        
        # Check if docker is available
        docker_check = self.run_command(["docker", "--version"], check=False)
        if docker_check.returncode != 0:
            self.log_error("Docker not found - cannot start services")
            self.log_error("Install Docker Desktop and try again")
            return False
            
        # Check docker-compose
        compose_check = self.run_command(["docker-compose", "--version"], check=False)
        if compose_check.returncode != 0:
            # Try docker compose (newer syntax)
            compose_check = self.run_command(["docker", "compose", "version"], check=False)
            if compose_check.returncode != 0:
                self.log_error("docker-compose not found")
                return False
                
        # Start services
        if self.auto_mode or self.prompt_user("Start Docker services (PostgreSQL, Redis)?"):
            self.log_success("Starting Docker services...")
            try:
                # Stop any existing services first
                self.run_command(["docker-compose", "down"], check=False)
                
                # Start services
                self.run_command(["docker-compose", "up", "-d", "postgresql", "redis"])
                
                # Wait for services to be ready
                self.log_success("Waiting for services to start...")
                time.sleep(10)
                
                # Check PostgreSQL
                pg_check = self.run_command([
                    "docker", "exec", "boarderframeos_postgres", 
                    "pg_isready", "-U", "boarderframe", "-d", "boarderframeos"
                ], check=False)
                
                if pg_check.returncode == 0:
                    self.log_success("PostgreSQL is ready")
                else:
                    self.log_warning("PostgreSQL may not be ready yet")
                    
                # Check Redis
                redis_check = self.run_command([
                    "docker", "exec", "boarderframeos_redis",
                    "redis-cli", "ping"
                ], check=False)
                
                if redis_check.returncode == 0 and "PONG" in redis_check.stdout:
                    self.log_success("Redis is ready")
                else:
                    self.log_warning("Redis may not be ready yet")
                    
            except Exception as e:
                self.log_error(f"Failed to start Docker services: {e}")
                return False
                
        return True
        
    def setup_database_schema(self) -> bool:
        """Set up database schema and migrations"""
        print("\n=== Setting Up Database Schema ===")
        
        if not self.auto_mode and not self.prompt_user("Run database migrations?"):
            self.log_warning("Skipping database migrations")
            return True
            
        # Get Python from venv
        if sys.platform == "win32":
            python_path = self.venv_path / "Scripts" / "python"
        else:
            python_path = self.venv_path / "bin" / "python"
            
        migrations_dir = self.target_dir / "migrations"
        if not migrations_dir.exists():
            self.log_error("Migrations directory not found")
            return False
            
        # Run SQL migrations first
        sql_files = sorted(migrations_dir.glob("*.sql"))
        for sql_file in sql_files:
            self.log_success(f"Running migration: {sql_file.name}")
            try:
                # Read SQL file
                with open(sql_file, 'r') as f:
                    sql_content = f.read()
                    
                # Execute via docker
                result = self.run_command([
                    "docker", "exec", "-i", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos"
                ], check=False)
                
                if result.returncode != 0:
                    self.log_warning(f"Migration {sql_file.name} may have failed")
            except Exception as e:
                self.log_warning(f"Could not run {sql_file.name}: {e}")
                
        # Run Python migrations
        py_migrations = [
            "migrate_departments.py",
            "populate_divisions_departments.py"
        ]
        
        for migration in py_migrations:
            migration_path = migrations_dir / migration
            if migration_path.exists():
                self.log_success(f"Running Python migration: {migration}")
                try:
                    self.run_command([str(python_path), str(migration_path)])
                except Exception as e:
                    self.log_warning(f"Migration {migration} failed: {e}")
                    
        return True
        
    def configure_environment(self) -> bool:
        """Configure environment variables"""
        print("\n=== Configuring Environment ===")
        
        env_file = self.target_dir / ".env"
        env_secret = self.target_dir / ".env.secret"
        
        if env_file.exists():
            self.log_success(".env file already exists")
        elif env_secret.exists():
            if self.auto_mode or self.prompt_user("Copy .env.secret to .env?"):
                shutil.copy2(env_secret, env_file)
                self.log_success("Created .env from .env.secret")
            else:
                self.log_warning("Remember to create .env file manually")
        else:
            self.log_error("No .env or .env.secret file found")
            return False
            
        # Check for required API key
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                
            if 'ANTHROPIC_API_KEY' in content:
                if 'YOUR_KEY_HERE' in content or 'sk-...' in content:
                    self.log_warning("ANTHROPIC_API_KEY needs to be configured in .env")
                    self.log_warning("Edit .env and add your actual API key")
            else:
                self.log_warning("ANTHROPIC_API_KEY not found in .env")
                
        return True
        
    def test_startup(self) -> bool:
        """Test system startup"""
        print("\n=== Testing System Startup ===")
        
        if not self.auto_mode and not self.prompt_user("Test system startup?"):
            return True
            
        # Get Python from venv
        if sys.platform == "win32":
            python_path = self.venv_path / "Scripts" / "python"
        else:
            python_path = self.venv_path / "bin" / "python"
            
        # Test imports
        self.log_success("Testing core imports...")
        test_imports = [
            "from core.message_bus import message_bus",
            "from core.base_agent import BaseAgent",
            "import anthropic"
        ]
        
        for import_stmt in test_imports:
            result = self.run_command(
                [str(python_path), "-c", import_stmt],
                check=False
            )
            if result.returncode == 0:
                self.log_success(f"Import successful: {import_stmt.split()[1]}")
            else:
                self.log_error(f"Import failed: {import_stmt}")
                
        # Test system_status.py
        if (self.target_dir / "system_status.py").exists():
            self.log_success("Running system status check...")
            result = self.run_command(
                [str(python_path), "system_status.py"],
                check=False
            )
            if result.returncode == 0:
                self.log_success("System status check passed")
            else:
                self.log_warning("System status check had issues")
                
        return True
        
    def prompt_user(self, question: str) -> bool:
        """Prompt user for yes/no question"""
        while True:
            response = input(f"\n{question} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")
                
    def create_startup_scripts(self):
        """Create helpful startup scripts"""
        print("\n=== Creating Startup Scripts ===")
        
        # Create start script for Unix-like systems
        if sys.platform != "win32":
            start_script = self.target_dir / "start.sh"
            script_content = """#!/bin/bash
# BoarderframeOS Startup Script

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH=.

# Start the system
echo "Starting BoarderframeOS..."
python startup.py
"""
            with open(start_script, 'w') as f:
                f.write(script_content)
            start_script.chmod(0o755)
            self.log_success("Created start.sh script")
            
        # Create batch script for Windows
        else:
            start_script = self.target_dir / "start.bat"
            script_content = """@echo off
REM BoarderframeOS Startup Script

REM Activate virtual environment
call venv\\Scripts\\activate

REM Set Python path
set PYTHONPATH=.

REM Start the system
echo Starting BoarderframeOS...
python startup.py
"""
            with open(start_script, 'w') as f:
                f.write(script_content)
            self.log_success("Created start.bat script")
            
    def generate_final_report(self):
        """Generate final setup report"""
        report_path = self.target_dir / "POST_MIGRATION_REPORT.md"
        
        report = f"""# BoarderframeOS Post-Migration Setup Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Setup Summary

- ✓ Successes: {len(self.successes)}
- ⚠ Warnings: {len(self.warnings)}
- ✗ Errors: {len(self.errors)}

## What Was Done

### Successes
"""
        for success in self.successes:
            report += f"- {success}\n"
            
        if self.warnings:
            report += "\n### Warnings\n"
            for warning in self.warnings:
                report += f"- {warning}\n"
                
        if self.errors:
            report += "\n### Errors\n"
            for error in self.errors:
                report += f"- {error}\n"
                
        report += """
## Next Steps

1. **Configure API Keys**:
   ```bash
   # Edit .env file and add your ANTHROPIC_API_KEY
   nano .env  # or use your preferred editor
   ```

2. **Start the System**:
   ```bash
   # Unix/Linux/macOS:
   ./start.sh
   
   # Windows:
   start.bat
   
   # Or manually:
   source venv/bin/activate  # or venv\\Scripts\\activate on Windows
   python startup.py
   ```

3. **Access the System**:
   - Corporate HQ: http://localhost:8888
   - Agent Cortex: http://localhost:8889
   - Agent Communication Center: http://localhost:8890

4. **Verify Everything is Working**:
   ```bash
   python system_status.py
   ```

5. **Check Logs** if issues occur:
   ```bash
   tail -f logs/startup.log
   ```

## Troubleshooting

- If Docker services fail: Ensure Docker Desktop is running
- If imports fail: Check virtual environment is activated
- If ports are in use: Change ports in .env file
- For database issues: Check PostgreSQL logs with `docker logs boarderframeos_postgres`

## Support

Refer to CLAUDE.md for detailed system documentation.
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
            
        print(f"\n{'='*60}")
        print(f"Setup report saved to: {report_path}")
        print(f"{'='*60}")
        
    def run_setup(self):
        """Run the complete post-migration setup"""
        print("=" * 60)
        print("BoarderframeOS Post-Migration Setup")
        print("=" * 60)
        
        # Check Python version first
        if not self.check_python_version():
            self.log_error("Python 3.13+ is required")
            return False
            
        # Run all setup steps
        steps = [
            ("Python Environment", self.setup_python_environment),
            ("Node.js Environment", self.setup_nodejs_environment),
            ("Docker Services", self.setup_docker_services),
            ("Database Schema", self.setup_database_schema),
            ("Environment Configuration", self.configure_environment),
            ("Startup Scripts", self.create_startup_scripts),
            ("System Test", self.test_startup),
        ]
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    self.log_error(f"{step_name} setup failed")
                    if not self.auto_mode:
                        if not self.prompt_user("Continue anyway?"):
                            break
            except Exception as e:
                self.log_error(f"{step_name} encountered error: {e}")
                if not self.auto_mode:
                    if not self.prompt_user("Continue anyway?"):
                        break
                        
        # Generate final report
        self.generate_final_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print(f"✓ Successes: {len(self.successes)}")
        print(f"⚠ Warnings: {len(self.warnings)}")
        print(f"✗ Errors: {len(self.errors)}")
        
        if len(self.errors) == 0:
            print("\n✅ BoarderframeOS is ready to start!")
            print("Run: ./start.sh (or start.bat on Windows)")
        else:
            print("\n⚠️  Setup completed with errors")
            print("Review POST_MIGRATION_REPORT.md for details")
            
        return len(self.errors) == 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Post-migration setup for BoarderframeOS"
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Target directory (default: current directory)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run in automatic mode (no prompts)"
    )
    
    args = parser.parse_args()
    
    target_path = Path(args.target_dir)
    if not target_path.exists():
        print(f"Error: Directory does not exist: {args.target_dir}")
        sys.exit(1)
        
    # Check if it looks like a BoarderframeOS installation
    if not (target_path / "startup.py").exists():
        print(f"Error: {args.target_dir} does not appear to be a BoarderframeOS installation")
        print("Run this from the migrated BoarderframeOS directory")
        sys.exit(1)
        
    setup = PostMigrationSetup(args.target_dir, args.auto)
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()