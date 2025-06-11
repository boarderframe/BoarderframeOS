#!/usr/bin/env python3
"""
Agent Cortex UI - Final Working Version
Simple launcher that just works
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable Flask warnings
os.environ["WERKZEUG_RUN_MAIN"] = "true"

import asyncio
import threading

from werkzeug.serving import make_server

from ui.agent_cortex_panel import AgentCortexPanel


def run_server(app):
    """Run server in thread"""
    server = make_server("localhost", 8890, app, threaded=True)
    server.serve_forever()


async def main():
    # Create and initialize panel
    panel = AgentCortexPanel(port=8890)
    await panel.initialize()

    # Start server
    thread = threading.Thread(target=run_server, args=(panel.app,), daemon=True)
    thread.start()

    print("\n" + "=" * 60)
    print("🧠 Agent Cortex Management Panel")
    print("=" * 60)
    print("\n✅ Server is running at: http://localhost:8890")
    print("\nFeatures available:")
    print("  • LLM Provider Management")
    print("  • Individual Agent Configuration")
    print("  • Tier-based Defaults")
    print("  • SDK Integration (40+ models)")
    print("\n🛑 Press Ctrl+C to stop")
    print("=" * 60)

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ Stopped")


if __name__ == "__main__":
    asyncio.run(main())
