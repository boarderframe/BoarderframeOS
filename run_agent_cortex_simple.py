#!/usr/bin/env python3
"""
Simple launcher for Agent Cortex Panel
Shows exactly what's happening step by step
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Step 1: Importing modules...")
try:
    from ui.agent_cortex_panel import AgentCortexPanel
    print("✅ Successfully imported AgentCortexPanel")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

print("\n🔍 Step 2: Creating panel instance...")
try:
    panel = AgentCortexPanel(port=8890)
    print("✅ Panel instance created")
except Exception as e:
    print(f"❌ Failed to create panel: {e}")
    sys.exit(1)

print("\n🔍 Step 3: Initializing panel (database, configs)...")
async def init_panel():
    try:
        await panel.initialize()
        print("✅ Panel initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run initialization
if not asyncio.run(init_panel()):
    sys.exit(1)

print("\n🔍 Step 4: Starting web server...")
print("=" * 60)
print("🌐 Server will run at: http://localhost:8890")
print("🛑 Press Ctrl+C to stop")
print("=" * 60)

try:
    # This will block and run the server
    panel.run()
except KeyboardInterrupt:
    print("\n\n✅ Server stopped by user")
except Exception as e:
    print(f"\n❌ Server error: {e}")
    import traceback
    traceback.print_exc()