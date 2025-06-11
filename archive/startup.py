#!/usr/bin/env python3
"""
BoarderframeOS Startup Script
Initializes the complete system with all agents and services
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import httpx

# Add boarderframeos to path
sys.path.insert(0, str(Path(__file__).parent))

import logging

from core.agent_orchestrator import OrchestrationMode, orchestrator
from core.message_bus import message_bus
from utils.logger import setup_logging

logger = logging.getLogger("startup")


class BoarderframeOSStartup:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.services_status = {}
        self.agents_status = {}
        self.startup_sequence = [
            # MCP Servers
            ("mcp_registry", "mcp/registry_server.py", 8000),
            ("mcp_filesystem", "mcp/filesystem_server.py", 8001),
            ("mcp_database", "mcp/database_server.py", 8004),
            ("mcp_llm", "mcp/llm_server.py", 8005),
            # UI Server
            ("ui_server", "../persistent_ui.py", 8888),
        ]
        self.core_agents = ["solomon", "david", "adam", "eve", "bezalel"]

    async def start_boarderframeos(self):
        """Start the complete BoarderframeOS system"""
        print("🚀 Starting BoarderframeOS...")
        print("=" * 60)

        # Setup logging
        setup_logging()

        # Start MCP servers
        print("\n📡 Starting MCP Services...")
        await self.start_mcp_servers()

        # Initialize database
        print("\n💾 Initializing Database...")
        await self.initialize_database()

        # Start UI server
        print("\n🖥️  Starting UI Server...")
        await self.start_ui_server()

        # Initialize orchestrator
        print("\n🎯 Initializing Agent Orchestrator...")
        await orchestrator.initialize()

        # Start core agents
        print("\n🤖 Starting Core Agents...")
        await self.start_core_agents()

        # Run health checks
        print("\n🏥 Running System Health Check...")
        health_status = await self.run_health_checks()

        # Display final status
        self.display_final_status(health_status)

        print("\n✅ BoarderframeOS initialized successfully!")
        print("🎯 Ready to create the first billion-dollar one-person company")
        print("\n📍 Dashboard: http://localhost:8888")
        print("💬 Solomon is ready to chat with you!")

        # Keep the system running
        await self.monitor_system()

    async def start_mcp_servers(self):
        """Start all MCP servers"""
        for service_name, script_path, port in self.startup_sequence[
            :-1
        ]:  # Exclude UI server
            try:
                # Check if already running
                if await self.check_port(port):
                    print(f"  ✅ {service_name} already running on port {port}")
                    self.services_status[service_name] = "running"
                    continue

                # Start the service
                full_path = self.base_dir / script_path
                process = subprocess.Popen(
                    [sys.executable, str(full_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.base_dir),
                )

                # Wait for service to start
                await asyncio.sleep(3)

                # Check if started successfully
                if await self.check_port(port):
                    print(f"  ✅ {service_name} started on port {port}")
                    self.services_status[service_name] = "running"
                else:
                    print(f"  ❌ {service_name} failed to start")
                    self.services_status[service_name] = "failed"

            except Exception as e:
                print(f"  ❌ Error starting {service_name}: {e}")
                self.services_status[service_name] = "error"

    async def start_ui_server(self):
        """Start the UI server"""
        try:
            if await self.check_port(8888):
                print("  ✅ UI server already running on port 8888")
                self.services_status["ui_server"] = "running"
                return

            ui_path = self.base_dir / "../persistent_ui.py"
            process = subprocess.Popen(
                [sys.executable, str(ui_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            await asyncio.sleep(3)

            if await self.check_port(8888):
                print("  ✅ UI server started on port 8888")
                self.services_status["ui_server"] = "running"
            else:
                print("  ❌ UI server failed to start")
                self.services_status["ui_server"] = "failed"

        except Exception as e:
            print(f"  ❌ Error starting UI server: {e}")
            self.services_status["ui_server"] = "error"

    async def initialize_database(self):
        """Initialize database with agent records"""
        try:
            # Create agent records if they don't exist
            async with httpx.AsyncClient() as client:
                for agent_name in self.core_agents:
                    agent_config = self.get_agent_config(agent_name)

                    # Check if agent exists
                    response = await client.post(
                        "http://localhost:8004/query",
                        json={
                            "sql": "SELECT id FROM agents WHERE name = ?",
                            "params": [agent_name.capitalize()],
                        },
                    )

                    if response.status_code == 200 and not response.json().get("data"):
                        # Create agent record
                        await client.post(
                            "http://localhost:8004/insert",
                            json={
                                "table": "agents",
                                "data": {
                                    "id": agent_name,
                                    "name": agent_name.capitalize(),
                                    "config": json.dumps(agent_config),
                                    "biome": agent_config["biome"],
                                    "status": "created",
                                    "generation": 1,
                                    "fitness_score": 0.5,
                                },
                            },
                        )
                        print(f"  ✅ Created database record for {agent_name}")

        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    def get_agent_config(self, agent_name: str) -> Dict:
        """Get configuration for a specific agent"""
        configs = {
            "solomon": {
                "name": "Solomon",
                "role": "Chief of Staff",
                "biome": "council",
                "class_name": "Solomon",
                "module_path": "agents.solomon.solomon",
            },
            "david": {
                "name": "David",
                "role": "CEO",
                "biome": "council",
                "class_name": "David",
                "module_path": "agents.david.david",
            },
            "adam": {
                "name": "Adam",
                "role": "The Builder",
                "biome": "forge",
                "class_name": "Adam",
                "module_path": "agents.primordials.adam",
            },
            "eve": {
                "name": "Eve",
                "role": "The Evolver",
                "biome": "garden",
                "class_name": "Eve",
                "module_path": "agents.primordials.eve",
            },
            "bezalel": {
                "name": "Bezalel",
                "role": "The Coder",
                "biome": "forge",
                "class_name": "Bezalel",
                "module_path": "agents.primordials.bezalel",
            },
        }
        return configs.get(agent_name, {})

    async def start_core_agents(self):
        """Start the core agents in proper order"""
        results = await orchestrator.start_core_agents()

        for agent_name, success in results.items():
            if success:
                print(f"  ✅ {agent_name.capitalize()} agent started")
                self.agents_status[agent_name] = "running"
            else:
                print(f"  ❌ {agent_name.capitalize()} agent failed to start")
                self.agents_status[agent_name] = "failed"

    async def check_port(self, port: int) -> bool:
        """Check if a port is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:{port}/health", timeout=2.0
                )
                return response.status_code == 200
        except:
            return False

    async def run_health_checks(self) -> Dict:
        """Run comprehensive health checks"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "agents": {},
            "overall": "healthy",
        }

        # Check MCP services
        for service_name, _, port in self.startup_sequence:
            health_status["services"][service_name] = await self.check_port(port)

        # Check agent status via orchestrator
        system_status = await orchestrator.get_system_status()
        for agent_id, agent_info in system_status.get("agents", {}).items():
            health_status["agents"][agent_id] = {
                "state": agent_info.get("state", "unknown"),
                "uptime": agent_info.get("uptime_minutes", 0),
            }

        # Determine overall health
        if (
            all(health_status["services"].values())
            and len(health_status["agents"]) >= 3
        ):
            health_status["overall"] = "healthy"
        elif any(health_status["services"].values()):
            health_status["overall"] = "degraded"
        else:
            health_status["overall"] = "critical"

        return health_status

    def display_final_status(self, health_status: Dict):
        """Display final system status"""
        print("\n" + "=" * 60)
        print("📊 System Status Report")
        print("=" * 60)

        print("\n🔧 Services:")
        for service, status in health_status["services"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {service}: {'Online' if status else 'Offline'}")

        print("\n🤖 Agents:")
        for agent, info in health_status["agents"].items():
            state = info.get("state", "unknown")
            status_icon = "✅" if state == "idle" else "⚠️"
            print(f"  {status_icon} {agent}: {state}")

        print(f"\n🏥 Overall Health: {health_status['overall'].upper()}")

    async def monitor_system(self):
        """Keep the system running and monitor health"""
        print("\n🔄 System monitoring active...")
        print("Press Ctrl+C to shutdown BoarderframeOS")

        try:
            while True:
                await asyncio.sleep(60)  # Check every minute

                # Run periodic health check
                health_status = await self.run_health_checks()

                # Log any issues
                if health_status["overall"] != "healthy":
                    logger.warning(f"System health degraded: {health_status}")

        except KeyboardInterrupt:
            print("\n🛑 Shutting down BoarderframeOS...")
            # Graceful shutdown would go here


async def main():
    """Main entry point"""
    startup = BoarderframeOSStartup()
    await startup.start_boarderframeos()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Startup interrupted")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        import traceback

        traceback.print_exc()
