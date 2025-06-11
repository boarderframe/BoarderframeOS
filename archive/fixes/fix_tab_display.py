#!/usr/bin/env python3
"""
Fix the tab display issue in Corporate HQ
"""

import re


def fix_tab_display():
    """Fix JavaScript issues preventing tabs from showing"""
    print("🔧 Fixing Tab Display Issues")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    # Check for any syntax issues in the HTML
    # Look for the erroneous </div>iv> near line 4962
    if "</div>iv>" in content:
        print("❌ Found HTML syntax error: </div>iv>")
        content = content.replace("</div>iv>", "</div>")
        print("✅ Fixed HTML syntax error")

    # Check for duplicate tab IDs
    tab_ids = re.findall(r'<div id="(\w+)" class="tab-content', content)
    print(f"\n📊 Found tabs: {', '.join(tab_ids)}")

    # Check for duplicate IDs
    duplicates = [x for x in tab_ids if tab_ids.count(x) > 1]
    if duplicates:
        print(f"❌ Found duplicate tab IDs: {set(duplicates)}")
    else:
        print("✅ No duplicate tab IDs found")

    # Ensure all nav links match tab IDs
    nav_links = re.findall(r'onclick="showTab\(\'(\w+)\'\)"', content)
    print(f"\n🔗 Navigation links: {', '.join(set(nav_links))}")

    missing_tabs = set(nav_links) - set(tab_ids)
    if missing_tabs:
        print(f"❌ Navigation links without matching tabs: {missing_tabs}")

    missing_links = set(tab_ids) - set(nav_links)
    if missing_links:
        print(f"❌ Tabs without navigation links: {missing_links}")

    # Check for the System tab issue
    if "system" in tab_ids and "system" not in nav_links:
        print("\n⚠️ System tab exists but no navigation link found")
        # Find where to add the system nav link (after services)
        services_nav_pattern = r'(<button class="nav-link" onclick="showTab\(\'services\'\)"[^>]*>.*?</button>)'
        match = re.search(services_nav_pattern, content, re.DOTALL)
        if match:
            print("✅ Adding System navigation link")
            system_nav = """
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('system')" data-tab="system">
                        <i class="fas fa-chart-line"></i>
                        <span>System</span>
                    </button>
                </li>"""
            # Insert after services nav item's parent li
            insert_point = content.find("</li>", match.end())
            content = (
                content[: insert_point + 5] + system_nav + content[insert_point + 5 :]
            )

    # Add reporting nav if missing
    if "reporting" in tab_ids and "reporting" not in nav_links:
        print("\n⚠️ Reporting tab exists but no navigation link found")
        # Find where to add (after system)
        system_nav_pattern = r'(<button class="nav-link" onclick="showTab\(\'system\'\)"[^>]*>.*?</button>)'
        match = re.search(system_nav_pattern, content, re.DOTALL)
        if match:
            print("✅ Adding Reporting navigation link")
            reporting_nav = """
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('reporting')" data-tab="reporting">
                        <i class="fas fa-chart-bar"></i>
                        <span>Reporting</span>
                    </button>
                </li>"""
            insert_point = content.find("</li>", match.end())
            content = (
                content[: insert_point + 5]
                + reporting_nav
                + content[insert_point + 5 :]
            )
        else:
            # Try after settings instead
            settings_nav_pattern = r'(<button class="nav-link" onclick="showTab\(\'settings\'\)"[^>]*>.*?</button>)'
            match = re.search(settings_nav_pattern, content, re.DOTALL)
            if match:
                print("✅ Adding Reporting navigation link after settings")
                reporting_nav = """
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('reporting')" data-tab="reporting">
                        <i class="fas fa-chart-bar"></i>
                        <span>Reporting</span>
                    </button>
                </li>"""
                insert_point = content.find("</li>", match.end())
                content = (
                    content[: insert_point + 5]
                    + reporting_nav
                    + content[insert_point + 5 :]
                )

    # Write back the fixed content
    with open(file_path, "w") as f:
        f.write(content)

    print("\n✅ Tab display fixes applied!")
    print("\n🚀 Please refresh Corporate HQ to see the changes")
    print("   All tabs should now be clickable and display properly")


if __name__ == "__main__":
    fix_tab_display()
