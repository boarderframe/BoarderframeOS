#!/usr/bin/env python3
"""
Debug why tabs are not showing content
"""

import re


def analyze_tab_visibility():
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    print("=== TAB VISIBILITY ANALYSIS ===\n")

    # 1. Check CSS rules
    print("1. CSS Rules for tabs:")
    css_section = re.search(r'/\* Tab Content.*?\*/.*?\.tab-content\.active\s*{[^}]+}', content, re.DOTALL)
    if css_section:
        print(css_section.group())

    # 2. Check which tabs have content
    print("\n2. Tab Content Summary:")
    tabs = re.findall(r'<div id="([^"]+)" class="tab-content[^"]*">', content)

    for tab in tabs:
        tab_match = re.search(rf'<div id="{tab}" class="tab-content[^"]*">(.{{0,200}})', content, re.DOTALL)
        if tab_match:
            content_preview = tab_match.group(1).strip()
            # Check if it's using metrics layer
            if 'metrics_layer' in content_preview:
                print(f"\n{tab}: Uses metrics layer")
            elif len(content_preview) < 50:
                print(f"\n{tab}: Very short content ({len(content_preview)} chars)")
            else:
                print(f"\n{tab}: Has inline content ({len(content_preview)} chars)")

            # Show preview
            print(f"  Preview: {content_preview[:100]}...")

    # 3. Check showTab function
    print("\n\n3. ShowTab Function Check:")
    show_tab_match = re.search(r'function showTab\(tabName\)\s*{([^}]+)}', content, re.DOTALL)
    if show_tab_match:
        func_body = show_tab_match.group(1)
        if 'classList.remove' in func_body and 'classList.add' in func_body:
            print("✓ ShowTab function appears to manipulate classes correctly")
        else:
            print("⚠️  ShowTab function may not be working properly")

    # 4. Check for potential JavaScript errors
    print("\n4. Potential JavaScript Issues:")

    # Look for syntax errors
    js_sections = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    for i, js in enumerate(js_sections):
        # Check for common syntax errors
        if '$$' in js or '$1' in js:
            print(f"⚠️  Script block {i+1} contains suspicious $ characters")
        if js.count('{') != js.count('}'):
            print(f"⚠️  Script block {i+1} has unbalanced braces")
        if js.count('(') != js.count(')'):
            print(f"⚠️  Script block {i+1} has unbalanced parentheses")

if __name__ == "__main__":
    analyze_tab_visibility()
