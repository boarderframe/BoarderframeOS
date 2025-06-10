#!/usr/bin/env python3
"""
Demo: Agent Variable Control
Shows how the Agent Cortex Management Center controls actual agent variables
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.agent_variable_inspector import agent_variable_inspector
from core.base_agent import BaseAgent, AgentConfig
from agents.solomon.solomon import Solomon

async def demo_variable_control():
    """Demonstrate variable control across all layers"""
    
    print("🎛️ Agent Variable Control Demo")
    print("=" * 60)
    print("This shows all the ACTUAL variables you can control in the UI")
    print("=" * 60)
    
    # 1. Show all variable layers
    print("📋 Variable Layers Available:")
    layers = set(var.layer for var in agent_variable_inspector.variable_definitions.values())
    for layer in sorted(layers):
        layer_vars = agent_variable_inspector.get_variables_by_layer(layer)
        editable_count = len([v for v in layer_vars.values() if v.editable])
        print(f"   • {layer}: {len(layer_vars)} variables ({editable_count} editable)")
    
    print()
    
    # 2. Show BaseAgent layer variables (most important)
    print("🤖 BaseAgent Layer Variables (affects ALL agents):")
    base_vars = agent_variable_inspector.get_variables_by_layer("BaseAgent")
    for name, var in base_vars.items():
        status = "✏️ " if var.editable else "👁️ "
        affects = f" → affects: {', '.join(var.affects[:3])}" if var.affects else ""
        print(f"   {status}{name}: {var.current_value} ({var.type}){affects}")
    
    print()
    
    # 3. Show Cost Management variables (critical for budget control)
    print("💰 Cost Management Variables (controls API usage & budget):")
    cost_vars = agent_variable_inspector.get_variables_by_layer("CostManagement")
    for name, var in cost_vars.items():
        status = "✏️ " if var.editable else "👁️ "
        print(f"   {status}{name}: {var.current_value} ({var.type})")
        print(f"      📄 {var.description}")
    
    print()
    
    # 4. Show LLM Client variables (affects model behavior)
    print("🧠 LLM Client Variables (controls model behavior):")
    llm_vars = agent_variable_inspector.get_variables_by_layer("LLMClient")
    for name, var in llm_vars.items():
        status = "✏️ " if var.editable else "👁️ "
        print(f"   {status}{name}: {var.current_value} ({var.type})")
        print(f"      📄 {var.description}")
    
    print()
    
    # 5. Create a test agent and register it
    print("🚀 Creating Test Agent to Show Live Control...")
    test_config = AgentConfig(
        name="demo_agent",
        role="demo",
        goals=["demonstrate variable control"],
        tools=["filesystem"],
        temperature=0.7,
        max_concurrent_tasks=3
    )
    
    try:
        # Create Solomon agent for demo
        solomon_config = AgentConfig(
            name="solomon",
            role="chief_of_staff",
            goals=["business intelligence", "decision making"],
            tools=["filesystem", "analytics"],
            temperature=0.8,
            max_concurrent_tasks=5
        )
        solomon = Solomon(solomon_config)
        
        # Register with variable inspector
        agent_variable_inspector.register_agent_instance(solomon)
        
        print(f"   ✅ Registered Solomon agent with variable inspector")
        print(f"   📊 Agent state: {solomon.state.value}")
        print(f"   🔢 API calls made: {solomon.api_call_count}")
        print(f"   💵 Daily cost: ${solomon.daily_cost:.4f}")
        
        # Show Solomon-specific variables
        print()
        print("👑 Solomon-Specific Variables:")
        solomon_vars = agent_variable_inspector.get_variables_by_agent("solomon")
        solomon_specific = {k: v for k, v in solomon_vars.items() if v.layer == "Solomon"}
        
        for name, var in solomon_specific.items():
            status = "✏️ " if var.editable else "👁️ "
            print(f"   {status}{name}: {var.current_value} ({var.type})")
            print(f"      📄 {var.description}")
        
        print()
        
        # 6. Demonstrate variable update
        print("🔧 Demonstrating Variable Update...")
        print("   Original temperature:", solomon.config.temperature)
        
        # Update temperature via variable inspector
        success = agent_variable_inspector.update_variable(
            "config.temperature", 0.9, "solomon"
        )
        
        if success:
            print(f"   ✅ Updated temperature to: {solomon.config.temperature}")
            print("   💡 This change would be reflected immediately in the agent!")
        else:
            print("   ❌ Failed to update temperature")
        
        print()
        
        # 7. Show what's available in the UI
        print("🌐 What You Can Control in the UI (http://localhost:8889):")
        print("   📋 Agent Variables Tab:")
        print("      • View variables by layer (BaseAgent, LLMClient, Cost, etc.)")
        print("      • See live agent instances and their current states")
        print("      • Edit any variable marked as editable (✏️)")
        print("      • See what each variable affects")
        print("      • Real-time updates to live agents")
        print("      • Export/import variable configurations")
        print("      • Change log to track modifications")
        print()
        print("   🎯 Key Variables You Can Control:")
        
        controllable_vars = [
            ("config.temperature", "How creative/random agent responses are"),
            ("config.max_concurrent_tasks", "How many tasks agent can handle at once"),
            ("cost.rate_limiting.max_calls_per_minute", "API call throttling"),
            ("cost.cost_monitoring.daily_budget_usd", "Daily spending limit"),
            ("llm.config.max_tokens", "Maximum response length"),
            ("solomon.decision_framework.maximize", "Solomon's decision priorities"),
            ("memory.max_short_term", "How many recent memories to keep"),
            ("cost.smart_batching.enabled", "Enable efficient message batching")
        ]
        
        for var_name, description in controllable_vars:
            if var_name in agent_variable_inspector.variable_definitions:
                var = agent_variable_inspector.variable_definitions[var_name]
                print(f"      • {var_name}: {description}")
                print(f"        Current: {var.current_value}, Default: {var.default_value}")
        
        print()
        print("💡 All changes in the UI immediately affect the actual running agents!")
        print("💾 All settings are persisted to database and survive restarts!")
        
    except Exception as e:
        print(f"❌ Error creating demo agent: {e}")
    
    print()
    print("🚀 Next Steps:")
    print("   1. Visit http://localhost:8889")
    print("   2. Click 'Agent Variables' tab")
    print("   3. Select different layers to see all controllable variables")
    print("   4. Edit any variable and click save to see immediate effect")
    print("   5. Check 'Live Agents' section to see real-time agent states")

if __name__ == "__main__":
    asyncio.run(demo_variable_control())