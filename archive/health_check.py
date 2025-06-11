#!/usr/bin/env python3
"""
BoarderframeOS System Health Check
Quick verification that all components are running
"""

import subprocess
import sys
from pathlib import Path

import psutil
import requests


def check_dashboard():
    """Check if dashboard is running"""
    try:
        response = requests.get("http://localhost:8888/health", timeout=2)
        if response.status_code == 200:
            print("✅ Dashboard: Running on port 8888")
            return True
        else:
            print(f"⚠️ Dashboard: Unexpected response {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard: Not running on port 8888")
        return False
    except Exception as e:
        print(f"❌ Dashboard: Error {e}")
        return False

def check_agents():
    """Check for running agent processes"""
    running_agents = []

    try:
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(process.info['cmdline'] or [])

                if 'solomon.py' in cmdline:
                    running_agents.append(f"Solomon (PID: {process.info['pid']})")
                elif 'david.py' in cmdline:
                    running_agents.append(f"David (PID: {process.info['pid']})")
                elif 'analyst_agent.py' in cmdline:
                    running_agents.append(f"Analyst (PID: {process.info['pid']})")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    except ImportError:
        print("⚠️ psutil not available for process checking")
        return []

    if running_agents:
        print("✅ Agents: " + ", ".join(running_agents))
    else:
        print("❌ Agents: No agent processes found")

    return running_agents

def main():
    """Run health check"""
    print("🏥 BoarderframeOS Health Check")
    print("=" * 40)

    dashboard_ok = check_dashboard()
    agents = check_agents()

    print("\n" + "=" * 40)
    if dashboard_ok and agents:
        print("✅ System Status: All components operational!")
        print("📍 Dashboard: http://localhost:8888")
    elif dashboard_ok:
        print("⚠️ System Status: Dashboard running, agents may need restart")
    else:
        print("❌ System Status: Issues detected")

    print("\n💡 To start the complete system: python start_system_simple.py")

if __name__ == "__main__":
    main()
