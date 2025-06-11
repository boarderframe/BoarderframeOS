#!/usr/bin/env python3
"""
Add database and registry page methods to HQ metrics integration
"""


def add_database_registry_methods():
    """Add get_database_page_html and get_registry_page_html methods"""

    # Read the metrics integration file
    with open("core/hq_metrics_integration.py", "r") as f:
        content = f.read()

    # Check if methods already exist
    if (
        "def get_database_page_html" in content
        and "def get_registry_page_html" in content
    ):
        print("Methods already exist")
        return True

    # Find where to insert (at the end of the class, before the last line)
    last_method_pos = content.rfind("\n    def ")
    if last_method_pos == -1:
        print("Could not find insertion point")
        return False

    # Find the end of the last method
    next_class_or_end = content.find("\nclass ", last_method_pos)
    if next_class_or_end == -1:
        # No more classes, find the end
        insert_pos = content.rfind("\n")
    else:
        insert_pos = next_class_or_end

    # Add the new methods
    new_methods = '''
    def get_database_page_html(self) -> str:
        """Generate comprehensive database page with metrics and table information"""
        try:
            # Get database metrics from dashboard data
            db_metrics = self.dashboard_data.unified_data.get('database_health', {})
            db_tables = self._get_database_tables()

            return f"""
            <div class="metrics-container" style="padding: 1rem;">
                <!-- Database Overview -->
                <div class="metric-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-database"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            PostgreSQL
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Database Type
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {db_metrics.get('status', 'Unknown')}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Health Status
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-table"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {db_metrics.get('total_tables', len(db_tables))}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Total Tables
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-link"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {db_metrics.get('active_connections', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Active Connections
                        </div>
                    </div>
                </div>

                <!-- Database Performance -->
                <div class="card" style="padding: 1.5rem; margin-bottom: 2rem;">
                    <h3 style="margin-bottom: 1rem;">
                        <i class="fas fa-tachometer-alt"></i> Performance Metrics
                    </h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                        <div class="metric-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--secondary-text);">Cache Hit Ratio</span>
                                <span style="font-weight: bold; color: var(--success-color);">
                                    {db_metrics.get('cache_hit_ratio', 'N/A')}%
                                </span>
                            </div>
                        </div>
                        <div class="metric-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--secondary-text);">Database Size</span>
                                <span style="font-weight: bold;">
                                    {db_metrics.get('database_size', 'N/A')}
                                </span>
                            </div>
                        </div>
                        <div class="metric-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="color: var(--secondary-text);">Uptime</span>
                                <span style="font-weight: bold; color: var(--info-color);">
                                    {db_metrics.get('uptime', 'N/A')}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Database Tables -->
                <div class="card" style="padding: 1.5rem;">
                    <h3 style="margin-bottom: 1rem;">
                        <i class="fas fa-table"></i> Database Tables
                    </h3>
                    {self._generate_database_tables_html(db_tables)}
                </div>
            </div>
            """
        except Exception as e:
            logger.error(f"Error generating database page HTML: {e}")
            return self._generate_error_html("database", str(e))

    def get_registry_page_html(self) -> str:
        """Generate comprehensive registry page with service information"""
        try:
            # Get registry data
            registry_data = self.dashboard_data.unified_data.get('registry_data', {})
            services_status = self.dashboard_data.unified_data.get('services_status', {})

            return f"""
            <div class="metrics-container" style="padding: 1rem;">
                <!-- Registry Overview -->
                <div class="metric-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    <div class="metric-card" style="background: linear-gradient(135deg, #ec4899, #db2777); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-network-wired"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {len(services_status)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Registered Services
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {sum(1 for s in services_status.values() if s.get('status') == 'healthy')}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Healthy Services
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {registry_data.get('total_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Registered Agents
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-building"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {registry_data.get('total_departments', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Departments
                        </div>
                    </div>
                </div>

                <!-- Service Status -->
                <div class="card" style="padding: 1.5rem; margin-bottom: 2rem;">
                    <h3 style="margin-bottom: 1rem;">
                        <i class="fas fa-server"></i> Service Status
                    </h3>
                    {self._generate_services_status_html(services_status)}
                </div>

                <!-- Registry Details -->
                <div class="card" style="padding: 1.5rem;">
                    <h3 style="margin-bottom: 1rem;">
                        <i class="fas fa-list"></i> Registry Information
                    </h3>
                    {self._generate_registry_details_html(registry_data)}
                </div>
            </div>
            """
        except Exception as e:
            logger.error(f"Error generating registry page HTML: {e}")
            return self._generate_error_html("registry", str(e))

    def _get_database_tables(self) -> Dict[str, Any]:
        """Get database table information"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5434,
                user="boarderframe",
                password="boarderframe_secure_2025",
                database="boarderframeos"
            )
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("""
                SELECT tablename,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            tables = {}
            for row in cursor.fetchall():
                tables[row[0]] = {'size': row[1]}

            cursor.close()
            conn.close()

            return tables
        except Exception as e:
            logger.error(f"Error fetching database tables: {e}")
            return {}

    def _generate_database_tables_html(self, tables: Dict[str, Any]) -> str:
        """Generate HTML for database tables list"""
        if not tables:
            return "<p>No tables found</p>"

        html = '<div style="display: grid; gap: 0.5rem;">'
        for table_name, info in sorted(tables.items()):
            html += f"""
            <div style="display: grid; grid-template-columns: 1fr auto; align-items: center; padding: 0.75rem; background: var(--secondary-bg); border-radius: 8px;">
                <div>
                    <i class="fas fa-table" style="color: var(--accent-color); margin-right: 0.5rem;"></i>
                    <span style="font-weight: 500;">{table_name}</span>
                </div>
                <div style="color: var(--secondary-text); font-size: 0.9rem;">
                    {info.get('size', 'Unknown')}
                </div>
            </div>
            """
        html += '</div>'
        return html

    def _generate_services_status_html(self, services: Dict[str, Any]) -> str:
        """Generate HTML for services status"""
        if not services:
            return "<p>No services registered</p>"

        html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem;">'

        for service_name, status in sorted(services.items()):
            status_color = {
                'healthy': 'var(--success-color)',
                'unhealthy': 'var(--warning-color)',
                'offline': 'var(--danger-color)'
            }.get(status.get('status', 'unknown'), 'var(--neutral-color)')

            html += f"""
            <div style="padding: 1rem; background: var(--secondary-bg); border-radius: 8px; border: 1px solid var(--border-color);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <h4 style="margin: 0; text-transform: capitalize;">{service_name}</h4>
                    <span style="color: {status_color};">
                        <i class="fas fa-circle" style="font-size: 0.5rem;"></i> {status.get('status', 'unknown')}
                    </span>
                </div>
                <div style="font-size: 0.9rem; color: var(--secondary-text);">
                    Port: {status.get('port', 'N/A')}
                </div>
                {f'<div style="font-size: 0.85rem; color: var(--secondary-text); margin-top: 0.25rem;">Response: {status.get("response_time", 0):.2f}s</div>' if 'response_time' in status else ''}
            </div>
            """

        html += '</div>'
        return html

    def _generate_registry_details_html(self, registry_data: Dict[str, Any]) -> str:
        """Generate HTML for registry details"""
        html = '<div style="display: grid; gap: 1rem;">'

        # Add registry statistics
        stats = [
            ('Total Agents', registry_data.get('total_agents', 0), 'fa-robot'),
            ('Active Agents', registry_data.get('active_agents', 0), 'fa-check-circle'),
            ('Total Departments', registry_data.get('total_departments', 0), 'fa-building'),
            ('Total Leaders', registry_data.get('total_leaders', 0), 'fa-crown'),
            ('Total Services', registry_data.get('total_services', 0), 'fa-server'),
        ]

        for label, value, icon in stats:
            html += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: var(--secondary-bg); border-radius: 8px;">
                <div>
                    <i class="fas {icon}" style="color: var(--accent-color); margin-right: 0.5rem;"></i>
                    <span>{label}</span>
                </div>
                <div style="font-weight: bold;">{value}</div>
            </div>
            """

        html += '</div>'
        return html

    def _generate_error_html(self, page_name: str, error: str) -> str:
        """Generate error HTML for a page"""
        return f"""
        <div class="error-container" style="padding: 2rem; text-align: center;">
            <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: var(--danger-color); margin-bottom: 1rem;"></i>
            <h3>Error Loading {page_name.title()} Page</h3>
            <p style="color: var(--secondary-text);">{error}</p>
            <button onclick="location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: 8px; cursor: pointer;">
                <i class="fas fa-sync-alt"></i> Reload Page
            </button>
        </div>
        """
'''

    # Insert the methods
    content = content[:insert_pos] + new_methods + content[insert_pos:]

    # Save the file
    with open("core/hq_metrics_integration.py", "w") as f:
        f.write(content)

    print("Successfully added database and registry page methods")
    return True


