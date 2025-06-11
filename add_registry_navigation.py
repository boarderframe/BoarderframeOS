#!/usr/bin/env python3
"""
Add registry navigation button to corporate headquarters
"""

def add_registry_nav():
    """Add registry button to navigation"""

    # Read the file
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    # Check if registry nav already exists
    if 'showTab(\'registry\')' in content:
        print("Registry navigation already exists")
        return True

    # Find the database nav button
    database_nav_pos = content.find('onclick="showTab(\'database\')"')
    if database_nav_pos == -1:
        print("Could not find database navigation button")
        return False

    # Find the end of the database nav item
    nav_item_end = content.find('</li>', database_nav_pos)
    if nav_item_end == -1:
        print("Could not find end of database nav item")
        return False

    # Insert registry nav after database
    registry_nav = '''

                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('registry')" data-tab="registry">
                        <i class="fas fa-network-wired"></i>
                        <span>Registry</span>
                    </button>
                </li>'''

    # Insert after the database nav item
    insert_pos = nav_item_end + 5  # After </li>
    content = content[:insert_pos] + registry_nav + content[insert_pos:]

    # Save the file
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)

    print("Successfully added registry navigation button")
    return True

if __name__ == "__main__":
    if add_registry_nav():
        print("✓ Registry navigation added successfully")
    else:
        print("✗ Failed to add registry navigation")
