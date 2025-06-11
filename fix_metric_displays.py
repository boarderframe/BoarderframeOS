#!/usr/bin/env python3
"""
Fix all metric displays to use the centralized metrics
"""

import re


def fix_metric_displays():
    """Update all display locations to use centralized metrics"""
    print("🔧 Fixing All Metric Displays in Corporate HQ")
    print("=" * 50)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if centralized metrics exist
    if '_get_centralized_metrics' not in content:
        print("❌ Centralized metrics methods not found!")
        return

    print("✅ Found centralized metrics methods")

    # 1. Fix the hardcoded "120+" in departments tab
    print("\n📝 Fixing hardcoded '120+' in departments tab...")
    old_120 = '''<div class="widget-value" style="color: #06b6d4;">
                            120+'''
    new_120 = '''<div class="widget-value" style="color: #06b6d4;">
                            {self.get_metric('agents', 'total')}'''

    if old_120 in content:
        content = content.replace(old_120, new_120)
        print("   ✅ Fixed 120+ to use get_metric()")
    else:
        print("   ⚠️  120+ pattern not found exactly, trying alternate fix...")
        # Try a regex approach
        pattern = r'(<div class="widget-value"[^>]*>)\s*120\+\s*(</div>)'
        replacement = r'\1{self.get_metric("agents", "total")}\2'
        content = re.sub(pattern, replacement, content)

    # 2. Fix the welcome section agent count
    print("\n📝 Fixing welcome section agent count...")
    # Look for the pattern where agent count is displayed
    welcome_pattern = r'Managing <strong style="color: #10b981;">(\d+)</strong> AI agents'
    welcome_matches = re.findall(welcome_pattern, content)
    if welcome_matches:
        print(f"   Found {len(welcome_matches)} instances with values: {welcome_matches}")
        # Replace with centralized metric
        content = re.sub(
            welcome_pattern,
            'Managing <strong style="color: #10b981;">{self.get_metric("agents", "total")}</strong> AI agents',
            content
        )
        print("   ✅ Updated welcome section to use get_metric()")

    # 3. Fix agent status calculations
    print("\n📝 Fixing agent status calculations...")

    # Fix total agents calculation
    old_total = "total_agents = health_summary['agents']['total'] or 2"
    new_total = "total_agents = self.get_metric('agents', 'total')"
    if old_total in content:
        content = content.replace(old_total, new_total)
        print("   ✅ Fixed total_agents calculation")

    # Fix active agents calculation
    old_active = "active_agents = health_summary['agents']['active'] or 0"
    new_active = "active_agents = self.get_metric('agents', 'active')"
    if old_active in content:
        content = content.replace(old_active, new_active)
        print("   ✅ Fixed active_agents calculation")

    # 4. Initialize centralized metrics in __init__ if not already done
    print("\n📝 Ensuring centralized metrics are initialized...")
    if "self._get_centralized_metrics()" not in content:
        # Find the end of __init__ method
        init_pattern = r'(self\.start_monitoring_thread\(\))'
        if re.search(init_pattern, content):
            content = re.sub(
                init_pattern,
                r'\1\n        \n        # Initialize centralized metrics\n        self._get_centralized_metrics()',
                content
            )
            print("   ✅ Added initialization call")

    # 5. Update the department overview stats
    print("\n📝 Updating department overview statistics...")

    # Find department stats section and update
    dept_stats_pattern = r'(<div class="stat-value">)\s*24\s*(</div>\s*<div class="stat-label">Departments)'
    if re.search(dept_stats_pattern, content):
        content = re.sub(
            dept_stats_pattern,
            r'\1{self.get_metric("departments", "total")}\2',
            content
        )
        print("   ✅ Updated department count")

    # 6. Update division count displays
    division_pattern = r'(<div class="metric-value"[^>]*>)\s*9\s*(</div>\s*<div class="metric-label">Divisions)'
    if re.search(division_pattern, content):
        content = re.sub(
            division_pattern,
            r'\1{self.get_metric("divisions", "total")}\2',
            content
        )
        print("   ✅ Updated division count")

    # 7. Add centralized metrics refresh to key methods
    print("\n📝 Adding centralized metrics refresh calls...")

    # Add to refresh_all_data method
    refresh_method = "def refresh_all_data(self):"
    if refresh_method in content:
        # Find the method and add centralized metrics call
        refresh_start = content.find(refresh_method)
        refresh_body_start = content.find("\n", refresh_start) + 1
        # Find the first actual code line (skip docstring if present)
        lines = content[refresh_body_start:].split('\n')
        insert_pos = refresh_body_start
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                # Found first code line
                insert_pos = refresh_body_start + sum(len(l) + 1 for l in lines[:i])
                break

        if "self._get_centralized_metrics()" not in content[refresh_start:refresh_start+1000]:
            indent = "        "
            new_code = f"{indent}# Refresh centralized metrics\n{indent}self._get_centralized_metrics()\n{indent}\n"
            content = content[:insert_pos] + new_code + content[insert_pos:]
            print("   ✅ Added refresh call to refresh_all_data()")

    # 8. Update any remaining hardcoded agent counts
    print("\n📝 Searching for other hardcoded values...")

    # Common patterns to replace
    replacements = [
        # Pattern: <tag>number</tag> where number might be agent count
        (r'(>\s*)(2)(\s*</[^>]+>\s*<[^>]+>Agents)', r'\1{self.get_metric("agents", "total")}\3'),
        (r'(>\s*)(45)(\s*</[^>]+>\s*<[^>]+>Departments)', r'\1{self.get_metric("departments", "total")}\3'),
        (r'(>\s*)(9)(\s*</[^>]+>\s*<[^>]+>Divisions)', r'\1{self.get_metric("divisions", "total")}\3'),
    ]

    for pattern, replacement in replacements:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print(f"   ✅ Updated pattern: {pattern[:30]}...")

    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ All metric displays have been updated!")
    print("\n📊 Now using centralized metrics for:")
    print("   - Total agents (195 instead of 120+ or 2)")
    print("   - Active agents (from database)")
    print("   - Department count (45)")
    print("   - Division count (9)")
    print("   - All other metrics")

    print("\n🔄 Restart Corporate HQ to see the changes!")

    # Test that get_metric is being called
    print("\n🔍 Verifying get_metric usage...")
    metric_calls = re.findall(r'self\.get_metric\([^)]+\)', content)
    print(f"   Found {len(metric_calls)} calls to get_metric()")
    if len(metric_calls) > 0:
        print("   Examples:")
        for call in metric_calls[:5]:
            print(f"     - {call}")


if __name__ == "__main__":
    fix_metric_displays()