def update_tabs_to_use_metrics():
    """Update database and registry tabs to use metrics layer"""

    # Read corporate headquarters
    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    # Update database tab
    database_start = content.find('<div id="database" class="tab-content">')
    if database_start != -1:
        # Find the end of database tab
        next_tab = content.find('<div id="', database_start + 10)
        if next_tab == -1:
            next_tab = content.find("<!-- System Tab -->", database_start)

        if next_tab != -1:
            # Replace database tab content
            new_database_content = """<div id="database" class="tab-content">
            {self.metrics_layer.get_database_page_html() if self.metrics_layer and hasattr(self.metrics_layer, 'get_database_page_html') else self._generate_database_content()}
        </div>

        """
            content = (
                content[:database_start] + new_database_content + content[next_tab:]
            )
            print("Updated database tab to use metrics layer")

    # Check if registry tab exists
    if 'id="registry"' not in content:
        # Add registry tab after database tab
        system_tab_pos = content.find("<!-- System Tab -->")
        if system_tab_pos != -1:
            registry_tab = """<!-- Registry Tab -->
        <div id="registry" class="tab-content">
            {self.metrics_layer.get_registry_page_html() if self.metrics_layer and hasattr(self.metrics_layer, 'get_registry_page_html') else self._generate_registry_overview_html()}
        </div>

        """
            content = content[:system_tab_pos] + registry_tab + content[system_tab_pos:]
            print("Added registry tab")

    # Save the file
    with open("corporate_headquarters.py", "w") as f:
        f.write(content)

    return True


if __name__ == "__main__":
    print("Adding database and registry page methods...")

    if add_database_registry_methods():
        print("✓ Added page methods to metrics integration")

    if update_tabs_to_use_metrics():
        print("✓ Updated tabs to use metrics layer")

    print("\nAll updates complete!")
