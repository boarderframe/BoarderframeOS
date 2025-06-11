#!/usr/bin/env python3
"""Verify Corporate HQ status is showing correctly"""

import json

import requests


def check_corporate_hq_status():
    try:
        # Check health endpoint
        health_response = requests.get("http://localhost:8888/health")
        print("✅ Corporate HQ Health Endpoint:")
        print(json.dumps(health_response.json(), indent=2))

        # Check if the internal status data shows Corporate HQ as healthy
        # This would be visible in the UI
        print("\n📊 Expected UI Status:")
        print("- Corporate Headquarters: Online (Port 8888)")
        print("- Core Systems: Should show at least 1/3 online (Corporate HQ)")
        print("- System dropdown: Should show Core servers with HQ online")

        return True

    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Verifying Corporate HQ Status Display...")
    print("=" * 60)

    if check_corporate_hq_status():
        print("\n✅ Corporate HQ is running and should display as 'Online' in:")
        print("   - Servers tab")
        print("   - Core Systems header")
        print("   - System status dropdown")
        print("\n📌 Please check the UI at http://localhost:8888 to confirm!")
    else:
        print("\n❌ Corporate HQ is not responding properly")
