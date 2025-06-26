#!/usr/bin/env python3
"""
Comprehensive Server Health Checker for BoarderframeOS
Checks all documented servers and provides real-time health status
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import psutil

logger = logging.getLogger(__name__)


class ServerHealthChecker:
    """Comprehensive health checker for all BoarderframeOS servers"""

    # Complete list of all BoarderframeOS servers
    SERVERS = {
        # Core Infrastructure (4 servers)
        "corporate_headquarters": {
            "port": 8888,
            "name": "Corporate Headquarters",
            "category": "Core",
            "health_endpoint": "/health",
            "icon": "fa-building",
        },
        "agent_cortex": {
            "port": 8889,
            "name": "Agent Cortex",
            "category": "Core",
            "health_endpoint": "/health",
            "icon": "fa-brain",
        },
        "agent_communication_center": {
            "port": 8890,
            "name": "Agent Communication Center",
            "category": "Core",
            "health_endpoint": "/health",
            "icon": "fa-comments",
        },
        "registry": {
            "port": 8000,
            "name": "Registry Server",
            "category": "Core",
            "health_endpoint": "/health",
            "icon": "fa-network-wired",
        },
        # MCP Servers (5 servers)
        "filesystem": {
            "port": 8001,
            "name": "Filesystem Server",
            "category": "MCP",
            "health_endpoint": "/health",
            "icon": "fa-folder-open",
        },
        "database_postgres": {
            "port": 8010,
            "name": "PostgreSQL Database",
            "category": "MCP",
            "health_endpoint": "/health",
            "icon": "fa-database",
        },
        "database_sqlite": {
            "port": 8004,
            "name": "SQLite Database",
            "category": "MCP",
            "health_endpoint": "/health",
            "icon": "fa-database",
        },
        "llm": {
            "port": 8005,
            "name": "LLM Server",
            "category": "MCP",
            "health_endpoint": "/health",
            "icon": "fa-robot",
        },
        "screenshot": {
            "port": 8011,
            "name": "Screenshot Server",
            "category": "MCP",
            "health_endpoint": "/health",
            "icon": "fa-camera",
        },
        # Business Services (3 servers)
        "analytics": {
            "port": 8007,
            "name": "Analytics Server",
            "category": "Business",
            "health_endpoint": "/health",
            "icon": "fa-chart-line",
        },
        "payment": {
            "port": 8006,
            "name": "Payment Server",
            "category": "Business",
            "health_endpoint": "/health",
            "icon": "fa-credit-card",
        },
        "customer": {
            "port": 8008,
            "name": "Customer Server",
            "category": "Business",
            "health_endpoint": "/health",
            "icon": "fa-users",
        },
    }

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
        self._last_check_time = None
        self._last_results = {}

    async def check_server_health(
        self, server_id: str, server_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check health of a single server"""
        port = server_info["port"]
        endpoint = server_info.get("health_endpoint", "/health")

        start_time = asyncio.get_event_loop().time()

        try:
            # Direct HTTP health check (don't rely on port check as it may be inaccurate)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"http://localhost:{port}{endpoint}"
                response = await client.get(url)

                response_time = asyncio.get_event_loop().time() - start_time

                if response.status_code == 200:
                    # Try to parse JSON response
                    try:
                        health_data = response.json()
                        status = health_data.get("status", "healthy")
                    except:
                        status = "healthy"

                    return {
                        "status": status,
                        "port": port,
                        "response_time": response_time,
                        "category": server_info["category"],
                        "name": server_info["name"],
                        "icon": server_info["icon"],
                        "last_check": datetime.now().isoformat(),
                        "details": health_data if "health_data" in locals() else {},
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "port": port,
                        "response_time": response_time,
                        "error": f"HTTP {response.status_code}",
                        "category": server_info["category"],
                        "name": server_info["name"],
                        "icon": server_info["icon"],
                        "last_check": datetime.now().isoformat(),
                    }

        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "port": port,
                "response_time": self.timeout,
                "error": "Request timeout",
                "category": server_info["category"],
                "name": server_info["name"],
                "icon": server_info["icon"],
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "port": port,
                "response_time": 0,
                "error": str(e)[:100],
                "category": server_info["category"],
                "name": server_info["name"],
                "icon": server_info["icon"],
                "last_check": datetime.now().isoformat(),
            }

    def _is_port_open(self, port: int) -> bool:
        """Check if a port is open using psutil"""
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.laddr.port == port and conn.status == "LISTEN":
                    return True
            return False
        except:
            return False

    async def check_all_servers(self) -> Dict[str, Any]:
        """Check health of all servers"""
        self._last_check_time = datetime.now()

        # Run all health checks concurrently
        tasks = []
        for server_id, server_info in self.SERVERS.items():
            task = self.check_server_health(server_id, server_info)
            tasks.append((server_id, task))

        results = {}
        for server_id, task in tasks:
            try:
                results[server_id] = await task
            except Exception as e:
                logger.error(f"Error checking {server_id}: {e}")
                results[server_id] = {
                    "status": "error",
                    "error": str(e)[:100],
                    "port": self.SERVERS[server_id]["port"],
                    "category": self.SERVERS[server_id]["category"],
                    "name": self.SERVERS[server_id]["name"],
                    "icon": self.SERVERS[server_id]["icon"],
                    "last_check": datetime.now().isoformat(),
                }

        self._last_results = results

        # Calculate summary statistics
        total_servers = len(results)
        healthy_servers = sum(1 for r in results.values() if r["status"] == "healthy")
        offline_servers = sum(1 for r in results.values() if r["status"] == "offline")
        error_servers = sum(
            1
            for r in results.values()
            if r["status"] in ["error", "unhealthy", "timeout"]
        )

        # Group by category
        categories = {}
        for server_id, result in results.items():
            category = result.get("category", "Unknown")
            if category not in categories:
                categories[category] = {"healthy": 0, "total": 0, "servers": []}
            categories[category]["total"] += 1
            if result["status"] == "healthy":
                categories[category]["healthy"] += 1
            categories[category]["servers"].append(
                {
                    "id": server_id,
                    "name": result["name"],
                    "status": result["status"],
                    "port": result["port"],
                }
            )

        return {
            "timestamp": self._last_check_time.isoformat(),
            "summary": {
                "total": total_servers,
                "healthy": healthy_servers,
                "offline": offline_servers,
                "errors": error_servers,
                "health_percentage": round((healthy_servers / total_servers) * 100, 1)
                if total_servers > 0
                else 0,
            },
            "categories": categories,
            "servers": results,
        }

    def get_cached_results(self) -> Optional[Dict[str, Any]]:
        """Get last cached results if available"""
        if self._last_results:
            return {
                "timestamp": self._last_check_time.isoformat()
                if self._last_check_time
                else None,
                "servers": self._last_results,
                "cached": True,
            }
        return None

    async def update_system_status_file(self, results: Dict[str, Any]):
        """Update the system_status.json file with real server health"""
        status_file = Path(__file__).parent.parent / "data" / "system_status.json"

        try:
            # Read existing status
            if status_file.exists():
                with open(status_file, "r") as f:
                    system_status = json.load(f)
            else:
                system_status = {}

            # Update services_status section
            if "services_status" not in system_status:
                system_status["services_status"] = {}

            # Update each server's status
            for server_id, server_data in results["servers"].items():
                system_status["services_status"][server_id] = {
                    "status": server_data["status"],
                    "port": server_data["port"],
                    "response_time": server_data.get("response_time", 0),
                    "last_check": server_data["last_check"],
                    "category": server_data["category"],
                    "name": server_data["name"],
                    "icon": server_data["icon"],
                    "error": server_data.get("error", None),
                }

            # Update global health metrics
            system_status["health_metrics"] = {
                "servers": results["summary"],
                "last_update": datetime.now().isoformat(),
            }

            # Write back
            with open(status_file, "w") as f:
                json.dump(system_status, f, indent=2)

            logger.info(
                f"Updated system_status.json with health data for {len(results['servers'])} servers"
            )

        except Exception as e:
            logger.error(f"Failed to update system_status.json: {e}")


# Convenience function for one-off checks
async def check_all_server_health():
    """Quick function to check all server health"""
    checker = ServerHealthChecker()
    results = await checker.check_all_servers()

    # Also update system_status.json
    await checker.update_system_status_file(results)

    return results


if __name__ == "__main__":
    # Run a health check when executed directly
    async def main():
        checker = ServerHealthChecker()
        results = await checker.check_all_servers()

        print("\n🏥 BoarderframeOS Server Health Check")
        print("=" * 50)

        summary = results["summary"]
        print(
            f"\n📊 Summary: {summary['healthy']}/{summary['total']} servers healthy ({summary['health_percentage']}%)"
        )
        print(f"   ❌ Offline: {summary['offline']}")
        print(f"   ⚠️  Errors: {summary['errors']}")

        print("\n📁 By Category:")
        for category, data in results["categories"].items():
            print(f"\n   {category}: {data['healthy']}/{data['total']} healthy")
            for server in data["servers"]:
                status_icon = "✅" if server["status"] == "healthy" else "❌"
                print(
                    f"      {status_icon} {server['name']} (:{server['port']}) - {server['status']}"
                )

        # Update system_status.json
        await checker.update_system_status_file(results)
        print("\n✅ Updated system_status.json")

    asyncio.run(main())
