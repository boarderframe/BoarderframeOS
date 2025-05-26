#!/usr/bin/env python3
"""
Enhanced BoarderframeOS System Startup
Clean, organized startup with comprehensive error handling
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

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

class EnhancedSystemStartup:
    """Enhanced system startup with clean terminal output and robust error handling"""
    
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
        
        # Configure clean logging
        logging.basicConfig(
            level=logging.WARNING,  # Reduce noise
            format='%(message)s'
        )
        self.logger = logging.getLogger("startup")
        
    def print_section(self, title: str, emoji: str = "🔧"):
        """Print a clean section header"""
        print(f"\n{emoji} {title}")
        print("" + "━" * (len(title) + 4))

    def print_step(self, message: str, status: str = "info", agent=False):
        """Print a step with appropriate emoji, with special handling for MCP/Agent startup"""
        if status == "success" and agent:
            print(f"    🤖 {message}")
        elif status == "success":
            print(f"    ✅ {message}")
        elif status == "starting":
            print(f"    🚀 {message}")
        elif status == "error":
            print(f"    ❌ {message}")
        elif status == "warning":
            print(f"    ⚠️ {message}")
        else:
            print(f"    • {message}")
        
    def log_status(self, message: str, component: str = "system", status: str = "info"):
        """Log status without printing (for file only)"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "message": message,
            "status": status
        }
        
        self.status_data["logs"].append(log_entry)
        
        # Keep only last 20 log entries
        if len(self.status_data["logs"]) > 20:
            self.status_data["logs"] = self.status_data["logs"][-20:]
            
        self.save_status()
        
    def save_status(self):
        """Save current status to file for dashboard"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status_data, f, indent=2)
        except Exception as e:
            pass  # Silent fail for status file
    
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
    
    def check_dependencies(self):
        """Check and install required dependencies"""
        self.print_section("Dependency Check", "📦")
        
        try:
            # Check if we're in virtual environment
            venv_path = Path(__file__).parent / ".venv"
            if not venv_path.exists():
                self.print_step("Virtual environment not found, creating...", "warning")
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], 
                             check=True, capture_output=True)
                self.print_step("Virtual environment created", "success")
            
            # Install required packages
            self.print_step("Installing/updating dependencies...", "starting")
            
            packages = [
                "fastapi", "uvicorn", "aiofiles", "python-multipart",
                "httpx", "psutil", "requests", "aiosqlite"
            ]
            
            venv_python = venv_path / "bin" / "python"
            if not venv_python.exists():  # Windows
                venv_python = venv_path / "Scripts" / "python.exe"
            
            for package in packages:
                result = subprocess.run([
                    str(venv_python), "-m", "pip", "install", package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.print_step(f"Failed to install {package}", "error")
                    return False
            
            self.print_step("All dependencies ready", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Dependency check failed: {e}", "error")
            return False
    
    async def start_mcp_server(self, server_info: Dict) -> bool:
        """Start a single MCP server with enhanced error handling"""
        name = server_info["name"]
        port = server_info["port"]
        script = server_info["script"]
        
        try:
            self.print_step(f"Starting {name} server (port {port})", "starting")
            
            # Update status to starting
            self.update_component_status("mcp_servers", name, "starting", {
                "port": port,
                "script": script
            })
            
            # Check if port is already in use
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    self.print_step(f"{name} server already running on port {port}", "warning")
                    self.update_component_status("mcp_servers", name, "running", {"port": port})
                    return True
            except:
                pass
            
            # Start the server with virtual environment
            script_path = Path(__file__).parent / "mcp" / script
            venv_python = Path(__file__).parent / ".venv" / "bin" / "python"
            
            if not script_path.exists():
                self.print_step(f"{name} server script not found", "error")
                self.update_component_status("mcp_servers", name, "not_found", {
                    "expected_path": str(script_path)
                })
                return False
            
            # Start process with virtual environment
            process = subprocess.Popen(
                [str(venv_python), str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                env={**os.environ, "PYTHONPATH": str(Path(__file__).parent)}
            )
            
            self.processes[f"mcp_{name}"] = process
            
            # Wait for startup with timeout
            for i in range(10):  # 5 second timeout
                await asyncio.sleep(0.5)
                if process.poll() is not None:
                    # Process died
                    stdout, stderr = process.communicate()
                    self.print_step(f"{name} server failed: {stderr.decode()[:100]}", "error")
                    self.update_component_status("mcp_servers", name, "failed", {
                        "error": stderr.decode()[:200]
                    })
                    return False
                
                # Check if port is responding
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    if result == 0:
                        self.print_step(f"{name} server started successfully", "success")
                        self.update_component_status("mcp_servers", name, "running", {
                            "port": port,
                            "pid": process.pid
                        })
                        return True
                except:
                    continue
            
            # Timeout reached
            self.print_step(f"{name} server startup timeout", "warning")
            self.update_component_status("mcp_servers", name, "timeout", {"port": port})
            return False
            
        except Exception as e:
            self.print_step(f"{name} server error: {str(e)[:100]}", "error")
            self.update_component_status("mcp_servers", name, "error", {"error": str(e)})
            return False
    
    async def start_mcp_servers(self):
        """Start all MCP servers, show only checkmarks for started servers, then health check"""
        self.print_section("MCP Servers", "�️")
        self.status_data["startup_phase"] = "starting_mcp_servers"
        mcp_servers = [
            {"name": "registry", "port": 8000, "script": "registry_server.py"},
            {"name": "filesystem", "port": 8001, "script": "filesystem_server.py"},
            {"name": "database", "port": 8004, "script": "database_server.py"},
            {"name": "llm", "port": 8005, "script": "llm_server.py"},
            {"name": "payment", "port": 8006, "script": "payment_server.py"},
            {"name": "analytics", "port": 8007, "script": "analytics_server.py"},
            {"name": "customer", "port": 8008, "script": "customer_server.py"},
        ]
        results = []
        for server in mcp_servers:
            ok = await self.start_mcp_server(server)
            results.append((server["name"], ok, server["port"]))
        # Print summary line
        summary = " ".join(["✅" if ok else "❌" for _, ok, _ in results])
        print(f"\n    MCP Servers: {summary}")
        # Health check
        all_healthy = await self.health_check_mcps(mcp_servers)
        return sum(1 for _, ok, _ in results if ok)

    async def health_check_mcps(self, mcp_servers):
        """Health check for all MCP servers"""
        import httpx
        healthy = True
        for server in mcp_servers:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"http://localhost:{server['port']}/health")
                    if resp.status_code == 200:
                        self.print_step(f"{server['name'].title()} healthy", "success")
                    else:
                        self.print_step(f"{server['name'].title()} unhealthy", "warning")
                        healthy = False
            except Exception:
                self.print_step(f"{server['name'].title()} not responding", "error")
                healthy = False
        return healthy
    
    async def start_dashboard(self):
        """Start the enhanced dashboard"""
        self.print_section("Dashboard Service", "📊")
        self.status_data["startup_phase"] = "starting_dashboard"
        
        try:
            # Kill any existing dashboard
            subprocess.run(["pkill", "-f", "python.*dashboard.py"], 
                         stderr=subprocess.DEVNULL)
            await asyncio.sleep(1)
            
            self.print_step("Starting dashboard on port 8888", "starting")
            
            # Start new dashboard with virtual environment
            venv_python = Path(__file__).parent / ".venv" / "bin" / "python"
            dashboard_process = subprocess.Popen(
                [str(venv_python), "dashboard.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent)
            )
            
            self.processes["dashboard"] = dashboard_process
            
            # Wait for startup
            await asyncio.sleep(3)
            
            # Verify dashboard is running
            if dashboard_process.poll() is None:
                self.print_step("Dashboard started successfully", "success")
                self.update_component_status("services", "dashboard", "running", {
                    "port": 8888,
                    "pid": dashboard_process.pid,
                    "url": "http://localhost:8888"
                })
                return True
            else:
                stdout, stderr = dashboard_process.communicate()
                self.print_step(f"Dashboard failed: {stderr.decode()[:100]}", "error")
                self.update_component_status("services", "dashboard", "failed", {
                    "error": stderr.decode()[:200]
                })
                return False
                
        except Exception as e:
            self.print_step(f"Dashboard error: {str(e)[:100]}", "error")
            self.update_component_status("services", "dashboard", "error", {"error": str(e)})
            return False
    
    async def start_agents(self):
        """Start agent coordination system, show only 🤖 for started agents, then health check"""
        self.print_section("Agents", "🤖")
        self.status_data["startup_phase"] = "starting_agents"
        try:
            self.print_step("Checking for running agents", "starting")
            
            # Check for running agents
            agents = ["solomon", "david"]
            results = []
            for agent_name in agents:
                # Check if agent process exists
                agent_running = False
                for process in psutil.process_iter(['pid', 'cmdline']):
                    try:
                        cmdline = ' '.join(process.info['cmdline'] or [])
                        if f"{agent_name}.py" in cmdline:
                            self.print_step(f"{agent_name.title()} running (PID: {process.info['pid']})", "success", agent=True)
                            self.update_component_status("agents", agent_name, "running", {"pid": process.info['pid']})
                            agent_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                if not agent_running:
                    self.print_step(f"{agent_name.title()} not found", "warning", agent=True)
                results.append(agent_running)
            # Print summary line
            summary = " ".join(["🤖" if ok else "❌" for ok in results])
            print(f"\n    Agents: {summary}")
            # Health check
            await self.health_check_agents(agents)
            return True
        except Exception as e:
            self.print_step(f"Agent system error: {str(e)[:100]}", "error")
            return True

    async def health_check_agents(self, agents):
        """Health check for all agents (process check)"""
        for agent in agents:
            found = False
            for process in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = ' '.join(process.info['cmdline'] or [])
                    if f"{agent}.py" in cmdline:
                        self.print_step(f"{agent.title()} healthy (PID: {process.info['pid']})", "success", agent=True)
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if not found:
                self.print_step(f"{agent.title()} not running", "warning", agent=True)
    
    async def run_startup(self):
        """Run the complete system startup"""
        print("🚀 BoarderframeOS Enhanced Startup")
        print("=" * 40)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Initialize status
        self.status_data["startup_phase"] = "initializing"
        self.save_status()
        
        success_count = 0
        total_steps = 4
        
        # Step 1: Dependencies
        if not self.check_dependencies():
            print("\n❌ Startup failed at dependency check")
            return False
        success_count += 1
        
        # Step 2: MCP Servers
        mcp_count = await self.start_mcp_servers()
        if mcp_count > 0:
            success_count += 1
        
        # Step 3: Dashboard
        if await self.start_dashboard():
            success_count += 1
        
        # Step 4: Agents
        if await self.start_agents():
            success_count += 1
        
        # Final status
        self.print_section("Startup Complete", "🎉")
        self.status_data["startup_phase"] = "operational"
        self.save_status()
        
        if success_count == total_steps:
            self.print_section("Summary", "🎉")
            print("\n    ✅ All systems operational!")
            print("    Dashboard: http://localhost:8888\n")
            # Launch dashboard in browser
            try:
                import webbrowser
                webbrowser.open("http://localhost:8888")
                self.print_step("Dashboard opened in browser", "success")
            except Exception:
                self.print_step("Could not open browser", "warning")
        else:
            self.print_section("Summary", "⚠️")
            print(f"\n    Partial startup: {success_count}/{total_steps} components")
        print(f"\n🔍 Use 'python system_status.py' to check status\n")
        return success_count >= 2
    
    def setup_signal_handlers(self):
        """Setup clean shutdown handlers"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received shutdown signal...")
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def cleanup(self):
        """Clean shutdown of all processes"""
        self.print_step("Cleaning up processes", "info")
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass

async def main():
    """Main startup function"""
    startup = EnhancedSystemStartup()
    startup.setup_signal_handlers()
    
    try:
        success = await startup.run_startup()
        if success:
            # Keep running to maintain processes
            print("\n⏳ System running... Press Ctrl+C to stop")
            while True:
                await asyncio.sleep(10)
        else:
            print("\n❌ Startup failed")
            return 1
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
    finally:
        startup.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
