#!/usr/bin/env python3
"""Test script to run Agent Cortex Panel"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import asyncio

    from ui.agent_cortex_panel import AgentCortexPanel

    async def run():
        panel = AgentCortexPanel(port=8890)
        await panel.initialize()
        print("\n✅ Panel initialized successfully!")
        print(f"🌐 Starting server on http://localhost:8890")
        panel.run()

    if __name__ == "__main__":
        asyncio.run(run())

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
