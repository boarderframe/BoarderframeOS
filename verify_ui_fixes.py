#!/usr/bin/env python3
"""
Verify that all UI fixes have been properly applied
"""

def verify_fixes():
    """Check that all fixes are in place"""

    issues = []

    # Read corporate headquarters
    with open('corporate_headquarters.py', 'r') as f:
        hq_content = f.read()

    # Read metrics integration
    with open('core/hq_metrics_integration.py', 'r') as f:
        metrics_content = f.read()

    print("Verifying UI fixes...")
    print("-" * 50)

    # Check agents tab
    if 'get_agents_page_html() if self.metrics_layer' in hq_content:
        print("✓ Agents tab uses metrics layer")
    else:
        issues.append("Agents tab not using metrics layer")
        print("✗ Agents tab not using metrics layer")

    # Check database tab
    if 'get_database_page_html() if self.metrics_layer' in hq_content:
        print("✓ Database tab uses metrics layer")
    else:
        issues.append("Database tab not using metrics layer")
        print("✗ Database tab not using metrics layer")

    # Check registry tab
    if 'get_registry_page_html() if self.metrics_layer' in hq_content:
        print("✓ Registry tab uses metrics layer")
    else:
        issues.append("Registry tab not using metrics layer")
        print("✗ Registry tab not using metrics layer")

    # Check registry navigation
    if "showTab('registry')" in hq_content:
        print("✓ Registry navigation button exists")
    else:
        issues.append("Registry navigation button missing")
        print("✗ Registry navigation button missing")

    # Check metrics methods
    if 'def get_agents_page_html' in metrics_content:
        print("✓ get_agents_page_html method exists")
    else:
        issues.append("get_agents_page_html method missing")
        print("✗ get_agents_page_html method missing")

    if 'def get_database_page_html' in metrics_content:
        print("✓ get_database_page_html method exists")
    else:
        issues.append("get_database_page_html method missing")
        print("✗ get_database_page_html method missing")

    if 'def get_registry_page_html' in metrics_content:
        print("✓ get_registry_page_html method exists")
    else:
        issues.append("get_registry_page_html method missing")
        print("✗ get_registry_page_html method missing")

    # Check for proper tab structure
    agents_tab_count = hq_content.count('<div id="agents" class="tab-content">')
    database_tab_count = hq_content.count('<div id="database" class="tab-content">')
    registry_tab_count = hq_content.count('<div id="registry" class="tab-content">')

    print(f"\nTab counts:")
    print(f"  Agents tabs: {agents_tab_count}")
    print(f"  Database tabs: {database_tab_count}")
    print(f"  Registry tabs: {registry_tab_count}")

    if agents_tab_count != 1:
        issues.append(f"Agents tab count is {agents_tab_count}, should be 1")
    if database_tab_count != 1:
        issues.append(f"Database tab count is {database_tab_count}, should be 1")
    if registry_tab_count != 1:
        issues.append(f"Registry tab count is {registry_tab_count}, should be 1")

    print("-" * 50)

    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ All UI fixes have been successfully applied!")
        print("\nThe following pages should now display properly:")
        print("  - Agents page: Shows agent metrics and list")
        print("  - Database page: Shows database health and tables")
        print("  - Registry page: Shows service registry information")
        print("\nRestart the Corporate Headquarters server to see the changes.")
        return True

if __name__ == "__main__":
    verify_fixes()
