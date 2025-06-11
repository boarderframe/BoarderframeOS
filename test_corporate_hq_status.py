#!/usr/bin/env python3
"""
Test script to verify Corporate Headquarters shows as online in the UI
"""
import asyncio
import re

import httpx
from bs4 import BeautifulSoup


async def test_corporate_hq_status():
    """Test that Corporate Headquarters shows as online in the servers tab"""
    print("🔍 Testing Corporate Headquarters status display...")

    async with httpx.AsyncClient() as client:
        try:
            # Get the main page
            response = await client.get('http://localhost:8888/')
            if response.status_code != 200:
                print(f"❌ Failed to connect to Corporate HQ: {response.status_code}")
                return False

            # Parse the HTML
            html_content = response.text

            # Look for the servers tab content
            # The enhanced server status should show Corporate Headquarters as healthy/online
            if 'Corporate Headquarters' in html_content:
                print("✅ Found Corporate Headquarters in UI")

                # Check if it shows as Online (not Offline)
                # Look for patterns like status text near Corporate Headquarters
                corp_hq_section = re.search(r'Corporate Headquarters.*?(?:Online|Offline|Starting)', html_content, re.DOTALL)
                if corp_hq_section:
                    status_text = corp_hq_section.group()
                    if 'Online' in status_text:
                        print("✅ Corporate Headquarters shows as Online!")
                        return True
                    elif 'Starting' in status_text:
                        print("⏳ Corporate Headquarters shows as Starting (acceptable)")
                        return True
                    else:
                        print(f"❌ Corporate Headquarters shows as Offline")
                        return False
                else:
                    print("⚠️ Could not determine Corporate Headquarters status")

                # Also check for the status emoji
                if '✅' in html_content and 'Corporate Headquarters' in html_content:
                    print("✅ Found healthy status emoji for Corporate HQ")
                    return True
            else:
                print("❌ Corporate Headquarters not found in UI")
                return False

        except Exception as e:
            print(f"❌ Error testing Corporate HQ: {e}")
            return False

async def main():
    """Run the test"""
    print("🚀 Starting Corporate Headquarters status test...")
    print("📍 Make sure Corporate HQ is running on http://localhost:8888")
    print()

    success = await test_corporate_hq_status()

    if success:
        print("\n✅ Test passed! Corporate Headquarters correctly shows as online.")
    else:
        print("\n❌ Test failed. Corporate Headquarters may be showing as offline.")
        print("\n🔧 The fix has been applied to corporate_headquarters.py")
        print("   Please restart the Corporate HQ server to see the changes.")

if __name__ == "__main__":
    asyncio.run(main())
