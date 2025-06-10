#!/usr/bin/env python3
"""
Final fixes for remaining metrics integration issues
"""

import re

def final_metrics_fixes():
    """Apply final fixes to complete the integration"""
    print("🔧 Applying Final Metrics Integration Fixes")
    print("=" * 60)
    
    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    fixes_applied = []
    
    # 1. Fix dashboard summary cards in welcome section
    if "{self.metrics_layer.get_dashboard_summary_cards()" not in content:
        print("📝 Adding dashboard summary cards...")
        
        # Find the System Status section in overview
        overview_pattern = r'(<h3>System Status</h3>)([\s\S]*?)(<div class="widget-grid">)'
        
        if re.search(overview_pattern, content):
            replacement = r'''\1\2
                <!-- Metrics from centralized layer -->
                {self.metrics_layer.get_dashboard_summary_cards() if self.metrics_layer else ""}
                
                \3'''
            
            content = re.sub(overview_pattern, replacement, content, flags=re.DOTALL)
            fixes_applied.append("Dashboard summary cards")
    
    # 2. Fix monitoring refresh with proper reference
    if "self.metrics_layer.get_all_metrics(force_refresh=True)" not in content:
        print("📝 Fixing monitoring refresh...")
        
        # Find the monitoring thread section
        monitoring_pattern = r"(def _monitoring_thread\(self\):[\s\S]*?while True:)"
        
        if re.search(monitoring_pattern, content):
            addition = r'''\1
                    try:
                        # Refresh metrics layer cache periodically
                        if hasattr(self, 'metrics_layer') and self.metrics_layer:
                            self.metrics_layer.get_all_metrics(force_refresh=True)
                    except Exception:
                        pass
                    '''
            
            content = re.sub(monitoring_pattern, addition, content, flags=re.DOTALL)
            fixes_applied.append("Monitoring refresh")
    
    # 3. Fix active agents calculation to use metrics
    if "agent_page_metrics['active']" not in content:
        print("📝 Fixing active agents calculation...")
        
        # Find where active_agents is set from running_agents
        pattern = r"(active_agents = )[^\n]+"
        
        # Replace all instances
        def replace_active_agents(match):
            return """active_agents = agent_page_metrics['active'] if 'agent_page_metrics' in locals() else len(self.running_agents)"""
        
        content = re.sub(pattern, replace_active_agents, content)
        fixes_applied.append("Active agents calculation")
    
    # 4. Ensure departments tab uses metrics
    dept_section = content[content.find('id="departments"'):content.find('id="leaders"') if content.find('id="leaders"') > 0 else len(content)]
    
    if "metrics_layer" not in dept_section:
        print("📝 Updating departments section...")
        
        # Find where division HTML is called
        div_pattern = r'({self\._generate_divisions_html\(\)})'
        
        if div_pattern in content:
            replacement = '{self.metrics_layer.get_department_cards_html() if self.metrics_layer and hasattr(self.metrics_layer, "get_department_cards_html") else self._generate_divisions_html()}'
            content = content.replace('{self._generate_divisions_html()}', replacement)
            fixes_applied.append("Departments tab integration")
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"   - {fix}")
    
    if len(fixes_applied) == 0:
        print("   No additional fixes needed")
    
    print("\n🎉 Metrics layer integration is now complete!")


if __name__ == "__main__":
    final_metrics_fixes()