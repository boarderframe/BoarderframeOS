#!/usr/bin/env python3
"""
Fix f-string by converting CSS section to regular string
"""


def fix_fstring_properly():
    """Convert the problematic f-string to avoid CSS brace issues"""

    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    print("Converting f-string to avoid CSS syntax issues...")

    # Find the generate_dashboard_html method
    method_start = content.find("def generate_dashboard_html(self):")
    if method_start == -1:
        print("Could not find generate_dashboard_html method")
        return False

    # Find the return statement
    return_start = content.find('return f"""<!DOCTYPE html>', method_start)
    if return_start == -1:
        print("Could not find return statement")
        return False

    # Find the end of the method (next def or class)
    method_end = content.find("\n    def ", return_start)
    if method_end == -1:
        method_end = content.find("\nclass ", return_start)

    # Extract the method
    method_content = content[method_start:method_end]

    # Create a new version that builds the HTML in parts
    new_method = '''def generate_dashboard_html(self):
        """Generate the enhanced dashboard HTML"""
        # Ensure we're getting fresh metrics from database
        try:
            self._last_metrics = self._get_centralized_metrics()
        except Exception as e:
            print(f"Warning: Could not refresh metrics: {e}")

        # Get metrics
        all_metrics = self._last_metrics if hasattr(self, '_last_metrics') and self._last_metrics else self._get_centralized_metrics()

        # Agent metrics with fallback
        agent_page_metrics = self.metrics_layer.get_agents_page_metrics() if self.metrics_layer else {
            'total': 195, 'active': len(self.running_agents), 'inactive': 0, 'by_department': {}
        }

        # Extract values
        if self.metrics_layer:
            active_agents = self.metrics_layer.get_metric_value('agents', 'summary.active', len(self.running_agents))
            total_agents = self.metrics_layer.get_metric_value('agents', 'summary.total', 195)
            inactive_agents = self.metrics_layer.get_metric_value('agents', 'summary.inactive', 0)

            # Department metrics
            dept_data = all_metrics.get('departments', {})
            total_departments = self.metrics_layer.get_metric_value('departments', 'summary.total', 45)
            active_departments = self.metrics_layer.get_metric_value('departments', 'summary.active', 45)

            # Server metrics
            server_data = all_metrics.get('servers', {})
            total_services = self.metrics_layer.get_metric_value('servers', 'summary.total', 8)
            healthy_services = self.metrics_layer.get_metric_value('servers', 'summary.healthy', 6)
        else:
            # Fallback values
            active_agents = len(self.running_agents)
            total_agents = 195
            inactive_agents = 0
            total_departments = 45
            active_departments = 45
            total_services = 8
            healthy_services = 6

        # Calculate percentage for Overall Status
        active_percentage = (active_agents / total_agents * 100) if total_agents > 0 else 0

        if active_agents == 0:
            overall_status_text = 'All Agents Offline'
            overall_status_color = 'var(--danger-color)'
        elif active_agents < total_agents * 0.5:
            overall_status_text = 'Degraded Performance'
            overall_status_color = 'var(--warning-color)'
        elif active_agents < total_agents:
            overall_status_text = 'Partially Operational'
            overall_status_color = 'var(--info-color)'
        else:
            overall_status_text = 'Fully Operational'
            overall_status_color = 'var(--success-color)'

        # Other metrics
        total_divisions = 9
        total_leaders = 24
        offline_services = total_services - healthy_services
        degraded_services = 0

        # Build CSS separately to avoid f-string issues
        css_content = """<style>
        """ + METRICS_CSS + """

        /* Emergency tab visibility fix */
        .tab-content { display: none !important; }
        .tab-content.active {
            display: block !important;
            opacity: 1 !important;
            visibility: visible !important;
            position: static !important;
        }
        </style>"""

        # Build the HTML
        html_parts = ['<!DOCTYPE html>']
        html_parts.append('<html lang="en">')
        html_parts.append('<head>')
        html_parts.append('<meta charset="UTF-8">')
        html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append('<title>BoarderframeOS Corporate Headquarters</title>')
        html_parts.append('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">')
        html_parts.append(css_content)
        html_parts.append('</head>')
        html_parts.append('<body>')

        # Continue building the rest of the HTML...
        # For now, return a basic structure
        html_parts.append(self._generate_dashboard_body(
            active_agents, total_agents, inactive_agents,
            total_departments, active_departments,
            total_services, healthy_services, offline_services, degraded_services,
            total_divisions, total_leaders,
            overall_status_text, overall_status_color
        ))

        html_parts.append('</body>')
        html_parts.append('</html>')

        return '\\n'.join(html_parts)
'''

    # Replace the method
    new_content = content[:method_start] + new_method

    # Now we need to add a helper method for the body
    # Find where to insert it (after generate_dashboard_html)
    insert_pos = method_end

    body_method = '''

    def _generate_dashboard_body(self, active_agents, total_agents, inactive_agents,
                                 total_departments, active_departments,
                                 total_services, healthy_services, offline_services, degraded_services,
                                 total_divisions, total_leaders,
                                 overall_status_text, overall_status_color):
        """Generate the dashboard body HTML"""
        # This will contain all the HTML that was previously in the f-string
        # For now, return the basic structure
        return f"""
    <nav class="navbar">
        <div class="navbar-container">
            <div class="navbar-brand">
                <i class="fas fa-building"></i>
                <span class="brand-text">BoarderframeOS</span>
                <span class="brand-subtitle">Corporate Headquarters</span>
            </div>
            <ul class="nav-links">
                <li class="nav-item">
                    <button class="nav-link active" onclick="showTab('dashboard'); return false;" data-tab="dashboard">
                        <i class="fas fa-home"></i>
                        <span>Dashboard</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('agents'); return false;" data-tab="agents">
                        <i class="fas fa-robot"></i>
                        <span>Agents</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('database'); return false;" data-tab="database">
                        <i class="fas fa-database"></i>
                        <span>Database</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('services'); return false;" data-tab="services">
                        <i class="fas fa-server"></i>
                        <span>Services</span>
                    </button>
                </li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <div id="dashboard" class="tab-content active">
            <h2>Dashboard - Active Agents: {active_agents}/{total_agents}</h2>
        </div>

        <div id="agents" class="tab-content">
            <h2>Agents Page</h2>
        </div>

        <div id="database" class="tab-content">
            <h2>Database Page</h2>
            <!-- Database content will be here -->
        </div>

        <div id="services" class="tab-content">
            <h2>Services Page</h2>
        </div>
    </div>

    <script>
        {self._generate_dashboard_scripts()}
    </script>
    """'''

    new_content = new_content[:insert_pos] + body_method + new_content[insert_pos:]

    # Save
    with open("corporate_headquarters.py.fixed", "w") as f:
        f.write(new_content)

    print("Created corporate_headquarters.py.fixed")
    print("This is a simplified version to test if the server starts")

    return True


if __name__ == "__main__":
    fix_fstring_properly()
