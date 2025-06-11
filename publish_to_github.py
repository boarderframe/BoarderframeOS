#!/usr/bin/env python3
"""
Publish BoarderframeOS to GitHub - Force push local state to remote
This will completely overwrite the remote repository with local changes
"""

import os
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
        if result.stderr:
            print(f"   ⚠️  {result.stderr.strip()}")
        return result
    else:
        return subprocess.run(cmd, shell=True)

def main():
    print("🚀 BoarderframeOS GitHub Publisher")
    print("=" * 50)
    print("⚠️  WARNING: This will COMPLETELY OVERWRITE the remote repository!")
    print("    All remote changes will be lost.")
    print("=" * 50)

    # Confirm action
    response = input("\n❓ Are you sure you want to force push to GitHub? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled by user")
        return

    print("\n📋 Current Status:")
    print("-" * 30)

    # Show current branch
    result = run_command("git branch --show-current")
    current_branch = result.stdout.strip() if result.stdout else "main"
    print(f"📌 Current branch: {current_branch}")

    # Show remote
    run_command("git remote -v | head -1")

    # Count changes
    result = run_command("git status --porcelain | wc -l")
    change_count = result.stdout.strip()
    print(f"📝 Files with changes: {change_count}")

    print("\n🔧 Starting publish process...")
    print("-" * 30)

    # Step 1: Add all files
    print("\n1️⃣ Adding all files to git...")
    run_command("git add -A")

    # Step 2: Create commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Complete BoarderframeOS update - {timestamp}"

    print(f"\n2️⃣ Creating commit: {commit_message}")
    result = run_command(f'git commit -m "{commit_message}"')

    if result.returncode != 0:
        # Check if there's nothing to commit
        status_result = run_command("git status --porcelain")
        if not status_result.stdout:
            print("ℹ️  No changes to commit - working directory clean")
        else:
            print("❌ Commit failed!")
            return

    # Step 3: Force push to remote
    print(f"\n3️⃣ Force pushing to origin/{current_branch}...")
    print("   ⚠️  This will overwrite the remote repository!")

    # Use force-with-lease for slightly safer force push
    result = run_command(f"git push origin {current_branch} --force-with-lease")

    if result.returncode != 0:
        print("\n❌ Force push with lease failed, trying regular force push...")
        result = run_command(f"git push origin {current_branch} --force")

    if result.returncode == 0:
        print("\n✅ Successfully published to GitHub!")
        print(f"🌐 Repository: https://github.com/boarderframe/BoarderframeOS")
        print(f"🔗 Branch: {current_branch}")

        # Show what was pushed
        print("\n📊 Summary:")
        run_command("git log --oneline -1")

    else:
        print("\n❌ Push failed!")
        print("💡 Possible issues:")
        print("   - Check your GitHub credentials")
        print("   - Ensure you have push access to the repository")
        print("   - Try: git remote set-url origin https://github.com/boarderframe/BoarderframeOS.git")

if __name__ == "__main__":
    main()
