#!/usr/bin/env python3
"""
Refresh server status in Corporate Headquarters with real-time health data
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hq_metrics_layer import MetricsCalculator
from utils.server_health_checker import ServerHealthChecker


async def refresh_server_status():
    """Refresh server status with real-time health checks"""
    print("🔄 Refreshing server status with real-time health data...")

    # Step 1: Check all server health
    checker = ServerHealthChecker()
    health_results = await checker.check_all_servers()

    print(f"✅ Checked {len(health_results['servers'])} servers")
    print(f"   Healthy: {health_results['summary']['healthy']}")
    print(
        f"   Offline/Error: {health_results['summary']['total'] - health_results['summary']['healthy']}"
    )

    # Step 2: Update system_status.json
    await checker.update_system_status_file(health_results)
    print("✅ Updated system_status.json")

    # Step 3: Update metrics layer if available
    try:
        metrics = MetricsCalculator()

        # Convert health results to format expected by metrics layer
        server_status = {}
        for server_id, server_data in health_results["servers"].items():
            server_status[server_id] = {
                "status": server_data["status"],
                "port": server_data["port"],
                "response_time": server_data.get("response_time", 0),
                "category": server_data["category"],
                "name": server_data["name"],
                "icon": server_data["icon"],
            }

        metrics.set_server_status(server_status)
        print(f"✅ Updated metrics layer with {len(server_status)} server statuses")

        # Force metrics refresh
        all_metrics = metrics.get_all_metrics(force_refresh=True)
        print(f"✅ Refreshed metrics cache")

    except Exception as e:
        print(f"⚠️  Could not update metrics layer: {e}")

    # Step 4: Notify Corporate HQ to refresh (if running)
    try:
        import httpx

        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post("http://localhost:8888/api/global/refresh")
            if response.status_code == 200:
                print("✅ Triggered Corporate HQ global refresh")
            else:
                print(
                    f"⚠️  Corporate HQ refresh returned status {response.status_code}"
                )
    except Exception as e:
        print(f"⚠️  Could not trigger Corporate HQ refresh: {e}")

    print("\n🎉 Server status refresh complete!")

    # Print summary
    print("\n📊 Current Server Status:")
    for category, data in health_results["categories"].items():
        print(f"\n{category}: {data['healthy']}/{data['total']} healthy")
        for server in data["servers"]:
            status_icon = "✅" if server["status"] == "healthy" else "❌"
            print(f"   {status_icon} {server['name']} (:{server['port']})")


if __name__ == "__main__":
    asyncio.run(refresh_server_status())
