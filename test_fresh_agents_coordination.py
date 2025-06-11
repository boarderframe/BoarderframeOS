"""
Test Fresh Solomon and David Agent Coordination
Test the new Brain + LangGraph agents working together
"""

import asyncio
import json
from datetime import datetime

from agents.david.david_fresh import create_fresh_david

# Import the fresh agents
from agents.solomon.solomon_fresh import create_fresh_solomon
from core.brain_langgraph_orchestrator import get_orchestrator


async def test_agent_coordination():
    """Test Solomon and David coordination through multiple scenarios"""

    print("🚀 Testing Fresh Agent Coordination")
    print("=" * 60)

    # Initialize agents
    print("🧠 Initializing Fresh Solomon...")
    solomon = await create_fresh_solomon()
    print("✅ Solomon ready")

    print("👨‍💼 Initializing Fresh David...")
    david = await create_fresh_david()
    print("✅ David ready")

    print("🕸️ Initializing Brain LangGraph Orchestrator...")
    orchestrator = await get_orchestrator()
    print("✅ Orchestrator ready")

    print("\n" + "=" * 60)

    # Test Scenario 1: Strategic Analysis to Executive Decision
    print("📊 Scenario 1: Strategic Analysis to Executive Decision")
    print("-" * 40)

    strategic_request = """
    I need a comprehensive strategic analysis and executive decision on scaling our agent architecture.
    Current situation: We have 5 agents and want to scale to 120+ agents to achieve $15K monthly revenue.

    Budget considerations: $250K investment available
    Timeline: 6 months to full deployment
    Risk tolerance: Medium-high for strategic growth

    Please provide Solomon's strategic analysis followed by David's executive decision.
    """

    print(f"Request: {strategic_request[:100]}...")

    # Process through orchestrator
    result1 = await orchestrator.process_user_request(strategic_request)

    print(f"\n🎯 Orchestrator Result:")
    print(f"Agent Chain: {' → '.join(result1['agent_chain'])}")
    print(f"Quality Score: {result1['quality_score']:.2f}")
    print(f"Processing Time: {result1['processing_time']:.2f}s")
    print(f"Brain Models Used: {len(result1['brain_selections'])}")

    print(f"\n📋 Response Summary:")
    response_lines = result1['response'].split('\n')
    for i, line in enumerate(response_lines[:10]):  # First 10 lines
        print(f"  {line}")
    if len(response_lines) > 10:
        print(f"  ... (+{len(response_lines)-10} more lines)")

    print("\n" + "=" * 60)

    # Test Scenario 2: Direct Solomon Strategic Intelligence
    print("🧠 Scenario 2: Solomon Strategic Intelligence")
    print("-" * 40)

    solomon_request = "Analyze our competitive position and recommend strategic initiatives for Q1"

    print(f"Request: {solomon_request}")

    solomon_response = await solomon.handle_user_chat(solomon_request)

    print(f"\n📊 Solomon's Response:")
    response_lines = solomon_response.split('\n')
    for i, line in enumerate(response_lines[:8]):  # First 8 lines
        print(f"  {line}")
    if len(response_lines) > 8:
        print(f"  ... (+{len(response_lines)-8} more lines)")

    print("\n" + "=" * 60)

    # Test Scenario 3: Direct David Executive Decision
    print("👨‍💼 Scenario 3: David Executive Decision")
    print("-" * 40)

    david_request = "I need your executive approval for hiring 3 new engineers at $120K each to accelerate development"

    print(f"Request: {david_request}")

    david_response = await david.handle_user_chat(david_request)

    print(f"\n💼 David's Response:")
    response_lines = david_response.split('\n')
    for i, line in enumerate(response_lines[:8]):  # First 8 lines
        print(f"  {line}")
    if len(response_lines) > 8:
        print(f"  ... (+{len(response_lines)-8} more lines)")

    print("\n" + "=" * 60)

    # Test Scenario 4: Complex Multi-Agent Coordination
    print("🔄 Scenario 4: Complex Multi-Agent Coordination")
    print("-" * 40)

    complex_request = """
    We have a potential partnership opportunity with a major enterprise client who wants to integrate
    our agent technology into their platform. This could generate $50K monthly revenue but requires
    significant technical integration work and creates new support obligations.

    I need:
    1. Solomon's strategic analysis of the opportunity
    2. David's executive decision on proceeding
    3. Resource allocation recommendations
    4. Implementation timeline
    """

    print(f"Request: {complex_request[:100]}...")

    result2 = await orchestrator.process_user_request(complex_request)

    print(f"\n🎯 Complex Coordination Result:")
    print(f"Agent Chain: {' → '.join(result2['agent_chain'])}")
    print(f"Quality Score: {result2['quality_score']:.2f}")
    print(f"Processing Time: {result2['processing_time']:.2f}s")
    print(f"Completion Status: {result2['completion_status']}")

    print(f"\n📋 Complex Response Summary:")
    response_lines = result2['response'].split('\n')
    for i, line in enumerate(response_lines[:12]):  # First 12 lines
        print(f"  {line}")
    if len(response_lines) > 12:
        print(f"  ... (+{len(response_lines)-12} more lines)")

    print("\n" + "=" * 60)

    # Agent Status Summary
    print("📈 Agent Status Summary")
    print("-" * 40)

    solomon_status = await solomon.get_enhanced_status()
    david_status = await david.get_enhanced_status()

    print(f"Solomon:")
    print(f"  State: {solomon_status['state']}")
    print(f"  Brain Requests: {solomon_status['metrics']['brain_requests']}")
    print(f"  Workflows: {solomon_status['metrics']['workflows_completed']}")
    print(f"  Quality Score: {solomon_status['metrics']['quality_score']:.2f}")

    print(f"\nDavid:")
    print(f"  State: {david_status['state']}")
    print(f"  Brain Requests: {david_status['metrics']['brain_requests']}")
    print(f"  Workflows: {david_status['metrics']['workflows_completed']}")
    print(f"  Quality Score: {david_status['metrics']['quality_score']:.2f}")

    print("\n" + "=" * 60)
    print("✅ Fresh Agent Coordination Testing Complete!")

    return {
        "solomon_status": solomon_status,
        "david_status": david_status,
        "coordination_results": [result1, result2],
        "test_timestamp": datetime.now().isoformat()
    }


async def main():
    """Run the coordination tests"""

    try:
        results = await test_agent_coordination()
        print(f"\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
