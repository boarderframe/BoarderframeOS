#!/usr/bin/env python3
"""
Inspect the raw HTML to see what's actually being served
"""

import requests


def inspect_raw_html():
    """Check what HTML is actually being served"""
    print("🔍 Inspecting Raw HTML Structure")
    print("=" * 60)

    response = requests.get('http://localhost:8888')
    html = response.text

    # Check if the HTML is being properly formatted
    print(f"\n📊 HTML Length: {len(html)} characters")

    # Look for the tab content divs
    import re

    # Find all tab divs
    tab_divs = re.findall(r'<div id="(\w+)" class="tab-content[^"]*"[^>]*>', html)
    print(f"\n📑 Found {len(tab_divs)} tab divs: {', '.join(tab_divs)}")

    # Check if content is actually inside the tabs
    print("\n📊 Checking tab content lengths:")
    for tab_id in tab_divs:
        # Find content between opening and closing div
        pattern = f'<div id="{tab_id}" class="tab-content[^"]*"[^>]*>(.*?)</div>\\s*<div id="'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            content_length = len(match.group(1))
            # Check if it's just whitespace
            stripped_length = len(match.group(1).strip())
            print(f"  {tab_id}: {content_length} chars ({stripped_length} non-whitespace)")

            # Show first 100 chars if very short
            if stripped_length < 100:
                print(f"    Content: {match.group(1).strip()[:100]}")

    # Check for Python template variables that weren't replaced
    unresolved_vars = re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', html)
    if unresolved_vars:
        print(f"\n⚠️ Found {len(set(unresolved_vars))} unresolved template variables!")
        print(f"   Examples: {', '.join(list(set(unresolved_vars))[:5])}")

    # Check for f-string syntax
    fstring_vars = re.findall(r'\{self\.[^}]+\}', html)
    if fstring_vars:
        print(f"\n⚠️ Found {len(set(fstring_vars))} unresolved f-string variables!")
        print(f"   Examples: {', '.join(list(set(fstring_vars))[:5])}")

    # Save a sample for manual inspection
    with open('/tmp/hq_sample.html', 'w') as f:
        f.write(html)
    print("\n💾 Saved full HTML to /tmp/hq_sample.html for inspection")

    # Check specific problematic tabs
    print("\n🔍 Checking specific tab content:")
    for tab in ['departments', 'leaders', 'database']:
        print(f"\n📑 {tab.upper()} tab:")
        pattern = f'<div id="{tab}" class="tab-content">([\\s\\S]*?)</div>\\s*(?:<div id=|</div>\\s*<script>)'
        match = re.search(pattern, html)
        if match:
            content = match.group(1).strip()
            if len(content) < 50:
                print(f"  ❌ Very short content: {content}")
            elif '{' in content and '}' in content:
                print(f"  ⚠️ Contains template variables")
                # Show some examples
                vars_in_content = re.findall(r'\{[^}]+\}', content[:500])
                if vars_in_content:
                    print(f"     Found: {vars_in_content[:3]}")
            else:
                print(f"  ✅ Has content ({len(content)} chars)")


if __name__ == "__main__":
    inspect_raw_html()
