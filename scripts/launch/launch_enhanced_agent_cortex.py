#!/usr/bin/env python3
"""
Launch Enhanced Agent Cortex Management Panel with SDK Integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.enhanced_agent_cortex_panel import create_enhanced_panel


async def main():
    """Initialize and run enhanced Agent Cortex Panel"""
    print("\n🚀 Launching Enhanced Agent Cortex Management Panel...")
    print("=" * 60)
    print("✨ NEW FEATURES:")
    print("  • LLM Provider SDK - 40+ models from 8+ providers")
    print("  • Agent Development Kit (ADK) - Template-based agent creation")
    print("  • Model Explorer - Filter by capabilities")
    print("  • AI Recommendations - Best model for your task")
    print("  • Swarm Builder - Create agent collaboration patterns")
    print("  • Cost Calculator - Estimate LLM usage costs")
    print("=" * 60)

    # Create enhanced panel instance
    panel = create_enhanced_panel(port=8890)

    # Initialize connections
    print("📊 Initializing SDK and database connections...")
    await panel.initialize()

    print("✅ Enhanced Agent Cortex Panel ready!")
    print("=" * 60)

    # Run the web server
    panel.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Enhanced Agent Cortex Panel stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
