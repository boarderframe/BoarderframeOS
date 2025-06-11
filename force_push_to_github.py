#!/usr/bin/env python3
"""
Force push BoarderframeOS to GitHub - Non-interactive version
"""

import subprocess
import sys
from datetime import datetime


def run_command(cmd, capture_output=True):
    """Run a shell command and return the result"""
    print(f"📍 Running: {cmd}")
    if capture_output:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        if result.stderr and result.returncode != 0:
            print(f"   ⚠️  {result.stderr.strip()}")
        return result
    else:
        return subprocess.run(cmd, shell=True)

def main():
    print("🚀 BoarderframeOS GitHub Force Push")
    print("=" * 50)

    # Show current status
    print("\n📋 Current Status:")
    result = run_command("git branch --show-current")
    current_branch = result.stdout.strip() if result.stdout else "main"
    print(f"📌 Branch: {current_branch}")

    # Add all files
    print("\n1️⃣ Adding all files...")
    run_command("git add -A")

    # Create commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Complete BoarderframeOS update - {timestamp}"

    print(f"\n2️⃣ Creating commit...")
    result = run_command(f'git commit -m "{commit_message}"')

    # Force push
    print(f"\n3️⃣ Force pushing to origin/{current_branch}...")
    result = run_command(f"git push origin {current_branch} --force")

    if result.returncode == 0:
        print("\n✅ Successfully published to GitHub!")
        print(f"🌐 https://github.com/boarderframe/BoarderframeOS")
    else:
        print("\n❌ Push failed! Check your GitHub credentials.")

if __name__ == "__main__":
    main()
