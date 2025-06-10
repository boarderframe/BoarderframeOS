#!/usr/bin/env python3
"""
Add page-specific methods to HQMetricsIntegration
"""

def add_page_methods():
    """Add the missing page methods to HQMetricsIntegration"""
    print("🔧 Adding Page Methods to HQMetricsIntegration")
    print("=" * 60)
    
    file_path = "/Users/cosburn/BoarderframeOS/core/hq_metrics_integration.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if methods already exist
    if "get_agent_metrics_cards" in content:
        print("⚠️ Methods already exist, skipping")
        return
    
    # Find the last method in the class
    last_method_end = content.rfind("        return html")
    if last_method_end < 0:
        print("❌ Could not find insertion point")
        return
    
    # Find the end of that return statement
    insertion_point = content.find("\n", last_method_end) + 1
    
    # New methods to add
    new_methods = '''
    def get_agent_metrics_cards(self) -> str:
        """Generate metric cards for the agents page"""
        metrics = self.get_all_metrics()
        agent_metrics = self.get_agents_page_metrics()
        
        cards_html = f"""
        <div style="display: flex; justify-content: space-around; gap: 2rem; align-items: stretch; flex-wrap: nowrap;">
            <div class="metric-card">
                <div class="metric-header">
                    <i class="fas fa-check-circle" style="color: #10b981;"></i>
                    <span>Active</span>
                </div>
                <div class="metric-value" style="color: #10b981;">
                    {agent_metrics['active']}
                </div>
                <div class="metric-subtitle">Currently Running</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <i class="fas fa-pause-circle" style="color: #f59e0b;"></i>
                    <span>Inactive</span>
                </div>
                <div class="metric-value" style="color: #f59e0b;">
                    {agent_metrics['inactive']}
                </div>
                <div class="metric-subtitle">Not Running</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <i class="fas fa-robot" style="color: #3b82f6;"></i>
                    <span>Total</span>
                </div>
                <div class="metric-value" style="color: #3b82f6;">
                    {agent_metrics['total']}
                </div>
                <div class="metric-subtitle">Registered Agents</div>
            </div>
        </div>
        """
        
        return cards_html
    
    def get_department_metrics_cards(self) -> str:
        """Generate metric cards for the departments page"""
        metrics = self.get_all_metrics()
        dept_data = metrics.get('departments', {})
        dept_summary = dept_data.get('summary', {})
        
        total = self.get_metric_value('departments', 'summary.total', 45)
        active = self.get_metric_value('departments', 'summary.active', 45)
        divisions = self.get_metric_value('departments', 'summary.divisions', 9)
        
        cards_html = f"""
        <div style="display: flex; justify-content: space-around; gap: 2rem; align-items: stretch; flex-wrap: nowrap; margin-bottom: 2rem;">
            <div class="metric-card">
                <div class="metric-header">
                    <i class="fas fa-building" style="color: #ec4899;"></i>
                    <span>Total Departments</span>
                </div>
                <div class="metric-value" style="color: #ec4899;">
                    {total}
                </div>
                <div class="metric-subtitle">Across Organization</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <i class="fas fa-check-circle" style="color: #10b981;"></i>
                    <span>Active</span>
                </div>
                <div class="metric-value" style="color: #10b981;">
                    {active}
                </div>
                <div class="metric-subtitle">Operational</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-header">
                    <i class="fas fa-sitemap" style="color: #8b5cf6;"></i>
                    <span>Divisions</span>
                </div>
                <div class="metric-value" style="color: #8b5cf6;">
                    {divisions}
                </div>
                <div class="metric-subtitle">Organizational Units</div>
            </div>
        </div>
        """
        
        return cards_html
    
    def get_leaders_page_html(self) -> str:
        """Generate complete leaders page with metrics"""
        metrics = self.get_all_metrics()
        
        # For now, return a placeholder that indicates metrics integration
        # In a full implementation, this would query leader data
        html = """
        <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #8b5cf620; background: linear-gradient(135deg, #8b5cf608, #8b5cf603);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="
                        width: 60px; height: 60px; 
                        background: linear-gradient(135deg, #8b5cf6, #8b5cf6cc); 
                        border-radius: 12px; 
                        display: flex; align-items: center; justify-content: center; 
                        color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #8b5cf640;
                    ">
                        <i class="fas fa-crown"></i>
                    </div>
                    <div>
                        <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Leadership Overview</h3>
                        <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                            Executive and department leadership • Metrics powered view
                        </p>
                    </div>
                </div>
            </div>
            
            <div class="metrics-note" style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                <i class="fas fa-chart-line" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <h4>Leaders Metrics Integration</h4>
                <p>Leaders data will be displayed here using the metrics layer.</p>
                <p style="margin-top: 1rem; font-size: 0.9rem;">
                    This page will show leadership hierarchy, department heads, and performance metrics.
                </p>
            </div>
        </div>
        """
        
        return html
    
    def get_divisions_page_html(self) -> str:
        """Generate complete divisions page with metrics"""
        metrics = self.get_all_metrics()
        dept_data = metrics.get('departments', {})
        
        # Group departments by division
        divisions_map = {}
        for dept in dept_data.get('individual', []):
            division = dept.metrics.get('division', self.calculator.MetricValue('Unassigned', '')).value
            if division not in divisions_map:
                divisions_map[division] = []
            divisions_map[division].append(dept)
        
        html = f"""
        <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #7c3aed20; background: linear-gradient(135deg, #7c3aed08, #7c3aed03);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="
                        width: 60px; height: 60px; 
                        background: linear-gradient(135deg, #7c3aed, #7c3aed cc); 
                        border-radius: 12px; 
                        display: flex; align-items: center; justify-content: center; 
                        color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #7c3aed40;
                    ">
                        <i class="fas fa-sitemap"></i>
                    </div>
                    <div>
                        <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Divisions Overview</h3>
                        <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                            {len(divisions_map)} divisions • Organizational structure powered by metrics
                        </p>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Division cards
        html += '<div class="divisions-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem;">'
        
        for division_name, departments in divisions_map.items():
            dept_count = len(departments)
            agent_count = sum(d.metrics.get('agents_total', self.calculator.MetricValue(0, '')).value for d in departments)
            
            html += f"""
            <div class="division-card" style="
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 1.5rem;
                transition: transform 0.2s ease;
            ">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <div style="
                        width: 48px; height: 48px;
                        background: linear-gradient(135deg, #7c3aed, #6d28d9);
                        border-radius: 10px;
                        display: flex; align-items: center; justify-content: center;
                        color: white;
                    ">
                        <i class="fas fa-sitemap"></i>
                    </div>
                    <div>
                        <h4 style="margin: 0; color: var(--primary-text);">{division_name}</h4>
                        <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.875rem;">
                            {dept_count} departments • {agent_count} agents
                        </p>
                    </div>
                </div>
                
                <div style="border-top: 1px solid var(--border-color); padding-top: 1rem;">
                    <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.5rem;">
                        DEPARTMENTS
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
            """
            
            # Add department chips
            for i, dept in enumerate(departments[:3]):
                html += f'<span style="background: var(--secondary-bg); padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem;">{dept.name}</span>'
            
            if dept_count > 3:
                html += f'<span style="color: var(--secondary-text); font-size: 0.8rem;">+{dept_count - 3} more</span>'
            
            html += """
                    </div>
                </div>
            </div>
            """
        
        html += '</div>'
        
        return html
'''
    
    # Insert the new methods
    content = content[:insertion_point] + new_methods + content[insertion_point:]
    
    # Write the updated content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Successfully added page methods to HQMetricsIntegration:")
    print("   - get_agent_metrics_cards()")
    print("   - get_department_metrics_cards()")
    print("   - get_leaders_page_html()")
    print("   - get_divisions_page_html()")


if __name__ == "__main__":
    add_page_methods()