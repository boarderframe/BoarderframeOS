#!/usr/bin/env python3
"""
Use the LLM SDK and ADK directly without web interface
"""

import asyncio

from core.agent_development_kit import AgentTemplate, get_adk
from core.llm_provider_sdk import ModelCapability, get_llm_sdk


async def main():
    print("🧠 BoarderframeOS LLM SDK & ADK Demo")
    print("=" * 60)

    # Get SDK instance
    sdk = get_llm_sdk()

    # List all providers
    print("\n📊 Available LLM Providers:")
    for provider in sdk.list_providers():
        status = sdk.get_provider_status(provider)
        print(f"  • {provider}: {status['total_models']} models")

    # Find best model for coding
    print("\n🔍 Finding best model for coding...")
    coding_models = sdk.registry.get_models_by_capability(ModelCapability.CODE_GENERATION)
    best_coding = coding_models[0] if coding_models else None
    if best_coding:
        print(f"  ✅ Recommended: {best_coding.provider}/{best_coding.model_name}")
        print(f"     Quality: {best_coding.quality_score:.0%}")
        print(f"     Cost: ${best_coding.cost_per_1k_input}/1K tokens")

    # Get ADK instance
    adk = get_adk()

    print("\n🤖 Available Agent Templates:")
    for template in AgentTemplate:
        print(f"  • {template.value}")

    print("\n✅ SDK and ADK are working correctly!")
    print("\nYou can now:")
    print("1. Create agents programmatically")
    print("2. Query model information")
    print("3. Build agent swarms")
    print("4. Estimate costs")

    # Example: Create a coding agent
    print("\n📝 Example: Creating a coding agent...")
    coder = await adk.create_agent_from_template(
        name="test_coder",
        template=AgentTemplate.CODER,
        department="Engineering",
        goals=["Write clean code", "Debug issues"]
    )
    print(f"✅ Created agent: {coder.name}")

if __name__ == "__main__":
    asyncio.run(main())
