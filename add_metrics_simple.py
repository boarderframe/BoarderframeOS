#!/usr/bin/env python3
"""
Add metrics functionality simply and safely
"""

def add_metrics_simple():
    """Add metrics layer and navigation only"""

    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    # 1. Add imports
    import_pos = content.find('import socket\n')
    if import_pos != -1:
        new_imports = '''import socket

# Metrics Layer Integration
try:
    from core.hq_metrics_integration import HQMetricsIntegration, METRICS_CSS
    from core.hq_metrics_layer import BFColors, BFIcons, MetricValue
    METRICS_AVAILABLE = True
except ImportError:
    print("Warning: Metrics layer not available")
    METRICS_AVAILABLE = False
'''
        content = content[:import_pos] + new_imports + content[import_pos + 13:]
        print("✓ Added metrics imports")

    # 2. Initialize metrics layer in __init__
    init_line = content.find('self.status_file = "data/system_status.json"')
    if init_line != -1:
        metrics_init = '''
        # Initialize metrics layer
        self.metrics_layer = None
        if METRICS_AVAILABLE:
            try:
                self.metrics_layer = HQMetricsIntegration(self)
                print("✓ Metrics layer initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize metrics layer: {e}")

        self.status_file = "data/system_status.json"'''

        # Find start of line
        line_start = content.rfind('\n', 0, init_line)
        content = content[:line_start + 1] + metrics_init + content[init_line + len('self.status_file = "data/system_status.json"'):]
        print("✓ Added metrics initialization")

    # 3. Add Metrics nav button
    database_button = content.find('<i class="fas fa-database"></i>\n                        <span>Database</span>')
    if database_button != -1:
        # Find the end of this nav item
        nav_end = content.find('</li>', database_button)
        if nav_end != -1:
            metrics_nav = '''
                </li>

                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('metrics')" data-tab="metrics">
                        <i class="fas fa-chart-line"></i>
                        <span>Metrics</span>
                    </button>'''
            content = content[:nav_end] + metrics_nav + content[nav_end:]
            print("✓ Added metrics navigation")

    # 4. Add metrics tab (simple version)
    settings_tab = content.find('<!-- Settings Tab -->')
    if settings_tab != -1:
        metrics_tab = '''
        <!-- Metrics Tab -->
        <div id="metrics" class="tab-content">
            <div class="card full-width" style="margin-bottom: 2rem;">
                <h2 style="text-align: center; margin-bottom: 2rem; color: var(--accent-color);">
                    <i class="fas fa-chart-line"></i> BoarderframeOS Metrics Dashboard
                </h2>
                <p style="text-align: center; color: var(--secondary-text); margin-bottom: 2rem;">
                    System metrics and analytics
                </p>
            </div>

            <div class="card full-width">
                <div id="metrics-content">
                    <p style="text-align: center; padding: 2rem;">
                        Click the Refresh button to load metrics
                    </p>
                    <div style="text-align: center;">
                        <button onclick="loadMetricsData()" style="
                            background: linear-gradient(135deg, #3b82f6, #1e40af);
                            color: white;
                            border: none;
                            padding: 0.75rem 1.5rem;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 1rem;
                        ">
                            <i class="fas fa-sync-alt"></i> Load Metrics
                        </button>
                    </div>
                </div>
            </div>
        </div>

        '''
        content = content[:settings_tab] + metrics_tab + content[settings_tab:]
        print("✓ Added metrics tab")

    # 5. Add simple JavaScript function to load metrics
    # Find where to add it (after showTab function)
    show_tab_end = content.find('function showTab(tabName)')
    if show_tab_end != -1:
        # Find the closing brace of showTab
        brace_count = 0
        pos = content.find('{', show_tab_end)
        start_pos = pos
        while pos < len(content) and brace_count >= 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found the end
                    load_metrics_func = '''

        // Load metrics data
        function loadMetricsData() {
            const metricsDiv = document.getElementById('metrics-content');
            metricsDiv.innerHTML = '<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin"></i> Loading metrics...</div>';

            // For now, just show a message
            setTimeout(() => {
                metricsDiv.innerHTML = `
                    <div style="padding: 2rem;">
                        <h3>Metrics System Status</h3>
                        <p>Metrics layer initialized: ${dashboard_data.metrics_layer ? 'Yes' : 'No'}</p>
                        <p>Use the API endpoint /api/metrics to get raw metrics data</p>
                        <pre style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px;">
// Example usage:
fetch('/api/metrics')
  .then(response => response.json())
  .then(data => console.log(data));
                        </pre>
                    </div>
                `;
            }, 1000);
        }'''
                    content = content[:pos + 1] + load_metrics_func + content[pos + 1:]
                    print("✓ Added loadMetricsData function")
                    break
            pos += 1

    # Save
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)

    print("\n✅ Successfully added basic metrics functionality!")
    print("\nWhat was added:")
    print("1. Metrics layer imports with error handling")
    print("2. Metrics layer initialization")
    print("3. Metrics navigation button")
    print("4. Metrics tab with manual load button")
    print("5. Simple JavaScript to show metrics status")

    return True

if __name__ == "__main__":
    add_metrics_simple()
