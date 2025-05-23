#!/usr/bin/env python3
"""
BoarderframeOS Startup Manager
Launch the full AI operating system
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
import signal
import os

class BoarderframeOS:
    def __init__(self):
        self.processes = []
        self.running = True
        
    async def start_mcp_servers(self):
        """Start all MCP servers"""
        print("🔌 Starting MCP servers...")
        
        # Filesystem server
        fs_process = subprocess.Popen([
            sys.executable, "mcp-servers/filesystem_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(("filesystem", fs_process))
        
        # Wait for servers to start
        await asyncio.sleep(2)
        print("   ✓ Filesystem server on port 8001")
        
    async def start_agents(self):
        """Start all configured agents"""
        print("🤖 Starting AI agents...")
        
        # Start Jarvis
        jarvis_process = subprocess.Popen([
            sys.executable, "agents/jarvis_template.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(("jarvis", jarvis_process))
        
        await asyncio.sleep(1)
        print("   ✓ Jarvis (Chief of Staff)")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down BoarderframeOS...")
        self.running = False
        
        for name, process in self.processes:
            print(f"   Stopping {name}...")
            process.terminate()
            
        print("👋 BoarderframeOS stopped")
        sys.exit(0)
        
    async def monitor_system(self):
        """Monitor system health"""
        while self.running:
            # Check if all processes are still running
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"⚠️  {name} process died, restarting...")
                    # TODO: Implement restart logic
                    
            await asyncio.sleep(5)
    
    async def run(self):
        """Main startup sequence"""
        print("\n🚀 BoarderframeOS Starting...")
        print("=" * 40)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start MCP servers
            await self.start_mcp_servers()
            
            # Start agents
            await self.start_agents()
            
            print("\n✅ BoarderframeOS is operational!")
            print("\n📊 System Overview:")
            print("   • MCP Servers: filesystem (8001)")
            print("   • Active Agents: jarvis")
            print("   • Compute Zones: executive")
            print("\n📝 Monitoring:")
            print("   • Status reports: data/status_*.json")
            print("   • Agent logs: logs/agents/")
            print("   • CLI commands: ./boarderctl status")
            print("\nPress Ctrl+C to stop")
            
            # Monitor system
            await self.monitor_system()
            
        except Exception as e:
            print(f"❌ Startup error: {e}")
            self.signal_handler(None, None)

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    bos = BoarderframeOS()
    asyncio.run(bos.run())