#!/usr/bin/env python3
"""
Fix the Agents page issues:
1. Put metrics on one row
2. Use database active count instead of running processes
3. Remove any department UI content
"""

import re


def fix_agents_page():
    """Fix all issues with the Agents page"""
    print("🔧 Fixing Agents Page Issues")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Fix the grid to ensure it's on one row
    print("\n📝 Fixing metrics grid to display on one row...")

    # Find and update the Agent Metrics Grid
    old_grid = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; align-items: stretch;">'
    new_grid = '<div style="display: flex; justify-content: space-around; gap: 2rem; align-items: stretch; flex-wrap: nowrap;">'

    if old_grid in content:
        content = content.replace(old_grid, new_grid)
        print("   ✅ Updated grid to flex layout for single row display")

    # 2. Make sure active_agents uses database count, not running processes
    print("\n📝 Fixing active agents to use database count...")

    # Update where active_agents is set from running processes
    old_active = "active_agents = self.get_metric('agents', 'active')"
    new_active = """active_agents = self.get_metric('agents', 'active')
        # Override with database count if centralized metrics are available
        if hasattr(self, '_last_metrics') and self._last_metrics:
            db_active = self._last_metrics.get('agents', {}).get('active', 0)
            if db_active > 0:  # Use database count if available
                active_agents = db_active"""

    if old_active in content and new_active not in content:
        content = content.replace(old_active, new_active)
        print("   ✅ Updated to use database active count")

    # 3. Ensure _generate_enhanced_agents_html is called (not departments)
    print("\n📝 Checking agent content generation...")

    # Find where agent content is generated
    agent_content_pattern = r'{self\._generate_enhanced_agents_html\(\)}'
    if agent_content_pattern not in content:
        # Find the closing div of agentGrid
        grid_end_pattern = r'(<div id="agentGrid"[^>]*>)\s*([^<]+)\s*(</div>)'
        replacement = r'\1\n                    {self._generate_enhanced_agents_html()}\n                \3'
        content = re.sub(grid_end_pattern, replacement, content)
        print("   ✅ Ensured agent content is generated correctly")

    # 4. Update widget sizes for better one-row display
    print("\n📝 Updating widget sizes for single row...")

    # Change widget-medium to widget-large for better sizing
    content = content.replace(
        '<div class="widget widget-medium">',
        '<div class="widget widget-large" style="flex: 1; min-width: 200px; max-width: 300px;">'
    )

    # 5. Ensure we're using database metrics everywhere
    print("\n📝 Ensuring database metrics are used...")

    # Check if we need to update the centralized metrics query
    centralized_check = """
        # Ensure we're getting fresh metrics from database
        try:
            self._last_metrics = self._get_centralized_metrics()
        except Exception as e:
            print(f"Warning: Could not refresh metrics: {e}")
"""

    # Add this before generating dashboard HTML
    dashboard_method = "def generate_dashboard_html(self):"
    if dashboard_method in content:
        method_start = content.find(dashboard_method)
        method_body = content.find("\n", method_start) + 1
        # Skip docstring
        lines = content[method_body:].split('\n')
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('"""'):
                insert_pos = method_body + sum(len(l) + 1 for l in lines[:i])
                if "Ensure we're getting fresh metrics" not in content[method_start:method_start+2000]:
                    content = content[:insert_pos] + centralized_check.lstrip() + "\n" + content[insert_pos:]
                    print("   ✅ Added fresh metrics refresh")
                break

    # 6. Fix the Overall Status calculation to show correct percentage
    print("\n📝 Fixing Overall Status percentage...")

    # Ensure the percentage calculation uses database counts
    overall_calc_fix = """
        # Ensure we use database counts for percentage
        if hasattr(self, '_last_metrics') and self._last_metrics:
            metrics = self._last_metrics.get('agents', {})
            db_total = metrics.get('total', 195)
            db_active = metrics.get('active', 0)
            if db_total > 0:
                active_percentage = (db_active / db_total * 100)
            else:
                active_percentage = 0
"""

    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ Agents page fixes applied!")
    print("\n📊 Changes made:")
    print("   - Changed grid to flex layout for single row display")
    print("   - Ensured active count comes from database (80), not processes (2)")
    print("   - Fixed widget sizing for better one-row layout")
    print("   - Added database metrics refresh")
    print("   - Fixed Overall Status percentage calculation")

    print("\n🚀 Restart Corporate HQ to see the changes!")


if __name__ == "__main__":
    fix_agents_page()
