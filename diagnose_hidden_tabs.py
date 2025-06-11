#!/usr/bin/env python3
"""
Diagnose why tabs are staying hidden
"""

import requests
from bs4 import BeautifulSoup


def diagnose_hidden_tabs():
    """Check what's keeping tabs hidden"""
    print("🔍 Diagnosing Hidden Tab Issue")
    print("=" * 60)

    # Get the page
    response = requests.get("http://localhost:8888")

    # Check the CSS for tab-content
    print("\n🎨 Checking CSS rules for .tab-content:")

    # Find all style blocks
    css_content = ""
    if "<style>" in response.text:
        import re

        style_blocks = re.findall(r"<style>(.*?)</style>", response.text, re.DOTALL)
        for block in style_blocks:
            css_content += block

    # Look for tab-content rules
    tab_content_rules = []
    for line in css_content.split("\n"):
        if "tab-content" in line:
            tab_content_rules.append(line.strip())

    print("Found CSS rules:")
    for rule in tab_content_rules[:10]:  # First 10 rules
        print(f"  {rule}")

    # Check if there's a display:none that's not being overridden
    if any("display: none" in rule for rule in tab_content_rules):
        print("\n⚠️ Found display: none for tab-content")

    if any("display: block" in rule for rule in tab_content_rules):
        print("✅ Found display: block for active tabs")

    # Check the actual computed styles by looking at the HTML
    soup = BeautifulSoup(response.text, "html.parser")

    print("\n📊 Checking inline styles on tabs:")
    tabs = soup.find_all("div", class_="tab-content")
    for tab in tabs:
        tab_id = tab.get("id", "unknown")
        style = tab.get("style", "")
        classes = " ".join(tab.get("class", []))
        if style:
            print(f"  {tab_id}: style='{style}' classes='{classes}'")

    # Check for JavaScript errors
    print("\n🔧 Checking for potential JavaScript issues:")

    # Look for the showTab function
    if "function showTab" in response.text:
        # Extract the function
        import re

        match = re.search(
            r"function showTab\(tabName\)\s*{([^}]+)}", response.text, re.DOTALL
        )
        if match:
            print("showTab function found:")
            func_body = match.group(1)
            print(func_body[:200] + "...")

            # Check if it's using {{ }} template syntax
            if "{{" in func_body:
                print("\n❌ FOUND THE ISSUE: Template syntax {{ }} in JavaScript!")
                print("   This breaks the JavaScript when rendered")

    # Check for console.log or errors
    if "console.error" in response.text:
        print("\n⚠️ Found console.error calls in the code")

    # Check if jQuery is being used but not loaded
    if "$(" in response.text and "jquery" not in response.text.lower():
        print("\n⚠️ jQuery syntax used but jQuery might not be loaded")

    print("\n💡 Diagnosis complete!")


if __name__ == "__main__":
    diagnose_hidden_tabs()
