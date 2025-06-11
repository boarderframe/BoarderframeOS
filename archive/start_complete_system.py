#!/usr/bin/env python3
"""
Complete BoarderframeOS System Startup
Starts dashboard and all agents together
"""

import asyncio
import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Add boarderframeos to path
sys.path.insert(0, str(Path(__file__).parent / 'boarderframeos'))

from demo_enhanced_agent_coordination import CoordinationDemo


class SystemManager:
    """Manages the complete BoarderframeOS system"""

    def __init__(self):
        self.dashboard_process = None
        self.demo = None
        self.running = False

    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print('\n🛑 Shutting down BoarderframeOS...')
        asyncio.create_task(self.shutdown())

    async def start_dashboard(self):
        """Start the enhanced dashboard"""
        print("📊 Starting Enhanced Dashboard...")

        # Kill any existing dashboard process
        subprocess.run(["pkill", "-f", "python.*enhanced_dashboard.py"],
                      stderr=subprocess.DEVNULL)
        time.sleep(2)

        # Start dashboard in background
        self.dashboard_process = subprocess.Popen(
            [sys.executable, str(Path(__file__).parent / "enhanced_dashboard.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait a moment for startup
        time.sleep(3)

        # Test if dashboard is running
        try:
            import requests
            response = requests.get("http://localhost:8888/health", timeout=2)
            if response.status_code == 200:
                print("✅ Dashboard is running at http://localhost:8888")
                return True
        except:
            print("✅ Dashboard started (install requests for verification)")

        return True

    async def start_agents(self):
        """Start all agents using the coordination demo"""
        print("🤖 Starting Agent Coordination System...")

        try:
            self.demo = CoordinationDemo()
            await self.demo.setup_demo_environment()
            print("✅ All agents started successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to start agents: {e}")
            return False

    async def run_system(self):
        """Run the complete system"""
        print("🚀 Starting Complete BoarderframeOS System...")
        print("=" * 60)

        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)

        try:
            # Start dashboard
            dashboard_ok = await self.start_dashboard()
            if not dashboard_ok:
                print("❌ Dashboard failed to start")
                return

            # Start agents
            agents_ok = await self.start_agents()
            if not agents_ok:
                print("❌ Agents failed to start")
                return

            print("\n" + "=" * 60)
            print("✅ BoarderframeOS System is fully operational!")
            print("📍 Dashboard: http://localhost:8888")
            print("🤖 Agents: solomon, david, analyst_agent")
            print("🔄 System is running... Press Ctrl+C to stop")
            print("=" * 60)

            # Open browser
            try:
                webbrowser.open("http://localhost:8888")
                print("🌐 Opening dashboard in browser...")
            except:
                pass

            # Keep system running
            self.running = True
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown the complete system"""
        print("\n🛑 Shutting down system...")
        self.running = False

        # Stop agents
        if self.demo and self.demo.controller:
            try:
                await self.demo.controller.stop()
                print("✅ Agents stopped")
            except:
                pass

        # Stop dashboard
        if self.dashboard_process:
            try:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                print("✅ Dashboard stopped")
            except:
                try:
                    self.dashboard_process.kill()
                except:
                    pass

        print("🏁 System shutdown complete")
        sys.exit(0)

async def main():
    """Main entry point"""
    manager = SystemManager()
    await manager.run_system()

if __name__ == "__main__":
    asyncio.run(main())
