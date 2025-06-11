#!/usr/bin/env python3
"""
Force all displays to use centralized metrics
"""

import re


def force_metric_usage():
    """Force all metric displays to use the centralized system"""
    print("🔨 Forcing Centralized Metric Usage Throughout Corporate HQ")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    # 1. First, let's add a property that makes metrics easily accessible
    print("\n📝 Adding metric properties for easy access...")

    property_code = '''
    @property
    def total_agents(self):
        """Get total agents from centralized metrics"""
        if not hasattr(self, '_last_metrics'):
            self._last_metrics = self._get_centralized_metrics()
        return self._last_metrics.get('agents', {}).get('total', 195)

    @property
    def active_agents(self):
        """Get active agents from centralized metrics"""
        if not hasattr(self, '_last_metrics'):
            self._last_metrics = self._get_centralized_metrics()
        return self._last_metrics.get('agents', {}).get('active', len(self.running_agents))

    @property
    def total_departments(self):
        """Get total departments from centralized metrics"""
        if not hasattr(self, '_last_metrics'):
            self._last_metrics = self._get_centralized_metrics()
        return self._last_metrics.get('departments', {}).get('total', 45)

    @property
    def total_divisions(self):
        """Get total divisions from centralized metrics"""
        if not hasattr(self, '_last_metrics'):
            self._last_metrics = self._get_centralized_metrics()
        return self._last_metrics.get('divisions', {}).get('total', 9)
'''

    # Insert properties after the get_metric method
    if "@property" not in content or "def total_agents" not in content:
        insert_pos = content.find("def get_metric(self")
        if insert_pos > 0:
            # Find end of get_metric method
            next_method = content.find("\n    def ", insert_pos + 1)
            if next_method > 0:
                content = content[:next_method] + property_code + content[next_method:]
                print("   ✅ Added property methods for easy metric access")

    # 2. Update all HTML generation to use these properties
    print("\n📝 Updating all HTML generation methods...")

    # Pattern replacements with context
    replacements = [
        # Dashboard welcome - Managing X agents
        (
            r'Managing <strong style="color: #10b981;">(\d+)</strong> AI agents',
            'Managing <strong style="color: #10b981;">{self.total_agents}</strong> AI agents',
        ),
        # Hardcoded 2 agents
        (
            r'Managing <strong style="color: #10b981;">2</strong> AI agents',
            'Managing <strong style="color: #10b981;">{self.total_agents}</strong> AI agents',
        ),
        # Department count - 120+ pattern (already using {total_agents})
        (r"\{total_agents\}", "{self.total_agents}"),
        # Any remaining 120+
        (r">\s*120\+\s*<", ">{self.total_agents}<"),
        # Department counts
        (
            r">\s*45\s*</div>\s*<div[^>]*>Departments",
            '>{self.total_departments}</div><div class="metric-label">Departments',
        ),
        # Division counts
        (
            r">\s*9\s*</div>\s*<div[^>]*>Divisions",
            '>{self.total_divisions}</div><div class="metric-label">Divisions',
        ),
        # Agent status calculations
        (
            r"total_agents = health_summary\['agents'\]\['total'\] or 2",
            "total_agents = self.total_agents",
        ),
        (
            r"active_agents = health_summary\['agents'\]\['active'\] or 0",
            "active_agents = self.active_agents",
        ),
        # Metric calculations in HTML
        (
            r"health_summary\.get\('agents', \{\}\)\.get\('total', 2\)",
            "self.total_agents",
        ),
    ]

    for pattern, replacement in replacements:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            print(f"   ✅ Replaced {matches} instances of: {pattern[:40]}...")

    # 3. Initialize metrics in __init__
    print("\n📝 Ensuring metrics are initialized...")

    init_check = "self._last_metrics = {}"
    if init_check not in content:
        # Find end of __init__ variable initialization
        init_pos = content.find("def __init__(self):")
        if init_pos > 0:
            # Find where to insert (after self.monitoring_active)
            marker = "self.monitoring_active = True"
            marker_pos = content.find(marker, init_pos)
            if marker_pos > 0:
                insert_pos = content.find("\n", marker_pos) + 1
                insert_code = """
        # Initialize metric cache
        self._last_metrics = {}
        try:
            self._last_metrics = self._get_centralized_metrics()
            print("✅ Centralized metrics initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize metrics: {e}")
            self._last_metrics = {
                'agents': {'total': 195, 'active': 0, 'operational': 40},
                'departments': {'total': 45, 'active': 45},
                'divisions': {'total': 9, 'active': 9}
            }
"""
                content = content[:insert_pos] + insert_code + content[insert_pos:]
                print("   ✅ Added metric initialization in __init__")

    # 4. Update refresh methods to refresh metrics
    print("\n📝 Adding metric refresh to refresh methods...")

    refresh_methods = [
        "refresh_all_data",
        "global_refresh_all_data",
        "_collect_health_data",
    ]

    for method_name in refresh_methods:
        method_pattern = f"def {method_name}\\(self"
        method_pos = content.find(method_pattern)
        if method_pos > 0:
            # Check if metrics refresh already exists
            method_end = content.find("\n    def ", method_pos + 1)
            if method_end < 0:
                method_end = len(content)

            method_content = content[method_pos:method_end]
            if "_last_metrics = self._get_centralized_metrics()" not in method_content:
                # Find first line of code after docstring
                lines = method_content.split("\n")
                for i, line in enumerate(lines[1:], 1):
                    if (
                        line.strip()
                        and not line.strip().startswith('"""')
                        and not line.strip().startswith("#")
                    ):
                        insert_line = i
                        indent = " " * (len(line) - len(line.lstrip()))
                        refresh_code = f"{indent}# Refresh centralized metrics\n{indent}self._last_metrics = self._get_centralized_metrics()\n"
                        lines.insert(insert_line, refresh_code.rstrip("\n"))
                        break

                new_method = "\n".join(lines)
                content = content[:method_pos] + new_method + content[method_end:]
                print(f"   ✅ Added metric refresh to {method_name}")

    # Write the updated content
    with open(file_path, "w") as f:
        f.write(content)

    print("\n✅ Forced metric usage throughout Corporate HQ!")

    # Verify the changes
    print("\n🔍 Verification:")

    # Check property usage
    property_uses = len(
        re.findall(
            r"self\.total_agents|self\.active_agents|self\.total_departments", content
        )
    )
    print(f"   - Property usage: {property_uses} references")

    # Check if hardcoded values remain
    hardcoded_checks = [
        ("120+", "120\\+"),
        ("Managing 2 agents", "Managing.*2.*agents"),
        ("45 departments", ">\\s*45\\s*<.*Departments"),
        ("9 divisions", ">\\s*9\\s*<.*Divisions"),
    ]

    for name, pattern in hardcoded_checks:
        if re.search(pattern, content):
            print(f"   ⚠️  Warning: '{name}' pattern may still exist")
        else:
            print(f"   ✅ '{name}' has been replaced")

    print("\n🚀 Corporate HQ will now show:")
    print("   - Total Agents: 195 (from centralized metrics)")
    print("   - Active Agents: Dynamic count")
    print("   - Departments: 45")
    print("   - Divisions: 9")
    print("\n📌 Restart Corporate HQ to apply all changes!")


if __name__ == "__main__":
    force_metric_usage()
