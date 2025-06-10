#!/usr/bin/env python3
"""
Fixed launcher for Agent Cortex Panel
Runs without debug mode issues
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable Flask reloader
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

async def main():
    print("🚀 Starting Agent Cortex Panel (Fixed Version)...")
    
    from ui.agent_cortex_panel import AgentCortexPanel
    
    # Create panel
    panel = AgentCortexPanel(port=8890)
    
    # Initialize
    await panel.initialize()
    
    # Override the run method to use simpler settings
    print("\n✅ Starting server on http://localhost:8890")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Run without debug mode
    panel.app.run(host='127.0.0.1', port=8890, debug=False, use_reloader=False)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Server stopped")