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
        """Start background data updates with immediate initial update"""
        # Run initial update immediately
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_update())
            loop.close()
        except Exception as e:
            print(f"Initial update error: {e}")
        
        # Start background update thread
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
            time.sleep(30)  # Update every 30 seconds
    
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
            "dashboard": {"port": 8888, "name": "Dashboard", "icon": "fas fa-chart-line"},
            "filesystem": {"port": 8001, "name": "File System Server", "icon": "fas fa-folder-tree"},
            "database": {"port": 8004, "name": "Database Server", "icon": "fas fa-database"},
            "llm": {"port": 8005, "name": "LLM Server", "icon": "fas fa-brain"},
            "registry": {"port": 8000, "name": "Registry Server", "icon": "fas fa-server"}
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
        
        # Enhanced system status with more information
        if total_services == 0:
            overall_status = "initializing"
            status_text = "System Initializing"
        elif healthy_services == total_services and total_services > 0:
            overall_status = "online"
            status_text = f"System Online ({healthy_services}/{total_services} services)"
        elif healthy_services > 0:
            overall_status = "warning"
            status_text = f"System Partial ({healthy_services}/{total_services} services)"
        else:
            overall_status = "offline"
            status_text = "System Offline"
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Control Center</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

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
            opacity: 0;
            transition: opacity 0.5s ease;
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
        .status-dot.initializing {{ 
            background: #3b82f6; 
            animation: pulse 1s infinite;
        }}

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
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        /* Section spacing */
        .section-separator {{
            margin: 3rem 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border-color), transparent);
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
            transition: all 0.3s ease;
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
            transition: all 0.3s ease;
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

        /* MCP Server colored borders */
        .server-registry {{
            border-left: 4px solid #6366f1 !important;
        }}

        .server-filesystem {{
            border-left: 4px solid #10b981 !important;
        }}

        .server-database {{
            border-left: 4px solid #f59e0b !important;
        }}

        .server-llm {{
            border-left: 4px solid #8b5cf6 !important;
        }}

        .server-dashboard {{
            border-left: 4px solid #ef4444 !important;
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
            transition: all 0.3s ease;
        }}

        .refresh-indicator.refreshing {{
            border-color: var(--accent-color);
            color: var(--accent-color);
            box-shadow: 0 0 20px var(--glow-color);
        }}

        .content-updating {{
            opacity: 0.7;
            transition: opacity 0.3s ease;
        }}

        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}

        .updating {{
            animation: pulse 0.5s ease-in-out;
        }}

        /* Enhanced Agent Cards */
        .enhanced-agent-card {{
            display: flex;
            align-items: flex-start;
            gap: 1.2rem;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }}

        .enhanced-agent-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}

        .agent-avatar {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-color), #4f46e5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            color: white;
            flex-shrink: 0;
        }}

        .agent-avatar.offline {{
            background: linear-gradient(135deg, var(--border-color), #374151);
            opacity: 0.6;
        }}

        .agent-info {{
            flex: 1;
        }}

        .agent-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}

        .agent-name {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-text);
            margin: 0;
        }}

        .agent-status-badge {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}

        .agent-status-badge.running {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .agent-status-badge.offline {{
            background: rgba(107, 114, 128, 0.2);
            color: var(--secondary-text);
            border: 1px solid var(--border-color);
        }}

        .agent-meta {{
            display: flex;
            gap: 1rem;
            margin-bottom: 0.8rem;
            font-size: 0.9rem;
            color: var(--secondary-text);
        }}

        .agent-type {{
            font-weight: 500;
        }}

        .agent-metrics {{
            display: flex;
            gap: 0.8rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}

        .metric-chip {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.3rem 0.6rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            font-size: 0.8rem;
            color: var(--secondary-text);
        }}

        .agent-capabilities {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }}

        .capability-tag {{
            padding: 0.2rem 0.6rem;
            background: rgba(99, 102, 241, 0.2);
            color: var(--accent-color);
            border-radius: 15px;
            font-size: 0.8rem;
            border: 1px solid var(--accent-color);
        }}

        .capability-tag.disabled {{
            background: rgba(107, 114, 128, 0.2);
            color: var(--secondary-text);
            border-color: var(--border-color);
        }}

        .agent-actions {{
            margin-top: 1rem;
        }}

        .start-agent-btn {{
            padding: 0.5rem 1rem;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }}

        .start-agent-btn:hover {{
            background: #4f46e5;
            transform: translateY(-1px);
        }}

        /* Enhanced Service Cards */
        .enhanced-service-card {{
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }}

        .enhanced-service-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}

        .service-header {{
            display: flex;
            align-items: center;
            gap: 1.2rem;
            margin-bottom: 1rem;
        }}

        .service-icon-large {{
            width: 50px;
            height: 50px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            flex-shrink: 0;
        }}

        .service-main-info {{
            flex: 1;
        }}

        .service-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-text);
            margin: 0 0 0.3rem 0;
        }}

        .service-meta {{
            display: flex;
            gap: 1rem;
            font-size: 0.9rem;
            color: var(--secondary-text);
        }}

        .service-meta span {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}

        .service-status-badge {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            flex-shrink: 0;
        }}

        .service-status-badge.healthy {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .service-status-badge.warning {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }}

        .service-status-badge.critical {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }}

        .service-tools {{
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
        }}

        .tools-label {{
            font-size: 0.9rem;
            color: var(--secondary-text);
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}

        .tool-charms {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .tool-charm {{
            padding: 0.3rem 0.8rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            font-size: 0.8rem;
            color: var(--secondary-text);
            transition: all 0.2s ease;
        }}

        .tool-charm:hover {{
            background: rgba(99, 102, 241, 0.2);
            border-color: var(--accent-color);
            color: var(--accent-color);
        }}
    </style>
</head>
<body>
    <div class="refresh-indicator">
        <i class="fas fa-sync-alt"></i> Auto-refresh: 30s
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
                    <span>{status_text}</span>
                </div>
                <div class="status-indicator">
                    <i class="fas fa-clock"></i>
                    <span>{self.last_update.strftime('%H:%M:%S') if self.last_update else datetime.now().strftime('%H:%M:%S')}</span>
                </div>
            </div>
        </div>
    </header>        <div class="container">
        <!-- Welcome Section -->
        <div class="card full-width">
            <h3><i class="fas fa-home"></i> Welcome to BoarderframeOS</h3>
            <div style="padding: 1rem; background: rgba(99, 102, 241, 0.1); border-radius: 12px; border-left: 4px solid var(--accent-color);">
                <h4 style="margin: 0 0 1rem 0; color: var(--accent-color);">
                    <i class="fas fa-user"></i> Hello Carl
                </h4>
                <p style="margin: 0 0 1rem 0; font-size: 1rem; line-height: 1.6; color: var(--primary-text);">
                    Welcome to your BoarderframeOS Control Center. Your intelligent agent ecosystem is {overall_status.replace('_', ' ')}, 
                    with {healthy_services} of {total_services} core services operational. 
                    The system is equipped with advanced MCP (Model Context Protocol) servers providing file operations, 
                    database management, AI processing, and service coordination capabilities.
                </p>
                <p style="margin: 0; font-size: 0.95rem; color: var(--secondary-text);">
                    <i class="fas fa-lightbulb"></i> 
                    Your AI agents Solomon and David are standing by, ready to assist with strategic planning, 
                    research tasks, and system management. All systems are being monitored in real-time for optimal performance.
                </p>
            </div>
        </div>

        <div class="section-separator"></div>

        <!-- AI Agents -->
        <div class="card full-width">
            <h3><i class="fas fa-robot"></i> AI Agents</h3>
            {self._generate_enhanced_agents_html()}
        </div>

        <div class="section-separator"></div>

        <!-- MCP Servers -->
        <div class="card full-width">
            <h3><i class="fas fa-server"></i> MCP Servers</h3>
            {self._generate_enhanced_services_html()}
        </div>

        <div class="section-separator"></div>

        <!-- MCP Server Details -->
        <div class="card full-width">
            <h3><i class="fas fa-cogs"></i> MCP Server Details</h3>
            <div class="grid">
                {self._generate_detailed_server_widgets()}
            </div>
        </div>

        <div class="section-separator"></div>

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
    </div>

    <script>
        // Non-intrusive AJAX refresh system
        let refreshCounter = 30;
        let refreshInterval;
        let isRefreshing = false;
        
        function updateRefreshDisplay() {{
            const indicator = document.querySelector('.refresh-indicator');
            if (indicator) {{
                indicator.innerHTML = `<i class="fas fa-sync-alt ${{isRefreshing ? 'fa-spin' : ''}}"></i> Auto-refresh: ${{refreshCounter}}s`;
                if (isRefreshing) {{
                    indicator.classList.add('refreshing');
                }} else {{
                    indicator.classList.remove('refreshing');
                }}
            }}
        }}
        
        async function refreshContent() {{
            if (isRefreshing) return;
            
            isRefreshing = true;
            updateRefreshDisplay();
            
            // Add subtle updating effect
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {{
                mainContent.classList.add('updating');
            }}
            
            try {{
                const response = await fetch(window.location.href);
                if (response.ok) {{
                    const html = await response.text();
                    const parser = new DOMParser();
                    const newDoc = parser.parseFromString(html, 'text/html');
                    
                    // Update main content areas without full page reload
                    const contentSelectors = ['.grid', '.agents-grid'];
                    contentSelectors.forEach(selector => {{
                        const oldElement = document.querySelector(selector);
                        const newElement = newDoc.querySelector(selector);
                        if (oldElement && newElement) {{
                            oldElement.innerHTML = newElement.innerHTML;
                        }}
                    }});
                    
                    // Update system metrics
                    const metricsElement = document.querySelector('.metrics-grid');
                    const newMetrics = newDoc.querySelector('.metrics-grid');
                    if (metricsElement && newMetrics) {{
                        metricsElement.innerHTML = newMetrics.innerHTML;
                    }}
                }}
            }} catch (error) {{
                console.warn('Refresh failed:', error);
                // Fallback to full page refresh if AJAX fails
                window.location.reload();
            }} finally {{
                isRefreshing = false;
                updateRefreshDisplay();
                
                // Remove updating effect
                const mainContent = document.querySelector('.main-content');
                if (mainContent) {{
                    mainContent.classList.remove('updating');
                }}
            }}
        }}
        
        function startRefreshCountdown() {{
            refreshInterval = setInterval(() => {{
                refreshCounter--;
                updateRefreshDisplay();
                
                if (refreshCounter <= 0) {{
                    refreshContent();
                    refreshCounter = 30;
                }}
            }}, 1000);
        }}
        
        // Reset refresh timer on user interaction
        function resetRefreshTimer() {{
            refreshCounter = 30;
            updateRefreshDisplay();
        }}
        
        // Agent management function
        function startAgent(agentId) {{
            // This would eventually call an API endpoint to start the agent
            alert(`Starting agent: ${{agentId}}. This feature will be implemented soon!`);
        }}
        
        // Start the refresh system
        document.addEventListener('DOMContentLoaded', () => {{
            document.body.style.opacity = '1';
            updateRefreshDisplay();
            startRefreshCountdown();
            
            // Reset timer on user interactions
            ['click', 'scroll', 'keypress', 'mousemove'].forEach(event => {{
                document.addEventListener(event, resetRefreshTimer, {{ passive: true, once: false }});
            }});
        }});
    </script>
</body>
</html>"""

    def _generate_services_html(self):
        """Generate enhanced services HTML"""
        if not self.services_status:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No services detected</div>'
        
        services_html = ""
        for service_id, service in self.services_status.items():
            status_class = service.get("status", "critical")
            
            # Add colored border class for each server
            border_class = f"server-{service_id}"
            
            response_time = service.get("response_time", 0)
            port = service.get("port", "Unknown")
            
            services_html += f'''
                <div class="service-item {border_class}">
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

    def _generate_enhanced_services_html(self):
        """Generate enhanced services HTML with tool charms"""
        if not self.services_status:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No services detected</div>'
        
        # Define tools/capabilities for each MCP server
        server_tools = {
            "registry": {
                "tools": ["🔍 Service Discovery", "📋 Health Monitoring", "🔗 Service Registry", "🎯 Load Balancing"],
                "color": "#8B5CF6"
            },
            "filesystem": {
                "tools": ["📁 File Operations", "🔍 Smart Search", "📊 Content Analysis", "🗂️ Directory Management"],
                "color": "#10B981"
            },
            "database": {
                "tools": ["💾 Data Storage", "🔍 Query Engine", "📈 Analytics", "🔐 Data Security"],
                "color": "#F59E0B"
            },
            "llm": {
                "tools": ["🧠 AI Processing", "💬 Chat Interface", "📝 Text Generation", "🔄 Model Management"],
                "color": "#EF4444"
            }
        }
        
        services_html = ""
        for service_id, service in self.services_status.items():
            status_class = service.get("status", "critical")
            border_class = f"server-{service_id}"
            response_time = service.get("response_time", 0)
            port = service.get("port", "Unknown")
            tools = server_tools.get(service_id, {"tools": ["🔧 General Tools"], "color": "#6B7280"})
            
            # Generate tool charms
            tool_charms = ""
            for tool in tools["tools"]:
                tool_charms += f'<div class="tool-charm">{tool}</div>'
            
            services_html += f'''
                <div class="enhanced-service-card {border_class}">
                    <div class="service-header">
                        <div class="service-icon-large {service_id}">
                            <i class="{service.get('icon', 'fas fa-server')}"></i>
                        </div>
                        <div class="service-main-info">
                            <h4 class="service-title">{service.get('name', service_id.title())}</h4>
                            <div class="service-meta">
                                <span class="service-port"><i class="fas fa-network-wired"></i> Port {port}</span>
                                <span class="service-response"><i class="fas fa-clock"></i> {response_time*1000:.0f}ms</span>
                            </div>
                        </div>
                        <div class="service-status-badge {status_class}">
                            <i class="fas fa-circle"></i>
                            <span>{status_class.title()}</span>
                        </div>
                    </div>
                    <div class="service-tools">
                        <div class="tools-label">Available Tools:</div>
                        <div class="tool-charms">
                            {tool_charms}
                        </div>
                    </div>
                </div>
            '''
        
        return services_html

    def _generate_enhanced_agents_html(self):
        """Generate enhanced agents HTML with detailed UI"""
        agents_html = ""
        all_agents = ["solomon", "david"]
        
        for agent_id in all_agents:
            if agent_id in self.running_agents:
                # Agent is currently running
                agent = self.running_agents[agent_id]
                agents_html += f'''
                    <div class="enhanced-agent-card active">
                        <div class="agent-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="agent-info">
                            <div class="agent-header">
                                <h4 class="agent-name">{agent['name']}</h4>
                                <div class="agent-status-badge running">
                                    <i class="fas fa-circle"></i>
                                    <span>Active</span>
                                </div>
                            </div>
                            <div class="agent-meta">
                                <span class="agent-type">{agent['type']}</span>
                                <span class="agent-uptime">Uptime: {agent.get('uptime', 'Unknown')}</span>
                            </div>
                            <div class="agent-metrics">
                                <div class="metric-chip">
                                    <i class="fas fa-hashtag"></i>
                                    <span>PID: {agent['pid']}</span>
                                </div>
                                <div class="metric-chip">
                                    <i class="fas fa-memory"></i>
                                    <span>{agent.get('memory_percent', 0):.1f}% RAM</span>
                                </div>
                                <div class="metric-chip">
                                    <i class="fas fa-microchip"></i>
                                    <span>{agent.get('cpu_percent', 0):.1f}% CPU</span>
                                </div>
                            </div>
                            <div class="agent-capabilities">
                                <div class="capability-tag">💬 Chat Processing</div>
                                <div class="capability-tag">🧠 AI Reasoning</div>
                                <div class="capability-tag">📝 Task Management</div>
                            </div>
                        </div>
                    </div>
                '''
            else:
                # Agent not found
                agent_name = agent_id.replace('_', ' ').title()
                capabilities = {
                    "solomon": ["🧠 Strategic Planning", "📊 System Analysis", "🔧 Problem Solving"],
                    "david": ["💬 Communication", "📝 Documentation", "🎯 Task Execution"]
                }
                
                agents_html += f'''
                    <div class="enhanced-agent-card inactive">
                        <div class="agent-avatar offline">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="agent-info">
                            <div class="agent-header">
                                <h4 class="agent-name">{agent_name}</h4>
                                <div class="agent-status-badge offline">
                                    <i class="fas fa-circle"></i>
                                    <span>Offline</span>
                                </div>
                            </div>
                            <div class="agent-meta">
                                <span class="agent-type">AI Assistant</span>
                                <span class="agent-uptime">Ready to start</span>
                            </div>
                            <div class="agent-capabilities">
                                {"".join([f'<div class="capability-tag disabled">{cap}</div>' for cap in capabilities.get(agent_id, ["🤖 AI Assistant"])])}
                            </div>
                            <div class="agent-actions">
                                <button class="start-agent-btn" onclick="startAgent('{agent_id}')">
                                    <i class="fas fa-play"></i> Start Agent
                                </button>
                            </div>
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
                        <div class="metric-label">Smart Analysis</div>
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

    def _generate_detailed_server_widgets(self):
        """Generate detailed widgets for each MCP server"""
        widgets_html = ""
        
        for service_id, service in self.services_status.items():
            if service.get("status") != "healthy":
                continue
                
            status_class = service.get("status", "critical")
            border_class = f"server-{service_id}"
            
            # Generate specific widget content based on server type
            if service_id == "filesystem":
                widget_content = self._generate_filesystem_widget_content()
                # Use proper title for File System Server
                server_title = "File System Server Details"
            elif service_id == "registry":
                widget_content = self._generate_registry_widget_content()
                server_title = f"{service.get('name', service_id.title())} Details"
            elif service_id == "database":
                widget_content = self._generate_database_widget_content()
                server_title = f"{service.get('name', service_id.title())} Details"
            elif service_id == "llm":
                widget_content = self._generate_llm_widget_content()
                server_title = f"{service.get('name', service_id.title())} Details"
            else:
                widget_content = self._generate_generic_widget_content(service)
                server_title = f"{service.get('name', service_id.title())} Details"
            
            widgets_html += f'''
                <div class="card {border_class}">
                    <h3>
                        <i class="{service.get('icon', 'fas fa-server')}"></i> 
                        {server_title}
                    </h3>
                    {widget_content}
                </div>
            '''
        
        return widgets_html

    def _generate_filesystem_widget_content(self):
        """Generate detailed filesystem server widget content"""
        if "filesystem" not in self.mcp_details:
            # If no MCP details, try to get basic service info
            fs_service = self.services_status.get("filesystem", {})
            if not fs_service:
                return '<div style="text-align: center; color: var(--secondary-text); padding: 1rem;">File System Server not available</div>'
            
            # Show basic info if detailed data is not available
            return f'''
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">{fs_service.get("port", "Unknown")}</div>
                        <div class="metric-label">Port</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{fs_service.get("response_time", 0)*1000:.0f}ms</div>
                        <div class="metric-label">Response Time</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{"✅" if fs_service.get("status") == "healthy" else "❌"}</div>
                        <div class="metric-label">Status</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">Ready</div>
                        <div class="metric-label">State</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border-left: 3px solid var(--success-color);">
                    <h4 style="margin: 0 0 0.5rem 0; color: var(--success-color);">
                        <i class="fas fa-folder-tree"></i> File System Operations
                    </h4>
                    <p style="margin: 0; color: var(--secondary-text); font-size: 0.9rem;">
                        Provides file operations, directory management, and AI-powered content analysis capabilities.
                    </p>
                </div>
            '''
        
        details = self.mcp_details["filesystem"]
        return f'''
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{details.get("total_operations", 0)}</div>
                    <div class="metric-label">Total Operations</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("active_clients", 0)}</div>
                    <div class="metric-label">Active Clients</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{"✅" if details.get("ai_features") else "❌"}</div>
                    <div class="metric-label">Smart Analysis</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("vector_db_size", 0)}</div>
                    <div class="metric-label">Vector DB Entries</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border-left: 3px solid var(--success-color);">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--success-color);">
                    <i class="fas fa-folder"></i> Configuration
                </h4>
                <div style="font-size: 0.9rem; color: var(--secondary-text);">
                    <div style="margin-bottom: 0.3rem;"><i class="fas fa-clock"></i> Uptime: {details.get('uptime', 'Unknown')}</div>
                    <div><i class="fas fa-folder-open"></i> Base Path: <code style="color: var(--primary-text); background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;">{details.get("base_path", "/")}</code></div>
                </div>
            </div>
        '''

    def _generate_registry_widget_content(self):
        """Generate registry server widget content"""
        registry_service = self.services_status.get("registry", {})
        details = registry_service.get("details", {})
        
        return f'''
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{details.get("registered_services", 0)}</div>
                    <div class="metric-label">Registered Services</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("active_connections", 0)}</div>
                    <div class="metric-label">Active Connections</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("uptime", "Unknown")}</div>
                    <div class="metric-label">Uptime</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">✅</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-network-wired"></i> Service Registry
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">Central coordination hub for all MCP services</p>
            </div>
        '''

    def _generate_database_widget_content(self):
        """Generate database server widget content"""
        db_service = self.services_status.get("database", {})
        details = db_service.get("details", {})
        
        return f'''
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{details.get("total_queries", 0)}</div>
                    <div class="metric-label">Total Queries</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("active_connections", 0)}</div>
                    <div class="metric-label">Active Connections</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("database_size", "Unknown")}</div>
                    <div class="metric-label">Database Size</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">✅</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-database"></i> Data Storage
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">Persistent storage for agent data and system state</p>
            </div>
        '''

    def _generate_llm_widget_content(self):
        """Generate LLM server widget content"""
        llm_service = self.services_status.get("llm", {})
        details = llm_service.get("details", {})
        
        return f'''
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{details.get("total_requests", 0)}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("active_sessions", 0)}</div>
                    <div class="metric-label">Active Sessions</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("model", "Unknown")}</div>
                    <div class="metric-label">Active Model</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">✅</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-brain"></i> AI Processing
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">Large Language Model inference and AI capabilities</p>
            </div>
        '''

    def _generate_generic_widget_content(self, service):
        """Generate generic widget content for unknown services"""
        details = service.get("details", {})
        
        return f'''
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{service.get("port", "Unknown")}</div>
                    <div class="metric-label">Port</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{service.get("response_time", 0)*1000:.0f}ms</div>
                    <div class="metric-label">Response Time</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">✅</div>
                    <div class="metric-label">Status</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("uptime", "Unknown")}</div>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-server"></i> Service Details
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">MCP service running on port {service.get("port", "Unknown")}</p>
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
        elif self.path == "/health":
            # Health endpoint for the dashboard itself
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                "status": "healthy",
                "uptime": "Active",
                "service": "BoarderframeOS Dashboard",
                "port": PORT,
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(health_data).encode('utf-8'))
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
    print("🔄 Real-time updates enabled (30s intervals)")
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
