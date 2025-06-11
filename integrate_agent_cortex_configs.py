#!/usr/bin/env python3
"""
Integrate Agent Cortex Panel with existing agent configurations
Updates agent configs to use the new LLM management system
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.agent_cortex_panel import AgentCortexPanel


async def integrate_configs():
    """Update existing agent configurations"""
    print("\n🔄 Integrating Agent Cortex with existing configurations...")
    print("=" * 60)

    # Create panel instance
    panel = AgentCortexPanel()
    await panel.initialize()

    # Update David and Solomon configs to use latest models
    updates = [
        {
            "name": "david",
            "title": "CEO",
            "tier": "executive",
            "department": "Executive Leadership",
            "provider": "anthropic",
            "model": "claude-opus-4-20250514",
            "temperature": 0.7,
            "max_tokens": 4000,
        },
        {
            "name": "solomon",
            "title": "Digital Twin",
            "tier": "executive",
            "department": "Executive Leadership",
            "provider": "anthropic",
            "model": "claude-opus-4-20250514",
            "temperature": 0.3,  # Lower for more focused reasoning
            "max_tokens": 4000,
        },
    ]

    print("\n📝 Updating agent LLM assignments:")
    for agent_data in updates:
        agent_name = agent_data.pop("name")
        title = agent_data.pop("title")

        print(f"\n   • {agent_name.title()} ({title}):")
        print(f"     - Provider: {agent_data['provider']}")
        print(f"     - Model: {agent_data['model']}")
        print(f"     - Temperature: {agent_data['temperature']}")

        # Update in database
        await panel._update_agent_llm(agent_name, agent_data)

        # Update config file
        config_path = Path(f"configs/agents/{agent_name}.json")
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)

            config["model"] = agent_data["model"]
            config["temperature"] = agent_data["temperature"]
            config["provider"] = agent_data["provider"]

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            print(f"     ✅ Config file updated")

    # Add other primordial agents
    primordials = [
        {
            "name": "adam",
            "title": "The Creator",
            "department": "Agent Development",
            "tier": "specialist",
            "provider": "anthropic",
            "model": "claude-4-sonnet-20250514",
            "temperature": 0.8,  # Higher for creativity
            "max_tokens": 2000,
        },
        {
            "name": "eve",
            "title": "The Evolver",
            "department": "Agent Development",
            "tier": "specialist",
            "provider": "anthropic",
            "model": "claude-4-sonnet-20250514",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        {
            "name": "bezalel",
            "title": "Master Programmer",
            "department": "Agent Development",
            "tier": "specialist",
            "provider": "anthropic",
            "model": "claude-4-sonnet-20250514",
            "temperature": 0.5,  # Lower for precise coding
            "max_tokens": 3000,
        },
    ]

    print("\n\n📝 Adding primordial agent configurations:")
    for agent_data in primordials:
        agent_name = agent_data.pop("name")
        title = agent_data.pop("title")

        print(f"\n   • {agent_name.title()} ({title}):")
        print(f"     - Model: {agent_data['model']}")

        await panel._update_agent_llm(agent_name, agent_data)
        print(f"     ✅ Added to Agent Cortex")

    print("\n\n✅ Integration complete!")
    print("=" * 60)
    print("\n📊 Summary:")

    # Get updated stats
    import aiosqlite

    async with aiosqlite.connect(panel.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM agent_llm_assignments")
        count = await cursor.fetchone()
        print(f"   - Total agents configured: {count[0]}")

        cursor = await db.execute(
            "SELECT COUNT(*) FROM llm_providers WHERE is_active = 1"
        )
        provider_count = await cursor.fetchone()
        print(f"   - Active LLM providers: {provider_count[0]}")

        cursor = await db.execute("SELECT COUNT(*) FROM tier_defaults")
        tier_count = await cursor.fetchone()
        print(f"   - Tier configurations: {tier_count[0]}")

    print("\n🚀 Agent Cortex Management Panel is ready!")
    print("   Run: python launch_agent_cortex_panel.py")
    print("   Then visit: http://localhost:8890")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(integrate_configs())
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
