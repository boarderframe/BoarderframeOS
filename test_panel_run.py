#!/usr/bin/env python3
"""Test script to run Agent Cortex Panel"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.agent_cortex_panel import AgentCortexPanel
    import asyncio
    
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