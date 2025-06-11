#!/usr/bin/env python3
"""
Check what's displayed in the Agents tab
"""

import re

import requests
from bs4 import BeautifulSoup


def check_agents_tab():
    """Check the Agents tab content"""
    print("🔍 Checking Agents Tab Content")
    print("=" * 60)

    try:
        # Fetch the dashboard
        response = requests.get("http://localhost:8888", timeout=5)
        if response.status_code != 200:
            print("❌ Failed to fetch dashboard")
            return

        html = response.text

        # Find the Agents tab section
        agents_start = html.find('<div id="agents" class="tab-content">')
        if agents_start == -1:
            print("❌ Could not find Agents tab")
            return

        agents_end = html.find("</div>\n\n        <!-- Leaders Tab -->", agents_start)
        if agents_end == -1:
            agents_end = html.find('<div id="leaders"', agents_start)

        agents_section = html[agents_start:agents_end]

        print("\n📊 Agents Tab Metrics:")

        # Check for metric widgets
        active_match = re.search(
            r"<span>Active</span>.*?widget-value.*?>(\d+|{[^}]+})<",
            agents_section,
            re.DOTALL,
        )
        inactive_match = re.search(
            r"<span>Inactive</span>.*?widget-value.*?>(\d+|{[^}]+})<",
            agents_section,
            re.DOTALL,
        )
        total_match = re.search(
            r"<span>Total</span>.*?widget-value.*?>(\d+|{[^}]+})<",
            agents_section,
            re.DOTALL,
        )

        if active_match:
            print(f"   ✅ Active metric found: {active_match.group(1)}")
        else:
            print("   ❌ Active metric not found")

        if inactive_match:
            print(f"   ✅ Inactive metric found: {inactive_match.group(1)}")
        else:
            print("   ❌ Inactive metric not found")

        if total_match:
            print(f"   ✅ Total metric found: {total_match.group(1)}")
        else:
            print("   ❌ Total metric not found")

        # Check grid layout
        grid_match = re.search(
            r"grid-template-columns:\s*repeat\((\d+),", agents_section
        )
        if grid_match:
            columns = grid_match.group(1)
            print(f"\n📐 Grid Layout: {columns} columns")
            if columns == "3":
                print("   ✅ Correct 3-column layout")
            else:
                print(f"   ❌ Wrong layout - expected 3 columns, got {columns}")

        # Check for old metrics that should be removed
        print("\n🔍 Checking for removed metrics:")
        old_metrics = ["Productive", "Healthy", "Idle"]
        for metric in old_metrics:
            if f"<span>{metric}</span>" in agents_section:
                print(f"   ❌ Old metric '{metric}' still present")
            else:
                print(f"   ✅ Old metric '{metric}' removed")

        # Check Overall Status
        overall_status = re.search(
            r"Overall Status.*?<div[^>]*>([^<]+)</div>", agents_section, re.DOTALL
        )
        if overall_status:
            print(f"\n📊 Overall Status: {overall_status.group(1).strip()}")

        # Show a snippet of the grid
        print("\n📄 Agents Metrics Grid HTML snippet:")
        grid_snippet = agents_section[
            agents_section.find("<!-- Agent Metrics Grid -->") : agents_section.find(
                "<!-- Agent Metrics Grid -->"
            )
            + 500
        ]
        print(grid_snippet[:500] + "...")

    except Exception as e:
        print(f"❌ Error checking agents tab: {e}")
        print("\n💡 Make sure Corporate HQ is running on http://localhost:8888")


if __name__ == "__main__":
    check_agents_tab()
