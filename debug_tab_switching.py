#!/usr/bin/env python3
"""
Debug why tabs aren't switching properly
"""

import re


def debug_tab_switching():
    """Check the complete tab switching mechanism"""

    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    print("=== TAB SWITCHING DEBUG ===\n")

    # 1. Check if database tab has proper structure
    print("1. Database Tab Structure:")
    db_tab_match = re.search(r'<div id="database" class="tab-content">(.*?)(?=<div id="|</div>\s*<div id="settings")', content, re.DOTALL)
    if db_tab_match:
        db_content = db_tab_match.group(1)
        print(f"  ✓ Database tab found, content length: {len(db_content)} chars")
        if len(db_content) > 100:
            print("  ✓ Database tab has substantial content")
        else:
            print("  ⚠️  Database tab content seems too short")
    else:
        print("  ✗ Could not find database tab content")

    # 2. Check showTab function
    print("\n2. ShowTab Function Analysis:")
    show_tab_match = re.search(r'function showTab\(tabName\)\s*\{(.*?)\n\s*\}', content, re.DOTALL)
    if show_tab_match:
        show_tab_body = show_tab_match.group(1)

        # Check for key functionality
        checks = {
            'Console logging': 'console.log',
            'Query all tabs': 'querySelectorAll.*tab-content',
            'Remove active class': 'classList.remove.*active',
            'Add active class': 'classList.add.*active',
            'Force display block': 'style.display.*block',
            'Force visibility': 'style.visibility.*visible'
        }

        for check_name, pattern in checks.items():
            if re.search(pattern, show_tab_body):
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name} - MISSING!")

    # 3. Check CSS rules
    print("\n3. CSS Analysis:")

    # Check if tab-content has display none
    if re.search(r'\.tab-content\s*\{[^}]*display:\s*none', content):
        print("  ✓ .tab-content has display: none")
    else:
        print("  ✗ .tab-content missing display: none")

    # Check if active class overrides
    active_css_match = re.search(r'\.tab-content\.active\s*\{([^}]+)\}', content)
    if active_css_match:
        active_rules = active_css_match.group(1)
        if 'display: block' in active_rules:
            print("  ✓ .tab-content.active has display: block")
        else:
            print("  ✗ .tab-content.active missing display: block")

        if '!important' in active_rules:
            print("  ✓ Using !important for override")
        else:
            print("  ⚠️  Not using !important (might not override)")

    # 4. Check for JavaScript errors
    print("\n4. Potential JavaScript Issues:")

    # Look for syntax issues
    script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)

    for i, script in enumerate(script_blocks):
        # Skip empty or very small scripts
        if len(script.strip()) < 50:
            continue

        print(f"\n  Script Block {i+1}:")

        # Check for common issues
        open_braces = script.count('{')
        close_braces = script.count('}')
        if open_braces != close_braces:
            print(f"    ✗ Unbalanced braces: {open_braces} open, {close_braces} close")
        else:
            print(f"    ✓ Braces balanced ({open_braces})")

        # Check for console errors
        if 'console.error' in script:
            errors = re.findall(r'console\.error\([\'"]([^\'"]+)', script)
            for error in errors[:3]:  # Show first 3
                print(f"    ⚠️  Error log: {error}")

    # 5. Check onclick handlers
    print("\n5. Navigation Button Handlers:")
    nav_buttons = re.findall(r'onclick="showTab\(\'([^\']+)\'\)[^"]*"', content)

    for tab in ['dashboard', 'agents', 'database', 'services']:
        if tab in nav_buttons:
            print(f"  ✓ {tab} button has onclick handler")
        else:
            print(f"  ✗ {tab} button missing onclick handler")

    # 6. Look for any overriding styles
    print("\n6. Inline Style Overrides:")

    # Check if any tabs have inline display: none
    inline_hidden = re.findall(r'id="([^"]+)"[^>]*class="tab-content[^"]*"[^>]*style="[^"]*display:\s*none', content)
    if inline_hidden:
        print(f"  ⚠️  These tabs have inline display:none: {', '.join(inline_hidden)}")
    else:
        print("  ✓ No tabs have inline display:none")

if __name__ == "__main__":
    debug_tab_switching()
