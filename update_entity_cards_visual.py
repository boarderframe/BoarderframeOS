#!/usr/bin/env python3
"""
Update all entity cards to use database visual metadata
"""

import re


def update_entity_cards():
    """Update entity card rendering methods to use visual metadata"""
    print("🎨 Updating entity card rendering methods")
    print("=" * 60)

    # Read hq_metrics_layer.py
    with open('core/hq_metrics_layer.py', 'r') as f:
        content = f.read()

    # Update agent metrics to include visual metadata
    agent_visual_update = """
            for row in cur.fetchall():
                # Get visual metadata for agent
                agent_visual = self._visual_cache.get_visual('agents', str(row[0]), row[1])

                agent = EntityMetrics(
                    entity_id=str(row[0]),
                    entity_type='agent',
                    name=row[1],
                    metrics={
                        'status': MetricValue(row[3], "Status",
                            color=BFColors.SUCCESS if row[3] == 'online' else BFColors.NEUTRAL),
                        'operational': MetricValue(row[4], "Operational Status"),
                        'development': MetricValue(row[5], "Development Status"),
                        'skill_level': MetricValue(row[6], "Skill Level", unit="level"),
                        'training': MetricValue(row[7], "Training Progress", unit="%"),
                        'load': MetricValue(row[8] or 0, "Current Load", unit="tasks"),
                        'capacity': MetricValue(row[9] or 10, "Max Capacity", unit="tasks"),
                        'response_time': MetricValue(row[10] or 0, "Response Time", unit="ms"),
                        'last_seen': MetricValue(row[11], "Last Heartbeat")
                    },
                    metadata={'type': row[2]},
                    color=agent_visual.get('color'),
                    icon=agent_visual.get('icon', BFIcons.AGENT)
                )
                metrics['individual'].append(agent)"""

    # Replace the agent loop
    pattern = r'for row in cur\.fetchall\(\):\s*agent = EntityMetrics\(.*?metrics\[\'individual\'\]\.append\(agent\)'
    content = re.sub(pattern, agent_visual_update.strip(), content, flags=re.DOTALL)

    # Update leader metrics to include visual metadata
    leader_visual_update = """
            for row in cur.fetchall():
                # Get visual metadata for leader
                leader_visual = self._visual_cache.get_visual('leaders', row[0], row[0])

                leader = EntityMetrics(
                    entity_id=row[0].lower().replace(' ', '_'),
                    entity_type='leader',
                    name=row[0],
                    metrics={
                        'title': MetricValue(row[1], "Title"),
                        'tier': MetricValue(row[2], "Leadership Tier"),
                        'authority': MetricValue(row[3], "Authority Level"),
                        'department': MetricValue(row[4], "Department"),
                        'division': MetricValue(row[5], "Division")
                    },
                    color=leader_visual.get('color', BFColors.LEADERSHIP),
                    icon=leader_visual.get('icon', BFIcons.LEADER)
                )
                metrics['individual'].append(leader)"""

    # Find and replace the leader loop
    leader_pattern = r'for row in cur\.fetchall\(\):\s*leader = EntityMetrics\(.*?entity_type=\'leader\'.*?metrics\[\'individual\'\]\.append\(leader\)'
    content = re.sub(leader_pattern, leader_visual_update.strip(), content, flags=re.DOTALL)

    # Update server metrics to use visual metadata
    server_visual_update = """
            for name, port, status, response_time in servers:
                # Get visual metadata for server
                server_visual = self._visual_cache.get_visual('servers', name, name)

                server = EntityMetrics(
                    entity_id=name,
                    entity_type='server',
                    name=name.title() + " Server",
                    metrics={
                        'status': MetricValue(status, "Status",
                            color=BFColors.SUCCESS if status == 'healthy' else BFColors.DANGER),
                        'port': MetricValue(port, "Port"),
                        'response_time': MetricValue(response_time, "Response Time", unit="ms"),
                        'uptime': MetricValue("99.9%", "Uptime")
                    },
                    icon=server_visual.get('icon', BFIcons.SERVER),
                    color=server_visual.get('color', BFColors.SUCCESS if status == 'healthy' else BFColors.DANGER)
                )
                metrics['individual'].append(server)"""

    # Replace server loop
    server_pattern = r'for name, port, status, response_time in servers:\s*server = EntityMetrics\(.*?metrics\[\'individual\'\]\.append\(server\)'
    content = re.sub(server_pattern, server_visual_update.strip(), content, flags=re.DOTALL)

    # Save updated file
    with open('core/hq_metrics_layer.py', 'w') as f:
        f.write(content)

    print("✅ Updated entity card rendering in hq_metrics_layer.py")

    # Now update the card renderer to use entity colors
    print("\n🎨 Updating card renderer...")

    # Find render_agent_card method
    agent_card_update = '''
    @staticmethod
    def render_agent_card(agent: EntityMetrics) -> str:
        """Render an agent card with metrics"""
        status = agent.metrics.get('status', MetricValue('unknown', 'Unknown'))
        status_class = 'active' if status.value == 'online' else 'inactive'

        # Use entity color if available
        card_color = agent.color or BFColors.INFO
        icon = agent.icon or BFIcons.AGENT

        return f"""
        <div class="agent-card {status_class}" style="border-left: 4px solid {card_color};">
            <div class="agent-header">
                <div>
                    <h4 class="agent-name">
                        <i class="fas {icon}" style="color: {card_color}; margin-right: 0.5rem;"></i>
                        {agent.name}
                    </h4>
                    <p class="agent-type">{agent.metadata.get('type', 'Agent')}</p>
                </div>
                <div class="agent-status {status.value}">
                    {status.value.upper()}
                </div>
            </div>
            <div class="agent-metrics">
                <div class="metric-chip">
                    <i class="fas fa-tachometer-alt"></i>
                    {agent.metrics.get('load', MetricValue(0, '')).value}/{agent.metrics.get('capacity', MetricValue(10, '')).value}
                </div>
                <div class="metric-chip">
                    <i class="fas fa-clock"></i>
                    {agent.metrics.get('response_time', MetricValue(0, '')).value}ms
                </div>
            </div>
        </div>
        """'''

    # Replace render_agent_card method
    agent_card_pattern = r'@staticmethod\s*def render_agent_card\(agent: EntityMetrics\) -> str:.*?"""'
    content = re.sub(agent_card_pattern, agent_card_update.strip(), content, flags=re.DOTALL)

    # Save final updates
    with open('core/hq_metrics_layer.py', 'w') as f:
        f.write(content)

    print("✅ Updated card renderer methods")

    # Update integration to use visual cache for individual metric cards
    print("\n🎨 Updating metric card generation in integration...")

    with open('core/hq_metrics_integration.py', 'r') as f:
        integration_content = f.read()

    # Update agent metrics cards to use database colors
    agent_metrics_update = '''
    def get_agent_metrics_cards(self) -> str:
        """Generate metric cards for the agents page with database colors"""
        metrics = self.get_all_metrics()
        agent_metrics = self.get_agents_page_metrics()

        # Get visual metadata for agents category
        visual_cache = None
        agent_visual = {'color': '#3b82f6', 'icon': 'fa-robot'}  # defaults

        if VisualMetadataCache:
            try:
                visual_cache = VisualMetadataCache(self.metrics_calc.db_config)
                agent_visual = visual_cache.get_visual('agents')
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

        return cards_html'''

    # Replace get_agent_metrics_cards method
    integration_content = re.sub(
        r'def get_agent_metrics_cards\(self\) -> str:.*?return cards_html',
        agent_metrics_update.strip(),
        integration_content,
        flags=re.DOTALL
    )

    # Update department metrics cards similarly
    dept_metrics_update = '''
    def get_department_metrics_cards(self) -> str:
        """Generate metric cards for the departments page with database colors"""
        metrics = self.get_all_metrics()
        dept_data = metrics.get('departments', {})
        dept_summary = dept_data.get('summary', {})

        total = self.get_metric_value('departments', 'summary.total', 45)
        active = self.get_metric_value('departments', 'summary.active', 45)
        divisions = self.get_metric_value('departments', 'summary.divisions', 9)

        # Get visual metadata for departments category
        visual_cache = None
        dept_visual = {'color': '#10b981', 'icon': 'fa-building'}  # defaults
        div_visual = {'color': '#8b5cf6', 'icon': 'fa-sitemap'}  # defaults

        if VisualMetadataCache:
            try:
                visual_cache = VisualMetadataCache(self.metrics_calc.db_config)
                dept_visual = visual_cache.get_visual('departments')
                div_visual = visual_cache.get_visual('divisions')
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

        return cards_html'''

    # Replace get_department_metrics_cards method
    integration_content = re.sub(
        r'def get_department_metrics_cards\(self\) -> str:.*?return cards_html',
        dept_metrics_update.strip(),
        integration_content,
        flags=re.DOTALL
    )

    # Save updated integration file
    with open('core/hq_metrics_integration.py', 'w') as f:
        f.write(integration_content)

    print("✅ Updated metric card generation methods")
    print("\n✅ Entity card visual integration complete!")


if __name__ == "__main__":
    update_entity_cards()
