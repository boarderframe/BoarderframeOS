#!/usr/bin/env python3
"""Force refresh and check server status"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corporate_headquarters import CorporateDashboard


async def main():
    print("🔄 Creating dashboard instance and forcing refresh...")

    # Create dashboard instance
    dashboard = CorporateDashboard()

    # Print current status
    print("\n📊 Current Status Before Refresh:")
    for name, status in dashboard.unified_data.get("services_status", {}).items():
        print(f"  - {name}: {status.get('status', 'unknown')}")

    # Force a global refresh
    print("\n🔄 Running global refresh...")
    if hasattr(dashboard, "health_manager"):
        await dashboard.health_manager.global_refresh_all_data()
    else:
        print("❌ No health manager found")

    # Print updated status
    print("\n📊 Status After Refresh:")
    for name, status in dashboard.unified_data.get("services_status", {}).items():
        print(f"  - {name}: {status.get('status', 'unknown')}")

    print("\n✅ Refresh complete!")


if __name__ == "__main__":
    asyncio.run(main())
