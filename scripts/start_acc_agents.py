#!/usr/bin/env python3
"""
Start ACC-enabled agents
These agents connect to ACC via WebSocket for real-time chat
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Agent configurations
ACC_AGENTS = {
    "solomon": "agents/solomon/solomon_acc.py",
    "david": "agents/david/david_acc.py"
}

# Track running processes
running_processes = {}


def start_agent(name, script_path):
    """Start an ACC-enabled agent"""
    print(f"🚀 Starting {name} (ACC-enabled)...")
    
    # Get absolute paths
    project_root = Path(__file__).parent.parent
    full_path = project_root / script_path
    
    if not full_path.exists():
        print(f"❌ Agent script not found: {full_path}")
        return None
        
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # Start the agent
    try:
        process = subprocess.Popen(
            [sys.executable, str(full_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            env=env,
            start_new_session=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if still running
        if process.poll() is None:
            print(f"✅ {name} started with PID {process.pid}")
            return process
        else:
            # Read error output
            stderr = process.stderr.read().decode('utf-8')
            print(f"❌ {name} failed to start")
            if stderr:
                print(f"   Error: {stderr[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None


def stop_agent(name, process):
    """Stop an agent gracefully"""
    if process and process.poll() is None:
        print(f"🛑 Stopping {name} (PID {process.pid})...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print(f"✅ {name} stopped")
        except subprocess.TimeoutExpired:
            print(f"⚠️  {name} didn't stop gracefully, forcing...")
            process.kill()
            process.wait()
            print(f"✅ {name} force stopped")
    else:
        print(f"ℹ️  {name} is not running")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down agents...")
    for name, process in running_processes.items():
        stop_agent(name, process)
    sys.exit(0)


def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🤖 BoarderframeOS ACC-Enabled Agent Manager")
    print("=" * 50)
    print("These agents connect to ACC via WebSocket for chat")
    print("=" * 50)
    
    # Check if ACC is running
    print("\n🔍 Checking ACC status...")
    try:
        import httpx
        response = httpx.get("http://localhost:8890/health", timeout=2)
        if response.status_code == 200:
            print("✅ ACC is running")
        else:
            print("⚠️  ACC responded but may not be healthy")
    except Exception:
        print("❌ ACC is not running! Please start it first:")
        print("   python agent_communication_center_enhanced.py")
        return
    
    # Start agents
    print("\n🚀 Starting ACC-enabled agents...")
    
    for name, script in ACC_AGENTS.items():
        process = start_agent(name, script)
        if process:
            running_processes[name] = process
            
    if not running_processes:
        print("\n❌ No agents started successfully")
        return
        
    print(f"\n✅ Started {len(running_processes)} agents")
    print("\n📝 Instructions:")
    print("1. Open http://localhost:8890 in your browser")
    print("2. You can now chat with Solomon and David!")
    print("3. Press Ctrl+C to stop all agents")
    
    # Keep running
    print("\n⏳ Agents are running. Press Ctrl+C to stop...")
    try:
        while True:
            # Check if agents are still running
            for name, process in list(running_processes.items()):
                if process.poll() is not None:
                    print(f"\n⚠️  {name} has stopped unexpectedly")
                    del running_processes[name]
                    
            # If no agents left, exit
            if not running_processes:
                print("\n❌ All agents have stopped")
                break
                
            time.sleep(5)
            
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()