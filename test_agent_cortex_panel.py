#!/usr/bin/env python3
"""
Test Agent Cortex Panel functionality
Verifies the panel can load and interact with BoarderframeOS
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.agent_cortex_panel import AgentCortexPanel


async def test_panel():
    """Test Agent Cortex Panel features"""
    print("\n🧪 Testing Agent Cortex Panel...")
    print("=" * 60)

    # Create panel instance
    panel = AgentCortexPanel()

    # Initialize
    print("📊 Initializing panel...")
    await panel.initialize()

    # Test 1: Check loaded configurations
    print("\n1️⃣ Checking loaded configurations:")
    print(f"   - Agent configs loaded: {len(panel.agent_configs)}")
    print(f"   - LLM providers: {list(panel.llm_providers.keys())}")
    print(f"   - Department structure loaded: {'boarderframeos_departments' in panel.department_structure}")

    # Test 2: Load agents from department structure
    print("\n2️⃣ Loading agents from departments:")
    agents_found = []
    departments = panel.department_structure.get("boarderframeos_departments", {})
    for phase_key, phase_data in departments.items():
        for dept_key, dept_data in phase_data.get("departments", {}).items():
            for leader in dept_data.get("leaders", []):
                agents_found.append({
                    "name": leader["name"],
                    "title": leader["title"],
                    "department": dept_data["department_name"]
                })

    print(f"   - Total agents found: {len(agents_found)}")
    if agents_found:
        print("   - Sample agents:")
        for agent in agents_found[:5]:
            tier = panel._determine_tier(agent["title"])
            print(f"     • {agent['name']} ({agent['title']}) - {agent['department']} - Tier: {tier}")

    # Test 3: Check tier defaults
    print("\n3️⃣ Loading tier defaults:")
    tiers = await panel._get_tier_defaults()
    for tier, config in tiers.items():
        print(f"   - {tier.upper()}: {config['default_provider']}/{config['default_model']}")

    # Test 4: Test LLM provider configurations
    print("\n4️⃣ Testing LLM providers:")
    for name, provider in panel.llm_providers.items():
        status = "✅ Active" if provider["is_active"] else "❌ Inactive"
        models_count = len(provider["models"])
        print(f"   - {name}: {status} ({models_count} models)")

    # Test 5: Check database tables
    print("\n5️⃣ Verifying database structure:")
    import aiosqlite
    async with aiosqlite.connect(panel.db_path) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await cursor.fetchall()
        print(f"   - Tables created: {[t[0] for t in tables]}")

    print("\n✅ All tests completed successfully!")
    print("=" * 60)
    print("\n📌 You can now launch the panel with:")
    print("   python launch_agent_cortex_panel.py")
    print("\n🌐 Then access it at: http://localhost:8890")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_panel())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
