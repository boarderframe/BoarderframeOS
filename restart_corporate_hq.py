#!/usr/bin/env python3
"""
Restart Corporate HQ to pick up code changes
"""
import subprocess
import sys
import time
from pathlib import Path

import requests


def kill_corporate_hq():
    """Kill existing Corporate HQ process"""
    print("🔄 Stopping Corporate HQ...")
    try:
        # Find and kill Corporate HQ processes
        result = subprocess.run(
            ["pgrep", "-f", "corporate_headquarters.py"], capture_output=True, text=True
        )

        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                print(f"   Killing PID {pid}")
                subprocess.run(["kill", pid])

            # Wait for processes to die
            time.sleep(2)
            print("✅ Corporate HQ stopped")
            return True
        else:
            print("   No Corporate HQ processes found")
            return True

    except Exception as e:
        print(f"❌ Error stopping Corporate HQ: {e}")
        return False


def start_corporate_hq():
    """Start Corporate HQ"""
    print("🚀 Starting Corporate HQ...")
    try:
        # Get the project directory
        project_dir = Path(__file__).parent

        # Start Corporate HQ as a background process
        process = subprocess.Popen(
            [sys.executable, "corporate_headquarters.py"],
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for startup
        print("   Waiting for Corporate HQ to start...")
        for i in range(15):
            time.sleep(1)
            try:
                response = requests.get("http://localhost:8888", timeout=2)
                if response.status_code == 200:
                    print("✅ Corporate HQ started successfully")
                    return True
            except:
                continue

        print("⚠️ Corporate HQ may not have started correctly")
        return False

    except Exception as e:
        print(f"❌ Error starting Corporate HQ: {e}")
        return False


def test_acc_visibility():
    """Test if ACC is now visible"""
    print("🧪 Testing ACC visibility...")
    try:
        response = requests.get(
            "http://localhost:8888/api/header-status-dropdown", timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            html = data["dropdown_html"]

            if "2/4" in html or "3/4" in html or "4/4" in html:
                print("✅ Core Systems now shows 4 servers!")
                return True
            elif "2/3" in html:
                print("❌ Still showing 2/3 for Core Systems")
                return False
            else:
                print("❓ Core Systems count format changed")
                return False
        else:
            print(f"❌ Dropdown API error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error testing visibility: {e}")
        return False


def main():
    print("🔧 Corporate HQ Restart Utility")
    print("=" * 50)

    # Stop Corporate HQ
    if not kill_corporate_hq():
        return

    # Start Corporate HQ
    if not start_corporate_hq():
        return

    # Test visibility
    test_acc_visibility()

    print("\n💡 Next Steps:")
    print("   1. Go to http://localhost:8888")
    print("   2. Click on 'Servers' tab")
    print("   3. Look for 'Agent Communication Center' card")
    print("   4. Check header dropdown shows correct Core Systems count")


if __name__ == "__main__":
    main()
