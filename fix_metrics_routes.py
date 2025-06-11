#!/usr/bin/env python3
"""
Fix the placement of metrics API routes
"""

def fix_metrics_routes():
    """Move the metrics routes to the correct location"""

    with open('corporate_headquarters.py', 'r') as f:
        content = f.read()

    # Remove the incorrectly placed routes
    bad_routes_start = content.find('\n@app.route(\'/api/metrics\')')
    if bad_routes_start != -1:
        # Find the end of the second route
        bad_routes_end = content.find('\n        }), 500', bad_routes_start)
        if bad_routes_end != -1:
            bad_routes_end = content.find('\n', bad_routes_end + 1)
            # Remove the bad routes
            content = content[:bad_routes_start] + content[bad_routes_end:]
            print("✓ Removed incorrectly placed routes")

    # Find the correct place to add routes (after the Flask app creation)
    # Look for the dashboard route
    dashboard_route = content.find('@app.route(\'/\')')
    if dashboard_route != -1:
        # Add the routes before the dashboard route
        metrics_routes = '''
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
        }), 500

'''
        content = content[:dashboard_route] + metrics_routes + content[dashboard_route:]
        print("✓ Added metrics routes in correct location")

    # Save the fixed file
    with open('corporate_headquarters.py', 'w') as f:
        f.write(content)

    print("✓ Fixed metrics routes placement")
    return True

if __name__ == "__main__":
    fix_metrics_routes()
