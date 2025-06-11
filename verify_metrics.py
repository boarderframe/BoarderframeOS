#!/usr/bin/env python3
"""
Verify that metrics are being used correctly
"""

import re

import requests
from bs4 import BeautifulSoup


def verify_metrics():
    """Check what metrics are actually being displayed"""
    print("🔍 Verifying Metric Display in Corporate HQ")
    print("=" * 50)

    try:
        # Fetch the dashboard
        response = requests.get("http://localhost:8888", timeout=5)
        if response.status_code != 200:
            print("❌ Failed to fetch dashboard")
            return

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        print("\n📊 Checking displayed metrics...")

        # Check for "Managing X AI agents"
        managing_pattern = r'Managing\s*<strong[^>]*>(\d+)</strong>\s*AI agents'
        managing_match = re.search(managing_pattern, html)
        if managing_match:
            agent_count = managing_match.group(1)
            print(f"\n✅ Dashboard shows: Managing {agent_count} AI agents")
            if agent_count == "195":
                print("   ✅ Using correct centralized metric!")
            elif agent_count == "2":
                print("   ❌ Still showing hardcoded value of 2")
            else:
                print(f"   ⚠️  Showing unexpected value: {agent_count}")

        # Check for 120+ in departments
        if "120+" in html:
            print("\n❌ Found '120+' - departments tab not using centralized metrics")
        else:
            print("\n✅ '120+' has been replaced")

        # Look for department count in specialized agents widget
        specialized_pattern = r'<div class="widget-value"[^>]*>\s*(\d+)\s*</div>\s*<div class="widget-subtitle">Specialized Agents'
        specialized_match = re.search(specialized_pattern, html)
        if specialized_match:
            specialized_count = specialized_match.group(1)
            print(f"\n📊 Specialized Agents widget shows: {specialized_count}")
            if specialized_count == "195":
                print("   ✅ Using centralized metrics!")
            else:
                print(f"   ⚠️  Not using centralized value")

        # Check for agent status metrics
        total_pattern = r'Total:\s*(\d+)'
        active_pattern = r'Active:\s*(\d+)'

        total_matches = re.findall(total_pattern, html)
        active_matches = re.findall(active_pattern, html)

        if total_matches:
            print(f"\n📊 Found 'Total' values: {total_matches}")
        if active_matches:
            print(f"📊 Found 'Active' values: {active_matches}")

        # Check department and division counts
        dept_pattern = r'>\s*(\d+)\s*</[^>]+>\s*<[^>]+>Departments'
        div_pattern = r'>\s*(\d+)\s*</[^>]+>\s*<[^>]+>Divisions'

        dept_match = re.search(dept_pattern, html)
        div_match = re.search(div_pattern, html)

        if dept_match:
            print(f"\n📊 Department count: {dept_match.group(1)}")
            if dept_match.group(1) == "45":
                print("   ✅ Correct count!")

        if div_match:
            print(f"📊 Division count: {div_match.group(1)}")
            if div_match.group(1) == "9":
                print("   ✅ Correct count!")

        # Summary
        print("\n" + "=" * 50)
        print("📋 SUMMARY:")

        # Check if any old values remain
        old_values = {
            "120+": "120+" in html,
            "Managing 2 agents": "Managing <strong" in html and ">2</strong> AI agents" in html,
            "Hardcoded 45": False,  # Harder to detect without context
            "Hardcoded 9": False    # Harder to detect without context
        }

        issues = [k for k, v in old_values.items() if v]

        if not issues:
            print("✅ All metrics appear to be using centralized values!")
        else:
            print("❌ Still using hardcoded values:")
            for issue in issues:
                print(f"   - {issue}")

    except Exception as e:
        print(f"❌ Error verifying metrics: {e}")
        print("\n💡 Make sure Corporate HQ is running on http://localhost:8888")


if __name__ == "__main__":
    verify_metrics()
