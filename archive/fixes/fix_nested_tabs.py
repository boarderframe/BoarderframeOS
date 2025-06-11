#!/usr/bin/env python3
"""
Fix the nested tab-content issue that's breaking tab display
"""


def fix_nested_tabs():
    """Remove nested tab-content classes that break display"""
    print("🔧 Fixing Nested Tab Issues")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    # The problem is in the agents tab - it has nested tab-content divs
    # These should probably be different classes

    # Find the agents tab section
    import re

    # Pattern to find nested tab-content within agents tab
    # We need to be careful to only fix the nested ones, not the main tab

    print("🔍 Looking for nested tab-content divs in agents section...")

    # First, let's identify where the agents tab starts and ends
    agents_start = content.find('<div id="agents" class="tab-content">')
    if agents_start == -1:
        print("❌ Could not find agents tab")
        return

    # Find the next main tab to know where agents section ends
    next_tab_pattern = r'<div id="(?:leaders|departments|divisions|services|system|reporting|database|settings)" class="tab-content">'
    match = re.search(next_tab_pattern, content[agents_start + 50 :])

    if match:
        agents_end = agents_start + 50 + match.start()
        print(f"✅ Found agents section ({agents_end - agents_start} chars)")

        # Extract agents section
        agents_section = content[agents_start:agents_end]

        # Count nested tab-content
        nested_count = (
            agents_section.count('class="tab-content"') - 1
        )  # -1 for the main div
        print(f"📊 Found {nested_count} nested tab-content classes")

        # Replace nested tab-content with agent-tab-content
        # Skip the first occurrence (the main agents tab)
        modified_section = agents_section
        first_occurrence = modified_section.find('class="tab-content">')
        if first_occurrence > -1:
            # Keep the first one, replace the rest
            before_first = modified_section[
                : first_occurrence + 19
            ]  # +19 for 'class="tab-content">'
            after_first = modified_section[first_occurrence + 19 :]

            # Replace all tab-content in the after_first part
            after_first = after_first.replace(
                'class="tab-content"', 'class="agent-tab-content"'
            )
            after_first = after_first.replace(
                'class="tab-content active"', 'class="agent-tab-content active"'
            )

            modified_section = before_first + after_first

        # Replace in original content
        content = content[:agents_start] + modified_section + content[agents_end:]

        print("✅ Replaced nested tab-content with agent-tab-content")

        # Also need to add CSS for the new class
        css_addition = """
        /* Agent nested tabs */
        .agent-tab-content {
            display: none;
        }

        .agent-tab-content.active {
            display: block;
        }"""

        # Find where to add CSS (after .tab-content rules)
        css_insert_point = content.find(".tab-content.active {")
        if css_insert_point > -1:
            css_insert_point = content.find("}", css_insert_point) + 1
            content = (
                content[:css_insert_point] + css_addition + content[css_insert_point:]
            )
            print("✅ Added CSS for agent-tab-content")

    # Write back
    with open(file_path, "w") as f:
        f.write(content)

    print("\n✅ Fixed nested tab issue!")
    print("🚀 The tabs should now display properly when clicked")

    # Also update any JavaScript that might be targeting these nested tabs
    print("\n🔍 Checking for JavaScript that needs updating...")

    # Read again to check
    with open(file_path, "r") as f:
        content = f.read()

    # Look for any showAgentTab or similar functions
    if "showAgentTab" in content:
        print("📊 Found showAgentTab function - updating selectors...")
        content = content.replace(
            "querySelectorAll('.tab-content')", "querySelectorAll('.agent-tab-content')"
        )
        content = content.replace(
            'getElementById(tabName).querySelector(".tab-content")',
            'getElementById(tabName).querySelector(".agent-tab-content")',
        )

        with open(file_path, "w") as f:
            f.write(content)

        print("✅ Updated agent tab JavaScript")


if __name__ == "__main__":
    fix_nested_tabs()
