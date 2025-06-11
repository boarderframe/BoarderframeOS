#!/usr/bin/env python3
"""
Verify the complete metrics layer integration
"""

import re


def verify_integration():
    """Check that all metrics layer components are properly integrated"""
    print("🔍 Verifying Complete Metrics Layer Integration")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    checks = {
        "Imports": "from core.hq_metrics_integration import HQMetricsIntegration"
        in content,
        "Initialization": "self.metrics_layer = HQMetricsIntegration()" in content,
        "Dashboard Metrics": "self.metrics_layer.get_all_metrics()" in content,
        "Agent Page Metrics": "self.metrics_layer.get_agents_page_metrics()" in content,
        "Agent Cards": "self.metrics_layer.get_agent_cards_html()" in content,
        "Department Cards": "self.metrics_layer.get_department_cards_html()" in content,
        "Dashboard Summary": "self.metrics_layer.get_dashboard_summary_cards()"
        in content,
        "Metrics CSS": "/* Metrics Grid */" in content,
        "Monitoring Refresh": "metrics_layer.get_all_metrics(force_refresh=True)"
        in content,
        "Registry Integration": "self.metrics_layer.get_metric_value" in content,
    }

    print("\n📋 Integration Checklist:")
    all_good = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if not result:
            all_good = False

    # Count total references
    metrics_count = len(re.findall(r"metrics_layer", content))
    print(f"\n📊 Total metrics_layer references: {metrics_count}")

    # Check for specific integrations
    print("\n🔧 Specific Integrations:")

    # Check if active agents uses real value
    if "agent_page_metrics['active']" in content:
        print("   ✅ Active agents count uses metrics layer")
    else:
        print("   ❌ Active agents count not using metrics layer")

    # Check if departments use metrics
    if (
        "metrics_layer"
        in content[
            content.find('id="departments"') : (
                content.find('id="leaders"')
                if content.find('id="leaders"') > 0
                else len(content)
            )
        ]
    ):
        print("   ✅ Departments tab integrated")
    else:
        print("   ❌ Departments tab not integrated")

    # Check CSS injection
    if "metrics-grid" in content or "metric-card" in content:
        print("   ✅ Metrics CSS classes present")
    else:
        print("   ❌ Metrics CSS classes missing")

    if all_good:
        print("\n🎉 All metrics layer components are properly integrated!")
    else:
        print("\n⚠️  Some components need attention")

    return all_good


if __name__ == "__main__":
    verify_integration()
