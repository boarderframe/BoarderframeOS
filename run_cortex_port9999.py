#!/usr/bin/env python3
"""
Run Agent Cortex Panel on port 9999
Working around port 8890 issues
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable Flask debug reloader
os.environ['FLASK_ENV'] = 'production'
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

from ui.agent_cortex_panel import AgentCortexPanel


async def main():
    print("\n🚀 Starting Agent Cortex Panel on alternate port...")
    print("=" * 60)

    # Create panel on port 9999
    panel = AgentCortexPanel(port=9999)

    # Initialize
    print("📊 Initializing database and configurations...")
    await panel.initialize()

    print("✅ Panel initialized successfully!")
    print("=" * 60)
    print("\n🌐 Starting server on http://localhost:9999")
    print("🛑 Press Ctrl+C to stop\n")

    # Override the run method to ensure it uses our port
    from flask import Flask
    panel.app.run(host='127.0.0.1', port=9999, debug=False, use_reloader=False)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
