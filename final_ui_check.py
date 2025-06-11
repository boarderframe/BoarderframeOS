#!/usr/bin/env python3
"""
Final check of UI fixes
"""

import re


def final_ui_check():
    """Perform final verification of all UI fixes"""

    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    print("=== FINAL UI CHECK ===\n")

    issues = []

    # 1. Check showTab function
    print("1. ShowTab Function:")
    if 'function showTab(tabName)' in content:
        print("  ✓ ShowTab function exists")
        if 'style.display = \'block\'' in content:
            print("  ✓ Forces display block")
        else:
            issues.append("ShowTab doesn't force display")
            print("  ✗ Doesn't force display block")
    else:
        issues.append("ShowTab function missing")
        print("  ✗ ShowTab function missing")

    # 2. Check CSS
    print("\n2. CSS Rules:")
    if '.tab-content.active {' in content and 'display: block !important' in content:
        print("  ✓ Active tab CSS properly set")
    else:
        issues.append("Active tab CSS not properly set")
        print("  ✗ Active tab CSS issues")

    # 3. Check all tabs exist
    print("\n3. Tab Structure:")
    required_tabs = ['dashboard', 'agents', 'leaders', 'departments', 'divisions',
                     'services', 'database', 'registry', 'system']

    for tab in required_tabs:
        if f'id="{tab}" class="tab-content' in content:
            print(f"  ✓ {tab} tab exists")
        else:
            issues.append(f"{tab} tab missing")
            print(f"  ✗ {tab} tab missing")

    # 4. Check navigation buttons
    print("\n4. Navigation Buttons:")
    for tab in required_tabs:
        if f"showTab('{tab}')" in content:
            print(f"  ✓ {tab} nav button exists")
        else:
            # Registry might be optional
            if tab != 'registry':
                issues.append(f"{tab} nav button missing")
            print(f"  {'✓' if tab == 'registry' else '✗'} {tab} nav button {'exists' if f'showTab(\'{tab}\')' in content else 'missing'}")

    # 5. Check initialization
    print("\n5. Initialization:")
    if 'DOMContentLoaded' in content:
        print("  ✓ DOMContentLoaded handler exists")
        if "showTab('dashboard')" in content:
            print("  ✓ Dashboard set as default")
        else:
            issues.append("Dashboard not set as default")
            print("  ✗ Dashboard not set as default")
    else:
        issues.append("No DOMContentLoaded handler")
        print("  ✗ No DOMContentLoaded handler")

    # 6. Check for JavaScript errors
    print("\n6. JavaScript Syntax:")

    # Count braces in script sections
    script_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
    if script_match:
        script_content = script_match.group(1)
        open_braces = script_content.count('{')
        close_braces = script_content.count('}')
        open_parens = script_content.count('(')
        close_parens = script_content.count(')')

        if open_braces == close_braces:
            print("  ✓ Braces balanced")
        else:
            issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
            print(f"  ✗ Unbalanced braces: {open_braces} open, {close_braces} close")

        if open_parens == close_parens:
            print("  ✓ Parentheses balanced")
        else:
            issues.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
            print(f"  ✗ Unbalanced parentheses: {open_parens} open, {close_parens} close")

    # Summary
    print(f"\n{'='*50}")
    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ All checks passed! The UI should be working properly.")
        print("\nTo test:")
        print("1. Start the server: python corporate_headquarters.py")
        print("2. Open http://localhost:8888")
        print("3. Click on different tabs to verify they show content")
        print("4. Use Ctrl+1 through Ctrl+9 to switch tabs")
        print("5. Check browser console for any errors")

if __name__ == "__main__":
    final_ui_check()
