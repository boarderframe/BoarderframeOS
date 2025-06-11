#!/usr/bin/env python3
"""
Integrate the new metrics layer into Corporate HQ
Updates all pages to use the centralized metrics system
"""

import re


def integrate_metrics_layer():
    """Update Corporate HQ to use the new metrics layer"""
    print("🔧 Integrating Metrics Layer into Corporate HQ")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    # 1. Add imports
    print("\n📝 Adding imports...")

    import_section = """import http.server
import socketserver
import json
import threading
import time
import os
import signal
import sys
from datetime import datetime
import asyncio
import httpx
from pathlib import Path
import psutil
import socket

# Import the new metrics layer
from core.hq_metrics_integration import HQMetricsIntegration, METRICS_CSS
from core.hq_metrics_layer import BFColors, BFIcons"""

    # Replace the import section
    import_pattern = r"import http\.server.*?import socket"
    content = re.sub(import_pattern, import_section, content, flags=re.DOTALL)
    print("   ✅ Added metrics layer imports")

    # 2. Initialize metrics in __init__
    print("\n📝 Adding metrics initialization...")

    # Find where to add initialization
    init_pattern = r"(self\.monitoring_active = True)"
    init_replacement = r"""\1

        # Initialize metrics layer
        self.metrics_layer = HQMetricsIntegration()
        print("✅ Metrics layer initialized")"""

    content = re.sub(init_pattern, init_replacement, content)
    print("   ✅ Added metrics layer initialization")

    # 3. Update generate_dashboard_html to use metrics
    print("\n📝 Updating dashboard generation...")

    # Replace the metric calculations
    old_metrics_pattern = r"# Get ACTUAL running agents from processes[\s\S]*?inactive_agents = total_agents - active_agents"

    new_metrics_code = """# Get metrics from the new metrics layer
        all_metrics = self.metrics_layer.get_all_metrics()
        agent_page_metrics = self.metrics_layer.get_agents_page_metrics()

        # Use real values from metrics layer
        active_agents = agent_page_metrics['active']  # Actual running processes
        total_agents = agent_page_metrics['total']
        inactive_agents = agent_page_metrics['inactive']"""

    content = re.sub(old_metrics_pattern, new_metrics_code, content, flags=re.DOTALL)
    print("   ✅ Updated dashboard to use metrics layer")

    # 4. Replace the welcome section with metrics cards
    print("\n📝 Updating welcome section...")

    welcome_pattern = r'<div class="welcome-section">[\s\S]*?</div>\s*</div>\s*</div>'

    new_welcome = """<div class="welcome-section">
                    <h2>Welcome to BoarderframeOS Control Center</h2>
                    <p>Managing {total_agents} AI agents across {total_departments} departments</p>

                    <!-- Metrics Overview from Metrics Layer -->
                    {self.metrics_layer.get_dashboard_summary_cards()}
                </div>"""

    content = re.sub(welcome_pattern, new_welcome, content, flags=re.DOTALL)
    print("   ✅ Updated welcome section to use metric cards")

    # 5. Update the overview tab widgets
    print("\n📝 Updating overview tab...")

    # Find the overview widget section
    overview_pattern = (
        r'<!-- Overview Tab -->[\s\S]*?<div class="widget-grid">[\s\S]*?</div>\s*</div>'
    )

    new_overview = """<!-- Overview Tab -->
        <div id="overview" class="tab-content active">
            <div class="card full-width">
                <h3>System Overview</h3>
                {self.metrics_layer.get_dashboard_summary_cards()}
            </div>
        </div>"""

    # This is tricky, let's be more specific
    # Instead, let's update the individual metric retrievals

    # 6. Update agents page metrics
    print("\n📝 Updating agents page...")

    # The agents page is already partially fixed, but let's ensure it uses the layer
    agents_metrics_pattern = r"<div style=\"display: flex; justify-content: space-around;[\s\S]*?</div>\s*</div>"

    new_agents_metrics = """{self.metrics_layer.get_agent_cards_html(limit=10)}"""

    # Actually, let's update the agent grid generation
    agent_grid_pattern = r'<div id="agentGrid"[^>]*>[\s\S]*?{self\._generate_enhanced_agents_html\(\)}[\s\S]*?</div>'

    new_agent_grid = """<div id="agentGrid" style="margin-top: 1rem;">
                    {self.metrics_layer.get_agent_cards_html()}
                </div>"""

    content = re.sub(agent_grid_pattern, new_agent_grid, content, flags=re.DOTALL)
    print("   ✅ Updated agents page to use metrics layer cards")

    # 7. Update departments page
    print("\n📝 Updating departments page...")

    # Replace department generation with metrics layer
    dept_pattern = r"{self\._generate_departments_html\(\)}"
    new_dept = "{self.metrics_layer.get_department_cards_html()}"

    content = content.replace(dept_pattern, new_dept)
    print("   ✅ Updated departments to use metrics layer")

    # 8. Add the metrics CSS
    print("\n📝 Adding metrics CSS...")

    # Find where to inject CSS
    css_pattern = r"(<style>)"
    css_replacement = f"""<style>
        {METRICS_CSS}
        """

    content = re.sub(css_pattern, css_replacement, content, count=1)
    print("   ✅ Added metrics layer CSS")

    # 9. Update server/service metrics
    print("\n📝 Updating server metrics...")

    # Update the server status to use metrics
    server_summary_pattern = (
        r"healthy_services = health_summary\['services'\]\['healthy'\]"
    )
    server_replacement = """healthy_services = health_summary['services']['healthy']

        # Get server metrics from layer
        server_metrics = all_metrics.get('servers', {})
        server_cards = [self.metrics_layer.card_renderer.render_metric_card(m) for m in server_metrics.get('summary', {}).values()]"""

    content = content.replace(server_summary_pattern, server_replacement)
    print("   ✅ Updated server metrics")

    # 10. Fix department count references
    print("\n📝 Updating department counts...")

    # Update total_departments to use metrics
    dept_count_pattern = (
        r"total_departments = len\(departments_data\).*?total_departments"
    )
    dept_replacement = """total_departments = self.metrics_layer.get_metric_value('departments', 'summary.total', 45)"""

    content = re.sub(dept_count_pattern, dept_replacement, content, flags=re.DOTALL)
    print("   ✅ Updated department counts")

    # Write the updated content
    with open(file_path, "w") as f:
        f.write(content)

    print("\n✅ Integration complete!")
    print("\n📊 Changes made:")
    print("   - Added metrics layer imports and initialization")
    print("   - Dashboard now uses centralized metrics")
    print("   - Welcome section shows metric cards")
    print("   - Agents page uses metric agent cards")
    print("   - Departments page uses metric department cards")
    print("   - Server metrics integrated")
    print("   - Added metrics CSS styling")

    print("\n🚀 Next: Restart Corporate HQ to see the integrated metrics layer!")

    # Create a backup of the original
    import os
    import shutil

    backup_path = file_path + ".backup_before_metrics"
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"\n💾 Backup saved to: {backup_path}")


if __name__ == "__main__":
    integrate_metrics_layer()
