#!/usr/bin/env python3
"""
Ensure startup.py runs with proper virtual environment
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Check and run startup with proper environment"""
    script_dir = Path(__file__).parent
    venv_python = script_dir / ".venv" / "bin" / "python"
    startup_script = script_dir / "startup.py"

    print("🔍 Checking Python environment...")
    print(f"Current Python: {sys.executable}")

    # Check if we're already in the venv
    if ".venv" in sys.executable:
        print("✅ Already using virtual environment")
        # Run startup directly
        os.execv(sys.executable, [sys.executable, str(startup_script)])
    else:
        print("⚠️  Not using virtual environment")

        if venv_python.exists():
            print(f"🔄 Switching to venv Python: {venv_python}")
            # Re-run this script with venv Python
            os.execv(str(venv_python), [str(venv_python), str(startup_script)])
        else:
            print("❌ Virtual environment not found!")
            print("📋 Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", ".venv"])

            print("📦 Installing requirements...")
            venv_pip = script_dir / ".venv" / "bin" / "pip"
            subprocess.run([str(venv_pip), "install", "-r", "requirements.txt"])

            print("🚀 Starting with new virtual environment...")
            os.execv(str(venv_python), [str(venv_python), str(startup_script)])


if __name__ == "__main__":
    main()
