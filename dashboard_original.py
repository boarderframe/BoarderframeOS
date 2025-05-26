#!/usr/bin/env python3
"""
Enhanced BoarderframeOS Dashboard with Real-Time Status
"""
import http.server
import socketserver
import json
import threading
import time
import os
import signal
import sys
from datetime import datetime
import asyncio
import httpx

PORT = 8888

class DashboardData:
    """Manages dashboard data updates"""
    def __init__(self):
        self.services_status = {}
        self.agents_status = {}
        self.system_metrics = {}
        self.health_status = {}
        self.running_agents = {}
        self.startup_status = {}
        self.last_update = None
        self.update_thread = None
        self.running = True
        
    def start_updates(self):
        """Start background data updates"""
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
    def _update_loop(self):
        """Background update loop"""
        while self.running:
            try:
                # Run async update in new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._async_update())
                loop.close()
            except Exception as e:
                print(f"Update error: {e}")
            time.sleep(5)  # Update every 5 seconds
    
    async def _update_services(self, client):
        """Update MCP services status with enhanced filesystem server monitoring"""
        services = [
            ("MCP Registry", 8000),
            ("Filesystem Server", 8001),
            ("Database Server", 8004),
            ("LLM Server", 8005),
            ("UI Dashboard", 8888)
        ]
        
        for service_name, port in services:
            try:
                response = await client.get(f"http://localhost:{port}/health", timeout=3.0)
                service_data = {"status": "online", "port": port}
                
                # Enhanced data for filesystem server
                if service_name == "Filesystem Server" and response.status_code == 200:
                    try:
                        health_data = response.json()
                        service_data.update({
                            "uptime": health_data.get("uptime", 0),
                            "ai_available": health_data.get("ai_available", False),
                            "active_operations": health_data.get("active_operations", 0),
                            "connected_clients": health_data.get("connected_clients", 0),
                            "features": health_data.get("features", {}),
                            "base_path": health_data.get("base_path", "unknown")
                        })
                    except:
                        pass  # Use basic status if JSON parsing fails
                
                self.services_status[service_name] = service_data
            except:
                self.services_status[service_name] = {
                    "status": "offline",
                    "port": port
                }
        
        # Update with startup status data if available
        if hasattr(self, 'startup_status') and 'mcp_servers' in self.startup_status:
            mcp_servers = self.startup_status.get('mcp_servers', {})
            for server_name, server_info in mcp_servers.items():
                service_display_name = f"{server_name.title()} Server"
                if service_display_name not in self.services_status:
                    self.services_status[service_display_name] = {
                        "status": server_info.get('status', 'unknown'),
                        "port": server_info.get('details', {}).get('port', 'unknown')
                    }
    
    async def _update_agents(self, client):
        """Update agents status from database"""
        try:
            response = await client.post("http://localhost:8004/query", json={
                "sql": "SELECT id, name, status, biome, generation, fitness_score FROM agents",
                "fetch_all": True
            })
            
            if response.status_code == 200 and response.json().get("success"):
                agents_data = response.json().get("data", [])
                
                for agent in agents_data:
                    self.agents_status[agent["id"]] = {
                        "name": agent["name"],
                        "status": agent["status"],
                        "biome": agent["biome"],
                        "generation": agent["generation"],
                        "fitness": agent["fitness_score"]
                    }
        except:
            pass  # Database might not be available
    
    def _load_startup_status(self):
        """Load startup status data if available"""
        try:
            startup_file = "/tmp/boarderframe_startup_status.json"
            if os.path.exists(startup_file):
                with open(startup_file, 'r') as f:
                    self.startup_status = json.load(f)
            else:
                self.startup_status = {}
        except Exception as e:
            self.startup_status = {}
            print(f"Error loading startup status: {e}")

    async def _update_running_agents(self):
        """Update running agents by checking processes"""
        try:
            import psutil
            
            # Check for running agent processes
            running_agents = {}
            
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(process.info['cmdline'] or [])
                    
                    # Check for agent processes
                    if 'solomon.py' in cmdline:
                        running_agents['solomon'] = {
                            'name': 'Solomon',
                            'status': 'running',
                            'pid': process.info['pid'],
                            'type': 'Strategic Planning Agent'
                        }
                    elif 'david.py' in cmdline:
                        running_agents['david'] = {
                            'name': 'David',
                            'status': 'running', 
                            'pid': process.info['pid'],
                            'type': 'Research Agent'
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except ImportError:
            # psutil not available, fall back to simpler check
            running_agents = {}
            
        # Update agents status with running processes
        self.running_agents = running_agents

    def _generate_startup_section(self):
        """Generate startup status section HTML"""
        if not self.startup_status:
            return ""
        
        startup_phase = self.startup_status.get('startup_phase', 'unknown')
        start_time = self.startup_status.get('start_time', '')
        logs = self.startup_status.get('logs', [])
        mcp_servers = self.startup_status.get('mcp_servers', {})
        
        # Show startup section only if we have startup data
        if startup_phase == 'initializing' or logs or mcp_servers:
            # Phase indicator
            phase_display = {
                'initializing': '🔄 Initializing System',
                'starting_mcp_servers': '🚀 Starting MCP Servers',
                'starting_dashboard': '📊 Starting Dashboard',
                'starting_agents': '🤖 Starting Agents',
                'complete': '✅ System Ready'
            }.get(startup_phase, f'📍 {startup_phase.replace("_", " ").title()}')
            
            # MCP Servers status
            mcp_status_html = ""
            for server_name, server_info in mcp_servers.items():
                status = server_info.get('status', 'unknown')
                status_icon = {
                    'starting': '🔄',
                    'running': '✅',
                    'failed': '❌',
                    'error': '❌',
                    'not_found': '⚠️'
                }.get(status, '❓')
                
                details = server_info.get('details', {})
                port_info = f"Port {details.get('port', 'N/A')}" if 'port' in details else ""
                
                mcp_status_html += f"""
                    <div class="startup-item">
                        <span class="startup-icon">{status_icon}</span>
                        <span class="startup-name">{server_name.title()} Server</span>
                        <span class="startup-status">{status.replace('_', ' ').title()}</span>
                        <span class="startup-details">{port_info}</span>
                    </div>"""
            
            # Recent logs
            recent_logs = logs[-5:] if len(logs) > 5 else logs
            logs_html = ""
            for log in recent_logs:
                timestamp = datetime.fromisoformat(log['timestamp']).strftime('%H:%M:%S')
                component = log.get('component', 'system')
                message = log.get('message', '')
                status = log.get('status', 'info')
                
                status_color = {
                    'success': '#10b981',
                    'error': '#ef4444', 
                    'warning': '#f59e0b',
                    'info': '#6b7280'
                }.get(status, '#6b7280')
                
                logs_html += f"""
                    <div class="log-entry" style="color: {status_color};">
                        <span class="log-time">{timestamp}</span>
                        <span class="log-component">[{component}]</span>
                        <span class="log-message">{message}</span>
                    </div>"""
            
            return f"""
                <div class="panel startup-panel">
                    <h3>🚀 System Startup Status</h3>
                    <div class="startup-phase">
                        <h4>{phase_display}</h4>
                        {f'<div class="startup-time">Started: {datetime.fromisoformat(start_time).strftime("%H:%M:%S")}</div>' if start_time else ''}
                    </div>
                    
                    {f'''
                    <div class="startup-section">
                        <h5>MCP Servers</h5>
                        <div class="startup-list">
                            {mcp_status_html}
                        </div>
                    </div>
                    ''' if mcp_status_html else ''}
                    
                    {f'''
                    <div class="startup-section">
                        <h5>Recent Activity</h5>
                        <div class="startup-logs">
                            {logs_html}
                        </div>
                    </div>
                    ''' if logs_html else ''}
                </div>"""
        
        return ""

    async def _update_metrics(self, client):
        """Update system metrics"""
        try:
            # Get database stats
            response = await client.get("http://localhost:8004/stats")
            if response.status_code == 200:
                self.system_metrics["database"] = response.json()
        except:
            pass
        
        # Calculate summary metrics
        self.system_metrics["summary"] = {
            "total_services": len(self.services_status),
            "online_services": sum(1 for s in self.services_status.values() if s["status"] == "online"),
            "total_agents": len(self.agents_status),
            "active_agents": sum(1 for a in self.agents_status.values() if a["status"] == "active")
        }
    
    def _load_health_data(self):
        """Load health check data if available"""
        try:
            health_file = "/tmp/boarderframe_health.json"
            if os.path.exists(health_file):
                with open(health_file, 'r') as f:
                    self.health_status = json.load(f)
        except:
            pass
    
    async def _async_update(self):
        """Async update of all data"""
        async with httpx.AsyncClient(timeout=2.0) as client:
            # Update services status
            await self._update_services(client)
            
            # Update agents status
            await self._update_agents(client)
            
            # Update running agents from processes
            await self._update_running_agents()
            
            # Load health check data if available
            self._load_health_data()
            
            # Load startup status data if available
            self._load_startup_status()
            
            self.last_update = datetime.now()
    
    def get_dashboard_html(self):
        """Generate dashboard HTML with current data"""
        # Startup status HTML
        startup_section_html = self._generate_startup_section()
        
        # Services status HTML
        services_html = ""
        for service, status in self.services_status.items():
            status_class = "online" if status["status"] == "online" else "offline"
            icon = "✓" if status["status"] == "online" else "✗"
            
            # Enhanced display for filesystem server
            if service == "Filesystem Server" and status["status"] == "online":
                uptime = status.get("uptime", 0)
                ai_status = "🤖" if status.get("ai_available", False) else ""
                active_ops = status.get("active_operations", 0)
                clients = status.get("connected_clients", 0)
                
                services_html += f"""
                    <div class="service-item filesystem-server">
                        <span class="status-icon {status_class}">{icon}</span>
                        <span class="service-name">{service} {ai_status}</span>
                        <span class="service-details">
                            Port {status['port']} | ⏱️ {uptime:.1f}s | 
                            🔄 {active_ops} ops | 👥 {clients} clients
                        </span>
                    </div>"""
            else:
                services_html += f"""
                    <div class="service-item">
                        <span class="status-icon {status_class}">{icon}</span>
                        <span class="service-name">{service}</span>
                        <span class="service-port">Port {status['port']}</span>
                    </div>"""
        
        # Agents status HTML - prioritize running agents
        agents_html = ""
        all_agents = ["solomon", "david"]
        
        for agent_id in all_agents:
            if agent_id in self.running_agents:
                # Agent is currently running
                agent = self.running_agents[agent_id]
                agents_html += f"""
                    <div class="agent-card">
                        <h4>{agent['name']}</h4>
                        <div class="agent-status active">RUNNING</div>
                        <div class="agent-details">
                            <div>Type: {agent['type']}</div>
                            <div>PID: {agent['pid']}</div>
                            <div>Status: Active Process</div>
                        </div>
                    </div>"""
            elif agent_id in self.agents_status:
                # Agent in database but not running
                agent = self.agents_status[agent_id]
                status_class = "active" if agent["status"] == "active" else "inactive"
                agents_html += f"""
                    <div class="agent-card {status_class}">
                        <h4>{agent['name']}</h4>
                        <div class="agent-status {status_class}">{agent['status'].upper()}</div>
                        <div class="agent-details">
                            <div>Biome: {agent['biome']}</div>
                            <div>Generation: {agent['generation']}</div>
                            <div>Fitness: {agent['fitness']:.2f}</div>
                        </div>
                    </div>"""
            else:
                # Agent not found
                agents_html += f"""
                    <div class="agent-card inactive">
                        <h4>{agent_id.replace('_', ' ').title()}</h4>
                        <div class="agent-status">NOT RUNNING</div>
                        <div class="agent-details">
                            <div>Status: Offline</div>
                        </div>
                    </div>"""
        
        # System metrics
        metrics = self.system_metrics.get("summary", {})
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Control Center</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a; 
            color: white; 
            margin: 0; 
            padding: 20px; 
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ 
            background: linear-gradient(135deg, #1e40af, #7c3aed);
            padding: 30px; 
            border-radius: 12px; 
            margin-bottom: 30px; 
            text-align: center;
            position: relative;
        }}
        .update-time {{
            position: absolute;
            top: 10px;
            right: 20px;
            font-size: 12px;
            opacity: 0.8;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .panel {{ 
            background: #1e293b; 
            padding: 20px; 
            border-radius: 12px; 
            border: 1px solid #334155; 
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #1e293b;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #334155;
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #94a3b8;
            font-size: 0.9em;
        }}
        .service-item {{
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: #0f172a;
            border-radius: 6px;
        }}
        .service-item.filesystem-server {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #334155;
        }}
        .status-icon {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            text-align: center;
            font-weight: bold;
        }}
        .status-icon.online {{ color: #10b981; }}
        .status-icon.offline {{ color: #ef4444; }}
        .service-name {{ flex: 1; }}
        .service-port {{ color: #6b7280; font-size: 0.9em; }}
        .service-details {{ 
            color: #94a3b8; 
            font-size: 0.85em; 
            white-space: nowrap;
        }}
        .agents-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .agent-card {{
            background: #374151;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .agent-card.inactive {{
            opacity: 0.5;
            border: 1px dashed #4b5563;
        }}
        .agent-card h4 {{
            margin: 0 0 10px 0;
            color: #60a5fa;
        }}
        .agent-status {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .agent-status.active {{ color: #10b981; }}
        .agent-status.inactive {{ color: #6b7280; }}
        .agent-details {{
            font-size: 0.85em;
            color: #9ca3af;
        }}
        .agent-details div {{
            margin: 2px 0;
        }}
        .solomon-interface {{
            background: #374151;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
        }}
        .chat-status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .chat-status.online {{ background: #059669; }}
        .chat-status.offline {{ background: #dc2626; }}
        .setup-section {{
            background: #1e40af;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        .code {{ 
            background: #000; 
            color: #00ff00; 
            padding: 10px; 
            border-radius: 4px; 
            font-family: monospace; 
            margin: 5px 0;
            display: block;
        }}
        .health-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }}
        .health-indicator.healthy {{ background: #10b981; }}
        .health-indicator.degraded {{ background: #f59e0b; }}
        .health-indicator.critical {{ background: #ef4444; }}
        
        /* Startup Status Styles */
        .startup-panel {{
            background: linear-gradient(135deg, #1e293b, #334155);
            border: 1px solid #475569;
            margin-bottom: 20px;
        }}
        .startup-phase {{
            text-align: center;
            padding: 15px;
            border-bottom: 1px solid #475569;
        }}
        .startup-phase h4 {{
            margin: 0;
            color: #60a5fa;
            font-size: 1.2em;
        }}
        .startup-time {{
            color: #94a3b8;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .startup-section {{
            margin: 15px 0;
        }}
        .startup-section h5 {{
            margin: 0 0 10px 0;
            color: #e2e8f0;
            font-size: 1em;
            border-bottom: 1px solid #475569;
            padding-bottom: 5px;
        }}
        .startup-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .startup-item {{
            display: flex;
            align-items: center;
            padding: 8px 12px;
            background: #0f172a;
            border-radius: 6px;
            border-left: 3px solid #475569;
        }}
        .startup-icon {{
            width: 20px;
            margin-right: 10px;
            text-align: center;
        }}
        .startup-name {{
            flex: 1;
            font-weight: 500;
        }}
        .startup-status {{
            color: #94a3b8;
            font-size: 0.9em;
            margin-right: 10px;
        }}
        .startup-details {{
            color: #6b7280;
            font-size: 0.8em;
        }}
        .startup-logs {{
            background: #0f172a;
            border-radius: 6px;
            padding: 10px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85em;
        }}
        .log-entry {{
            margin: 3px 0;
            display: flex;
            gap: 10px;
        }}
        .log-time {{
            color: #94a3b8;
            min-width: 60px;
        }}
        .log-component {{
            color: #60a5fa;
            min-width: 80px;
        }}
        .log-message {{
            flex: 1;
        }}
    </style>
    <script>
        // Auto-refresh countdown
        let countdown = 10;
        setInterval(() => {{
            countdown--;
            if (countdown <= 0) countdown = 10;
            document.getElementById('countdown').textContent = countdown;
        }}, 1000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 BoarderframeOS Dashboard</h1>
            <p>AI Operating System Control Center</p>
            <div class="update-time">
                Last Update: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'Never'}<br>
                Auto-refresh in <span id="countdown">10</span>s
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" style="color: #10b981;">{metrics.get('online_services', 0)}</div>
                <div class="metric-label">Services Online</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #3b82f6;">{metrics.get('total_services', 0)}</div>
                <div class="metric-label">Total Services</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #8b5cf6;">{metrics.get('active_agents', 0)}</div>
                <div class="metric-label">Active Agents</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #f59e0b;">{metrics.get('total_agents', 0)}</div>
                <div class="metric-label">Total Agents</div>
            </div>
        </div>

        <!-- Startup Status Section -->
        {startup_section_html}

        <div class="dashboard-grid">
            <div class="panel">
                <h3>📡 MCP Services</h3>
                {services_html if services_html else '<p style="color: #6b7280;">Loading services...</p>'}
            </div>
            
            <div class="panel" style="grid-column: span 2;">
                <h3>🤖 Core Agents</h3>
                <div class="agents-grid">
                    {agents_html if agents_html else '<p style="color: #6b7280;">No agents deployed yet</p>'}
                </div>
            </div>
        </div>

        <div class="panel">
            <h3>💬 Solomon Communication Interface</h3>
            <div class="solomon-interface">
                <div style="font-size: 3em; margin-bottom: 15px;">🤖</div>
                <h4>Solomon - Chief of Staff</h4>
                <div class="chat-status {'online' if 'solomon' in self.agents_status and self.agents_status['solomon']['status'] == 'active' else 'offline'}">
                    {'ONLINE - Ready to chat' if 'solomon' in self.agents_status and self.agents_status['solomon']['status'] == 'active' else 'OFFLINE - Awaiting deployment'}
                </div>
                <p style="margin-top: 15px; color: #9ca3af;">
                    {'Solomon is ready to assist you. Open the chat interface to begin.' if 'solomon' in self.agents_status and self.agents_status['solomon']['status'] == 'active' else 'Run startup.py to bring Solomon online'}
                </p>
            </div>
        </div>

        <div class="panel">
            <h3>🏥 System Health</h3>
            <div style="display: flex; align-items: center; margin: 20px 0;">
                <span class="health-indicator {self.health_status.get('results', {}).get('overall', 'unknown')}"></span>
                <span style="font-size: 1.2em; font-weight: bold;">
                    Overall Health: {self.health_status.get('results', {}).get('overall', 'Unknown').upper()}
                </span>
            </div>
            {'<p style="color: #6b7280;">Run health_check.py for detailed diagnostics</p>' if not self.health_status else ''}
        </div>

        <div class="panel">
            <h3>🛠️ Quick Commands</h3>
            <div class="setup-section">
                <p><strong>Start Everything:</strong></p>
                <code>cd /Users/cosburn/BoarderframeOS/boarderframeos && python startup.py</code>
                
                <p style="margin-top: 15px;"><strong>Health Check:</strong></p>
                <code>python health_check.py</code>
                
                <p style="margin-top: 15px;"><strong>Continuous Monitoring:</strong></p>
                <code>python health_check.py --continuous</code>
            </div>
        </div>
    </div>
</body>
</html>"""

# Global dashboard data manager
dashboard_data = DashboardData()

class EnhancedHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logs for cleaner output
        pass
    
    def do_GET(self):
        try:
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                html = dashboard_data.get_dashboard_html()
                self.wfile.write(html.encode())
                
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                health_data = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "services": dashboard_data.services_status,
                    "agents": len(dashboard_data.agents_status)
                }
                self.wfile.write(json.dumps(health_data).encode())
                
            elif self.path == '/api/status':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                status = {
                    "services": dashboard_data.services_status,
                    "agents": dashboard_data.agents_status,
                    "metrics": dashboard_data.system_metrics,
                    "health": dashboard_data.health_status,
                    "last_update": dashboard_data.last_update.isoformat() if dashboard_data.last_update else None
                }
                self.wfile.write(json.dumps(status).encode())
                
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            print(f"Request error: {e}")
            self.send_error(500)

def signal_handler(sig, frame):
    print("\n🛑 Shutting down dashboard...")
    dashboard_data.running = False
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Enhanced BoarderframeOS Dashboard...")
    print(f"📍 Dashboard URL: http://localhost:{PORT}")
    print("🔄 Real-time updates enabled")
    print("🛑 Press Ctrl+C to stop")
    print()
    
    # Start background updates
    dashboard_data.start_updates()
    
    try:
        with socketserver.TCPServer(("", PORT), EnhancedHandler) as httpd:
            print(f"✅ Dashboard running on port {PORT}")
            print(f"🎯 Access at: http://localhost:{PORT}")
            print()
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use")
        else:
            print(f"❌ Server error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")

if __name__ == "__main__":
    main()