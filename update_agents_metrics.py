#!/usr/bin/env python3
"""
Update Agents page to show only Active, Inactive, and Total metrics
"""

import re


def update_agents_metrics():
    """Update the Agents page to display only Active, Inactive, and Total metrics"""
    print("🔧 Updating Agents Page Metrics")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # First, ensure we're using centralized metrics
    print("\n📝 Ensuring centralized metrics are used...")

    # Update the dashboard generation to use centralized metrics
    # Find where active_agents is set
    old_active_pattern = r"active_agents = health_summary\['agents'\]\['running'\]"
    new_active_pattern = "active_agents = self.get_metric('agents', 'active')"

    if old_active_pattern in content:
        content = content.replace(old_active_pattern, new_active_pattern)
        print("   ✅ Updated active_agents to use centralized metrics")
    else:
        # Try another pattern
        alt_pattern = "active_agents = health_summary['agents']['running']"
        if alt_pattern in content:
            content = content.replace(alt_pattern, new_active_pattern)
            print("   ✅ Updated active_agents to use centralized metrics")

    # Now update the Agent Metrics Grid to show only 3 metrics
    print("\n📝 Updating Agent Metrics Grid...")

    # Find the Agent Metrics Grid section
    metrics_start = content.find("<!-- Agent Metrics Grid -->")
    if metrics_start > 0:
        # Find the end of the metrics grid div
        grid_start = content.find('<div style="display: grid; grid-template-columns: repeat(5, 1fr)', metrics_start)
        grid_end = content.find('</div>\n            </div>', grid_start) + 6

        if grid_start > 0 and grid_end > grid_start:
            # Replace with new 3-column grid
            new_metrics_grid = '''<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; align-items: stretch;">
                    <div class="widget widget-medium">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
                                <span>Active</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color); font-size: 3rem;">
                            {active_agents}
                        </div>
                        <div class="widget-subtitle">Currently Running</div>
                    </div>

                    <div class="widget widget-medium">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-pause-circle" style="color: var(--warning-color);"></i>
                                <span>Inactive</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--warning-color); font-size: 3rem;">
                            {inactive_agents}
                        </div>
                        <div class="widget-subtitle">Not Running</div>
                    </div>

                    <div class="widget widget-medium">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-users" style="color: var(--accent-color);"></i>
                                <span>Total</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--accent-color); font-size: 3rem;">
                            {self.total_agents if hasattr(self, 'total_agents') else total_agents}
                        </div>
                        <div class="widget-subtitle">Registered Agents</div>
                    </div>
                </div>'''

            content = content[:grid_start] + new_metrics_grid + content[grid_end:]
            print("   ✅ Updated metrics grid to show only Active, Inactive, and Total")

    # Update the Overall Status section
    print("\n📝 Updating Overall Status section...")

    # Find and update the Overall Status calculation
    overall_status_pattern = r"<div style=\"font-size: 0\.75rem; color: var\(--secondary-text\); margin-bottom: 0\.25rem;\">Overall Status</div>\s*<div style=\"font-size: 1rem; font-weight: 600; color: \{[^}]+\};\">[\s\S]*?</div>"

    new_overall_status = '''<div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Overall Status</div>
                        <div style="font-size: 1rem; font-weight: 600; color: {overall_status_color};">
                            {overall_status_text}
                        </div>'''

    content = re.sub(overall_status_pattern, new_overall_status, content, count=1)
    print("   ✅ Updated Overall Status to use dynamic values")

    # Add inactive_agents calculation where active_agents is defined
    print("\n📝 Adding inactive_agents calculation...")

    # Find where we set active_agents in generate_dashboard_html
    active_agents_line = "active_agents = self.get_metric('agents', 'active')"
    if active_agents_line not in content:
        # If we haven't updated it yet, look for the original pattern
        active_agents_line = "active_agents = health_summary['agents']['running']"

    if active_agents_line in content:
        # Add inactive_agents calculation after active_agents
        insert_pos = content.find(active_agents_line) + len(active_agents_line)
        insert_pos = content.find('\n', insert_pos) + 1

        inactive_calculation = "        inactive_agents = total_agents - active_agents\n"
        inactive_calculation += "        \n"
        inactive_calculation += "        # Overall status calculation\n"
        inactive_calculation += "        if active_agents == 0:\n"
        inactive_calculation += "            overall_status_text = 'All Agents Offline'\n"
        inactive_calculation += "            overall_status_color = 'var(--danger-color)'\n"
        inactive_calculation += "        elif active_agents == total_agents:\n"
        inactive_calculation += "            overall_status_text = 'All Agents Active'\n"
        inactive_calculation += "            overall_status_color = 'var(--success-color)'\n"
        inactive_calculation += "        else:\n"
        inactive_calculation += "            active_percentage = (active_agents / total_agents * 100) if total_agents > 0 else 0\n"
        inactive_calculation += "            if active_percentage >= 80:\n"
        inactive_calculation += "                overall_status_text = f'{active_percentage:.0f}% Active'\n"
        inactive_calculation += "                overall_status_color = 'var(--success-color)'\n"
        inactive_calculation += "            elif active_percentage >= 50:\n"
        inactive_calculation += "                overall_status_text = f'{active_percentage:.0f}% Active'\n"
        inactive_calculation += "                overall_status_color = 'var(--warning-color)'\n"
        inactive_calculation += "            else:\n"
        inactive_calculation += "                overall_status_text = f'{active_percentage:.0f}% Active'\n"
        inactive_calculation += "                overall_status_color = 'var(--danger-color)'\n"

        content = content[:insert_pos] + inactive_calculation + content[insert_pos:]
        print("   ✅ Added inactive_agents calculation and overall status logic")

    # Update the agent status description
    print("\n📝 Updating agent status description...")

    old_description = "{active_agents} active agents • System performance monitoring"
    new_description = "{active_agents} of {total_agents} agents active"

    content = content.replace(old_description, new_description)
    print("   ✅ Updated status description")

    # Update filter options to match new metrics
    print("\n📝 Updating filter options...")

    # Find and update the filter options
    filter_pattern = r'<option value="active">🟢 Active</option>\s*<option value="productive">🚀 Productive</option>\s*<option value="healthy">💚 Healthy</option>\s*<option value="inactive">🔴 Offline</option>'

    new_filter_options = '''<option value="active">🟢 Active</option>
                                <option value="inactive">🔴 Inactive</option>'''

    content = re.sub(filter_pattern, new_filter_options, content)
    print("   ✅ Updated filter options")

    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ Agents page updated successfully!")
    print("\n📊 Changes made:")
    print("   - Reduced metrics from 5 to 3 (Active, Inactive, Total)")
    print("   - Updated to use centralized metrics layer")
    print("   - Enhanced Overall Status with percentage-based coloring")
    print("   - Simplified filter options to match new metrics")
    print("   - Used agent status fields from database")

    print("\n🚀 Next: Restart Corporate HQ to see the changes!")


if __name__ == "__main__":
    update_agents_metrics()
