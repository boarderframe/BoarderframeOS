#!/usr/bin/env python3
"""
Demo script for the HQ Metrics Layer
Shows how to use the comprehensive metrics system
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from core.hq_metrics_integration import HQMetricsIntegration, METRICS_CSS
from core.hq_metrics_layer import BFColors, BFIcons

def demo_metrics_layer():
    """Demonstrate the metrics layer capabilities"""
    print("🎯 BoarderframeOS HQ Metrics Layer Demo")
    print("=" * 60)
    
    # Initialize metrics integration
    print("\n📊 Initializing Metrics Integration...")
    metrics = HQMetricsIntegration()
    
    # 1. Get all metrics
    print("\n1️⃣ Fetching All Metrics...")
    all_metrics = metrics.get_all_metrics()
    
    # Display agent metrics
    agent_summary = all_metrics.get('agents', {}).get('summary', {})
    print("\n📊 Agent Metrics:")
    for key, metric in agent_summary.items():
        if hasattr(metric, 'value'):
            print(f"   - {metric.label}: {metric.value}")
    
    # Display department metrics
    dept_summary = all_metrics.get('departments', {}).get('summary', {})
    print("\n🏢 Department Metrics:")
    for key, metric in dept_summary.items():
        if hasattr(metric, 'value'):
            print(f"   - {metric.label}: {metric.value}")
    
    # Display server metrics
    server_summary = all_metrics.get('servers', {}).get('summary', {})
    print("\n🖥️ Server Metrics:")
    for key, metric in server_summary.items():
        if hasattr(metric, 'value'):
            print(f"   - {metric.label}: {metric.value}")
    
    # 2. Generate dashboard cards
    print("\n2️⃣ Generating Dashboard Summary Cards...")
    summary_html = metrics.get_dashboard_summary_cards()
    print(f"   ✅ Generated {summary_html.count('widget')} dashboard widgets")
    
    # 3. Get agent-specific metrics
    print("\n3️⃣ Getting Agent Page Metrics...")
    agent_page = metrics.get_agents_page_metrics()
    print(f"   - Active: {agent_page['active']}")
    print(f"   - Inactive: {agent_page['inactive']}")
    print(f"   - Total: {agent_page['total']}")
    
    # Show by type
    print("\n   By Type:")
    for agent_type, metric in agent_page.get('by_type', {}).items():
        if hasattr(metric, 'value'):
            print(f"     - {agent_type}: {metric.value}")
    
    # 4. Get departments with visual data
    print("\n4️⃣ Getting Department Visual Data...")
    departments = metrics.get_departments_visual_data()
    print(f"   Found {len(departments)} departments with visual metadata")
    
    # Show first 5 departments
    for dept in departments[:5]:
        print(f"   - {dept['name']}: {dept['icon']} (color: {dept['color']})")
    
    # 5. Generate some cards
    print("\n5️⃣ Generating UI Cards...")
    
    # Agent cards
    agent_cards = metrics.get_agent_cards_html(limit=3)
    agent_count = agent_cards.count('agent-card')
    print(f"   ✅ Generated {agent_count} agent cards")
    
    # Department cards
    dept_cards = metrics.get_department_cards_html()
    dept_count = dept_cards.count('department-card')
    print(f"   ✅ Generated {dept_count} department cards")
    
    # 6. Test specific metric retrieval
    print("\n6️⃣ Testing Specific Metric Retrieval...")
    online_agents = metrics.get_metric_value('agents', 'summary.online', 0)
    print(f"   - Online agents: {online_agents}")
    
    total_servers = metrics.get_metric_value('servers', 'summary.total', 0)
    print(f"   - Total servers: {total_servers}")
    
    # 7. Show color palette
    print("\n🎨 Standard Color Palette:")
    print(f"   - SUCCESS: {BFColors.SUCCESS}")
    print(f"   - WARNING: {BFColors.WARNING}")
    print(f"   - DANGER: {BFColors.DANGER}")
    print(f"   - EXECUTIVE: {BFColors.EXECUTIVE}")
    print(f"   - ENGINEERING: {BFColors.ENGINEERING}")
    
    # 8. Show icon set
    print("\n🎯 Standard Icon Set:")
    print(f"   - AGENT: {BFIcons.AGENT}")
    print(f"   - DEPARTMENT: {BFIcons.DEPARTMENT}")
    print(f"   - SERVER: {BFIcons.SERVER}")
    print(f"   - ACTIVE: {BFIcons.ACTIVE}")
    
    # 9. Create sample HTML file
    print("\n📝 Creating sample HTML output...")
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>HQ Metrics Layer Demo</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary-bg: #0a0e27;
            --secondary-bg: #1a1d3a;
            --card-bg: #252853;
            --primary-text: #ffffff;
            --secondary-text: #b0b7c3;
            --accent-color: #6366f1;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --border-color: #374151;
        }}
        body {{
            background: var(--primary-bg);
            color: var(--primary-text);
            font-family: -apple-system, sans-serif;
            padding: 2rem;
        }}
        h1, h2 {{
            color: var(--accent-color);
        }}
        .section {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: var(--secondary-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }}
    </style>
    {METRICS_CSS}
</head>
<body>
    <h1>HQ Metrics Layer Demo</h1>
    
    <div class="section">
        <h2>Dashboard Summary</h2>
        {summary_html}
    </div>
    
    <div class="section">
        <h2>Agent Cards (First 3)</h2>
        {agent_cards}
    </div>
    
    <div class="section">
        <h2>Department Cards</h2>
        {dept_cards}
    </div>
</body>
</html>
"""
    
    with open('demo_metrics_output.html', 'w') as f:
        f.write(html_content)
    
    print("   ✅ Created demo_metrics_output.html")
    print("\n✨ Demo complete! Open demo_metrics_output.html to see the results.")

if __name__ == "__main__":
    demo_metrics_layer()