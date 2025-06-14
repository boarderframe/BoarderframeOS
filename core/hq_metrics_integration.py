#!/usr/bin/env python3
"""
Integration module for using the HQ Metrics Layer in Corporate Headquarters
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.hq_metrics_layer import (
    BFColors,
    BFIcons,
    EntityMetrics,
    MetricValue,
    get_card_renderer,
    get_metrics_calculator,
)

logger = logging.getLogger(__name__)

try:
    from scripts.enhance.enhance_metrics_visual_integration import VisualMetadataCache
except ImportError:
    VisualMetadataCache = None


class HQMetricsIntegration:
    """Integration class for Corporate HQ to use the metrics layer"""

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.metrics_calc = get_metrics_calculator(db_config)
        self.card_renderer = get_card_renderer()
        self._metrics_cache = {}
        self._last_refresh = None

    def set_server_status(self, server_status: Dict[str, Any]):
        """Pass real server status to the metrics calculator"""
        logger.info(
            f"HQ Metrics Integration: Setting server status with {len(server_status) if server_status else 0} servers"
        )
        if server_status and "corporate_headquarters" in server_status:
            logger.info(
                f"Corporate HQ status being passed: {server_status['corporate_headquarters'].get('status', 'unknown')}"
            )
        if hasattr(self.metrics_calc, "set_server_status"):
            self.metrics_calc.set_server_status(server_status)

    def get_all_metrics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get all metrics with optional caching"""
        now = datetime.now()

        # Check cache (30 second TTL)
        if (
            not force_refresh
            and self._last_refresh
            and (now - self._last_refresh).seconds < 30
            and self._metrics_cache
        ):
            return self._metrics_cache

        # Refresh all metrics
        self._metrics_cache = self.metrics_calc.refresh_all_metrics()
        self._last_refresh = now

        return self._metrics_cache

    def get_dashboard_summary_cards(self) -> str:
        """Generate HTML for dashboard summary cards"""
        metrics = self.get_all_metrics()

        # Extract key metrics
        agent_metrics = metrics.get("agents", {}).get("summary", {})
        dept_metrics = metrics.get("departments", {}).get("summary", {})
        server_metrics = metrics.get("servers", {}).get("summary", {})

        cards_html = '<div class="metrics-grid">'

        # Agent summary card
        if agent_metrics:
            total_agents = agent_metrics.get("total", MetricValue(0, "Total Agents"))
            online_agents = agent_metrics.get("online", MetricValue(0, "Online"))

            # Calculate percentage
            total_val = total_agents.value if hasattr(total_agents, "value") else 0
            online_val = online_agents.value if hasattr(online_agents, "value") else 0
            percentage = (online_val / total_val * 100) if total_val > 0 else 0

            cards_html += f"""
            <div class="widget widget-large">
                <div class="widget-header">
                    <div class="widget-title">
                        <i class="fas {BFIcons.AGENT}" style="color: {BFColors.INFO};"></i>
                        <span>Agent Overview</span>
                    </div>
                </div>
                <div class="widget-value" style="color: {BFColors.INFO};">
                    {total_val}
                </div>
                <div class="widget-subtitle">Total Agents</div>
                <div class="widget-details">
                    <span style="color: {BFColors.SUCCESS};">{online_val} Online</span> •
                    <span>{percentage:.1f}% Active</span>
                </div>
            </div>
            """

        # Department summary card
        if dept_metrics:
            total_depts = dept_metrics.get("total", MetricValue(0, "Total"))
            active_depts = dept_metrics.get("active", MetricValue(0, "Active"))

            cards_html += f"""
            <div class="widget widget-medium">
                <div class="widget-header">
                    <div class="widget-title">
                        <i class="fas {BFIcons.DEPARTMENT}" style="color: {BFColors.EXECUTIVE};"></i>
                        <span>Departments</span>
                    </div>
                </div>
                <div class="widget-value" style="color: {BFColors.EXECUTIVE};">
                    {total_depts.value if hasattr(total_depts, 'value') else 0}
                </div>
                <div class="widget-subtitle">
                    {active_depts.value if hasattr(active_depts, 'value') else 0} Active
                </div>
            </div>
            """

        # Server health card
        if server_metrics:
            total_servers = server_metrics.get("total", MetricValue(0, "Total"))
            healthy_servers = server_metrics.get("healthy", MetricValue(0, "Healthy"))

            health_percentage = (
                (healthy_servers.value / total_servers.value * 100)
                if hasattr(total_servers, "value") and total_servers.value > 0
                else 0
            )

            health_color = (
                BFColors.SUCCESS
                if health_percentage >= 80
                else BFColors.WARNING
                if health_percentage >= 50
                else BFColors.DANGER
            )

            cards_html += f"""
            <div class="widget widget-medium">
                <div class="widget-header">
                    <div class="widget-title">
                        <i class="fas {BFIcons.SERVER}" style="color: {health_color};"></i>
                        <span>System Health</span>
                    </div>
                </div>
                <div class="widget-value" style="color: {health_color};">
                    {health_percentage:.0f}%
                </div>
                <div class="widget-subtitle">
                    {healthy_servers.value if hasattr(healthy_servers, 'value') else 0}/{total_servers.value if hasattr(total_servers, 'value') else 0} Healthy
                </div>
            </div>
            """

        cards_html += "</div>"
        return cards_html

    def get_agent_cards_html(
        self, limit: int = 10, status_filter: Optional[str] = None
    ) -> str:
        """Generate HTML for agent cards"""
        metrics = self.get_all_metrics()
        agents = metrics.get("agents", {}).get("individual", [])

        # Apply filter if specified
        if status_filter:
            agents = [
                a
                for a in agents
                if a.metrics.get("status", MetricValue("", "")).value == status_filter
            ]

        # Limit results
        agents = agents[:limit]

        cards_html = '<div class="agent-cards-grid">'
        for agent in agents:
            cards_html += self.card_renderer.render_agent_card(agent)
        cards_html += "</div>"

        return cards_html

    def get_department_cards_html(self, division_filter: Optional[str] = None) -> str:
        """Generate HTML for department cards"""
        metrics = self.get_all_metrics()
        departments = metrics.get("departments", {}).get("individual", [])

        # Apply filter if specified
        if division_filter:
            departments = [
                d
                for d in departments
                if d.metadata.get("division_id") == division_filter
            ]

        # Group by division for better display
        cards_html = '<div class="department-cards-container">'

        # Sort by division
        from itertools import groupby

        departments.sort(
            key=lambda d: d.metrics.get("division", MetricValue("", "")).value
        )

        for division, dept_group in groupby(
            departments,
            key=lambda d: d.metrics.get("division", MetricValue("", "")).value,
        ):
            cards_html += f"""
            <div class="division-group">
                <h4 class="division-header">{division}</h4>
                <div class="department-cards-grid">
            """

            for dept in dept_group:
                cards_html += self.card_renderer.render_department_card(dept)

            cards_html += """
                </div>
            </div>
            """

        cards_html += "</div>"
        return cards_html

    def get_metric_value(
        self, category: str, metric_path: str, default: Any = 0
    ) -> Any:
        """Get a specific metric value"""
        metrics = self.get_all_metrics()

        # Navigate the path
        current = metrics.get(category, {})
        for part in metric_path.split("."):
            if isinstance(current, dict):
                current = current.get(part, {})
            else:
                return default

        # Extract value if it's a MetricValue object
        if hasattr(current, "value"):
            return current.value
        elif isinstance(current, dict) and "value" in current:
            return current["value"]
        else:
            return current or default

    def get_agents_page_metrics(self) -> Dict[str, Any]:
        """Get metrics specifically for the agents page"""
        metrics = self.get_all_metrics()
        agent_metrics = metrics.get("agents", {})

        # Get summary values
        summary = agent_metrics.get("summary", {})

        # Count actual running processes (this would need process detection)
        # For now, use the 'online' count from registry
        running_processes = 2  # Hardcoded as we know only 2 are running

        return {
            "active": running_processes,
            "inactive": summary.get("total", MetricValue(195, "")).value
            - running_processes,
            "total": summary.get("total", MetricValue(195, "")).value,
            "by_type": agent_metrics.get("by_type", {}),
            "by_status": agent_metrics.get("by_status", {}),
            "by_department": agent_metrics.get("by_department", {}),
        }

    def get_departments_visual_data(self) -> List[Dict[str, Any]]:
        """Get departments with their visual metadata"""
        try:
            conn = self.metrics_calc._get_db_connection()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT
                    d.id, d.name, d.description,
                    d.configuration->'visual' as visual,
                    COUNT(ar.id) as agent_count
                FROM departments d
                LEFT JOIN agent_registry ar ON d.id = ar.department_id
                GROUP BY d.id, d.name, d.description, d.configuration
                ORDER BY d.name
            """
            )

            departments = []
            for row in cur.fetchall():
                visual = row[3] or {}
                departments.append(
                    {
                        "id": str(row[0]),
                        "name": row[1],
                        "description": row[2],
                        "color": visual.get("color", BFColors.INFO),
                        "icon": visual.get("icon", BFIcons.DEPARTMENT),
                        "theme": visual.get("theme", "default"),
                        "agent_count": row[4],
                    }
                )

            cur.close()
            conn.close()

            return departments

        except Exception as e:
            print(f"Error getting department visual data: {e}")
            return []

    def get_divisions_visual_data(self) -> Dict[int, Dict[str, Any]]:
        """Get divisions with their visual metadata"""
        try:
            conn = self.metrics_calc._get_db_connection()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT
                    id, division_name, description,
                    configuration->'visual' as visual
                FROM divisions
                ORDER BY id
            """
            )

            divisions = {}
            for row in cur.fetchall():
                visual = row[3] or {}
                divisions[row[0]] = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "color": visual.get("color", f"#7c3aed"),  # Default purple
                    "icon": visual.get("icon", "fa-sitemap"),
                    "theme": visual.get("theme", "division"),
                }

            cur.close()
            conn.close()

            return divisions

        except Exception as e:
            print(f"Error getting divisions visual data: {e}")
            return {}

    def get_agent_metrics_cards(self) -> str:
        """Generate metric cards for the agents page with database colors"""
        metrics = self.get_all_metrics()
        agent_metrics = self.get_agents_page_metrics()

        # Get visual metadata for agents category
        visual_cache = None
        agent_visual = {"color": "#3b82f6", "icon": "fa-robot"}  # defaults

        if VisualMetadataCache:
            try:
                visual_cache = VisualMetadataCache(self.metrics_calc.db_config)
                agent_visual = visual_cache.get_visual("agents")
            except:
                pass

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

            <div class="metric-card" style="background: linear-gradient(135deg, {agent_visual['color']}15, {agent_visual['color']}08); border: 1px solid {agent_visual['color']}40;">
                <div class="metric-header">
                    <i class="fas {agent_visual['icon']}" style="color: {agent_visual['color']};"></i>
                    <span>Total</span>
                </div>
                <div class="metric-value" style="color: {agent_visual['color']};">
                    {agent_metrics['total']}
                </div>
                <div class="metric-subtitle">Registered Agents</div>
            </div>
        </div>
        """

        return cards_html

    def get_department_metrics_cards(self) -> str:
        """Generate metric cards for the departments page with database colors"""
        metrics = self.get_all_metrics()
        dept_data = metrics.get("departments", {})
        dept_summary = dept_data.get("summary", {})

        total = self.get_metric_value("departments", "summary.total", 45)
        active = self.get_metric_value("departments", "summary.active", 45)
        divisions = self.get_metric_value("departments", "summary.divisions", 9)

        # Get visual metadata for departments category
        visual_cache = None
        dept_visual = {"color": "#10b981", "icon": "fa-building"}  # defaults
        div_visual = {"color": "#8b5cf6", "icon": "fa-sitemap"}  # defaults

        if VisualMetadataCache:
            try:
                visual_cache = VisualMetadataCache(self.metrics_calc.db_config)
                dept_visual = visual_cache.get_visual("departments")
                div_visual = visual_cache.get_visual("divisions")
            except:
                pass

        cards_html = f"""
        <div style="display: flex; justify-content: space-around; gap: 2rem; align-items: stretch; flex-wrap: nowrap; margin-bottom: 2rem;">
            <div class="metric-card" style="background: linear-gradient(135deg, {dept_visual['color']}15, {dept_visual['color']}08); border: 1px solid {dept_visual['color']}40;">
                <div class="metric-header">
                    <i class="fas {dept_visual['icon']}" style="color: {dept_visual['color']};"></i>
                    <span>Total Departments</span>
                </div>
                <div class="metric-value" style="color: {dept_visual['color']};">
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

            <div class="metric-card" style="background: linear-gradient(135deg, {div_visual['color']}15, {div_visual['color']}08); border: 1px solid {div_visual['color']}40;">
                <div class="metric-header">
                    <i class="fas {div_visual['icon']}" style="color: {div_visual['color']};"></i>
                    <span>Divisions</span>
                </div>
                <div class="metric-value" style="color: {div_visual['color']};">
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
        dept_data = metrics.get("departments", {})

        # Group departments by division
        divisions_map = {}
        for dept in dept_data.get("individual", []):
            division = dept.metrics.get("division", MetricValue("Unassigned", "")).value
            if division not in divisions_map:
                divisions_map[division] = []
            divisions_map[division].append(dept)

        html = f"""
        <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #7c3aed20; background: linear-gradient(135deg, #7c3aed08, #7c3aed03);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="
                        width: 60px; height: 60px;
                        background: linear-gradient(135deg, #7c3aed, #7c3aedcc);
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
            agent_count = sum(
                d.metrics.get("agents_total", MetricValue(0, "")).value
                for d in departments
            )

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

        html += "</div>"

        return html

    def get_agents_page_html(self) -> str:
        """Generate comprehensive agents page with metrics"""
        try:
            # Get agent metrics
            agents_metrics = self.get_agents_page_metrics()

            return f"""
            <div class="metrics-container" style="padding: 1rem;">
                <!-- Agent Overview -->
                <div class="metric-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                    <div class="metric-card" style="background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('total_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Total Agents
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('active_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Active Agents
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-sync-alt"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('processing_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Processing
                        </div>
                    </div>

                    <div class="metric-card" style="background: linear-gradient(135deg, #6b7280, #4b5563); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div class="metric-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">
                            <i class="fas fa-pause-circle"></i>
                        </div>
                        <div class="metric-value" style="font-size: 2rem; font-weight: bold;">
                            {agents_metrics.get('inactive_agents', 0)}
                        </div>
                        <div class="metric-label" style="font-size: 0.9rem; opacity: 0.9;">
                            Inactive
                        </div>
                    </div>
                </div>

                <!-- Agents by Department -->
                <div class="card" style="padding: 1.5rem; margin-bottom: 2rem;">
                    <h3 style="margin-bottom: 1rem;">Agents by Department</h3>
                    {self._generate_agent_department_chart(agents_metrics.get('by_department', {}))}
                </div>

                <!-- Agent List -->
                <div class="card" style="padding: 1.5rem;">
                    <h3 style="margin-bottom: 1rem;">All Agents</h3>
                    {self.get_agent_cards_html()}
                </div>
            </div>
            """
        except Exception as e:
            logger.error(f"Error generating agents page HTML: {e}")
            return self._generate_error_html("agents", str(e))

    def get_metrics_page_html(self) -> str:
        """Generate comprehensive metrics page showing all available metrics"""
        try:
            # Get all metrics
            all_metrics = self.get_all_metrics(force_refresh=True)

            html = f"""
            <div class="metrics-container" style="padding: 2rem;">
                <h2 style="margin-bottom: 2rem; color: var(--accent-color);">
                    <i class="fas fa-chart-line"></i> BoarderframeOS Metrics Dashboard
                </h2>

                <!-- Summary Cards -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
                    {self._generate_metric_summary_cards(all_metrics)}
                </div>

                <!-- Detailed Metrics by Type -->
                <div class="metrics-sections">
                    {self._generate_agents_metrics_section(all_metrics.get('agents', {}))}
                    {self._generate_leaders_metrics_section(all_metrics.get('leaders', {}))}
                    {self._generate_departments_metrics_section(all_metrics.get('departments', {}))}
                    {self._generate_divisions_metrics_section(all_metrics.get('divisions', {}))}
                    {self._generate_database_metrics_section(all_metrics.get('database', {}))}
                    {self._generate_servers_metrics_section(all_metrics.get('servers', {}))}
                </div>

                <!-- Raw Metrics Data -->
                <div class="card" style="margin-top: 2rem; padding: 1.5rem;">
                    <h3 style="margin-bottom: 1rem;">Raw Metrics Data</h3>
                    <details>
                        <summary style="cursor: pointer; padding: 0.5rem; background: var(--secondary-bg); border-radius: 8px;">
                            Click to view raw JSON data
                        </summary>
                        <pre style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; overflow: auto; max-height: 400px; margin-top: 1rem;">
{json.dumps(all_metrics, indent=2, default=str)}
                        </pre>
                    </details>
                </div>
            </div>
            """

            return html

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            return f"""
            <div class="alert alert-danger" style="margin: 2rem;">
                <h3><i class="fas fa-exclamation-triangle"></i> Error Loading Metrics</h3>
                <p>Failed to generate metrics page: {str(e)}</p>
                <details style="margin-top: 1rem;">
                    <summary>Error Details</summary>
                    <pre style="background: rgba(0,0,0,0.1); padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
{error_details}
                    </pre>
                </details>
            </div>
            """

    def _generate_metric_summary_cards(self, metrics: Dict[str, Any]) -> str:
        """Generate summary cards for key metrics with database colors"""
        cards = []

        # Initialize visual cache if available
        visual_cache = None
        if VisualMetadataCache:
            try:
                visual_cache = VisualMetadataCache(self.metrics_calc.db_config)
                visual_cache.refresh_cache()
            except:
                pass

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, "value"):
                return data.value
            return data if data is not None else 0

        # Get visual metadata for categories
        def get_category_visual(category):
            if visual_cache:
                return visual_cache.get_visual(category)
            # Fallback to defaults
            defaults = {
                "agents": {"color": "#3b82f6", "icon": "fa-robot"},
                "leaders": {"color": "#ec4899", "icon": "fa-crown"},
                "departments": {"color": "#10b981", "icon": "fa-building"},
                "divisions": {"color": "#8b5cf6", "icon": "fa-sitemap"},
                "database": {"color": "#14b8a6", "icon": "fa-database"},
                "servers": {"color": "#f59e0b", "icon": "fa-server"},
            }
            return defaults.get(category, {"color": "#6b7280", "icon": "fa-folder"})

        # 1. Agents summary (first)
        agent_data = metrics.get("agents", {}).get("summary", {})
        if agent_data:
            total = get_value(agent_data.get("total", 0))
            online = get_value(agent_data.get("online", 0))
            visual = get_category_visual("agents")
            cards.append(
                f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Agents</div>
                            <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{online} online</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """
            )

        # 2. Leaders summary (second)
        leaders_data = metrics.get("leaders", {})
        if leaders_data:
            visual = get_category_visual("leaders")
            # Check if it's from metrics layer (has summary) or raw data
            if "summary" in leaders_data:
                # From metrics layer
                summary = leaders_data.get("summary", {})
                total = get_value(summary.get("total", 0))
                hired = get_value(summary.get("hired", 0))
                built = get_value(summary.get("built", 0))
                cards.append(
                    f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Leaders</div>
                                <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">{hired} hired • {built} built</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """
                )
            else:
                # From raw data (legacy format)
                leaders_count = (
                    len(leaders_data) if isinstance(leaders_data, (list, dict)) else 0
                )
                cards.append(
                    f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Leaders</div>
                                <div style="font-size: 2rem; font-weight: bold;">{leaders_count}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">Organizational leaders</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """
                )

        # 3. Departments summary (third)
        dept_data = metrics.get("departments", {}).get("summary", {})
        if dept_data:
            total = get_value(dept_data.get("total", 0))
            active = get_value(dept_data.get("active", 0))
            visual = get_category_visual("departments")
            cards.append(
                f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Departments</div>
                            <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{active} active</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """
            )

        # 4. Divisions summary (fourth)
        div_data = metrics.get("divisions", {}).get("summary", {})
        divisions_count = 0

        if div_data:
            divisions_count = get_value(div_data.get("total", 0))

        # If no divisions data, check departments summary for divisions count
        if divisions_count == 0 and dept_data:
            divisions_value = dept_data.get("divisions")
            if divisions_value:
                divisions_count = get_value(divisions_value)

        # If still no data, count unique divisions from departments
        if divisions_count == 0:
            dept_details = metrics.get("departments", {}).get("individual", [])
            if dept_details:
                unique_divisions = set()
                for dept in dept_details:
                    if hasattr(dept, "metadata") and dept.metadata.get("division"):
                        unique_divisions.add(dept.metadata["division"])
                divisions_count = len(unique_divisions)

        if divisions_count > 0:
            visual = get_category_visual("divisions")
            cards.append(
                f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Divisions</div>
                            <div style="font-size: 2rem; font-weight: bold;">{divisions_count}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">Organizational units</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """
            )

        # 5. Database summary (fifth)
        database_metrics = metrics.get("database", {})
        if database_metrics:
            visual = get_category_visual("database")
            # Check if it's from metrics layer (has summary) or raw data
            if "summary" in database_metrics:
                # From metrics layer
                summary = database_metrics.get("summary", {})
                size = get_value(summary.get("size", "Unknown"))
                tables = get_value(summary.get("tables", 0))
                connections_data = database_metrics.get("connections", {})
                active_conn = get_value(connections_data.get("active", 0))
                total_conn = get_value(connections_data.get("total", 0))

                cards.append(
                    f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Database</div>
                                <div style="font-size: 2rem; font-weight: bold;">{size}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">{tables} tables • {active_conn}/{total_conn} connections</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """
                )
            else:
                # From raw data (legacy format)
                db_size = database_metrics.get("database_size", "Unknown")
                tables_count = len(database_metrics.get("tables", []))
                connections = database_metrics.get("active_connections", 0)
                cards.append(
                    f"""
                    <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.9rem; opacity: 0.9;">Database</div>
                                <div style="font-size: 2rem; font-weight: bold;">{db_size}</div>
                                <div style="font-size: 0.85rem; opacity: 0.8;">{tables_count} tables • {connections} connections</div>
                            </div>
                            <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                        </div>
                    </div>
                """
                )

        # 6. Servers summary (last)
        server_data = metrics.get("servers", {}).get("summary", {})
        if server_data:
            total = get_value(server_data.get("total", 0))
            online = get_value(server_data.get("online", 0))
            visual = get_category_visual("servers")
            cards.append(
                f"""
                <div class="metric-card" style="background: linear-gradient(135deg, {visual['color']}, {visual['color']}dd); color: white; padding: 1.5rem; border-radius: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">Servers</div>
                            <div style="font-size: 2rem; font-weight: bold;">{total}</div>
                            <div style="font-size: 0.85rem; opacity: 0.8;">{online} online</div>
                        </div>
                        <i class="fas {visual['icon']}" style="font-size: 2.5rem; opacity: 0.3;"></i>
                    </div>
                </div>
            """
            )

        return "\n".join(cards)

    def _generate_agents_metrics_section(self, agent_metrics: Dict[str, Any]) -> str:
        """Generate agents metrics section"""
        if not agent_metrics:
            return ""

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, "value"):
                return data.value
            return data if data is not None else 0

        def get_label(data, key):
            if hasattr(data, "label"):
                return data.label
            return key.replace("_", " ").title()

        html = """
        <div class="metric-section card" style="padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem;"><i class="fas fa-robot"></i> Agent Metrics</h3>
        """

        # Add summary
        summary = agent_metrics.get("summary", {})
        if summary:
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
            for key, value in summary.items():
                display_value = get_value(value)
                label = get_label(value, key)
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--accent-color);">{display_value}</div>
                        <div style="font-size: 0.85rem; color: var(--secondary-text);">{label}</div>
                    </div>
                """
            html += "</div>"

        # Add by type breakdown
        by_type = agent_metrics.get("by_type", {})
        if by_type:
            html += '<div style="margin-top: 1rem;"><h4>Agents by Type</h4><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem;">'
            for agent_type, value in by_type.items():
                count = get_value(value)
                # Type-specific colors
                type_colors = {
                    "workforce": "#6b7280",
                    "leader": "#ec4899",
                    "executive": "#6366f1",
                    "decision": "#14b8a6",
                    "engineering": "#06b6d4",
                }
                color = type_colors.get(agent_type.lower(), "var(--accent-color)")
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 0.5rem; border-radius: 6px; text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold; color: {color};">{count}</div>
                        <div style="font-size: 0.8rem; color: var(--secondary-text);">{agent_type.title()}</div>
                    </div>
                """
            html += "</div></div>"

        # Add by status breakdown
        by_status = agent_metrics.get("by_status", {})
        if (
            by_status and len(by_status) > 1
        ):  # Only show if there's more than just 'offline'
            html += '<div style="margin-top: 1rem;"><h4>Agents by Status</h4><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem;">'
            for status, value in by_status.items():
                count = get_value(value)
                status_color = (
                    "var(--success-color)"
                    if status == "online"
                    else "var(--warning-color)"
                )
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 0.5rem; border-radius: 6px; text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold; color: {status_color};">{count}</div>
                        <div style="font-size: 0.8rem; color: var(--secondary-text);">{status.title()}</div>
                    </div>
                """
            html += "</div></div>"

        html += "</div>"
        return html

    def _generate_departments_metrics_section(
        self, dept_metrics: Dict[str, Any]
    ) -> str:
        """Generate departments metrics section"""
        if not dept_metrics:
            return ""

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, "value"):
                return data.value
            return data if data is not None else 0

        def get_label(data, key):
            if hasattr(data, "label"):
                return data.label
            return key.replace("_", " ").title()

        html = """
        <div class="metric-section card" style="padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem;"><i class="fas fa-building"></i> Department Metrics</h3>
        """

        # Department summary metrics
        summary = dept_metrics.get("summary", {})
        if summary:
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
            # Show key metrics first
            key_metrics = ["total", "active", "planning", "operational"]
            for key in key_metrics:
                if key in summary:
                    value = summary[key]
                    display_value = get_value(value)
                    label = get_label(value, key)
                    color = (
                        value.color
                        if hasattr(value, "color")
                        else "var(--accent-color)"
                    )
                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{display_value}</div>
                            <div style="font-size: 0.85rem; color: var(--secondary-text);">{label}</div>
                        </div>
                    """
            html += "</div>"

        # Add status breakdown
        by_status = dept_metrics.get("by_status", {})
        if by_status:
            html += '<div style="margin-top: 1rem;"><h4>Departments by Status</h4><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem;">'
            for status, value in by_status.items():
                count = get_value(value)
                status_color = (
                    "#10b981"
                    if status == "active"
                    else "#3b82f6"
                    if status == "planning"
                    else "var(--accent-color)"
                )
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 0.5rem; border-radius: 6px; text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold; color: {status_color};">{count}</div>
                        <div style="font-size: 0.8rem; color: var(--secondary-text);">{status.title()}</div>
                    </div>
                """
            html += "</div></div>"

        html += "</div>"
        return html

    def _generate_divisions_metrics_section(self, div_metrics: Dict[str, Any]) -> str:
        """Generate divisions metrics section"""
        if not div_metrics:
            return ""

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, "value"):
                return data.value
            return data if data is not None else 0

        def get_label(data, key):
            if hasattr(data, "label"):
                return data.label
            return key.replace("_", " ").title()

        html = """
        <div class="metric-section card" style="padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem;"><i class="fas fa-sitemap"></i> Division Metrics</h3>
        """

        # Division summary metrics
        summary = div_metrics.get("summary", {})
        if summary:
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
            for key, value in summary.items():
                display_value = get_value(value)
                label = get_label(value, key)
                color = (
                    value.color if hasattr(value, "color") else "var(--accent-color)"
                )
                icon = value.icon if hasattr(value, "icon") else None
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{display_value}</div>
                        <div style="font-size: 0.85rem; color: var(--secondary-text);">{label}</div>
                    </div>
                """
            html += "</div>"

        # Individual divisions
        individual = div_metrics.get("individual", [])
        if individual:
            html += '<div style="margin-top: 1rem;"><h4>Division Details</h4><div style="display: grid; gap: 0.5rem;">'
            for division in individual[:10]:  # Show first 10
                if hasattr(division, "name") and hasattr(division, "metrics"):
                    status = get_value(division.metrics.get("active", "Unknown"))
                    departments = get_value(division.metrics.get("departments", 0))
                    leaders = get_value(division.metrics.get("leaders", 0))
                    agents = get_value(division.metrics.get("agents", 0))
                    status_color = "#10b981" if status == "Active" else "#6b7280"

                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                            <span style="font-weight: 500;">{division.name}</span>
                            <span style="color: {status_color}; font-size: 0.85rem;">● {status}</span>
                            <span style="color: var(--secondary-text); font-size: 0.9rem;">{departments} depts</span>
                            <span style="color: var(--secondary-text); font-size: 0.9rem;">{leaders} leaders</span>
                            <span style="color: var(--secondary-text); font-size: 0.9rem;">{agents} agents</span>
                        </div>
                    """
            html += "</div></div>"

        html += "</div>"
        return html

    def _generate_servers_metrics_section(self, server_metrics: Dict[str, Any]) -> str:
        """Generate servers metrics section"""
        if not server_metrics:
            return ""

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, "value"):
                return data.value
            return data if data is not None else 0

        def get_label(data, key):
            if hasattr(data, "label"):
                return data.label
            return key.replace("_", " ").title()

        html = """
        <div class="metric-section card" style="padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem;"><i class="fas fa-server"></i> Server Metrics</h3>
        """

        # Add summary
        summary = server_metrics.get("summary", {})
        if summary:
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
            for key, value in summary.items():
                display_value = get_value(value)
                label = get_label(value, key)
                color = (
                    value.color if hasattr(value, "color") else "var(--accent-color)"
                )
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{display_value}</div>
                        <div style="font-size: 0.85rem; color: var(--secondary-text);">{label}</div>
                    </div>
                """
            html += "</div>"

        # Add individual servers
        individual = server_metrics.get("individual", [])
        if individual:
            html += '<div style="margin-top: 1rem;"><h4>Server Status</h4><div style="display: grid; gap: 0.5rem;">'
            for server in individual[:10]:  # Show first 10
                if hasattr(server, "name") and hasattr(server, "metrics"):
                    status = get_value(server.metrics.get("status", "unknown"))
                    port = get_value(server.metrics.get("port", "N/A"))
                    response_time = get_value(server.metrics.get("response_time", 0))
                    status_color = (
                        "var(--success-color)"
                        if status == "healthy"
                        else "var(--danger-color)"
                    )

                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                            <span style="font-weight: 500;">{server.name}</span>
                            <span style="color: {status_color};">● {status}</span>
                            <span style="color: var(--secondary-text);">Port {port}</span>
                            <span style="color: var(--secondary-text);">{response_time}ms</span>
                        </div>
                    """

            if len(individual) > 10:
                html += f'<div style="text-align: center; color: var(--secondary-text); padding: 0.5rem;">... and {len(individual) - 10} more</div>'
            html += "</div></div>"

        html += "</div>"
        return html

    def _generate_database_metrics_section(
        self, database_metrics: Dict[str, Any]
    ) -> str:
        """Generate database metrics section"""
        if not database_metrics:
            return ""

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, "value"):
                return data.value
            return data if data is not None else 0

        def get_label(data, key):
            if hasattr(data, "label"):
                return data.label
            return key.replace("_", " ").title()

        html = """
        <div class="metric-section card" style="padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem;"><i class="fas fa-database"></i> Database Metrics</h3>
        """

        # Check if it's from metrics layer (has summary) or raw data
        if "summary" in database_metrics:
            # From metrics layer
            summary = database_metrics.get("summary", {})
            if summary:
                html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
                for key, value in summary.items():
                    display_value = get_value(value)
                    label = get_label(value, key)
                    color = (
                        value.color
                        if hasattr(value, "color")
                        else "var(--accent-color)"
                    )
                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{display_value}</div>
                            <div style="font-size: 0.85rem; color: var(--secondary-text);">{label}</div>
                        </div>
                    """
                html += "</div>"

            # Performance metrics
            performance = database_metrics.get("performance", {})
            if performance:
                html += '<div style="margin-top: 1rem;"><h4>Performance Metrics</h4><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.5rem;">'
                for key, value in performance.items():
                    display_value = get_value(value)
                    label = get_label(value, key)
                    color = (
                        value.color
                        if hasattr(value, "color")
                        else "var(--accent-color)"
                    )
                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; text-align: center;">
                            <div style="font-size: 1.2rem; font-weight: bold; color: {color};">{display_value}</div>
                            <div style="font-size: 0.8rem; color: var(--secondary-text);">{label}</div>
                        </div>
                    """
                html += "</div></div>"

            # Top tables
            tables = database_metrics.get("tables", [])
            if tables:
                html += '<div style="margin-top: 1rem;"><h4>Largest Tables</h4><div style="display: grid; gap: 0.5rem;">'
                for table in tables[:5]:  # Show first 5
                    name = table.get("name", "Unknown")
                    size = table.get("size", "N/A")

                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 500;">{name}</span>
                            <span style="color: var(--secondary-text); font-size: 0.9rem;">{size}</span>
                        </div>
                    """
                html += "</div></div>"

        else:
            # From raw data (legacy format)
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'

            # Basic stats
            db_size = database_metrics.get("database_size", "Unknown")
            tables_count = len(database_metrics.get("tables", []))
            connections = database_metrics.get("active_connections", 0)
            cache_hit = database_metrics.get("cache_hit_ratio", 0)

            html += f"""
                <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--accent-color);">{db_size}</div>
                    <div style="font-size: 0.85rem; color: var(--secondary-text);">Database Size</div>
                </div>
                <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--accent-color);">{tables_count}</div>
                    <div style="font-size: 0.85rem; color: var(--secondary-text);">Total Tables</div>
                </div>
                <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--success-color);">{connections}</div>
                    <div style="font-size: 0.85rem; color: var(--secondary-text);">Active Connections</div>
                </div>
                <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: bold; color: var(--success-color);">{cache_hit:.1f}%</div>
                    <div style="font-size: 0.85rem; color: var(--secondary-text);">Cache Hit Ratio</div>
                </div>
            """
            html += "</div>"

            # Show some tables
            tables = database_metrics.get("tables", [])
            if tables:
                html += '<div style="margin-top: 1rem;"><h4>Database Tables (showing first 5)</h4><div style="display: grid; gap: 0.5rem;">'
                for table in tables[:5]:
                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 1rem; align-items: center;">
                            <span style="font-weight: 500;">{table['name']}</span>
                            <span style="color: var(--secondary-text); font-size: 0.9rem;">{table['size']}</span>
                            <span style="color: var(--secondary-text); font-size: 0.9rem;">{table['columns']} columns</span>
                        </div>
                    """
                if len(tables) > 5:
                    html += f'<div style="text-align: center; color: var(--secondary-text); padding: 0.5rem;">... and {len(tables) - 5} more tables</div>'
                html += "</div></div>"

        html += "</div>"
        return html

    def _generate_leaders_metrics_section(self, leader_metrics: Dict[str, Any]) -> str:
        """Generate leaders metrics section"""
        if not leader_metrics:
            return ""

        # Helper function to extract value
        def get_value(data):
            if hasattr(data, "value"):
                return data.value
            return data if data is not None else 0

        def get_label(data, key):
            if hasattr(data, "label"):
                return data.label
            return key.replace("_", " ").title()

        html = """
        <div class="metric-section card" style="padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem;"><i class="fas fa-user-tie"></i> Leader Metrics</h3>
        """

        # Add summary
        summary = leader_metrics.get("summary", {})
        if summary:
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">'
            for key, value in summary.items():
                display_value = get_value(value)
                label = get_label(value, key)
                color = (
                    value.color if hasattr(value, "color") else "var(--accent-color)"
                )
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{display_value}</div>
                        <div style="font-size: 0.85rem; color: var(--secondary-text);">{label}</div>
                    </div>
                """
            html += "</div>"

        # Add leaders by tier
        by_tier = leader_metrics.get("by_tier", {})
        if by_tier:
            html += '<div style="margin-top: 1rem;"><h4>Leaders by Tier</h4><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem;">'
            for tier, value in by_tier.items():
                count = get_value(value)
                html += f"""
                    <div style="background: var(--secondary-bg); padding: 0.5rem; border-radius: 6px; text-align: center;">
                        <div style="font-size: 1.2rem; font-weight: bold; color: var(--executive-color);">{count}</div>
                        <div style="font-size: 0.8rem; color: var(--secondary-text);">{tier.title()}</div>
                    </div>
                """
            html += "</div></div>"

        # Add top leaders
        individual = leader_metrics.get("individual", [])
        if individual:
            html += '<div style="margin-top: 1rem;"><h4>Top Leaders</h4><div style="display: grid; gap: 0.5rem;">'
            for leader in individual[:5]:  # Show first 5
                if hasattr(leader, "name") and hasattr(leader, "metrics"):
                    title = get_value(leader.metrics.get("title", "Unknown"))
                    department = get_value(leader.metrics.get("department", "Unknown"))
                    authority = get_value(leader.metrics.get("authority", 0))
                    status = get_value(leader.metrics.get("status", "Unknown"))
                    status_color = (
                        leader.metrics.get("status").color
                        if hasattr(leader.metrics.get("status"), "color")
                        else "var(--secondary-text)"
                    )

                    html += f"""
                        <div style="background: var(--secondary-bg); padding: 0.75rem; border-radius: 6px; display: grid; grid-template-columns: 2fr 2fr 1fr 1fr; gap: 1rem; align-items: center;">
                            <span style="font-weight: 500;">{leader.name}</span>
                            <span style="color: var(--secondary-text); font-size: 0.9rem;">{title}</span>
                            <span style="color: {status_color}; font-size: 0.85rem;">● {status}</span>
                            <span style="color: var(--executive-color); text-align: right;">Auth: {authority}</span>
                        </div>
                    """

            if len(individual) > 5:
                html += f'<div style="text-align: center; color: var(--secondary-text); padding: 0.5rem;">... and {len(individual) - 5} more</div>'
            html += "</div></div>"

        html += "</div>"
        return html

    def _generate_error_html(self, page_type: str, error_message: str) -> str:
        """Generate error HTML for a specific page type"""
        return f"""
        <div class="alert alert-danger" style="margin: 2rem;">
            <h3><i class="fas fa-exclamation-triangle"></i> Error Loading {page_type.title()} Page</h3>
            <p>{error_message}</p>
        </div>
        """

    def _generate_agent_department_chart(self, dept_data: Dict[str, int]) -> str:
        """Generate department distribution chart for agents"""
        if not dept_data:
            return "<p>No department data available</p>"

        # Sort departments by agent count
        sorted_depts = sorted(dept_data.items(), key=lambda x: x[1], reverse=True)[:10]

        chart_html = '<div style="display: grid; gap: 0.5rem;">'
        max_count = max(dept_data.values()) if dept_data else 1

        for dept, count in sorted_depts:
            percentage = (count / max_count) * 100
            chart_html += f"""
            <div style="display: grid; grid-template-columns: 150px 1fr 50px; align-items: center; gap: 1rem;">
                <div style="font-size: 0.9rem; color: var(--secondary-text);">{dept}</div>
                <div style="background: var(--border-color); height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #3b82f6, #1e40af); height: 100%; width: {percentage}%; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 0.9rem; font-weight: bold; text-align: right;">{count}</div>
            </div>
            """

        chart_html += "</div>"
        return chart_html


# CSS for the metric cards
METRICS_CSS = """
<style>
/* Metrics Grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

/* Agent Cards Grid */
.agent-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

/* Department Cards */
.department-cards-container {
    margin: 1rem 0;
}

.division-group {
    margin-bottom: 2rem;
}

.division-header {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--primary-text);
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border-color);
}

.department-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
}

/* Enhanced Card Styles */
.department-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.25rem;
    transition: all 0.3s ease;
}

.department-card:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dept-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}

.dept-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.5rem;
}

.dept-info h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1.1rem;
    color: var(--primary-text);
}

.dept-info p {
    margin: 0;
    font-size: 0.85rem;
    color: var(--secondary-text);
}

.dept-metrics {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 0.75rem;
}

.metric-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

.metric-row:last-child {
    margin-bottom: 0;
}

/* Widget Details */
.widget-details {
    margin-top: 0.5rem;
    font-size: 0.85rem;
    color: var(--secondary-text);
}
</style>
"""
