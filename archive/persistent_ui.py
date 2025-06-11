#!/usr/bin/env python3
"""
Enhanced BoarderframeOS Dashboard with Real-Time Status
"""
import asyncio
import http.server
import json
import os
import signal
import socketserver
import sys
import threading
import time
from datetime import datetime

import httpx

PORT = 8888


class DashboardData:
    """Manages dashboard data updates"""

    def __init__(self):
        self.services_status = {}
        self.agents_status = {}
        self.system_metrics = {}
        self.health_status = {}
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

    async def _async_update(self):
        """Async update of all data"""
        async with httpx.AsyncClient(timeout=2.0) as client:
            # Update services status
            await self._update_services(client)

            # Update agents status
            await self._update_agents(client)

            # Update system metrics
            await self._update_metrics(client)

            # Load health check data if available
            self._load_health_data()

            self.last_update = datetime.now()

    async def _update_services(self, client):
        """Update MCP services status"""
        services = [
            ("MCP Registry", 8000),
            ("Filesystem Server", 8001),
            ("Database Server", 8004),
            ("LLM Server", 8005),
            ("UI Dashboard", 8888),
        ]

        for service_name, port in services:
            try:
                response = await client.get(f"http://localhost:{port}/health")
                self.services_status[service_name] = {
                    "status": "online" if response.status_code == 200 else "offline",
                    "port": port,
                }
            except:
                self.services_status[service_name] = {"status": "offline", "port": port}

    async def _update_agents(self, client):
        """Update agents status from database"""
        try:
            response = await client.post(
                "http://localhost:8004/query",
                json={
                    "sql": "SELECT id, name, status, biome, generation, fitness_score FROM agents",
                    "fetch_all": True,
                },
            )

            if response.status_code == 200 and response.json().get("success"):
                agents_data = response.json().get("data", [])

                for agent in agents_data:
                    self.agents_status[agent["id"]] = {
                        "name": agent["name"],
                        "status": agent["status"],
                        "biome": agent["biome"],
                        "generation": agent["generation"],
                        "fitness": agent["fitness_score"],
                    }
        except:
            pass  # Database might not be available

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
            "online_services": sum(
                1 for s in self.services_status.values() if s["status"] == "online"
            ),
            "total_agents": len(self.agents_status),
            "active_agents": sum(
                1 for a in self.agents_status.values() if a["status"] == "active"
            ),
        }

    def _load_health_data(self):
        """Load health check data if available"""
        try:
            health_file = "/tmp/boarderframe_health.json"
            if os.path.exists(health_file):
                with open(health_file, "r") as f:
                    self.health_status = json.load(f)
        except:
            pass

    def get_dashboard_html(self):
        """Generate dashboard HTML with current data"""
        # Services status HTML
        services_html = ""
        for service, status in self.services_status.items():
            status_class = "online" if status["status"] == "online" else "offline"
            icon = "✓" if status["status"] == "online" else "✗"
            services_html += f"""
                <div class="service-item">
                    <span class="status-icon {status_class}">{icon}</span>
                    <span class="service-name">{service}</span>
                    <span class="service-port">Port {status['port']}</span>
                </div>"""

        # Agents status HTML
        agents_html = ""
        core_agents = ["solomon", "david", "adam", "eve", "bezalel"]

        for agent_id in core_agents:
            if agent_id in self.agents_status:
                agent = self.agents_status[agent_id]
                status_class = "active" if agent["status"] == "active" else "inactive"
                agents_html += f"""
                    <div class="agent-card">
                        <h4>{agent['name']}</h4>
                        <div class="agent-status {status_class}">{agent['status'].upper()}</div>
                        <div class="agent-details">
                            <div>Biome: {agent['biome']}</div>
                            <div>Generation: {agent['generation']}</div>
                            <div>Fitness: {agent['fitness']:.2f}</div>
                        </div>
                    </div>"""
            else:
                agents_html += f"""
                    <div class="agent-card inactive">
                        <h4>{agent_id.capitalize()}</h4>
                        <div class="agent-status">NOT DEPLOYED</div>
                    </div>"""

        # System metrics
        metrics = self.system_metrics.get("summary", {})

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                html = dashboard_data.get_dashboard_html()
                self.wfile.write(html.encode())

            elif self.path == "/health":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                health_data = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "services": dashboard_data.services_status,
                    "agents": len(dashboard_data.agents_status),
                }
                self.wfile.write(json.dumps(health_data).encode())

            elif self.path == "/api/status":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                status = {
                    "services": dashboard_data.services_status,
                    "agents": dashboard_data.agents_status,
                    "metrics": dashboard_data.system_metrics,
                    "health": dashboard_data.health_status,
                    "last_update": (
                        dashboard_data.last_update.isoformat()
                        if dashboard_data.last_update
                        else None
                    ),
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
