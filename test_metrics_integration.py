#!/usr/bin/env python3
"""
Test the metrics layer integration
"""

from core.hq_metrics_integration import HQMetricsIntegration
from core.hq_metrics_layer import BFColors, BFIcons

def test_metrics():
    """Test that metrics layer is working"""
    print("🧪 Testing Metrics Layer Integration")
    print("=" * 60)
    
    try:
        # Initialize metrics
        metrics = HQMetricsIntegration()
        print("✅ Metrics layer initialized")
        
        # Get agent metrics
        print("\n📊 Agent Metrics:")
        agent_metrics = metrics.get_agents_page_metrics()
        print(f"   Active Agents: {agent_metrics['active']} (actual running processes)")
        print(f"   Total Agents: {agent_metrics['total']} (registered in database)")
        print(f"   Inactive Agents: {agent_metrics['inactive']}")
        
        # Get all metrics
        print("\n📊 All Metrics Summary:")
        all_metrics = metrics.get_all_metrics()
        
        # Agents
        agent_summary = all_metrics.get('agents', {}).get('summary', {})
        print(f"\n   Agents:")
        print(f"     - Online in DB: {metrics.get_metric_value('agents', 'summary.online', 0)}")
        print(f"     - Operational: {metrics.get_metric_value('agents', 'summary.operational', 0)}")
        print(f"     - Deployed: {metrics.get_metric_value('agents', 'summary.deployed', 0)}")
        
        # Departments
        dept_summary = all_metrics.get('departments', {}).get('summary', {})
        print(f"\n   Departments:")
        print(f"     - Total: {metrics.get_metric_value('departments', 'summary.total', 0)}")
        print(f"     - Active: {metrics.get_metric_value('departments', 'summary.active', 0)}")
        
        # Servers
        server_summary = all_metrics.get('servers', {}).get('summary', {})
        print(f"\n   Servers:")
        print(f"     - Total: {metrics.get_metric_value('servers', 'summary.total', 0)}")
        print(f"     - Healthy: {metrics.get_metric_value('servers', 'summary.healthy', 0)}")
        
        # Test HTML generation
        print("\n🎨 Testing HTML Generation:")
        
        # Dashboard cards
        dashboard_html = metrics.get_dashboard_summary_cards()
        print(f"   - Dashboard cards HTML: {len(dashboard_html)} characters")
        
        # Agent cards
        agent_html = metrics.get_agent_cards_html(limit=5)
        print(f"   - Agent cards HTML: {len(agent_html)} characters")
        
        # Department cards
        dept_html = metrics.get_department_cards_html()
        print(f"   - Department cards HTML: {len(dept_html)} characters")
        
        print("\n✅ All metrics layer functions working correctly!")
        
        # Show visual standards
        print("\n🎨 Visual Standards:")
        print(f"   Success Color: {BFColors.SUCCESS}")
        print(f"   Executive Color: {BFColors.EXECUTIVE}")
        print(f"   Agent Icon: {BFIcons.AGENT}")
        print(f"   Department Icon: {BFIcons.DEPARTMENT}")
        
    except Exception as e:
        print(f"❌ Error testing metrics: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_metrics()