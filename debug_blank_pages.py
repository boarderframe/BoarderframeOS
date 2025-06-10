#!/usr/bin/env python3
"""
Debug why pages are showing blank
"""

from core.hq_metrics_integration import HQMetricsIntegration

def debug_pages():
    """Check what each page method returns"""
    print("🔍 Debugging Blank Pages")
    print("=" * 60)
    
    try:
        # Initialize metrics
        metrics = HQMetricsIntegration()
        print("✅ Metrics layer initialized")
        
        # Test agent metrics cards
        print("\n1️⃣ Testing Agent Metrics Cards:")
        agent_cards = metrics.get_agent_metrics_cards()
        print(f"   Length: {len(agent_cards)} characters")
        print(f"   First 200 chars: {agent_cards[:200]}...")
        print(f"   Contains div: {'<div' in agent_cards}")
        
        # Test department metrics cards  
        print("\n2️⃣ Testing Department Metrics Cards:")
        dept_cards = metrics.get_department_metrics_cards()
        print(f"   Length: {len(dept_cards)} characters")
        print(f"   First 200 chars: {dept_cards[:200]}...")
        
        # Test agent cards
        print("\n3️⃣ Testing Agent Cards HTML:")
        agent_html = metrics.get_agent_cards_html()
        print(f"   Length: {len(agent_html)} characters")
        print(f"   First 200 chars: {agent_html[:200]}...")
        
        # Test department cards
        print("\n4️⃣ Testing Department Cards HTML:")
        dept_html = metrics.get_department_cards_html()
        print(f"   Length: {len(dept_html)} characters")
        print(f"   First 200 chars: {dept_html[:200]}...")
        
        # Test leaders page
        print("\n5️⃣ Testing Leaders Page:")
        leaders_html = metrics.get_leaders_page_html()
        print(f"   Length: {len(leaders_html)} characters")
        print(f"   First 200 chars: {leaders_html[:200]}...")
        
        # Test divisions page
        print("\n6️⃣ Testing Divisions Page:")
        divisions_html = metrics.get_divisions_page_html()
        print(f"   Length: {len(divisions_html)} characters")
        print(f"   First 200 chars: {divisions_html[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_pages()