#!/usr/bin/env python3
"""
Add metrics API endpoint and dynamic loading
"""

import re

def add_metrics_endpoint():
    """Add API endpoint for metrics and dynamic loading"""
    
    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()
    
    print("Adding metrics API endpoint...")
    
    # 1. Find where to add the API endpoint (after other API endpoints)
    # Look for a Flask route pattern
    route_pattern = r'(@app\.route\(\'/api/[^\']+\'\)[^}]+\})'
    matches = list(re.finditer(route_pattern, content, re.DOTALL))
    
    if matches:
        # Insert after the last API route
        last_match = matches[-1]
        insert_pos = last_match.end()
        
        # Add the metrics API endpoint
        metrics_endpoint = '''

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics data"""
    try:
        # Get all metrics
        all_metrics = dashboard_data._get_centralized_metrics()
        
        # Add metrics layer status
        metrics_status = {
            'metrics_layer_available': dashboard_data.metrics_layer is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': all_metrics,
            'metrics_status': metrics_status
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/metrics/page')
def api_metrics_page():
    """API endpoint for metrics page HTML"""
    try:
        if dashboard_data.metrics_layer:
            html = dashboard_data._generate_metrics_page_content()
        else:
            html = dashboard_data._generate_metrics_fallback()
        
        return jsonify({
            'status': 'success',
            'html': html
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'html': f'<div class="alert alert-danger">Error loading metrics: {str(e)}</div>'
        }), 500'''
        
        content = content[:insert_pos] + metrics_endpoint + content[insert_pos:]
        print("✓ Added metrics API endpoints")
    
    # 2. Add JavaScript to load metrics dynamically
    # Find showTab function
    show_tab_pos = content.find('function showTab(tabName)')
    if show_tab_pos != -1:
        # Find the end of showTab function
        func_end = content.find('\n        }', show_tab_pos)
        if func_end != -1:
            # Add metrics loading logic before the closing brace
            metrics_loading = '''
            
            // Load metrics content if switching to metrics tab
            if (tabName === 'metrics') {
                loadMetricsContent();
            }'''
            
            content = content[:func_end] + metrics_loading + content[func_end:]
            print("✓ Added metrics loading to showTab")
    
    # 3. Add loadMetricsContent function
    # Find where to add it (after showTab function)
    load_metrics_func = '''
        
        // Load metrics content dynamically
        async function loadMetricsContent() {
            const metricsDiv = document.getElementById('metrics-content');
            if (!metricsDiv) return;
            
            // Show loading state
            metricsDiv.innerHTML = '<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin"></i> Loading metrics...</div>';
            
            try {
                const response = await fetch('/api/metrics/page');
                const data = await response.json();
                
                if (data.status === 'success') {
                    metricsDiv.innerHTML = data.html;
                } else {
                    metricsDiv.innerHTML = data.html || '<div class="alert alert-danger">Failed to load metrics</div>';
                }
            } catch (error) {
                console.error('Error loading metrics:', error);
                metricsDiv.innerHTML = '<div class="alert alert-danger">Error loading metrics: ' + error.message + '</div>';
            }
        }'''
    
    # Find where to insert (after debugTabs function if it exists)
    debug_tabs_pos = content.find('function debugTabs()')
    if debug_tabs_pos != -1:
        # Find the end of debugTabs
        func_end = content.find('\n        }', debug_tabs_pos)
        if func_end != -1:
            content = content[:func_end + 10] + load_metrics_func + content[func_end + 10:]
            print("✓ Added loadMetricsContent function")
    else:
        # Insert after showTab
        show_tab_end = content.find('\n        }', show_tab_pos)
        if show_tab_end != -1:
            content = content[:show_tab_end + 10] + load_metrics_func + content[show_tab_end + 10:]
            print("✓ Added loadMetricsContent function")
    
    # Save the updated file
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Successfully added metrics API endpoint and dynamic loading!")
    print("\nWhat was added:")
    print("1. /api/metrics - Returns raw metrics data")
    print("2. /api/metrics/page - Returns formatted metrics HTML")
    print("3. Dynamic loading when clicking Metrics tab")
    print("\nRestart the server to see the changes!")
    
    return True

if __name__ == "__main__":
    add_metrics_endpoint()