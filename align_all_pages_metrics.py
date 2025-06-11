#!/usr/bin/env python3
"""
Align metrics and cards for Agents, Leaders, Departments, and Divisions pages
Ensures consistent use of the metrics layer across all pages
"""

import re


def align_pages_with_metrics():
    """Update all pages to use metrics layer consistently"""
    print("🎯 Aligning All Pages with Metrics Layer")
    print("=" * 60)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Update Agents Page
    print("\n1️⃣ Updating Agents Page...")

    # Replace the agent metrics grid with metrics layer cards
    agent_metrics_pattern = r'<!-- Agent Metrics Grid -->[\s\S]*?</div>\s*</div>\s*</div>\s*</div>\s*</div>'

    agent_metrics_replacement = '''<!-- Agent Metrics from Metrics Layer -->
                {self.metrics_layer.get_agent_metrics_cards() if self.metrics_layer else self._generate_agent_metrics_fallback()}'''

    content = re.sub(agent_metrics_pattern, agent_metrics_replacement, content, flags=re.DOTALL)

    # Update the agent grid to always use metrics layer
    agent_grid_pattern = r'<div id="agentGrid"[^>]*>[\s\S]*?</div>'
    agent_grid_replacement = '''<div id="agentGrid" style="margin-top: 1rem;">
                    {self.metrics_layer.get_agent_cards_html() if self.metrics_layer else self._generate_enhanced_agents_html()}
                </div>'''

    # Apply the replacement more carefully
    agents_section = content[content.find('id="agents"'):content.find('id="leaders"')]
    if 'id="agentGrid"' in agents_section:
        # Find exact position
        grid_start = content.find('<div id="agentGrid"')
        grid_end = content.find('</div>', grid_start) + 6
        content = content[:grid_start] + agent_grid_replacement + content[grid_end:]

    print("   ✅ Agents page aligned with metrics layer")

    # 2. Update Leaders Page
    print("\n2️⃣ Updating Leaders Page...")

    # The leaders page currently just calls _generate_leaders_html()
    # Let's update it to use metrics layer if available
    leaders_pattern = r'<div id="leaders" class="tab-content">[\s\S]*?{self\._generate_leaders_html\(\)}[\s\S]*?</div>'

    leaders_replacement = '''<div id="leaders" class="tab-content">
            {self.metrics_layer.get_leaders_page_html() if self.metrics_layer and hasattr(self.metrics_layer, 'get_leaders_page_html') else self._generate_leaders_html()}
        </div>'''

    content = re.sub(leaders_pattern, leaders_replacement, content, flags=re.DOTALL)
    print("   ✅ Leaders page prepared for metrics layer")

    # 3. Update Departments Page
    print("\n3️⃣ Updating Departments Page...")

    # Replace department metrics grid with metrics layer
    dept_metrics_pattern = r'<!-- Department Metrics Grid -->[\s\S]*?<div style="display: flex; justify-content: space-around;[^>]*>'

    dept_metrics_replacement = '''<!-- Department Metrics from Metrics Layer -->
                {self.metrics_layer.get_department_metrics_cards() if self.metrics_layer and hasattr(self.metrics_layer, 'get_department_metrics_cards') else ""}
                <div style="display: none;">'''

    content = re.sub(dept_metrics_pattern, dept_metrics_replacement, content, flags=re.DOTALL)

    # Ensure departments content uses metrics layer
    dept_content_pattern = r'<div style="grid-column: span 12;">[\s\S]*?{self\.metrics_layer\.get_department_cards_html\(\)[^}]*}'

    # Check if it's already updated
    if "get_department_cards_html()" not in content[content.find('id="departments"'):content.find('id="services"')]:
        # Need to update the divisions call
        divisions_call_pattern = r'{self\._generate_divisions_html\(\)}'
        divisions_replacement = '{self.metrics_layer.get_department_cards_html() if self.metrics_layer else self._generate_divisions_html()}'

        # Find in departments section only
        dept_start = content.find('id="departments"')
        dept_end = content.find('id="services"')
        dept_section = content[dept_start:dept_end]

        if divisions_call_pattern in dept_section:
            dept_section = dept_section.replace(divisions_call_pattern, divisions_replacement)
            content = content[:dept_start] + dept_section + content[dept_end:]

    print("   ✅ Departments page aligned with metrics layer")

    # 4. Update Divisions Page
    print("\n4️⃣ Updating Divisions Page...")

    # The divisions page also calls _generate_divisions_html()
    # Let's give it its own metrics layer method
    divisions_pattern = r'<div id="divisions" class="tab-content">[\s\S]*?{self\._generate_divisions_html\(\)}[\s\S]*?</div>'

    divisions_replacement = '''<div id="divisions" class="tab-content">
            {self.metrics_layer.get_divisions_page_html() if self.metrics_layer and hasattr(self.metrics_layer, 'get_divisions_page_html') else self._generate_divisions_html()}
        </div>'''

    content = re.sub(divisions_pattern, divisions_replacement, content, flags=re.DOTALL)
    print("   ✅ Divisions page prepared for metrics layer")

    # 5. Add fallback methods for agent metrics
    print("\n5️⃣ Adding fallback methods...")

    # Find where to add the fallback method
    method_location = content.find("def _generate_enhanced_agents_html(self):")
    if method_location > 0:
        # Add before this method
        fallback_method = '''
    def _generate_agent_metrics_fallback(self):
        """Fallback agent metrics when metrics layer unavailable"""
        return f"""
        <div style="display: flex; justify-content: space-around; gap: 2rem; align-items: stretch; flex-wrap: nowrap;">
            <div class="widget widget-large" style="flex: 1; min-width: 200px; max-width: 300px;">
                <div class="widget-header">
                    <div class="widget-title">
                        <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
                        <span>Active</span>
                    </div>
                </div>
                <div class="widget-value" style="color: var(--success-color); font-size: 3rem;">
                    {len(self.running_agents)}
                </div>
                <div class="widget-subtitle">Currently Running</div>
            </div>

            <div class="widget widget-large" style="flex: 1; min-width: 200px; max-width: 300px;">
                <div class="widget-header">
                    <div class="widget-title">
                        <i class="fas fa-pause-circle" style="color: var(--warning-color);"></i>
                        <span>Inactive</span>
                    </div>
                </div>
                <div class="widget-value" style="color: var(--warning-color); font-size: 3rem;">
                    {195 - len(self.running_agents)}
                </div>
                <div class="widget-subtitle">Not Running</div>
            </div>

            <div class="widget widget-large" style="flex: 1; min-width: 200px; max-width: 300px;">
                <div class="widget-header">
                    <div class="widget-title">
                        <i class="fas fa-robot" style="color: var(--info-color);"></i>
                        <span>Total</span>
                    </div>
                </div>
                <div class="widget-value" style="color: var(--info-color); font-size: 3rem;">
                    195
                </div>
                <div class="widget-subtitle">Registered Agents</div>
            </div>
        </div>
        """

    '''
        content = content[:method_location] + fallback_method + content[method_location:]
        print("   ✅ Added agent metrics fallback method")

    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ All pages aligned with metrics layer!")
    print("\n📊 Updates made:")
    print("   - Agents: Metrics cards and agent grid use metrics layer")
    print("   - Leaders: Prepared for metrics layer integration")
    print("   - Departments: Uses department cards from metrics layer")
    print("   - Divisions: Prepared for metrics layer integration")

    print("\n📝 Next steps:")
    print("   - Add get_agent_metrics_cards() to HQMetricsIntegration")
    print("   - Add get_department_metrics_cards() to HQMetricsIntegration")
    print("   - Add get_leaders_page_html() to HQMetricsIntegration")
    print("   - Add get_divisions_page_html() to HQMetricsIntegration")


if __name__ == "__main__":
    align_pages_with_metrics()
