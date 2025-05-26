#!/usr/bin/env python3
"""
Complete BoarderframeOS System Startup with MCP Servers
Real-time status dashboard and comprehensive system launch
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import threading
import psutil

# Add boarderframeos to path
sys.path.insert(0, str(Path(__file__).parent / 'boarderframeos'))

class SystemStartupManager:
    """Manages the complete BoarderframeOS system startup with real-time monitoring"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.status_data = {
            "startup_phase": "initializing",
            "services": {},
            "agents": {},
            "mcp_servers": {},
            "start_time": datetime.now().isoformat(),
            "logs": []
        }
        self.running = False
        self.status_file = "/tmp/boarderframe_startup_status.json"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("system_startup")
        
    def log_status(self, message: str, component: str = "system", status: str = "info"):
        """Log a status message and update status data"""
        self.logger.info(f"[{component}] {message}")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "message": message,
            "status": status
        }
        
        self.status_data["logs"].append(log_entry)
        
        # Keep only last 50 log entries
        if len(self.status_data["logs"]) > 50:
            self.status_data["logs"] = self.status_data["logs"][-50:]
            
        self.save_status()
        
    def save_status(self):
        """Save current status to file for dashboard"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save status: {e}")
    
    def update_component_status(self, component_type: str, name: str, status: str, details: Dict = None):
        """Update status of a specific component"""
        if component_type not in self.status_data:
            self.status_data[component_type] = {}
            
        self.status_data[component_type][name] = {
            "status": status,
            "last_update": datetime.now().isoformat(),
            "details": details or {}
        }
        self.save_status()
    
    async def start_mcp_servers(self):
        """Start all MCP servers"""
        self.log_status("Starting MCP server infrastructure...", "mcp", "starting")
        self.status_data["startup_phase"] = "starting_mcp_servers"
        
        mcp_servers = [
            {"name": "registry", "port": 8000, "script": "registry_server.py"},
            {"name": "filesystem", "port": 8001, "script": "filesystem_server.py"},
            {"name": "database", "port": 8004, "script": "database_server.py"},
            {"name": "llm", "port": 8005, "script": "llm_server.py"},
        ]
        
        for server in mcp_servers:
            try:
                self.log_status(f"Starting {server['name']} server on port {server['port']}...", "mcp", "starting")
                
                # Update status to starting
                self.update_component_status("mcp_servers", server['name'], "starting", {
                    "port": server['port'],
                    "script": server['script']
                })
                
                # Start the server
                script_path = Path(__file__).parent / "boarderframeos" / "mcp" / server['script']
                if script_path.exists():
                    process = subprocess.Popen(
                        [sys.executable, str(script_path)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=str(Path(__file__).parent)
                    )
                    
                    self.processes[f"mcp_{server['name']}"] = process
                    
                    # Wait a moment for startup
                    await asyncio.sleep(2)
                    
                    # Check if process is still running
                    if process.poll() is None:
                        self.log_status(f"✅ {server['name']} server started successfully", "mcp", "success")
                        self.update_component_status("mcp_servers", server['name'], "running", {
                            "port": server['port'],
                            "pid": process.pid
                        })
                    else:
                        self.log_status(f"❌ {server['name']} server failed to start", "mcp", "error")
                        self.update_component_status("mcp_servers", server['name'], "failed", {
                            "port": server['port']
                        })
                else:
                    self.log_status(f"⚠️ {server['name']} server script not found", "mcp", "warning")
                    self.update_component_status("mcp_servers", server['name'], "not_found", {
                        "expected_path": str(script_path)
                    })
                    
            except Exception as e:
                self.log_status(f"❌ Failed to start {server['name']} server: {e}", "mcp", "error")
                self.update_component_status("mcp_servers", server['name'], "error", {
                    "error": str(e)
                })
    
    async def start_dashboard(self):
        """Start the enhanced dashboard"""
        self.log_status("Starting enhanced dashboard...", "dashboard", "starting")
        self.status_data["startup_phase"] = "starting_dashboard"
        
        try:
            # Kill any existing dashboard
            subprocess.run(["pkill", "-f", "python.*enhanced_dashboard.py"], stderr=subprocess.DEVNULL)
            await asyncio.sleep(2)
            
            # Start new dashboard
            dashboard_process = subprocess.Popen(
                [sys.executable, "enhanced_dashboard.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent)
            )
            
            self.processes["dashboard"] = dashboard_process
            
            # Wait for startup
            await asyncio.sleep(3)
            
            # Verify dashboard is running
            if dashboard_process.poll() is None:
                self.log_status("✅ Dashboard started successfully on port 8888", "dashboard", "success")
                self.update_component_status("services", "dashboard", "running", {
                    "port": 8888,
                    "pid": dashboard_process.pid,
                    "url": "http://localhost:8888"
                })
            else:
                self.log_status("❌ Dashboard failed to start", "dashboard", "error")
                self.update_component_status("services", "dashboard", "failed", {})
                
        except Exception as e:
            self.log_status(f"❌ Dashboard startup error: {e}", "dashboard", "error")
            self.update_component_status("services", "dashboard", "error", {"error": str(e)})
    
    async def start_agents(self):
        """Start agent coordination system"""
        self.log_status("Starting agent coordination system...", "agents", "starting")
        self.status_data["startup_phase"] = "starting_agents"
        
        try:
            # Import and start coordination demo
            from demo_enhanced_agent_coordination import CoordinationDemo
            
            self.demo = CoordinationDemo()
            await self.demo.setup_demo_environment()
            
            # Check which agents are actually running
            agents = ["solomon", "david", "analyst_agent"]
            for agent_name in agents:
                # Check if agent process exists
                agent_running = False
                try:
                    for process in psutil.process_iter(['pid', 'cmdline']):
                        cmdline = ' '.join(process.info['cmdline'] or [])
                        if f"{agent_name}.py" in cmdline:
                            agent_running = True
                            self.update_component_status("agents", agent_name, "running", {
                                "pid": process.info['pid']
                            })
                            break
                except:
                    pass
                
                if not agent_running:
                    self.update_component_status("agents", agent_name, "not_running", {})
            
            self.log_status("✅ Agent coordination system started", "agents", "success")
            
        except Exception as e:
            self.log_status(f"❌ Agent startup error: {e}", "agents", "error")
            self.update_component_status("agents", "system", "error", {"error": str(e)})
    
    async def start_system(self):
        """Start the complete system"""
        self.running = True
        self.log_status("🚀 Starting Complete BoarderframeOS System...", "system", "starting")
        
        try:
            # Phase 1: Start MCP servers
            await self.start_mcp_servers()
            await asyncio.sleep(2)
            
            # Phase 2: Start dashboard
            await self.start_dashboard()
            await asyncio.sleep(2)
            
            # Phase 3: Start agents
            await self.start_agents()
            
            # System fully operational
            self.status_data["startup_phase"] = "operational"
            self.log_status("✅ System fully operational!", "system", "success")
            
            # Open browser to dashboard
            try:
                import webbrowser
                webbrowser.open("http://localhost:8888")
                self.log_status("🌐 Dashboard opened in browser", "system", "info")
            except:
                pass
            
            return True
            
        except Exception as e:
            self.log_status(f"❌ System startup failed: {e}", "system", "error")
            self.status_data["startup_phase"] = "failed"
            return False
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        self.log_status("🛑 Shutting down system...", "system", "stopping")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Shutdown the complete system"""
        self.running = False
        self.status_data["startup_phase"] = "shutting_down"
        
        # Stop agents
        if hasattr(self, 'demo') and self.demo and self.demo.controller:
            try:
                await self.demo.controller.stop()
                self.log_status("✅ Agents stopped", "agents", "stopped")
            except:
                pass
        
        # Stop all processes
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
                    self.log_status(f"✅ {name} stopped", "system", "stopped")
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.log_status("🏁 System shutdown complete", "system", "stopped")
        sys.exit(0)

async def main():
    """Main entry point"""
    manager = SystemStartupManager()
    
    # Set up signal handler
    signal.signal(signal.SIGINT, manager.signal_handler)
    
    # Start system
    success = await manager.start_system()
    
    if success:
        # Keep running
        try:
            while manager.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await manager.shutdown()
    else:
        print("❌ System startup failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
