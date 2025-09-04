"""
MCP Server Manager
A simple interface to manage and view all MCP servers
"""

import os
import json
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MCPServer:
    name: str
    file_path: str
    category: str
    description: str
    port: Optional[int] = None
    status: str = "stopped"
    pid: Optional[int] = None
    last_started: Optional[str] = None


class MCPServerManager:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.servers = self._discover_servers()
        
    def _discover_servers(self) -> List[MCPServer]:
        """Discover all MCP servers in the organized structure"""
        servers = []
        
        # Server configurations
        server_configs = {
            # Active servers
            "servers/active/kroger_mcp_enhanced_ui.py": {
                "name": "Kroger MCP Enhanced UI",
                "description": "Main Kroger product search with MCP-UI protocol",
                "port": 9006,
                "category": "active"
            },
            "servers/active/simple_filesystem_server.py": {
                "name": "Simple Filesystem Server", 
                "description": "Basic filesystem operations MCP server",
                "port": 9001,
                "category": "active"
            },
            "servers/active/real_playwright_server.py": {
                "name": "Playwright Server",
                "description": "Browser automation MCP server",
                "port": 9002,
                "category": "active"
            },
            
            # Archived servers
            "servers/archive/kroger_mcp_server.py": {
                "name": "Kroger MCP Server (Original)",
                "description": "Original Kroger API server",
                "port": None,
                "category": "archive"
            },
            "servers/archive/kroger_mcp_server_enhanced.py": {
                "name": "Kroger MCP Server Enhanced",
                "description": "Enhanced version (superseded)",
                "port": None,
                "category": "archive"
            },
            "servers/archive/kroger_mcp_server_v2.py": {
                "name": "Kroger MCP Server v2",
                "description": "Version 2 (superseded)",
                "port": None,
                "category": "archive"
            },
            "servers/archive/kroger_mcp_server_phase2.py": {
                "name": "Kroger MCP Server Phase 2",
                "description": "Phase 2 implementation (superseded)",
                "port": None,
                "category": "archive"
            },
            "servers/archive/kroger_mcp_server_fixed.py": {
                "name": "Kroger MCP Server Fixed",
                "description": "Bug-fixed version (superseded)",
                "port": None,
                "category": "archive"
            },
            "servers/archive/kroger_mcp_enhanced_artifacts.py": {
                "name": "Kroger MCP Enhanced Artifacts",
                "description": "Artifacts-focused version (superseded)",
                "port": None,
                "category": "archive"
            },
            "servers/archive/advanced_filesystem_server.py": {
                "name": "Advanced Filesystem Server",
                "description": "Advanced filesystem operations (superseded)",
                "port": None,
                "category": "archive"
            },
            "servers/archive/playwright_mcp_server_real.py": {
                "name": "Playwright MCP Server Real",
                "description": "Alternative Playwright server (superseded)",
                "port": None,
                "category": "archive"
            },
            "servers/archive/simple_playwright_server.py": {
                "name": "Simple Playwright Server",
                "description": "Simple Playwright server (superseded)",
                "port": None,
                "category": "archive"
            }
        }
        
        for file_path, config in server_configs.items():
            full_path = self.base_path / file_path
            if full_path.exists():
                server = MCPServer(
                    name=config["name"],
                    file_path=str(full_path),
                    category=config["category"],
                    description=config["description"],
                    port=config["port"]
                )
                server.status = self._check_server_status(server)
                servers.append(server)
                
        return servers
    
    def _check_server_status(self, server: MCPServer) -> str:
        """Check if a server is currently running"""
        if not server.port:
            return "not-configured"
            
        # Try to check if port is in use (handle permission errors gracefully)
        try:
            # Use lsof command as fallback for macOS permission issues
            import subprocess
            result = subprocess.run(
                ['lsof', '-i', f':{server.port}'], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Port is in use
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            server.pid = pid
                            return "running"
                        except ValueError:
                            continue
            
            return "stopped"
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            # Fallback: try psutil with permission error handling
            try:
                for conn in psutil.net_connections():
                    if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == server.port:
                        if conn.status == 'LISTEN':
                            try:
                                proc = psutil.Process(conn.pid)
                                if server.file_path in ' '.join(proc.cmdline()):
                                    server.pid = conn.pid
                                    return "running"
                            except (psutil.AccessDenied, psutil.NoSuchProcess):
                                # Process exists but we can't access it - assume running
                                server.pid = conn.pid
                                return "running"
            except (psutil.AccessDenied, PermissionError):
                # Can't access network connections, assume stopped
                pass
            
            return "stopped"
    
    def get_servers_by_category(self) -> Dict[str, List[MCPServer]]:
        """Get servers grouped by category"""
        categorized = {"active": [], "archive": [], "development": []}
        
        for server in self.servers:
            if server.category in categorized:
                categorized[server.category].append(server)
                
        return categorized
    
    def start_server(self, server_name: str) -> bool:
        """Start a specific server"""
        server = next((s for s in self.servers if s.name == server_name), None)
        if not server or not server.port or server.status == "running":
            return False
            
        try:
            # Start the server in background
            cmd = f"cd {self.base_path} && python {server.file_path} > logs/{server.name.lower().replace(' ', '_')}.log 2>&1 &"
            subprocess.run(cmd, shell=True)
            server.last_started = datetime.now().isoformat()
            return True
        except Exception as e:
            print(f"Error starting {server_name}: {e}")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """Stop a specific server"""
        server = next((s for s in self.servers if s.name == server_name), None)
        if not server or server.status != "running":
            return False
            
        try:
            if server.pid:
                os.kill(server.pid, 9)
                return True
        except Exception as e:
            print(f"Error stopping {server_name}: {e}")
            
        return False
    
    def get_server_status(self) -> Dict:
        """Get overall status of all servers"""
        categorized = self.get_servers_by_category()
        
        status = {
            "total_servers": len(self.servers),
            "active_servers": len([s for s in self.servers if s.status == "running"]),
            "categories": {}
        }
        
        for category, servers in categorized.items():
            running = len([s for s in servers if s.status == "running"])
            status["categories"][category] = {
                "total": len(servers),
                "running": running,
                "servers": [
                    {
                        "name": s.name,
                        "status": s.status,
                        "port": s.port,
                        "description": s.description
                    } for s in servers
                ]
            }
            
        return status


def main():
    """Command line interface for MCP server management"""
    manager = MCPServerManager()
    
    print("🔧 MCP Server Manager")
    print("=" * 50)
    
    status = manager.get_server_status()
    
    print(f"📊 Total Servers: {status['total_servers']}")
    print(f"🟢 Active: {status['active_servers']}")
    print()
    
    for category, info in status["categories"].items():
        print(f"📁 {category.upper()} ({info['running']}/{info['total']} running)")
        for server in info["servers"]:
            status_icon = "🟢" if server["status"] == "running" else "⚫" if server["status"] == "stopped" else "⚪"
            port_info = f":{server['port']}" if server["port"] else ""
            print(f"   {status_icon} {server['name']}{port_info}")
            print(f"      {server['description']}")
        print()


if __name__ == "__main__":
    main()