#!/usr/bin/env python3
"""
Launch Agent Cortex Management UI
Quick launcher for the Agent Cortex Management interface
"""

import asyncio
import os
import subprocess
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.agent_cortex_management import AgentCortexManagementUI


async def main():
    """Launch Agent Cortex Management UI"""

    print("🧠 Agent Cortex Management Center - Enhanced Edition")
    print("=" * 60)
    print("🎛️ Features:")
    print("   • Full Database Persistence (SQLite)")
    print("   • Comprehensive Testing Suite")
    print("   • Real-time Model Configuration")
    print("   • Agent Settings Management")
    print("   • Performance Analytics")
    print("   • Configuration Backup/Restore")
    print("=" * 60)

    # Create UI instance
    ui = AgentCortexManagementUI(port=8889)

    print("📡 Initializing Agent Cortex connection...")
    await ui.initialize()

    print("✅ Agent Cortex connected successfully!")
    print("💾 Database persistence enabled")
    print(f"🗄️ Config DB: {ui.db_path}")
    print("🚀 Launching Management Center...")
    print("=" * 60)
    print(f"🌐 Access at: http://localhost:8889")
    print("📋 Tabs Available:")
    print("   • Overview - System status & strategy selection")
    print("   • Model Configuration - Per-tier model settings")
    print("   • Agent Settings - Per-agent configurations")
    print("   • Testing Suite - Comprehensive test scenarios")
    print("   • Configuration Management - Backup & persistence")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)

    # Open browser (optional)
    try:
        subprocess.run(["open", "http://localhost:8889"], check=False)
    except:
        pass  # Ignore if open command fails

    # Run the UI
    ui.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Agent Cortex Management UI stopped")
        sys.exit(0)
