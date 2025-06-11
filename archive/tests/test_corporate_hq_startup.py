#!/usr/bin/env python3
"""
Test script to verify Corporate HQ can start properly
"""

import signal
import socket
import subprocess
import sys
import time


def test_corporate_hq():
    """Test starting Corporate HQ directly"""
    print("🧪 Testing Corporate HQ startup...")

    # Start Corporate HQ
    print("🚀 Starting Corporate HQ...")
    process = subprocess.Popen(
        [sys.executable, "corporate_headquarters.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Give it time to start
    print("⏳ Waiting for startup...")
    time.sleep(5)

    # Check if process is still running
    if process.poll() is not None:
        # Process has exited
        stdout, stderr = process.communicate()
        print("❌ Corporate HQ exited prematurely!")
        print(f"Exit code: {process.returncode}")
        if stdout:
            print("STDOUT:")
            print(stdout)
        if stderr:
            print("STDERR:")
            print(stderr)
        return False

    # Check if port 8888 is open
    print("🔍 Checking port 8888...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 8888))
        sock.close()

        if result == 0:
            print("✅ Corporate HQ is running on port 8888!")
            print("🌐 You can access it at: http://localhost:8888")

            # Clean shutdown
            print("\n🛑 Stopping Corporate HQ...")
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
            print("✅ Corporate HQ stopped cleanly")
            return True
        else:
            print("❌ Port 8888 is not responding")
            process.terminate()
            return False

    except Exception as e:
        print(f"❌ Error checking port: {e}")
        process.terminate()
        return False


if __name__ == "__main__":
    if test_corporate_hq():
        print("\n✅ Corporate HQ can start successfully!")
        print("🚀 You can now run: python startup.py")
    else:
        print("\n❌ Corporate HQ failed to start")
        print("🔧 Check the error messages above")
