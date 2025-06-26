#!/usr/bin/env python3
"""
Start core BoarderframeOS agents
Quick launcher for Solomon, David, and other essential agents
"""

import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core agents to start
CORE_AGENTS = ["solomon", "david", "adam", "eve", "bezalel"]

def check_agent_file(agent_name):
    """Check if agent implementation exists"""
    agent_path = Path(f"agents/{agent_name}/{agent_name}.py")
    return agent_path.exists()

def start_agent(agent_name):
    """Start a single agent"""
    agent_path = f"agents/{agent_name}/{agent_name}.py"
    
    if not check_agent_file(agent_name):
        print(f"❌ Agent implementation not found: {agent_path}")
        return None
    
    print(f"🚀 Starting {agent_name.title()} agent...")
    
    try:
        # Start the agent process
        process = subprocess.Popen(
            [sys.executable, agent_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )
        
        print(f"✅ {agent_name.title()} started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start {agent_name}: {e}")
        return None

def check_running_agents():
    """Check which agents are currently running"""
    print("\n📊 Checking agent status...")
    
    try:
        # Use ps to find running agent processes
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        running = []
        for agent in CORE_AGENTS:
            if f"agents/{agent}/{agent}.py" in result.stdout:
                running.append(agent)
                print(f"✅ {agent.title()} is running")
            else:
                print(f"❌ {agent.title()} is not running")
        
        return running
    except Exception as e:
        print(f"Error checking processes: {e}")
        return []

def stop_agents():
    """Stop all running agents"""
    print("\n🛑 Stopping agents...")
    
    try:
        for agent in CORE_AGENTS:
            subprocess.run(
                ["pkill", "-f", f"agents/{agent}/{agent}.py"],
                capture_output=True
            )
        print("✅ All agents stopped")
    except Exception as e:
        print(f"Error stopping agents: {e}")

def main():
    """Main launcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage BoarderframeOS core agents")
    parser.add_argument("action", choices=["start", "stop", "status", "restart"],
                        help="Action to perform")
    parser.add_argument("--agents", nargs="+", default=CORE_AGENTS,
                        help="Specific agents to manage")
    
    args = parser.parse_args()
    
    if args.action == "status":
        check_running_agents()
    
    elif args.action == "stop":
        stop_agents()
    
    elif args.action == "start":
        print("🤖 Starting BoarderframeOS Core Agents")
        print("=" * 40)
        
        processes = []
        for agent in args.agents:
            if agent in CORE_AGENTS:
                process = start_agent(agent)
                if process:
                    processes.append((agent, process))
                    time.sleep(2)  # Give each agent time to initialize
            else:
                print(f"⚠️  Unknown agent: {agent}")
        
        print(f"\n✅ Started {len(processes)} agents")
        
        # Check they're still running after a moment
        time.sleep(3)
        check_running_agents()
    
    elif args.action == "restart":
        stop_agents()
        time.sleep(2)
        # Recursive call to start
        sys.argv[1] = "start"
        main()

if __name__ == "__main__":
    main()