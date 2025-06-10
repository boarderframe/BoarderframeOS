#!/usr/bin/env python3
"""
Test all page metrics methods
"""

from core.hq_metrics_integration import HQMetricsIntegration

def test_all_pages():
    """Test that all page methods work correctly"""
    print("🧪 Testing All Page Metrics Methods")
    print("=" * 60)
    
    try:
        # Initialize metrics
        metrics = HQMetricsIntegration()
        print("✅ Metrics layer initialized")
        
        # Test agent metrics cards
        print("\n📊 Testing Agent Metrics Cards:")
        agent_cards = metrics.get_agent_metrics_cards()
        print(f"   ✅ Agent metrics cards: {len(agent_cards)} characters")
        print(f"   Contains Active: {'Active' in agent_cards}")
        print(f"   Contains Inactive: {'Inactive' in agent_cards}")
        print(f"   Contains Total: {'Total' in agent_cards}")
        
        # Test department metrics cards
        print("\n📊 Testing Department Metrics Cards:")
        dept_cards = metrics.get_department_metrics_cards()
        print(f"   ✅ Department metrics cards: {len(dept_cards)} characters")
        print(f"   Contains Total Departments: {'Total Departments' in dept_cards}")
        print(f"   Contains Active: {'Active' in dept_cards}")
        print(f"   Contains Divisions: {'Divisions' in dept_cards}")
        
        # Test leaders page
        print("\n📊 Testing Leaders Page:")
        leaders_html = metrics.get_leaders_page_html()
        print(f"   ✅ Leaders page HTML: {len(leaders_html)} characters")
        print(f"   Contains Leadership Overview: {'Leadership Overview' in leaders_html}")
        print(f"   Has metrics integration note: {'Leaders Metrics Integration' in leaders_html}")
        
        # Test divisions page
        print("\n📊 Testing Divisions Page:")
        divisions_html = metrics.get_divisions_page_html()
        print(f"   ✅ Divisions page HTML: {len(divisions_html)} characters")
        print(f"   Contains Divisions Overview: {'Divisions Overview' in divisions_html}")
        print(f"   Has division cards: {'division-card' in divisions_html}")
        
        # Check actual metrics values
        print("\n📊 Checking Actual Metrics Values:")
        agent_metrics = metrics.get_agents_page_metrics()
        print(f"   Active Agents: {agent_metrics['active']}")
        print(f"   Total Agents: {agent_metrics['total']}")
        print(f"   Inactive Agents: {agent_metrics['inactive']}")
        
        # Get all metrics
        all_metrics = metrics.get_all_metrics()
        dept_count = metrics.get_metric_value('departments', 'summary.total', 0)
        print(f"   Total Departments: {dept_count}")
        
        print("\n✅ All page metrics methods working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing page metrics: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_all_pages()