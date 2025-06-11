#!/usr/bin/env python3
"""
Launch Agent Cortex UI - WORKING VERSION
This version properly initializes and runs the panel
"""

import asyncio
import os
import sys
import threading
import time
import webbrowser

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the panel
from ui.agent_cortex_panel import AgentCortexPanel


def run_in_thread(panel):
    """Run Flask server in a separate thread to avoid blocking"""
    # Use werkzeug directly to avoid issues
    from werkzeug.serving import make_server

    # Create a server that we can control
    server = make_server("localhost", 8890, panel.app, threaded=True)
    print("✅ Server created successfully")

    # Start serving
    server.serve_forever()


async def main():
    print("\n🚀 Launching Agent Cortex Management Panel...")
    print("=" * 60)

    # Create panel instance
    panel = AgentCortexPanel(port=8890)

    # Initialize panel (load data, setup database)
    print("📊 Initializing database and configurations...")
    await panel.initialize()
    print("✅ Panel initialized successfully!")

    # Start server in a thread
    print("\n🌐 Starting web server...")
    server_thread = threading.Thread(target=run_in_thread, args=(panel,), daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    print("\n" + "=" * 60)
    print("✅ Agent Cortex Panel is now running!")
    print("=" * 60)
    print("\n📌 Access the panel at:")
    print("   • http://localhost:8890")
    print("   • http://127.0.0.1:8890")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 60)

    # Test the server
    print("\n🧪 Testing server connection...")
    import requests

    try:
        response = requests.get("http://localhost:8890/api/cortex/overview", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is working correctly!")
            print(f"   • Total agents: {data.get('total_agents', 0)}")
            print(f"   • Active providers: {data.get('active_providers', 0)}")
            print(f"   • Departments: {data.get('departments', 0)}")

            # Try to open browser
            print("\n🌐 Opening browser...")
            webbrowser.open("http://localhost:8890")

        else:
            print(f"⚠️  Server returned status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        print("   The server might be blocked by firewall or security settings")
    except Exception as e:
        print(f"⚠️  Test error: {e}")

    print("\n💡 If the browser doesn't open automatically:")
    print("   1. Open your web browser manually")
    print("   2. Navigate to http://localhost:8890")
    print("   3. You should see the Agent Cortex Management Panel")

    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped by user")
        print("👋 Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
