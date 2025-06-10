#!/usr/bin/env python3
"""
Add metrics layer integration and create a Metrics page
"""

import re

def add_metrics_page():
    """Add metrics layer and create metrics page"""
    
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()
    
    print("Adding metrics layer integration and Metrics page...")
    
    # 1. Add imports for metrics layer
    imports_pattern = r'(import socket\n)'
    metrics_imports = '''import socket

# Metrics Layer Integration
from core.hq_metrics_integration import HQMetricsIntegration, METRICS_CSS
from core.hq_metrics_layer import BFColors, BFIcons, MetricValue
'''
    
    content = re.sub(imports_pattern, metrics_imports, content, count=1)
    print("✓ Added metrics layer imports")
    
    # 2. Initialize metrics layer in __init__
    init_pattern = r'(self\.monitoring_config = \{[^}]+\})'
    init_addition = r'''\1
        
        # Initialize metrics layer
        try:
            self.metrics_layer = HQMetricsIntegration(self)
            print("✓ Metrics layer initialized successfully")
        except Exception as e:
            print(f"⚠️ Failed to initialize metrics layer: {e}")
            self.metrics_layer = None'''
    
    content = re.sub(init_pattern, init_addition, content, count=1)
    print("✓ Added metrics layer initialization")
    
    # 3. Add Metrics navigation button
    # Find the database nav button and add after it
    nav_pattern = r'(<button class="nav-link" onclick="showTab\(\'database\'\)"[^>]+>[^<]+<i class="fas fa-database">[^<]+</i>[^<]+<span>Database</span>[^<]+</button>[^<]+</li>)'
    nav_addition = r'''\1
                
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('metrics')" data-tab="metrics">
                        <i class="fas fa-chart-line"></i>
                        <span>Metrics</span>
                    </button>
                </li>'''
    
    content = re.sub(nav_pattern, nav_addition, content, count=1)
    print("✓ Added Metrics navigation button")
    
    # 4. Add Metrics tab content
    # Find where to insert (after database tab)
    database_tab_end = content.find('<!-- Settings Tab -->')
    if database_tab_end == -1:
        # Try another marker
        database_tab_end = content.find('<div id="settings" class="tab-content">')
    
    if database_tab_end != -1:
        metrics_tab = '''
        <!-- Metrics Tab -->
        <div id="metrics" class="tab-content">
            <div class="card full-width" style="margin-bottom: 2rem;">
                <h2 style="text-align: center; margin-bottom: 2rem; color: var(--accent-color);">
                    <i class="fas fa-chart-line"></i> BoarderframeOS Metrics Dashboard
                </h2>
                <p style="text-align: center; color: var(--secondary-text); margin-bottom: 2rem;">
                    Comprehensive view of all system metrics organized by category
                </p>
            </div>
            
            <!-- Metrics Content -->
            {self._generate_metrics_page_content() if self.metrics_layer else self._generate_metrics_fallback()}
        </div>
        '''
        
        content = content[:database_tab_end] + metrics_tab + '\n        ' + content[database_tab_end:]
        print("✓ Added Metrics tab")
    
    # 5. Add the metrics content generation method
    # Find where to add it (after other _generate methods)
    method_insert_pos = content.rfind('def _generate_')
    if method_insert_pos != -1:
        # Find the end of that method
        next_method = content.find('\n    def ', method_insert_pos + 10)
        if next_method == -1:
            next_method = content.find('\nclass ', method_insert_pos)
        
        metrics_methods = '''
    def _generate_metrics_page_content(self):
        """Generate comprehensive metrics display"""
        try:
            all_metrics = self._get_centralized_metrics()
            
            html = '<div class="metrics-container">'
            
            # Create sections for each metric category
            categories = [
                ('agents', 'Agents', 'fa-robot', BFColors.INFO),
                ('leaders', 'Leaders', 'fa-crown', BFColors.EXECUTIVE),
                ('departments', 'Departments', 'fa-building', BFColors.INTELLIGENCE),
                ('divisions', 'Divisions', 'fa-sitemap', BFColors.DIVISION_1),
                ('servers', 'Servers', 'fa-server', BFColors.SUCCESS),
                ('database', 'Database', 'fa-database', BFColors.WARNING),
                ('registry', 'Registry', 'fa-network-wired', BFColors.INNOVATION),
            ]
            
            for metric_key, title, icon, color in categories:
                metric_data = all_metrics.get(metric_key, {})
                html += self._generate_metric_section(title, icon, color, metric_data)
            
            # Add raw metrics display
            html += self._generate_raw_metrics_section(all_metrics)
            
            html += '</div>'
            return html
            
        except Exception as e:
            return f'<div class="alert alert-danger">Error loading metrics: {str(e)}</div>'
    
    def _generate_metric_section(self, title, icon, color, data):
        """Generate a section for a specific metric category"""
        html = f'''
        <div class="card" style="margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                <div style="width: 50px; height: 50px; background: {color}; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white;">
                    <i class="fas {icon}" style="font-size: 1.5rem;"></i>
                </div>
                <h3 style="margin: 0; color: var(--primary-text);">{title} Metrics</h3>
            </div>
            '''
        
        if data:
            # Display summary if available
            if 'summary' in data:
                html += '<div class="metrics-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
                for key, value in data['summary'].items():
                    html += f'''
                    <div class="metric-item" style="padding: 1rem; background: var(--secondary-bg); border-radius: 8px;">
                        <div style="font-size: 0.9rem; color: var(--secondary-text); text-transform: capitalize;">{key}</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{value}</div>
                    </div>
                    '''
                html += '</div>'
            
            # Display all data as JSON for inspection
            html += f'''
            <details style="margin-top: 1rem;">
                <summary style="cursor: pointer; color: var(--accent-color);">View Raw Data</summary>
                <pre style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; overflow-x: auto; margin-top: 0.5rem;">
{json.dumps(data, indent=2)}
                </pre>
            </details>
            '''
        else:
            html += '<p style="color: var(--secondary-text);">No data available</p>'
        
        html += '</div>'
        return html
    
    def _generate_raw_metrics_section(self, all_metrics):
        """Generate raw metrics display for debugging"""
        return f'''
        <div class="card">
            <h3 style="margin-bottom: 1rem;">
                <i class="fas fa-code"></i> All Available Metrics (Raw)
            </h3>
            <pre style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; overflow-x: auto; max-height: 600px;">
{json.dumps(all_metrics, indent=2, default=str)}
            </pre>
        </div>
        '''
    
    def _generate_metrics_fallback(self):
        """Fallback content when metrics layer is not available"""
        return '''
        <div class="card">
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i> Metrics layer not initialized.
                <p>Please check the logs for initialization errors.</p>
            </div>
        </div>
        '''
'''
        
        if next_method != -1:
            content = content[:next_method] + metrics_methods + content[next_method:]
            print("✓ Added metrics page methods")
    
    # 6. Add json import if not present
    if 'import json' not in content[:1000]:
        json_import_pos = content.find('import threading')
        if json_import_pos != -1:
            content = content[:json_import_pos] + 'import json\n' + content[json_import_pos:]
    
    # Save the updated file
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Successfully added metrics layer integration and Metrics page!")
    print("\nWhat was added:")
    print("1. Metrics layer imports from core modules")
    print("2. Metrics layer initialization in __init__")
    print("3. Metrics navigation button in the UI")
    print("4. Metrics tab with comprehensive display")
    print("5. Methods to display all metrics by category")
    print("\nRestart the server to see the new Metrics page!")
    
    return True

if __name__ == "__main__":
    add_metrics_page()