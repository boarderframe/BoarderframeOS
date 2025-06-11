#!/usr/bin/env python3
"""
Simple script to start BoarderframeOS dashboard
"""
import signal
import subprocess
import sys
import time
import webbrowser


def signal_handler(sig, frame):
    print('\n🛑 Stopping BoarderframeOS...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("🚀 Starting BoarderframeOS Enhanced Dashboard...")
print("=" * 60)

# Kill any existing processes on port 8888
subprocess.run(["pkill", "-f", "python.*8888"], stderr=subprocess.DEVNULL)
time.sleep(2)

# Start the enhanced dashboard
print("📊 Starting Enhanced Dashboard on http://localhost:8888")
dashboard_process = subprocess.Popen(
    [sys.executable, "/Users/cosburn/BoarderframeOS/enhanced_dashboard.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Give it time to start
time.sleep(3)

# Check if it started
try:
    import requests
    response = requests.get("http://localhost:8888/health", timeout=2)
    if response.status_code == 200:
        print("✅ Dashboard is running!")
        print("🌐 Opening browser...")
        webbrowser.open("http://localhost:8888")
    else:
        print("⚠️  Dashboard started but not responding correctly")
except:
    print("✅ Dashboard started (install requests for automatic verification)")
    print("📍 Open http://localhost:8888 in your browser")

print("\n" + "=" * 60)
print("📍 Dashboard: http://localhost:8888")
print("🏥 Health Check: python /Users/cosburn/BoarderframeOS/boarderframeos/health_check.py")
print("🚀 Full System: python /Users/cosburn/BoarderframeOS/boarderframeos/startup.py")
print("\nPress Ctrl+C to stop")
print("=" * 60)

# Keep running
try:
    dashboard_process.wait()
except KeyboardInterrupt:
    print("\n🛑 Stopping dashboard...")
    dashboard_process.terminate()
