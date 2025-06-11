#!/usr/bin/env python3
"""
Find the exact issue with tab structure
"""

import requests
from bs4 import BeautifulSoup


def find_tab_structure_issue():
    """Analyze the exact DOM structure"""
    print("🔍 Analyzing Tab DOM Structure")
    print("=" * 60)

    response = requests.get("http://localhost:8888")
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all tab-content divs
    tabs = soup.find_all("div", class_="tab-content")

    print(f"\n📊 Found {len(tabs)} tab-content divs")

    # Check each tab's structure
    for tab in tabs:
        tab_id = tab.get("id", "NO_ID")
        classes = tab.get("class", [])
        parent = tab.parent.name if tab.parent else "NO_PARENT"

        print(f"\n📑 Tab: {tab_id}")
        print(f"   Classes: {' '.join(classes)}")
        print(f"   Parent element: {parent}")

        # Check if it has the active class
        if "active" in classes:
            print("   ✅ Has 'active' class")
        else:
            print("   ❌ Missing 'active' class")

        # Check computed style hint
        style = tab.get("style", "")
        if style:
            print(f"   Inline style: {style}")

        # Check immediate children
        children = list(tab.children)
        child_count = len([c for c in children if hasattr(c, "name")])
        text_content = tab.get_text(strip=True)[:50]

        print(f"   Child elements: {child_count}")
        print(f"   Text preview: {text_content}...")

        # Look for nested tab-content (which would be wrong)
        nested = tab.find_all("div", class_="tab-content")
        if nested:
            print(f"   ⚠️ WARNING: Contains {len(nested)} nested tab-content divs!")

    # Check if showTab function exists in a script tag
    print("\n🔧 Checking JavaScript:")
    scripts = soup.find_all("script")
    showTab_found = False
    for script in scripts:
        if script.string and "function showTab" in script.string:
            showTab_found = True
            # Check if the function looks correct
            if "style.display" in script.string:
                print("   ✅ showTab function found with style.display")
            else:
                print("   ⚠️ showTab function found but might not set display style")
            break

    if not showTab_found:
        print("   ❌ showTab function NOT found in any script tag!")

    # Check navigation structure
    print("\n🔗 Checking Navigation:")
    nav_links = soup.find_all("button", class_="nav-link")
    print(f"   Found {len(nav_links)} navigation buttons")

    for link in nav_links[:5]:  # First 5
        onclick = link.get("onclick", "")
        data_tab = link.get("data-tab", "")
        text = link.get_text(strip=True)
        active = "active" in link.get("class", [])
        print(
            f"   - {text}: onclick='{onclick}', data-tab='{data_tab}', active={active}"
        )

    # Final check - look for any CSS that might override
    print("\n🎨 Checking for problematic CSS:")
    for style in soup.find_all("style"):
        if style.string:
            # Look for any !important on display
            if "display" in style.string and "!important" in style.string:
                lines = style.string.split("\n")
                for i, line in enumerate(lines):
                    if "display" in line and "!important" in line:
                        print(f"   ⚠️ Found !important display rule: {line.strip()}")


if __name__ == "__main__":
    find_tab_structure_issue()
