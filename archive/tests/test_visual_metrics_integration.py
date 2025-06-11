#!/usr/bin/env python3
"""
Test the visual metrics integration
"""

import json

from core.hq_metrics_integration import HQMetricsIntegration
from enhance_metrics_visual_integration import VisualMetadataCache


def test_visual_integration():
    print("🧪 Testing Visual Metrics Integration")
    print("=" * 60)

    # Initialize the metrics integration
    db_config = {
        "host": "localhost",
        "port": 5434,
        "database": "boarderframeos",
        "user": "boarderframe",
        "password": "boarderframe_secure_2025",
    }

    # Test visual cache
    print("\n1. Testing Visual Metadata Cache")
    visual_cache = VisualMetadataCache(db_config)
    visual_cache.refresh_cache()

    # Test category visuals
    print("\n📊 Category Visuals:")
    for category in [
        "agents",
        "leaders",
        "departments",
        "divisions",
        "database",
        "servers",
    ]:
        visual = visual_cache.get_visual(category)
        print(f"  • {category}: {visual['icon']} ({visual['color']})")

    # Test some department visuals
    print("\n🏢 Sample Department Visuals:")
    test_depts = [
        "Executive Leadership",
        "Engineering Department",
        "Security Department",
    ]
    for dept in test_depts:
        visual = visual_cache.get_visual("departments", entity_name=dept)
        print(f"  • {dept}: {visual['icon']} ({visual['color']})")

    # Test metrics integration
    print("\n2. Testing Metrics Integration")
    hq_metrics = HQMetricsIntegration(db_config)

    # Get all metrics
    all_metrics = hq_metrics.get_all_metrics(force_refresh=True)

    print("\n📈 Metrics Summary:")
    for category, data in all_metrics.items():
        if category != "timestamp" and isinstance(data, dict):
            summary = data.get("summary", {})
            if summary:
                print(f"\n  {category.upper()}:")
                for key, value in summary.items():
                    if hasattr(value, "value"):
                        print(f"    • {key}: {value.value}")
                    else:
                        print(f"    • {key}: {value}")

    # Test summary cards generation
    print("\n3. Testing Summary Cards HTML Generation")
    summary_html = hq_metrics.get_dashboard_summary_cards()

    # Count how many cards use database colors
    import re

    gradient_matches = re.findall(
        r"background: linear-gradient\(135deg, (#[a-fA-F0-9]{6})", summary_html
    )
    print(f"\n  Found {len(gradient_matches)} metric cards with colors:")
    for i, color in enumerate(gradient_matches, 1):
        print(f"    {i}. {color}")

    # Test agent metrics cards
    print("\n4. Testing Agent Metrics Cards")
    agent_cards_html = hq_metrics.get_agent_metrics_cards()

    # Check for visual integration
    if "fa-robot" in agent_cards_html and "#3b82f6" in agent_cards_html:
        print("  ✅ Agent cards using database visual metadata")
    else:
        print("  ❌ Agent cards not using visual metadata properly")

    # Test department metrics cards
    print("\n5. Testing Department Metrics Cards")
    dept_cards_html = hq_metrics.get_department_metrics_cards()

    # Check for visual integration
    if "fa-building" in dept_cards_html and "fa-sitemap" in dept_cards_html:
        print("  ✅ Department cards using database visual metadata")
    else:
        print("  ❌ Department cards not using visual metadata properly")

    # Test individual entity cards
    print("\n6. Testing Individual Entity Visual Metadata")

    # Check a few departments
    dept_data = all_metrics.get("departments", {}).get("individual", [])
    if dept_data and len(dept_data) > 0:
        print("\n  Sample Department Colors:")
        for dept in dept_data[:5]:
            if hasattr(dept, "color") and dept.color:
                print(f"    • {dept.name}: {dept.icon} ({dept.color})")

    # Check agents
    agent_data = all_metrics.get("agents", {}).get("individual", [])
    if agent_data and len(agent_data) > 0:
        print("\n  Sample Agent Visual Data:")
        for agent in agent_data[:3]:
            if hasattr(agent, "color") and agent.color:
                print(f"    • {agent.name}: {agent.icon} ({agent.color})")

    print("\n✅ Visual metrics integration test complete!")


if __name__ == "__main__":
    test_visual_integration()
