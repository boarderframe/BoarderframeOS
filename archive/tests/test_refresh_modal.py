#!/usr/bin/env python3
"""
Test script to verify the refresh modal component card functionality
"""

import sys
import time

import requests


def test_refresh_api():
    """Test the enhanced refresh API endpoint"""
    try:
        print("🔄 Testing enhanced refresh API...")

        response = requests.post(
            "http://localhost:8888/api/enhanced/refresh", json={}, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ API Response received successfully")
            print(f"📊 Status: {result.get('status', 'unknown')}")
            print(
                f"📋 Refreshed components: {result.get('result', {}).get('refreshed_components', [])}"
            )
            print(f"⏱️  Duration: {result.get('result', {}).get('duration', 'unknown')}")
            return True
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"🔍 Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False


def check_corporate_hq():
    """Check if corporate headquarters is running"""
    try:
        response = requests.get("http://localhost:8888", timeout=5)
        if response.status_code == 200:
            print("✅ Corporate Headquarters is running on http://localhost:8888")
            return True
        else:
            print(
                f"❌ Corporate Headquarters returned status code: {response.status_code}"
            )
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Corporate Headquarters is not accessible: {e}")
        return False


def main():
    print("🧪 Testing Refresh Modal Component Cards")
    print("=" * 50)

    # Check if corporate headquarters is running
    if not check_corporate_hq():
        print("\n💡 Instructions:")
        print(
            "1. Make sure corporate headquarters is running: python corporate_headquarters.py"
        )
        print(
            "2. Then test the refresh functionality in the browser at http://localhost:8888"
        )
        print("3. Click the 'Refresh OS' button to see the component cards animate")
        sys.exit(1)

    # Test the API
    if test_refresh_api():
        print("\n✅ Enhanced refresh API is working!")
        print("\n🎯 What to test in the browser:")
        print("1. Go to http://localhost:8888")
        print("2. Click the 'Refresh OS' button")
        print("3. Watch the component cards:")
        print("   - Should start as 'Pending' with clock icons")
        print("   - Should transition to 'Refreshing...' with spinning icons")
        print("   - Should complete as 'Complete' with check marks")
        print("   - Should have animated scaling and glow effects")
        print("4. Components should complete in this order:")
        print("   - system_metrics → database_health → services_status → agents_status")
        print(
            "   - mcp_servers → registry_data → departments_data → organizational_data"
        )
    else:
        print("\n❌ Enhanced refresh API has issues")
        print("Check the corporate headquarters logs for more details")


if __name__ == "__main__":
    main()
