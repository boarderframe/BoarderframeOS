#!/usr/bin/env python3
"""
Final fix for Flask routes
"""


def final_fix_routes():
    """Remove the metrics routes and add them properly after the dashboard route"""

    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    # Remove the incorrectly placed metrics routes
    # Find where they start
    bad_start = content.find("         @app.route('/api/metrics')")
    if bad_start != -1:
        # Find where they end (look for the dashboard route)
        bad_end = content.find("@app.route('/')", bad_start)
        if bad_end != -1:
            content = content[:bad_start] + content[bad_end:]
            print("✓ Removed incorrectly placed metrics routes")

    # Now add them after the dashboard route with proper indentation
    # Find the dashboard route
    dashboard_route = content.find("@app.route('/')")
    if dashboard_route != -1:
        # Find the end of the dashboard function
        # Look for the next @app.route or the end of the Flask section
        next_route = content.find("@app.route", dashboard_route + 10)
        if next_route == -1:
            # Look for app.run
            next_route = content.find("app.run(", dashboard_route)

        if next_route != -1:
            # Insert the metrics routes with proper indentation (12 spaces)
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

            content = (
                content[:next_route] + metrics_routes + "\n" + content[next_route:]
            )
            print("✓ Added metrics routes with correct indentation")

    # Save the file
    with open("corporate_headquarters.py", "w") as f:
        f.write(content)

    print("✅ Flask routes fixed!")
    return True


if __name__ == "__main__":
    final_fix_routes()
