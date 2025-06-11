#!/usr/bin/env python3
"""
Debug why tabs are appearing blank
"""

import requests
from bs4 import BeautifulSoup


def debug_tabs():
    """Check the HTML structure of tabs"""
    print("🔍 Debugging Tab Display Issues")
    print("=" * 60)

    # Get the HTML
    response = requests.get('http://localhost:8888')
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all tabs
    tabs = soup.find_all('div', class_='tab-content')

    print(f"\n📊 Found {len(tabs)} tabs total")

    for tab in tabs:
        tab_id = tab.get('id', 'unknown')
        classes = tab.get('class', [])
        is_active = 'active' in classes

        # Check content length
        content = str(tab)
        content_length = len(content)

        # Check if it has actual content
        has_content = len(tab.text.strip()) > 0

        print(f"\n📑 Tab: {tab_id}")
        print(f"   Active: {is_active}")
        print(f"   Classes: {' '.join(classes)}")
        print(f"   Content Length: {content_length} chars")
        print(f"   Has Text Content: {has_content}")

        # For blank tabs, show first 200 chars
        if tab_id in ['leaders', 'departments', 'divisions', 'services'] and content_length < 1000:
            print(f"   Preview: {content[:200]}...")

    # Check JavaScript
    print("\n🔧 Checking JavaScript:")

    # Find showTab function
    if 'function showTab' in response.text:
        print("   ✅ showTab function found")
    else:
        print("   ❌ showTab function NOT found")

    # Check for console errors
    script_tags = soup.find_all('script')
    print(f"   Found {len(script_tags)} script tags")


if __name__ == "__main__":
    debug_tabs()
