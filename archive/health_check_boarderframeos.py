#!/usr/bin/env python3
"""
BoarderframeOS Health Check and Communication Test System
Tests all components and agent communication
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class HealthChecker:
    def __init__(self):
        self.services = {
            "MCP Registry": ("http://localhost:8000/health", 8000),
            "Filesystem Server": ("http://localhost:8001/health", 8001),
            "Database Server": ("http://localhost:8004/health", 8004),
            "LLM Server": ("http://localhost:8005/health", 8005),
            "UI Dashboard": ("http://localhost:8888/health", 8888),
        }

        self.test_results = {
            "services": {},
            "agents": {},
            "communication": {},
            "database": {},
            "overall": "unknown"
        }

    async def run_full_health_check(self):
        """Run comprehensive health check"""
        print(f"\n{Colors.BOLD}🏥 BoarderframeOS Health Check{Colors.END}")
        print("=" * 60)

        # Test MCP services
        await self.test_mcp_services()

        # Test database connectivity
        await self.test_database()

        # Test agent status
        await self.test_agents()

        # Test agent communication
        await self.test_agent_communication()

        # Calculate overall health
        self.calculate_overall_health()

        # Display summary
        self.display_summary()

        return self.test_results

    async def test_mcp_services(self):
        """Test all MCP services"""
        print(f"\n{Colors.BLUE}📡 Testing MCP Services...{Colors.END}")

        async with httpx.AsyncClient(timeout=3.0) as client:
            for service_name, (url, port) in self.services.items():
                try:
                    start_time = time.time()
                    response = await client.get(url)
                    response_time = (time.time() - start_time) * 1000

                    if response.status_code == 200:
                        self.test_results["services"][service_name] = {
                            "status": "healthy",
                            "response_time_ms": round(response_time, 2),
                            "port": port
                        }
                        print(f"  {Colors.GREEN}✓{Colors.END} {service_name}: Online ({response_time:.0f}ms)")
                    else:
                        self.test_results["services"][service_name] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status_code}",
                            "port": port
                        }
                        print(f"  {Colors.RED}✗{Colors.END} {service_name}: Unhealthy (HTTP {response.status_code})")

                except Exception as e:
                    self.test_results["services"][service_name] = {
                        "status": "offline",
                        "error": str(e),
                        "port": port
                    }
                    print(f"  {Colors.RED}✗{Colors.END} {service_name}: Offline")

    async def test_database(self):
        """Test database connectivity and basic operations"""
        print(f"\n{Colors.BLUE}💾 Testing Database...{Colors.END}")

        try:
            async with httpx.AsyncClient() as client:
                # Test query
                response = await client.post("http://localhost:8004/query", json={
                    "sql": "SELECT COUNT(*) as count FROM agents",
                    "fetch_all": True
                })

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        agent_count = data["data"][0]["count"] if data.get("data") else 0
                        self.test_results["database"] = {
                            "status": "healthy",
                            "agent_count": agent_count
                        }
                        print(f"  {Colors.GREEN}✓{Colors.END} Database: Connected ({agent_count} agents)")
                    else:
                        self.test_results["database"] = {"status": "error", "error": "Query failed"}
                        print(f"  {Colors.RED}✗{Colors.END} Database: Query failed")
                else:
                    self.test_results["database"] = {"status": "offline"}
                    print(f"  {Colors.RED}✗{Colors.END} Database: Offline")

        except Exception as e:
            self.test_results["database"] = {"status": "offline", "error": str(e)}
            print(f"  {Colors.RED}✗{Colors.END} Database: Connection failed")

    async def test_agents(self):
        """Test agent status via orchestrator"""
        print(f"\n{Colors.BLUE}🤖 Testing Agents...{Colors.END}")

        try:
            # Get agent status from database
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8004/query", json={
                    "sql": "SELECT id, name, status, biome FROM agents WHERE status = 'active'",
                    "fetch_all": True
                })

                if response.status_code == 200 and response.json().get("success"):
                    agents = response.json().get("data", [])

                    for agent in agents:
                        agent_id = agent["id"]
                        agent_name = agent["name"]
                        status = agent["status"]

                        self.test_results["agents"][agent_id] = {
                            "name": agent_name,
                            "status": status,
                            "biome": agent["biome"]
                        }

                        status_icon = Colors.GREEN + "✓" + Colors.END if status == "active" else Colors.YELLOW + "⚠" + Colors.END
                        print(f"  {status_icon} {agent_name}: {status}")
                else:
                    print(f"  {Colors.YELLOW}⚠{Colors.END} Could not retrieve agent status")

        except Exception as e:
            print(f"  {Colors.RED}✗{Colors.END} Agent test failed: {e}")

    async def test_agent_communication(self):
        """Test agent communication channels"""
        print(f"\n{Colors.BLUE}💬 Testing Agent Communication...{Colors.END}")

        # Test Solomon communication
        await self.test_solomon_chat()

        # Test inter-agent messaging
        await self.test_message_bus()

    async def test_solomon_chat(self):
        """Test Solomon chat functionality"""
        try:
            async with httpx.AsyncClient() as client:
                # Send test message to Solomon
                test_message = "System health check - please respond"

                response = await client.post("http://localhost:8080/api/solomon/message", json={
                    "message": test_message,
                    "session_id": "health_check"
                })

                if response.status_code == 200:
                    self.test_results["communication"]["solomon_chat"] = {
                        "status": "functional",
                        "test": "passed"
                    }
                    print(f"  {Colors.GREEN}✓{Colors.END} Solomon Chat: Functional")
                else:
                    self.test_results["communication"]["solomon_chat"] = {
                        "status": "error",
                        "test": "failed"
                    }
                    print(f"  {Colors.RED}✗{Colors.END} Solomon Chat: Not responding")

        except Exception as e:
            self.test_results["communication"]["solomon_chat"] = {
                "status": "offline",
                "error": str(e)
            }
            print(f"  {Colors.YELLOW}⚠{Colors.END} Solomon Chat: Offline (normal if agents not started)")

    async def test_message_bus(self):
        """Test message bus functionality"""
        # This would test the actual message bus if it's running
        print(f"  {Colors.YELLOW}⚠{Colors.END} Message Bus: Test pending (requires running agents)")
        self.test_results["communication"]["message_bus"] = {
            "status": "pending",
            "note": "Requires active agents"
        }

    def calculate_overall_health(self):
        """Calculate overall system health"""
        # Count healthy services
        healthy_services = sum(1 for s in self.test_results["services"].values()
                             if s.get("status") == "healthy")
        total_services = len(self.test_results["services"])

        # Check critical services
        critical_services = ["Database Server", "UI Dashboard"]
        critical_healthy = all(
            self.test_results["services"].get(s, {}).get("status") == "healthy"
            for s in critical_services
        )

        # Determine overall health
        if healthy_services == total_services:
            self.test_results["overall"] = "healthy"
        elif critical_healthy and healthy_services >= total_services * 0.6:
            self.test_results["overall"] = "degraded"
        else:
            self.test_results["overall"] = "critical"

    def display_summary(self):
        """Display health check summary"""
        print(f"\n{Colors.BOLD}📊 Health Check Summary{Colors.END}")
        print("=" * 60)

        # Service summary
        healthy = sum(1 for s in self.test_results["services"].values()
                     if s.get("status") == "healthy")
        total = len(self.test_results["services"])

        print(f"\nServices: {healthy}/{total} healthy")

        # Agent summary
        if self.test_results["agents"]:
            active_agents = sum(1 for a in self.test_results["agents"].values()
                              if a.get("status") == "active")
            print(f"Agents: {active_agents} active")
        else:
            print("Agents: Not deployed")

        # Overall status
        overall = self.test_results["overall"]
        if overall == "healthy":
            status_text = f"{Colors.GREEN}✓ HEALTHY{Colors.END}"
        elif overall == "degraded":
            status_text = f"{Colors.YELLOW}⚠ DEGRADED{Colors.END}"
        else:
            status_text = f"{Colors.RED}✗ CRITICAL{Colors.END}"

        print(f"\nOverall System Health: {status_text}")

        # Recommendations
        if overall != "healthy":
            print(f"\n{Colors.YELLOW}Recommendations:{Colors.END}")

            offline_services = [name for name, status in self.test_results["services"].items()
                              if status.get("status") == "offline"]

            if offline_services:
                print(f"  • Start offline services: {', '.join(offline_services)}")

            if not self.test_results["agents"]:
                print("  • Run startup.py to deploy agents")

    async def continuous_monitoring(self, interval: int = 30):
        """Run continuous health monitoring"""
        print(f"\n{Colors.BOLD}🔄 Starting continuous monitoring (every {interval}s){Colors.END}")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                await self.run_full_health_check()

                # Write results to file for dashboard
                await self.write_health_status()

                print(f"\n⏰ Next check in {interval} seconds...")
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Monitoring stopped{Colors.END}")

    async def write_health_status(self):
        """Write health status to file for dashboard"""
        try:
            status_file = Path("/tmp/boarderframe_health.json")
            with open(status_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "results": self.test_results
                }, f, indent=2)
        except Exception as e:
            print(f"Could not write health status file: {e}")

async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="BoarderframeOS Health Check")
    parser.add_argument("--continuous", "-c", action="store_true",
                       help="Run continuous monitoring")
    parser.add_argument("--interval", "-i", type=int, default=30,
                       help="Monitoring interval in seconds (default: 30)")

    args = parser.parse_args()

    checker = HealthChecker()

    if args.continuous:
        await checker.continuous_monitoring(args.interval)
    else:
        await checker.run_full_health_check()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Health check interrupted")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        import traceback
        traceback.print_exc()
