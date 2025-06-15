#!/usr/bin/env python3
"""
Diagnose Agent Cortex startup issues
"""

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def check_port(port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        return result == 0
    except:
        return False


def check_dependencies():
    """Check if all dependencies are available"""
    print("🔍 Checking dependencies...")
    deps = ["litellm", "qdrant_client", "flask"]
    missing = []

    for dep in deps:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep}")
            missing.append(dep)

    return len(missing) == 0


async def test_startup_sequence():
    """Test the exact startup sequence from startup.py"""
    print("\n🧪 Testing startup sequence...")

    # Kill any existing processes
    print("  ⏳ Killing existing processes...")
    subprocess.run(["pkill", "-f", "agent_cortex"], capture_output=True)
    time.sleep(2)

    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent)
    env["BOARDERFRAME_STARTUP"] = "1"
    env["FLASK_DEBUG"] = "0"

    # Try to start Agent Cortex UI
    print("  ⏳ Starting Agent Cortex UI...")

    # Use the exact command from startup.py
    process = subprocess.Popen(
        [sys.executable, "ui/agent_cortex_simple_launcher.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).parent),
        env=env,
        start_new_session=True,
        close_fds=True,
    )

    print(f"  ℹ️  Process started with PID: {process.pid}")

    # Monitor startup
    start_time = time.time()
    max_wait = 30  # seconds
    check_interval = 0.5

    while time.time() - start_time < max_wait:
        # Check if process died
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"  ❌ Process died with exit code: {process.returncode}")
            print(f"  📋 STDOUT: {stdout.decode()[:500]}")
            print(f"  📋 STDERR: {stderr.decode()[:500]}")
            return False

        # Check if port is open
        if check_port(8889):
            print(
                f"  ✅ Agent Cortex UI started successfully after {time.time() - start_time:.1f}s"
            )

            # Test the API
            try:
                import requests

                response = requests.get(
                    "http://localhost:8889/api/agent-cortex/status", timeout=5
                )
                if response.status_code == 200:
                    print("  ✅ API is responding correctly")
                else:
                    print(f"  ⚠️  API returned status {response.status_code}")
            except Exception as e:
                print(f"  ❌ API test failed: {e}")

            # Let it run for a bit
            time.sleep(5)

            # Clean up
            process.terminate()
            process.wait()
            return True

        await asyncio.sleep(check_interval)

    print(f"  ❌ Timeout after {max_wait}s - port 8889 never opened")

    # Check if process is still running
    if process.poll() is None:
        print("  ℹ️  Process is still running but not responding on port")
        process.terminate()
        process.wait()

    return False


def check_manual_start():
    """Test manual start method"""
    print("\n🧪 Testing manual start...")

    # Kill any existing processes
    subprocess.run(["pkill", "-f", "agent_cortex"], capture_output=True)
    time.sleep(2)

    # Try manual start
    process = subprocess.Popen(
        ["python", "ui/agent_cortex_simple_launcher.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    time.sleep(5)

    if check_port(8889):
        print("  ✅ Manual start works")
        process.terminate()
        process.wait()
        return True
    else:
        print("  ❌ Manual start failed")
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"  📋 Error: {stderr.decode()[:500]}")
        process.terminate()
        process.wait()
        return False


async def main():
    """Run all diagnostics"""
    print("🔧 Agent Cortex Startup Diagnostics")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies - install required packages first")
        return

    # Test startup sequence
    startup_works = await test_startup_sequence()

    # Test manual start
    manual_works = check_manual_start()

    # Summary
    print("\n📊 Summary")
    print("=" * 50)
    print(f"Dependencies: ✅ All present")
    print(f"Startup sequence: {'✅ Works' if startup_works else '❌ Fails'}")
    print(f"Manual start: {'✅ Works' if manual_works else '❌ Fails'}")

    if not startup_works:
        print("\n💡 Recommendations:")
        print("1. Check if there are any Flask/Werkzeug conflicts")
        print("2. Ensure all paths are correct")
        print("3. Check for any async/subprocess conflicts")
        print("4. Review the simple launcher for any issues")


if __name__ == "__main__":
    asyncio.run(main())
