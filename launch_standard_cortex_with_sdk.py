#!/usr/bin/env python3
"""
Launch Standard Agent Cortex Panel with SDK features added
A simpler approach that adds SDK endpoints to the existing panel
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.agent_cortex_panel import AgentCortexPanel
from flask import jsonify


async def add_sdk_features(panel):
    """Add SDK features to standard panel"""
    
    # Import SDK components
    from core.llm_provider_sdk import get_llm_sdk, ModelCapability
    from core.agent_development_kit import get_adk, AgentTemplate
    
    sdk = get_llm_sdk()
    adk = get_adk()
    
    # Add SDK routes
    @panel.app.route('/api/cortex/sdk/providers')
    def get_sdk_providers():
        """Get all SDK providers with detailed info"""
        providers = {}
        
        for provider_name in sdk.list_providers():
            provider_info = sdk.get_provider_status(provider_name)
            models = sdk.list_models(provider_name)
            
            providers[provider_name] = {
                **provider_info,
                "models": [
                    {
                        "name": model.model_name,
                        "capabilities": [cap.value for cap in model.capabilities],
                        "context_window": model.context_window,
                        "cost_per_1k_input": model.cost_per_1k_input,
                        "cost_per_1k_output": model.cost_per_1k_output,
                        "quality_score": model.quality_score,
                        "specialties": model.specialties
                    }
                    for model in models
                ]
            }
        
        return jsonify(providers)
    
    @panel.app.route('/api/cortex/sdk/models/<capability>')
    def get_models_by_capability(capability):
        """Get models with specific capability"""
        try:
            cap_enum = ModelCapability(capability)
            models = sdk.registry.get_models_by_capability(cap_enum)
            
            return jsonify([
                {
                    "provider": model.provider,
                    "model": model.model_name,
                    "quality_score": model.quality_score,
                    "cost_per_1k": model.cost_per_1k_input,
                    "latency_ms": model.latency_ms,
                    "context_window": model.context_window
                }
                for model in models
            ])
        except ValueError:
            return jsonify({"error": f"Unknown capability: {capability}"}), 400
    
    @panel.app.route('/api/cortex/capabilities')
    def get_all_capabilities():
        """Get all available model capabilities"""
        capabilities = [
            {
                "name": cap.value,
                "description": _get_capability_description(cap)
            }
            for cap in ModelCapability
        ]
        
        return jsonify(capabilities)
    
    @panel.app.route('/api/cortex/adk/templates')
    def get_agent_templates():
        """Get available agent templates"""
        templates = []
        
        for template in AgentTemplate:
            template_config = adk.factory.templates.get(template, {})
            templates.append({
                "name": template.value,
                "description": f"Pre-built {template.value} agent template"
            })
        
        return jsonify(templates)
    
    print("✅ SDK features added to Agent Cortex Panel")


def _get_capability_description(capability):
    """Get human-readable capability description"""
    
    descriptions = {
        ModelCapability.CHAT: "General conversation and Q&A",
        ModelCapability.CODE_GENERATION: "Writing and debugging code",
        ModelCapability.EMBEDDINGS: "Text similarity and search",
        ModelCapability.VISION: "Image understanding and analysis",
        ModelCapability.FUNCTION_CALLING: "Tool use and API integration",
        ModelCapability.STREAMING: "Real-time response streaming",
        ModelCapability.LONG_CONTEXT: "Handle 100k+ token contexts",
        ModelCapability.REASONING: "Complex logical reasoning",
        ModelCapability.CREATIVE_WRITING: "Creative content generation"
    }
    
    return descriptions.get(capability, capability.value)


async def main():
    """Initialize and run standard panel with SDK features"""
    print("\n🚀 Launching Agent Cortex Panel with SDK Features...")
    print("=" * 60)
    print("📌 This version adds SDK endpoints to the standard panel")
    print("=" * 60)
    
    # Create standard panel instance
    panel = AgentCortexPanel(port=8890)
    
    # Initialize connections
    print("📊 Initializing database and configurations...")
    await panel.initialize()
    
    # Add SDK features
    await add_sdk_features(panel)
    
    print("\n✅ Agent Cortex Panel ready with SDK features!")
    print("=" * 60)
    print("🆕 New API endpoints:")
    print("  • /api/cortex/sdk/providers - List all SDK providers")
    print("  • /api/cortex/sdk/models/<capability> - Get models by capability")
    print("  • /api/cortex/capabilities - List all capabilities")
    print("  • /api/cortex/adk/templates - List agent templates")
    print("=" * 60)
    
    # Run the web server
    panel.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Agent Cortex Panel stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)