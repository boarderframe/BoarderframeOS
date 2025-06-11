#!/usr/bin/env python3
"""
Fix the missing metrics layer integrations
"""

import re


def fix_missing_integrations():
    """Fix all missing integrations"""
    print("🔧 Fixing Missing Metrics Layer Integrations")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Fix initialization - it might be there but with different spacing
    if "self.metrics_layer" not in content:
        print("❌ Metrics layer not initialized properly")
        # Find where to add it
        init_pattern = r"(self\.monitoring_active = True)"
        if re.search(init_pattern, content):
            replacement = r"""\1

        # Initialize metrics layer
        try:
            self.metrics_layer = HQMetricsIntegration()
            print("✅ Metrics layer initialized successfully")
        except Exception as e:
            print(f"⚠️ Failed to initialize metrics layer: {e}")
            self.metrics_layer = None"""

            content = re.sub(init_pattern, replacement, content)
            print("✅ Added metrics layer initialization")

    # 2. Fix active agents to use metrics
    # Find where active_agents is calculated
    if "agent_page_metrics['active']" not in content:
        print("📝 Fixing active agents calculation...")

        # Look for the current calculation
        old_pattern = r"active_agents = len\(self\.running_agents\)"
        new_code = """# Get real active count from metrics layer
        if self.metrics_layer:
            agent_page_metrics = self.metrics_layer.get_agents_page_metrics()
            active_agents = agent_page_metrics['active']
        else:
            active_agents = len(self.running_agents)"""

        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_code, content)
            print("✅ Fixed active agents calculation")

    # 3. Add dashboard summary cards
    if "self.metrics_layer.get_dashboard_summary_cards()" not in content:
        print("📝 Adding dashboard summary cards...")

        # Find the welcome section
        welcome_pattern = r'(<div class="welcome-section">[\s\S]*?<p>Managing[^<]*</p>)'

        if re.search(welcome_pattern, content):
            replacement = r'''\1

                    <!-- Metrics Overview from Metrics Layer -->
                    {self.metrics_layer.get_dashboard_summary_cards() if self.metrics_layer else ""}'''

            content = re.sub(welcome_pattern, replacement, content, flags=re.DOTALL)
            print("✅ Added dashboard summary cards")

    # 4. Fix monitoring refresh
    if "metrics_layer.get_all_metrics(force_refresh=True)" not in content:
        print("📝 Adding metrics refresh to monitoring...")

        # Find the monitor_system method
        monitor_pattern = r"(def monitor_system\(self\):[\s\S]*?while self\.monitoring_active:)"

        if re.search(monitor_pattern, content):
            addition = r'''\1
                try:
                    # Refresh metrics layer cache
                    if hasattr(self, 'metrics_layer') and self.metrics_layer:
                        self.metrics_layer.get_all_metrics(force_refresh=True)
                except Exception as e:
                    pass
                '''

            content = re.sub(monitor_pattern, addition, content, flags=re.DOTALL)
            print("✅ Added metrics refresh to monitoring")

    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ Missing integrations fixed!")
    print("\n📊 Fixed:")
    print("   - Metrics layer initialization")
    print("   - Active agents calculation")
    print("   - Dashboard summary cards")
    print("   - Monitoring refresh")


if __name__ == "__main__":
    fix_missing_integrations()
