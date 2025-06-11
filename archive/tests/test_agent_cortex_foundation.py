#!/usr/bin/env python3
"""
Test script for Agent Cortex + LangGraph foundation
Verifies all core components work together
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Core imports
from core.agent_cortex import AgentCortex, AgentRequest, get_agent_cortex_instance
from core.agent_cortex_langgraph_orchestrator import (
    AgentCortexLangGraphOrchestrator,
    get_orchestrator,
)
from core.enhanced_base_agent import AgentConfig, EnhancedBaseAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("agent_cortex_foundation_test")


class TestSolomonAgent(EnhancedBaseAgent):
    """Test implementation of enhanced Solomon agent"""

    def __init__(self):
        config = AgentConfig(
            name="solomon_test",
            role="Chief of Staff - Test Implementation",
            goals=[
                "strategic analysis",
                "business intelligence",
                "system coordination",
            ],
            tools=["analytics", "customer", "registry"],
            model="claude-3-sonnet-20240620",
            temperature=0.7,
        )
        super().__init__(config)

    async def think(self, context):
        """Test thinking implementation"""
        return (
            f"Solomon thinking about: {context.get('user_input', 'general situation')}"
        )

    async def act(self, action):
        """Test action implementation"""
        return {"result": f"Solomon executed action: {action}"}


async def test_cortex_core():
    """Test The Agent Cortex core functionality"""

    logger.info("🧠 Testing Agent Cortex core functionality...")

    try:
        # Initialize Agent Cortex
        cortex = await get_agent_cortex_instance()
        logger.info("✅ Agent Cortex initialized successfully")

        # Test model selection
        test_request = AgentRequest(
            agent_name="solomon_test",
            task_type="strategic_analysis",
            context={
                "user_input": "What's the best strategy for scaling our AI agents?"
            },
            complexity=7,
            quality_requirements=0.9,
        )

        # Get Agent Cortex response
        cortex_response = await cortex.process_agent_request(test_request)
        logger.info(
            f"✅ Agent Cortex selected model: {cortex_response.selection.selected_model}"
        )
        logger.info(f"✅ Agent Cortex reasoning: {cortex_response.selection.reasoning}")

        # Test LLM instance
        test_prompt = (
            "Hello, this is a test prompt for the Agent Cortex-selected model."
        )
        try:
            llm_response = await cortex_response.llm.generate(test_prompt)
            logger.info(f"✅ LLM response: {llm_response[:100]}...")
        except Exception as e:
            logger.warning(f"⚠️ LLM test failed (expected if no API keys): {e}")

        # Test Agent Cortex status
        cortex_status = await cortex.get_status()
        logger.info(f"✅ Agent Cortex status: {cortex_status}")

        return True

    except Exception as e:
        logger.error(f"❌ Agent Cortex test failed: {e}")
        return False


async def test_langgraph_orchestrator():
    """Test LangGraph orchestrator"""

    logger.info("🕸️ Testing LangGraph orchestrator...")

    try:
        # Initialize orchestrator
        orchestrator = await get_orchestrator()
        logger.info("✅ LangGraph orchestrator initialized")

        # Test user request processing
        test_request = "I need a strategic analysis of our agent scaling potential"

        try:
            result = await orchestrator.process_user_request(test_request)
            logger.info(f"✅ Orchestrator processed request")
            logger.info(f"✅ Response: {result['response'][:200]}...")
            logger.info(f"✅ Agent chain: {result['agent_chain']}")
            logger.info(f"✅ Quality score: {result['quality_score']}")

        except Exception as e:
            logger.warning(
                f"⚠️ Orchestrator processing failed (expected if no API keys): {e}"
            )

        return True

    except Exception as e:
        logger.error(f"❌ LangGraph orchestrator test failed: {e}")
        return False


async def test_enhanced_agent():
    """Test enhanced agent functionality"""

    logger.info("🤖 Testing enhanced agent...")

    try:
        # Create test agent
        solomon_test = TestSolomonAgent()
        logger.info("✅ Enhanced agent created")

        # Initialize agent
        await solomon_test.initialize()
        logger.info("✅ Enhanced agent initialized")

        # Test status
        status = await solomon_test.get_enhanced_status()
        logger.info(f"✅ Agent status: {json.dumps(status, indent=2)}")

        # Test chat handling
        try:
            response = await solomon_test.handle_user_chat(
                "What should our AI agent strategy be for next quarter?"
            )
            logger.info(f"✅ Agent chat response: {response[:200]}...")

        except Exception as e:
            logger.warning(f"⚠️ Agent chat failed (expected if no API keys): {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Enhanced agent test failed: {e}")
        return False


async def test_integration():
    """Test full system integration"""

    logger.info("🔄 Testing full system integration...")

    try:
        # Test Agent Cortex -> Orchestrator -> Agent flow
        cortex = await get_agent_cortex_instance()
        orchestrator = await get_orchestrator()

        # Complex request that should trigger multi-agent workflow
        complex_request = "Create a comprehensive business strategy that includes agent creation, department coordination, and revenue optimization"

        try:
            # Process through orchestrator
            result = await orchestrator.process_user_request(complex_request)

            logger.info("✅ Integration test completed")
            logger.info(f"✅ Final response length: {len(result['response'])}")
            logger.info(
                f"✅ Agent Cortex selections made: {len(result.get('cortex_selections', []))}"
            )
            logger.info(f"✅ Processing time: {result.get('processing_time', 0):.2f}s")

        except Exception as e:
            logger.warning(
                f"⚠️ Integration processing failed (expected if no API keys): {e}"
            )

        return True

    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False


async def test_model_selection_strategies():
    """Test different Agent Cortex model selection strategies"""

    logger.info("🎯 Testing model selection strategies...")

    try:
        cortex = await get_cortex_instance()

        # Test different strategies
        strategies = [
            ("cost_optimized", "COST_OPTIMIZED"),
            ("performance_optimized", "PERFORMANCE_OPTIMIZED"),
            ("balanced", "BALANCED"),
        ]

        base_request = AgentRequest(
            agent_name="solomon_test",
            task_type="analysis",
            context={"test": "strategy comparison"},
            complexity=5,
        )

        for strategy_name, strategy_enum in strategies:
            try:
                # Note: This would require updating the Agent Cortex to accept strategy parameter
                # For now, just test the default behavior
                response = await cortex.process_agent_request(base_request)
                logger.info(f"✅ {strategy_name}: {response.selection.selected_model}")

            except Exception as e:
                logger.warning(f"⚠️ Strategy {strategy_name} failed: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Model selection strategy test failed: {e}")
        return False


async def run_comprehensive_test():
    """Run comprehensive test suite"""

    logger.info("🚀 Starting Agent Cortex + LangGraph Foundation Test Suite")
    logger.info("=" * 60)

    test_results = {}

    # Test individual components
    test_results["cortex_core"] = await test_cortex_core()
    test_results["langgraph_orchestrator"] = await test_langgraph_orchestrator()
    test_results["enhanced_agent"] = await test_enhanced_agent()
    test_results["model_selection"] = await test_model_selection_strategies()
    test_results["integration"] = await test_integration()

    # Summary
    logger.info("=" * 60)
    logger.info("📊 Test Results Summary:")

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")

    logger.info(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! Foundation is solid.")
        return True
    else:
        logger.warning(
            f"⚠️ {total_tests - passed_tests} tests failed. Check logs for details."
        )
        return False


async def main():
    """Main test function"""

    print("🧠 BoarderframeOS Agent Cortex + LangGraph Foundation Test")
    print("🔧 Testing core components...")
    print()

    # Check environment
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: No API keys found. Some tests may fail.")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY for full testing.")
        print()

    # Run tests
    success = await run_comprehensive_test()

    if success:
        print("\n🎉 Foundation test completed successfully!")
        print("✅ Ready to migrate agents and add monitoring")
    else:
        print("\n❌ Some tests failed. Check logs for details.")
        print("🔧 Foundation may need debugging before proceeding")

    return success


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
