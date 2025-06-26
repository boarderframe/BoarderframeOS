#!/usr/bin/env python3
"""
BoarderframeOS Verification Environment Setup
Installs required dependencies and prepares the system for verification
"""

import subprocess
import sys
import os
from datetime import datetime


def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "WARNING": "⚠️ ",
        "ERROR": "❌"
    }.get(level, "")
    print(f"[{timestamp}] {prefix} {message}")


def run_command(command, description=""):
    """Run a shell command and return success status"""
    if description:
        log(description)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)


def main():
    print("="*60)
    print("BoarderframeOS Verification Environment Setup")
    print("="*60)
    
    # Check Python version
    log(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        log("Python 3.8+ is required", "ERROR")
        sys.exit(1)
    
    # Check if in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        log("Not in a virtual environment", "WARNING")
        log("It's recommended to use a virtual environment:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # On macOS/Linux")
        print("  # or")
        print("  venv\\Scripts\\activate  # On Windows")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Upgrade pip
    log("Upgrading pip...")
    success, output = run_command(f"{sys.executable} -m pip install --upgrade pip")
    if success:
        log("pip upgraded successfully", "SUCCESS")
    else:
        log(f"Failed to upgrade pip: {output}", "ERROR")
    
    # Install verification requirements
    log("Installing verification requirements...")
    req_file = "requirements-verification.txt"
    
    if os.path.exists(req_file):
        success, output = run_command(
            f"{sys.executable} -m pip install -r {req_file}",
            "Installing packages from requirements-verification.txt"
        )
        
        if success:
            log("Verification requirements installed successfully", "SUCCESS")
        else:
            log(f"Failed to install some requirements: {output}", "ERROR")
            
            # Try installing packages one by one
            log("Attempting to install packages individually...")
            packages = [
                "psycopg2-binary",
                "aiohttp",
                "httpx",
                "websockets",
                "psutil",
                "redis",
                "pytest",
                "pytest-asyncio"
            ]
            
            for package in packages:
                success, _ = run_command(
                    f"{sys.executable} -m pip install {package}",
                    f"Installing {package}..."
                )
                if success:
                    log(f"{package} installed", "SUCCESS")
                else:
                    log(f"Failed to install {package}", "WARNING")
    else:
        log(f"{req_file} not found", "ERROR")
        sys.exit(1)
    
    # Check Docker
    log("Checking Docker installation...")
    success, output = run_command("docker --version")
    if success:
        log(f"Docker found: {output.strip()}", "SUCCESS")
        
        # Check if Docker is running
        success, _ = run_command("docker ps", "Checking if Docker is running")
        if success:
            log("Docker is running", "SUCCESS")
        else:
            log("Docker is not running. Please start Docker Desktop", "WARNING")
    else:
        log("Docker not found. Please install Docker Desktop", "ERROR")
    
    # Create necessary directories
    log("Creating necessary directories...")
    directories = ["logs", "data", "configs", "monitoring"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        log(f"Created directory: {directory}", "SUCCESS")
    
    # Check for main requirements.txt
    if os.path.exists("requirements.txt"):
        response = input("\nDo you want to install main application requirements too? (y/N): ")
        if response.lower() == 'y':
            success, output = run_command(
                f"{sys.executable} -m pip install -r requirements.txt",
                "Installing main application requirements..."
            )
            if success:
                log("Main requirements installed", "SUCCESS")
            else:
                log(f"Some main requirements failed: {output}", "WARNING")
    
    print("\n" + "="*60)
    print("Setup Summary")
    print("="*60)
    
    # Quick dependency check
    log("Checking installed packages...")
    critical_packages = ["psycopg2", "aiohttp", "httpx", "websockets"]
    missing_packages = []
    
    for package in critical_packages:
        try:
            __import__(package)
            log(f"{package} ✓", "SUCCESS")
        except ImportError:
            log(f"{package} ✗", "ERROR")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Try installing them manually:")
        for pkg in missing_packages:
            print(f"  pip install {pkg}")
    else:
        print("\n✅ All critical packages installed!")
    
    print("\nNext steps:")
    print("1. Start Docker services:")
    print("   docker-compose up -d postgresql redis")
    print("\n2. Run the verification suite:")
    print("   python run_all_verifications.py")
    print("\n3. View results:")
    print("   open verification_report.html")


if __name__ == "__main__":
    main()