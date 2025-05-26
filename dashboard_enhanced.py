#!/usr/bin/env python3
"""
Enhanced BoarderframeOS Dashboard with Modern UI and Real-Time Status
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
        self.mcp_details = {}
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
            time.sleep(3)  # Update every 3 seconds
    
    async def _async_update(self):
        """Async update of all dashboard data"""
        async with httpx.AsyncClient(timeout=3.0) as client:
            await self._update_services(client)
            await self._update_agents()
            await self._update_system_metrics()
            await self._update_startup_status()
            self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def _update_services(self, client):
        """Update services status with enhanced MCP server details"""
        services = {
            "registry": {"port": 8000, "name": "Registry Server", "icon": "fas fa-server"},
            "filesystem": {"port": 8001, "name": "Filesystem Server", "icon": "fas fa-folder-tree"},
            "database": {"port": 8004, "name": "Database Server", "icon": "fas fa-database"},
            "llm": {"port": 8005, "name": "LLM Server", "icon": "fas fa-brain"},
            "dashboard": {"port": 8888, "name": "Dashboard", "icon": "fas fa-chart-line"}
        }
        
        for service_id, service_info in services.items():
            try:
                resp = await client.get(f"http://localhost:{service_info['port']}/health")
                if resp.status_code == 200:
                    health_data = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {}
                    
                    # Enhanced data for filesystem server
                    if service_id == "filesystem":
                        self.mcp_details[service_id] = {
                            "uptime": health_data.get("uptime", "Unknown"),
                            "total_operations": health_data.get("total_operations", 0),
                            "active_clients": health_data.get("active_clients", 0),
                            "ai_features": health_data.get("ai_available", False),
                            "vector_db_size": health_data.get("vector_db_entries", 0),
                            "base_path": health_data.get("base_path", "/"),
                            "disk_usage": health_data.get("disk_usage", {}),
                            "recent_operations": health_data.get("recent_operations", [])
                        }
                    
                    self.services_status[service_id] = {
                        "status": "healthy",
                        "response_time": resp.elapsed.total_seconds(),
                        "details": health_data,
                        **service_info
                    }
                else:
                    self.services_status[service_id] = {
                        "status": "degraded", 
                        "error": f"HTTP {resp.status_code}",
                        **service_info
                    }
            except Exception as e:
                self.services_status[service_id] = {
                    "status": "critical", 
                    "error": str(e)[:50],
                    **service_info
                }

    async def _update_agents(self):
        """Update agents status"""
        # Check for running agent processes
        running_agents = {}
        try:
            import psutil
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(process.info['cmdline']) if process.info['cmdline'] else ''
                    if 'solomon.py' in cmdline or 'solomon' in process.info['name'].lower():
                        running_agents['solomon'] = {
                            'name': 'Solomon',
                            'status': 'running', 
                            'pid': process.info['pid'],
                            'type': 'Strategic Planning Agent',
                            'memory_percent': process.memory_percent(),
                            'cpu_percent': process.cpu_percent()
                        }
                    elif 'david.py' in cmdline or 'david' in process.info['name'].lower():
                        running_agents['david'] = {
                            'name': 'David',
                            'status': 'running', 
                            'pid': process.info['pid'],
                            'type': 'Research Agent',
                            'memory_percent': process.memory_percent(),
                            'cpu_percent': process.cpu_percent()
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            pass
            
        self.running_agents = running_agents

    async def _update_system_metrics(self):
        """Update system metrics"""
        try:
            import psutil
            self.system_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "active_connections": len(psutil.net_connections()),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        except ImportError:
            self.system_metrics = {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "active_connections": 0,
                "boot_time": "Unknown",
                "load_avg": [0, 0, 0]
            }

    async def _update_startup_status(self):
        """Update startup status from file"""
        try:
            if os.path.exists('startup_status.json'):
                with open('startup_status.json', 'r') as f:
                    self.startup_status = json.load(f)
        except:
            pass

    def generate_dashboard_html(self):
        """Generate the enhanced dashboard HTML"""
        # Calculate service summary
        total_services = len(self.services_status)
        healthy_services = sum(1 for s in self.services_status.values() if s.get("status") == "healthy")
        
        # System status
        overall_status = "online" if healthy_services == total_services else "warning" if healthy_services > 0 else "offline"
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Control Center</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <meta http-equiv="refresh" content="5">
    <style>
        :root {{
            --primary-bg: #0a0e27;
            --secondary-bg: #1a1d3a;
            --card-bg: #252853;
            --accent-bg: #2d3561;
            --primary-text: #ffffff;
            --secondary-text: #b0b7c3;
            --accent-color: #6366f1;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --border-color: #374151;
            --glow-color: rgba(99, 102, 241, 0.3);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--primary-bg) 0%, #0f1629 100%);
            color: var(--primary-text);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* Header */
        .header {{
            background: linear-gradient(90deg, var(--secondary-bg) 0%, var(--card-bg) 100%);
            border-bottom: 2px solid var(--accent-color);
            padding: 1.5rem 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .logo i {{
            font-size: 2rem;
            color: var(--accent-color);
            text-shadow: 0 0 20px var(--glow-color);
        }}

        .logo h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(45deg, var(--accent-color), #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .system-status {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .status-indicator {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border-color);
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        .status-dot.online {{ background: var(--success-color); }}
        .status-dot.warning {{ background: var(--warning-color); }}
        .status-dot.offline {{ background: var(--danger-color); }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}

        /* Main Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        /* Card Styles */
        .card {{
            background: linear-gradient(135deg, var(--card-bg) 0%, var(--accent-bg) 100%);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent-color), #8b5cf6, var(--accent-color));
            opacity: 0.8;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            border-color: var(--accent-color);
        }}

        .card h3 {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 1rem;
            font-size: 1.3rem;
            font-weight: 600;
            color: var(--primary-text);
        }}

        .card h3 i {{
            color: var(--accent-color);
            font-size: 1.2rem;
        }}

        /* Service Cards */
        .service-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 0.8rem;
            transition: all 0.2s ease;
        }}

        .service-item:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
        }}

        .service-info {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .service-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            color: white;
        }}

        .service-icon.filesystem {{ background: linear-gradient(45deg, #10b981, #059669); }}
        .service-icon.registry {{ background: linear-gradient(45deg, #6366f1, #4f46e5); }}
        .service-icon.database {{ background: linear-gradient(45deg, #f59e0b, #d97706); }}
        .service-icon.llm {{ background: linear-gradient(45deg, #8b5cf6, #7c3aed); }}
        .service-icon.dashboard {{ background: linear-gradient(45deg, #ef4444, #dc2626); }}

        .service-details h4 {{
            margin: 0;
            font-size: 1rem;
            font-weight: 600;
        }}

        .service-details p {{
            margin: 0;
            font-size: 0.9rem;
            color: var(--secondary-text);
        }}

        .service-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }}

        .service-status.healthy {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .service-status.degraded {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }}

        .service-status.critical {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }}

        /* Agents */
        .agent-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }}

        .agent-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-1px);
        }}

        .agent-card.active {{
            border-color: var(--success-color);
            background: rgba(16, 185, 129, 0.1);
        }}

        .agent-card.inactive {{
            border-color: var(--border-color);
            opacity: 0.7;
        }}

        .agent-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
        }}

        .agent-name {{
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0;
        }}

        .agent-status {{
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }}

        .agent-status.running {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .agent-status.inactive {{
            background: rgba(107, 114, 128, 0.2);
            color: #9ca3af;
            border: 1px solid #6b7280;
        }}

        .agent-details {{
            color: var(--secondary-text);
            font-size: 0.9rem;
            line-height: 1.4;
        }}

        .agent-details div {{
            margin-bottom: 0.3rem;
        }}

        /* Metrics */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}

        .metric-item {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 0.5rem;
        }}

        .metric-label {{
            font-size: 0.9rem;
            color: var(--secondary-text);
        }}

        /* Special filesystem display */
        .filesystem-enhanced {{
            border-left: 3px solid var(--success-color) !important;
        }}

        .filesystem-enhanced .service-details p::after {{
            content: " 🤖 AI";
            color: var(--success-color);
            font-weight: 600;
            font-size: 0.8rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .header-content {{
                flex-direction: column;
                gap: 1rem;
            }}
            
            .grid {{
                grid-template-columns: 1fr;
            }}
            
            .service-item {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.8rem;
            }}
        }}

        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .card {{
            animation: fadeInUp 0.6s ease forwards;
        }}

        .card:nth-child(1) {{ animation-delay: 0.1s; }}
        .card:nth-child(2) {{ animation-delay: 0.2s; }}
        .card:nth-child(3) {{ animation-delay: 0.3s; }}
        .card:nth-child(4) {{ animation-delay: 0.4s; }}

        /* Auto-refresh indicator */
        .refresh-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 30px;
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
            color: var(--secondary-text);
            z-index: 1000;
        }}

        .refresh-indicator.active {{
            border-color: var(--accent-color);
            color: var(--accent-color);
        }}
    </style>
</head>
<body>
    <div class="refresh-indicator">
        <i class="fas fa-sync-alt"></i> Auto-refresh: 5s
    </div>

    <header class="header">
        <div class="header-content">
            <div class="logo">
                <i class="fas fa-microchip"></i>
                <h1>BoarderframeOS</h1>
            </div>
            <div class="system-status">
                <div class="status-indicator">
                    <div class="status-dot {overall_status}"></div>
                    <span>System {overall_status.title()}</span>
                </div>
                <div class="status-indicator">
                    <i class="fas fa-clock"></i>
                    <span>{self.last_update or 'Loading...'}</span>
                </div>
            </div>
        </div>
    </header>

    <div class="container">
        <!-- System Metrics -->
        <div class="card full-width">
            <h3><i class="fas fa-chart-line"></i> System Metrics</h3>
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{self.system_metrics.get('cpu_percent', 0):.1f}%</div>
                    <div class="metric-label">CPU Usage</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{self.system_metrics.get('memory_percent', 0):.1f}%</div>
                    <div class="metric-label">Memory Usage</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{self.system_metrics.get('disk_percent', 0):.1f}%</div>
                    <div class="metric-label">Disk Usage</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{len(self.services_status)}</div>
                    <div class="metric-label">Active Services</div>
                </div>
            </div>
        </div>

        <div class="grid">
            <!-- MCP Services -->
            <div class="card">
                <h3><i class="fas fa-server"></i> MCP Services</h3>
                {self._generate_services_html()}
            </div>

            <!-- Agents -->
            <div class="card">
                <h3><i class="fas fa-robot"></i> AI Agents</h3>
                {self._generate_agents_html()}
            </div>

            <!-- Filesystem Server Details -->
            {self._generate_filesystem_details_html()}
        </div>
    </div>
</body>
</html>"""

    def _generate_services_html(self):
        """Generate enhanced services HTML"""
        if not self.services_status:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No services detected</div>'
        
        services_html = ""
        for service_id, service in self.services_status.items():
            status_class = service.get("status", "critical")
            
            # Special handling for filesystem server
            enhanced_class = "filesystem-enhanced" if service_id == "filesystem" and status_class == "healthy" else ""
            
            response_time = service.get("response_time", 0)
            port = service.get("port", "Unknown")
            
            services_html += f'''
                <div class="service-item {enhanced_class}">
                    <div class="service-info">
                        <div class="service-icon {service_id}">
                            <i class="{service.get('icon', 'fas fa-server')}"></i>
                        </div>
                        <div class="service-details">
                            <h4>{service.get('name', service_id.title())}</h4>
                            <p>Port {port} • {response_time*1000:.0f}ms</p>
                        </div>
                    </div>
                    <div class="service-status {status_class}">
                        <i class="fas fa-circle"></i>
                        {status_class.title()}
                    </div>
                </div>
            '''
        
        return services_html

    def _generate_agents_html(self):
        """Generate enhanced agents HTML"""
        agents_html = ""
        all_agents = ["solomon", "david"]
        
        for agent_id in all_agents:
            if agent_id in self.running_agents:
                # Agent is currently running
                agent = self.running_agents[agent_id]
                agents_html += f'''
                    <div class="agent-card active">
                        <div class="agent-header">
                            <h4 class="agent-name">{agent['name']}</h4>
                            <div class="agent-status running">
                                <i class="fas fa-circle"></i>
                                Running
                            </div>
                        </div>
                        <div class="agent-details">
                            <div><i class="fas fa-microchip"></i> {agent['type']}</div>
                            <div><i class="fas fa-hashtag"></i> PID: {agent['pid']}</div>
                            <div><i class="fas fa-memory"></i> Memory: {agent.get('memory_percent', 0):.1f}%</div>
                            <div><i class="fas fa-tachometer-alt"></i> CPU: {agent.get('cpu_percent', 0):.1f}%</div>
                        </div>
                    </div>
                '''
            else:
                # Agent not found
                agents_html += f'''
                    <div class="agent-card inactive">
                        <div class="agent-header">
                            <h4 class="agent-name">{agent_id.replace('_', ' ').title()}</h4>
                            <div class="agent-status inactive">
                                <i class="fas fa-circle"></i>
                                Offline
                            </div>
                        </div>
                        <div class="agent-details">
                            <div><i class="fas fa-power-off"></i> Not running</div>
                        </div>
                    </div>
                '''
        
        return agents_html or '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No agents configured</div>'

    def _generate_filesystem_details_html(self):
        """Generate detailed filesystem server information"""
        if "filesystem" not in self.mcp_details:
            return ""
        
        details = self.mcp_details["filesystem"]
        
        return f'''
            <div class="card">
                <h3><i class="fas fa-folder-tree"></i> Filesystem Server Details</h3>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">{details.get('total_operations', 0)}</div>
                        <div class="metric-label">Total Operations</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{details.get('active_clients', 0)}</div>
                        <div class="metric-label">Active Clients</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{details.get('vector_db_size', 0)}</div>
                        <div class="metric-label">Vector DB Entries</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{'✓' if details.get('ai_features') else '✗'}</div>
                        <div class="metric-label">AI Features</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                    <div style="font-size: 0.9rem; color: var(--secondary-text);">
                        <div><i class="fas fa-clock"></i> Uptime: {details.get('uptime', 'Unknown')}</div>
                        <div><i class="fas fa-folder"></i> Base Path: {details.get('base_path', '/')}</div>
                    </div>
                </div>
            </div>
        '''

# Global dashboard data instance
dashboard_data = DashboardData()

class EnhancedHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = dashboard_data.generate_dashboard_html()
            self.wfile.write(html_content.encode('utf-8'))
        else:
            super().do_GET()

def signal_handler(sig, frame):
    print("\n🛑 Shutting down dashboard...")
    dashboard_data.running = False
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Enhanced BoarderframeOS Dashboard...")
    print(f"📍 Dashboard URL: http://localhost:{PORT}")
    print("🔄 Real-time updates enabled (3s intervals)")
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
