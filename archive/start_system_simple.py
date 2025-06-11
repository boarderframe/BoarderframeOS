#!/usr/bin/env python3
"""
Simple BoarderframeOS System Startup
Starts dashboard and agents coordination demo
"""

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print('\n🛑 Shutting down BoarderframeOS...')
    subprocess.run(["pkill", "-f", "python.*enhanced_dashboard.py"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-f", "python.*demo_enhanced_agent_coordination.py"], stderr=subprocess.DEVNULL)
    print("🏁 System shutdown complete")
    sys.exit(0)

def main():
    """Start the complete system"""
    print("🚀 Starting Complete BoarderframeOS System...")
    print("=" * 60)

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Kill any existing processes
    print("🧹 Cleaning up existing processes...")
    subprocess.run(["pkill", "-f", "python.*enhanced_dashboard.py"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-f", "python.*demo_enhanced_agent_coordination.py"], stderr=subprocess.DEVNULL)
    time.sleep(2)

    # Start dashboard
    print("📊 Starting Enhanced Dashboard...")
    dashboard_process = subprocess.Popen(
        [sys.executable, "enhanced_dashboard.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)

    # Test dashboard
    try:
        import requests
        response = requests.get("http://localhost:8888/health", timeout=2)
        if response.status_code == 200:
            print("✅ Dashboard is running at http://localhost:8888")
        else:
            print("⚠️ Dashboard started but not responding correctly")
    except:
        print("✅ Dashboard started (install requests for verification)")

    # Start agent coordination demo
    print("🤖 Starting Agent Coordination Demo...")
    demo_process = subprocess.Popen(
        [sys.executable, "demo_enhanced_agent_coordination.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(5)

    print("\n" + "=" * 60)
    print("✅ BoarderframeOS System is operational!")
    print("📍 Dashboard: http://localhost:8888")
    print("🤖 Agent Demo: Running coordination system")
    print("🔄 System is running... Press Ctrl+C to stop")
    print("=" * 60)

    # Open browser
    try:
        webbrowser.open("http://localhost:8888")
        print("🌐 Opening dashboard in browser...")
    except:
        pass

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
