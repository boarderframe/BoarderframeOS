#!/usr/bin/env python3
"""
Launch Agent Cortex Management Panel
Quick launcher for the comprehensive LLM configuration interface
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.agent_cortex_panel import AgentCortexPanel


async def main():
    """Initialize and run Agent Cortex Panel"""
    print("\n🚀 Launching Agent Cortex Management Panel...")
    print("=" * 60)

    # Create panel instance
    panel = AgentCortexPanel(port=8890)

    # Initialize connections
    print("📊 Initializing database and configurations...")
    await panel.initialize()

    print("✅ Agent Cortex Panel initialized successfully!")
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
        sys.exit(1)
