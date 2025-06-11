#!/usr/bin/env python3
"""
Development startup script for BoarderframeOS Control Center with hot-reload
"""
import os
import subprocess
import sys


def main():
    print("🚀 Starting BoarderframeOS Control Center in Development Mode")
    print("⚡ Flask hot-reload enabled - file changes will auto-restart")
    print("🔧 Edit boarderframeos_bcc.py to see real-time changes")
    print("🌐 Access: http://localhost:8888")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 60)

    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Run the control center with Flask hot-reload
    try:
        subprocess.run([sys.executable, "boarderframeos_bcc.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
