#!/usr/bin/env python3
"""
MCP Filesystem Server Health Monitor
Provides continuous monitoring and diagnostics for the filesystem server
"""

import asyncio
import httpx
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any

class FilesystemServerMonitor:
    """Monitor and report on filesystem server health and performance"""
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.monitoring = False
        
    async def get_server_status(self) -> Dict[str, Any]:
        """Get comprehensive server status"""
        try:
            async with httpx.AsyncClient() as client:
                # Health check
                health_response = await client.get(f"{self.base_url}/health", timeout=5.0)
                health_data = health_response.json()
                
                # Statistics
                try:
                    stats_response = await client.get(f"{self.base_url}/stats", timeout=5.0)
                    stats_data = stats_response.json()
                except:
                    stats_data = {}
                
                return {
                    "timestamp": datetime.now().isoformat(),
                    "status": "online",
                    "health": health_data,
                    "stats": stats_data
                }
        except httpx.ConnectError:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "offline",
                "error": "Connection refused"
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def format_status_display(self, status: Dict[str, Any]) -> str:
        """Format status for console display"""
        timestamp = status["timestamp"]
        server_status = status["status"]
        
        if server_status == "offline":
            return f"[{timestamp}] ❌ Server OFFLINE - {status.get('error', 'Unknown error')}"
        
        if server_status == "error":
            return f"[{timestamp}] ⚠️  Server ERROR - {status.get('error', 'Unknown error')}"
        
        # Online status - show detailed info
        health = status.get("health", {})
        uptime = health.get("uptime", 0)
        ai_available = health.get("ai_available", False)
        active_ops = health.get("active_operations", 0)
        clients = health.get("connected_clients", 0)
        base_path = health.get("base_path", "unknown")
        
        ai_indicator = "🤖" if ai_available else "📁"
        
        return f"""[{timestamp}] ✅ Server ONLINE {ai_indicator}
  ⏱️  Uptime: {uptime:.1f}s
  📁 Base Path: {base_path}
  🔄 Active Operations: {active_ops}
  👥 Connected Clients: {clients}
  🤖 AI Features: {'enabled' if ai_available else 'disabled'}"""
    
    async def run_continuous_monitor(self, interval: int = 30):
        """Run continuous monitoring with specified interval"""
        print(f"🔍 Starting continuous monitoring of filesystem server on port {self.port}")
        print(f"📊 Update interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        self.monitoring = True
        try:
            while self.monitoring:
                status = await self.get_server_status()
                print(self.format_status_display(status))
                print("-" * 60)
                
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            self.monitoring = False
    
    async def run_single_check(self, verbose: bool = False):
        """Perform single health check"""
        status = await self.get_server_status()
        
        if verbose or status["status"] != "online":
            print(self.format_status_display(status))
        else:
            # Brief status for successful checks
            health = status.get("health", {})
            uptime = health.get("uptime", 0)
            ai_available = health.get("ai_available", False)
            ai_indicator = "🤖" if ai_available else "📁"
            print(f"✅ Server ONLINE {ai_indicator} (uptime: {uptime:.1f}s)")
        
        return status["status"] == "online"

async def main():
    parser = argparse.ArgumentParser(description="Monitor MCP Filesystem Server health")
    parser.add_argument("--port", "-p", type=int, default=8001, help="Server port (default: 8001)")
    parser.add_argument("--continuous", "-c", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", "-i", type=int, default=30, help="Update interval for continuous mode (default: 30s)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    monitor = FilesystemServerMonitor(port=args.port)
    
    if args.continuous:
        await monitor.run_continuous_monitor(interval=args.interval)
    else:
        success = await monitor.run_single_check(verbose=args.verbose)
        exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
