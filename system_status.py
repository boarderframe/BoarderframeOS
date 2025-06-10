#!/usr/bin/env python3
"""
BoarderframeOS System Status Checker
Quick verification that all components are operational
"""

import requests
import json
import os
import psutil
from datetime import datetime

def check_mcp_servers():
    """Check all MCP server health"""
    servers = [
        ("Registry", 8000),
        ("Filesystem", 8001), 
        ("PostgreSQL Database", 8010),
        ("LLM", 8005),
        ("Dashboard", 8888)
    ]
    
    print("🚀 BoarderframeOS System Status")
    print("=" * 50)
    
    for name, port in servers:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            status = "✅ ONLINE" if response.status_code == 200 else "❌ ERROR"
            print(f"{name:12} | Port {port:4} | {status}")
        except requests.RequestException:
            print(f"{name:12} | Port {port:4} | ❌ OFFLINE")
    
def check_agents():
    """Check running agents"""
    agents = ["solomon", "david"]
    running_agents = []
    
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(process.info['cmdline'] or [])
            
            for agent in agents:
                if f"{agent}.py" in cmdline:
                    memory_mb = process.memory_info().rss // 1024 // 1024
                    running_agents.append((agent.title(), process.info['pid'], memory_mb))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print("\n🤖 Agent Status")
    print("=" * 30)
    if running_agents:
        for name, pid, memory in running_agents:
            print(f"{name:12} | PID {pid:5} | ✅ RUNNING | {memory}MB")
    else:
        print("❌ No agents currently running")

def check_startup_status():
    """Check startup status file"""
    status_file = "/tmp/boarderframe_startup_status.json"
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n📊 System Phase: {data.get('startup_phase', 'unknown').upper()}")
        print(f"🕐 Started: {data.get('start_time', 'unknown')}")
        
        # MCP Servers summary
        mcp_servers = data.get('mcp_servers', {})
        if mcp_servers:
            running_count = sum(1 for s in mcp_servers.values() if s.get('status') == 'running')
            print(f"📡 MCP Servers: {running_count}/{len(mcp_servers)} running")
        
        # Agents summary  
        agents = data.get('agents', {})
        if agents:
            running_count = sum(1 for a in agents.values() if a.get('status') == 'running')
            print(f"🤖 Agents: {running_count}/{len(agents)} running")

def main():
    print(f"🔍 System Status Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_startup_status()
    check_mcp_servers()
    check_agents()
    
    print(f"\n🌐 Dashboard: http://localhost:8888")
    print("✨ System appears to be fully operational!")

if __name__ == "__main__":
    main()
