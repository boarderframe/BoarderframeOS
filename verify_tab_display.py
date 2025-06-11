#!/usr/bin/env python3
"""
Verify tab display will work correctly
"""

import re


def verify_tab_display():
    """Check that tabs will display properly"""

    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    print("=== TAB DISPLAY VERIFICATION ===\n")

    # 1. Check CSS rules
    print("1. CSS Rules Check:")

    # Find all CSS rules for tab-content
    css_rules = re.findall(r"\.tab-content[^{]*{[^}]+}", content)

    problematic = False
    for rule in css_rules:
        print(f"\n{rule}")
        if "display: none !important" in rule and ".active" not in rule:
            print(
                "  ⚠️  This rule uses !important which could prevent tabs from showing"
            )
            problematic = True

    # 2. Check if .tab-content.active overrides properly
    active_rule = re.search(r"\.tab-content\.active\s*{([^}]+)}", content)
    if active_rule:
        print(f"\n2. Active tab rule:\n.tab-content.active {{{active_rule.group(1)}}}")
        if "display: block !important" in active_rule.group(1):
            print("  ✓ Active rule properly overrides with !important")
        else:
            print("  ⚠️  Active rule may not override properly")

    # 3. Check JavaScript showTab function
    print("\n3. JavaScript showTab Function:")
    show_tab = re.search(
        r"function showTab\(tabName\)\s*{([^}]+(?:{[^}]*}[^}]*)*)}", content
    )
    if show_tab:
        func_body = show_tab.group(1)

        checks = {
            "Removes active class": "classList.remove('active')",
            "Adds active class": "classList.add('active')",
            "Sets display style": "style.display",
            "Has error handling": "console.error",
        }

        for check_name, check_pattern in checks.items():
            if check_pattern in func_body:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ⚠️  Missing: {check_name}")

    # 4. Check tab content
    print("\n4. Tab Content Status:")
    tabs = [
        "dashboard",
        "agents",
        "leaders",
        "departments",
        "divisions",
        "services",
        "database",
        "registry",
        "system",
    ]

    for tab in tabs:
        tab_match = re.search(
            rf'<div id="{tab}" class="tab-content[^"]*">(.{{0,100}})',
            content,
            re.DOTALL,
        )
        if tab_match:
            content_preview = tab_match.group(1).strip()
            if not content_preview or len(content_preview) < 10:
                print(f"  ⚠️  {tab}: Empty or minimal content")
            elif "metrics_layer" in content_preview:
                print(f"  ℹ️  {tab}: Uses metrics layer")
            else:
                print(f"  ✓ {tab}: Has content")

    # 5. Look for any other potential issues
    print("\n5. Other Potential Issues:")

    # Check for multiple script blocks that might interfere
    script_blocks = len(re.findall(r"<script[^>]*>", content))
    print(f"  Script blocks found: {script_blocks}")

    # Check for console errors
    if "console.error" in content:
        error_count = content.count("console.error")
        print(f"  Console error statements: {error_count}")

    # Check if tabs have closing divs
    for tab in tabs:
        tab_section = re.search(
            rf'<div id="{tab}" class="tab-content[^>]*>.*?(?=<div id="|</script>)',
            content,
            re.DOTALL,
        )
        if tab_section:
            section = tab_section.group()
            open_divs = section.count("<div")
            close_divs = section.count("</div>")
            if open_divs != close_divs:
                print(
                    f"  ⚠️  {tab}: Unbalanced divs (open: {open_divs}, close: {close_divs})"
                )


if __name__ == "__main__":
    verify_tab_display()
