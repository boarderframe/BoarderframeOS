#!/usr/bin/env python3
"""
Agent Startup Script for BoarderframeOS
Manages starting, stopping, and monitoring AI agents
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import psutil

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class AgentManager:
    """Manages BoarderframeOS agents"""

    def __init__(self):
        self.project_root = project_root
        self.agents_dir = self.project_root / "agents"
        self.running_agents: Dict[str, subprocess.Popen] = {}
        self.agent_configs = {
            "solomon": {
                "path": "agents/solomon/solomon.py",
                "description": "Chief of Staff AI - Business intelligence and strategic planning",
                "model": "claude-3-5-sonnet-latest",
                "priority": 1
            },
            "david": {
                "path": "agents/david/david.py",
                "description": "CEO Agent - Strategic leadership and organizational management",
                "model": "claude-3-5-sonnet-latest",
                "priority": 2
            }

            # Commented out agents - still available in the system but won't auto-start
            # "eve": {
            #     "path": "agents/primordials/eve.py",
            #     "description": "Primordial Agent - System evolution and adaptation",
            #     "model": "claude-3-5-sonnet-latest",
            #     "priority": 3
            # },
            # "adam": {
            #     "path": "agents/primordials/adam.py",
            #     "description": "Creator Agent - Agent creation and management",
            #     "model": "claude-3-5-sonnet-latest",
            #     "priority": 4
            # },
            # "bezalel": {
            #     "path": "agents/primordials/bezalel.py",
            #     "description": "Coder Agent - Application development",
            #     "model": "claude-3-5-sonnet-latest",
            #     "priority": 5
            # }
        }

    def is_agent_running(self, agent_name: str) -> bool:
        """Check if an agent process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any(f"{agent_name}.py" in arg for arg in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return False

    def get_agent_pid(self, agent_name: str) -> Optional[int]:
        """Get PID of running agent"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any(f"{agent_name}.py" in arg for arg in cmdline):
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None

    def start_agent(self, agent_name: str) -> bool:
        """Start a specific agent"""
        if agent_name not in self.agent_configs:
            print(f"❌ Unknown agent: {agent_name}")
            return False

        if self.is_agent_running(agent_name):
            print(f"⚠️  Agent {agent_name} is already running")
            return True

        config = self.agent_configs[agent_name]
        agent_path = self.project_root / config["path"]

        if not agent_path.exists():
            print(f"❌ Agent file not found: {agent_path}")
            return False

        try:
            print(f"🚀 Starting {agent_name} agent...")
            print(f"   Model: {config['model']}")
            print(f"   Description: {config['description']}")

            # Start agent in background
            process = subprocess.Popen(
                [sys.executable, str(agent_path)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )

            # Give it a moment to start
            time.sleep(2)

            # Check if it's actually running
            if self.is_agent_running(agent_name):
                print(f"✅ {agent_name} agent started successfully")
                self.running_agents[agent_name] = process
                return True
            else:
                print(f"❌ Failed to start {agent_name} agent")
                return False

        except Exception as e:
            print(f"❌ Error starting {agent_name}: {e}")
            return False

    def stop_agent(self, agent_name: str) -> bool:
        """Stop a specific agent"""
        pid = self.get_agent_pid(agent_name)
        if not pid:
            print(f"⚠️  Agent {agent_name} is not running")
            return True

        try:
            print(f"🛑 Stopping {agent_name} agent (PID: {pid})...")

            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)
            time.sleep(3)

            # Check if it stopped
            if not self.is_agent_running(agent_name):
                print(f"✅ {agent_name} agent stopped successfully")
                if agent_name in self.running_agents:
                    del self.running_agents[agent_name]
                return True

            # Force kill if necessary
            print(f"⚠️  Force killing {agent_name} agent...")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)

            if not self.is_agent_running(agent_name):
                print(f"✅ {agent_name} agent force stopped")
                if agent_name in self.running_agents:
                    del self.running_agents[agent_name]
                return True
            else:
                print(f"❌ Failed to stop {agent_name} agent")
                return False

        except Exception as e:
            print(f"❌ Error stopping {agent_name}: {e}")
            return False

    def start_all_agents(self) -> None:
        """Start all agents in priority order"""
        print("🚀 Starting all BoarderframeOS agents...")
        print("=" * 50)

        # Sort by priority
        sorted_agents = sorted(
            self.agent_configs.items(),
            key=lambda x: x[1]['priority']
        )

        for agent_name, config in sorted_agents:
            self.start_agent(agent_name)
            time.sleep(1)  # Stagger starts

        print("\n📊 Agent Status Summary:")
        self.show_status()

    def stop_all_agents(self) -> None:
        """Stop all running agents"""
        print("🛑 Stopping all BoarderframeOS agents...")
        print("=" * 50)

        for agent_name in self.agent_configs.keys():
            if self.is_agent_running(agent_name):
                self.stop_agent(agent_name)

        print("✅ All agents stopped")

    def restart_agent(self, agent_name: str) -> bool:
        """Restart a specific agent"""
        print(f"🔄 Restarting {agent_name} agent...")
        self.stop_agent(agent_name)
        time.sleep(2)
        return self.start_agent(agent_name)

    def show_status(self) -> None:
        """Show status of all agents"""
        print("\n📊 BoarderframeOS Agent Status:")
        print("=" * 50)

        for agent_name, config in self.agent_configs.items():
            is_running = self.is_agent_running(agent_name)
            pid = self.get_agent_pid(agent_name) if is_running else None
            status = "🟢 RUNNING" if is_running else "🔴 STOPPED"
            pid_info = f" (PID: {pid})" if pid else ""

            print(f"{status} {agent_name.upper()}{pid_info}")
            print(f"   Model: {config['model']}")
            print(f"   Description: {config['description']}")
            print()

    def get_status_json(self) -> str:
        """Get agent status as JSON for dashboard"""
        status = {}
        for agent_name, config in self.agent_configs.items():
            is_running = self.is_agent_running(agent_name)
            pid = self.get_agent_pid(agent_name) if is_running else None

            status[agent_name] = {
                "running": is_running,
                "pid": pid,
                "model": config["model"],
                "description": config["description"],
                "priority": config["priority"]
            }

        return json.dumps(status, indent=2)

def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="BoarderframeOS Agent Manager")
    parser.add_argument("action", choices=[
        "start", "stop", "restart", "status", "start-all", "stop-all", "json"
    ], help="Action to perform")
    parser.add_argument("--agent", help="Specific agent name (solomon, david, eve)")

    args = parser.parse_args()
    manager = AgentManager()

    if args.action == "start":
        if args.agent:
            manager.start_agent(args.agent)
        else:
            print("❌ Please specify --agent for start action")

    elif args.action == "stop":
        if args.agent:
            manager.stop_agent(args.agent)
        else:
            print("❌ Please specify --agent for stop action")

    elif args.action == "restart":
        if args.agent:
            manager.restart_agent(args.agent)
        else:
            print("❌ Please specify --agent for restart action")

    elif args.action == "start-all":
        manager.start_all_agents()

    elif args.action == "stop-all":
        manager.stop_all_agents()

    elif args.action == "status":
        manager.show_status()

    elif args.action == "json":
        print(manager.get_status_json())

if __name__ == "__main__":
    main()
