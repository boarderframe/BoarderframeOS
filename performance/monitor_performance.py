#!/usr/bin/env python3
"""
Real-time Performance Monitoring Script
Monitors BoarderframeOS performance metrics in real-time
"""

import asyncio
import psutil
import time
from datetime import datetime
import json
import os
from collections import deque
import aiohttp
import redis.asyncio as redis
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn
import asyncpg


class PerformanceMonitor:
    """Real-time performance monitoring tool"""
    
    def __init__(self):
        self.console = Console()
        self.metrics_history = {
            "cpu": deque(maxlen=60),
            "memory": deque(maxlen=60),
            "disk_io": deque(maxlen=60),
            "network_io": deque(maxlen=60),
            "agent_response_times": deque(maxlen=100),
            "database_queries": deque(maxlen=100),
            "api_calls": deque(maxlen=100)
        }
        self.mcp_servers = {
            8000: "Registry Server",
            8001: "Filesystem Server",
            8007: "Analytics Server",
            8008: "Customer Server",
            8010: "PostgreSQL Server"
        }
        self.alerts = []
        self.monitoring = True
    
    async def collect_system_metrics(self):
        """Collect system-level metrics"""
        metrics = {
            "timestamp": datetime.now(),
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "per_core": psutil.cpu_percent(interval=0.1, percpu=True),
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used / (1024**3),  # GB
                "available": psutil.virtual_memory().available / (1024**3),  # GB
                "swap_percent": psutil.swap_memory().percent
            },
            "disk": {
                "read_bytes": 0,
                "write_bytes": 0,
                "read_time": 0,
                "write_time": 0
            },
            "network": {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0
            }
        }
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        if disk_io:
            if hasattr(self, '_last_disk_io'):
                metrics["disk"]["read_bytes"] = disk_io.read_bytes - self._last_disk_io.read_bytes
                metrics["disk"]["write_bytes"] = disk_io.write_bytes - self._last_disk_io.write_bytes
            self._last_disk_io = disk_io
        
        # Network I/O
        net_io = psutil.net_io_counters()
        if hasattr(self, '_last_net_io'):
            metrics["network"]["bytes_sent"] = net_io.bytes_sent - self._last_net_io.bytes_sent
            metrics["network"]["bytes_recv"] = net_io.bytes_recv - self._last_net_io.bytes_recv
        self._last_net_io = net_io
        
        return metrics
    
    async def check_mcp_servers(self):
        """Check MCP server health"""
        server_status = {}
        
        async with aiohttp.ClientSession() as session:
            for port, name in self.mcp_servers.items():
                try:
                    start_time = time.time()
                    async with session.get(
                        f"http://localhost:{port}/health",
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        if response.status == 200:
                            server_status[name] = {
                                "status": "healthy",
                                "response_time": response_time
                            }
                        else:
                            server_status[name] = {
                                "status": "unhealthy",
                                "response_time": response_time
                            }
                except:
                    server_status[name] = {
                        "status": "offline",
                        "response_time": None
                    }
        
        return server_status
    
    async def check_database_performance(self):
        """Check database performance metrics"""
        db_metrics = {
            "postgresql": {
                "connections": 0,
                "active_queries": 0,
                "cache_hit_ratio": 0,
                "avg_query_time": 0
            },
            "redis": {
                "connected_clients": 0,
                "used_memory": 0,
                "ops_per_sec": 0,
                "hit_rate": 0
            }
        }
        
        # PostgreSQL metrics
        try:
            conn = await asyncpg.connect(
                host='localhost',
                port=5434,
                user='boarderframe',
                password='securepass123',
                database='boarderframeos'
            )
            
            # Connection count
            result = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            db_metrics["postgresql"]["connections"] = result
            
            # Cache hit ratio
            cache_result = await conn.fetchrow("""
                SELECT 
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
                FROM pg_statio_user_tables
            """)
            if cache_result and cache_result['ratio']:
                db_metrics["postgresql"]["cache_hit_ratio"] = float(cache_result['ratio'])
            
            await conn.close()
        except:
            pass
        
        # Redis metrics
        try:
            r = await redis.from_url("redis://localhost:6379")
            info = await r.info()
            
            db_metrics["redis"]["connected_clients"] = info.get("connected_clients", 0)
            db_metrics["redis"]["used_memory"] = info.get("used_memory", 0) / (1024**2)  # MB
            db_metrics["redis"]["ops_per_sec"] = info.get("instantaneous_ops_per_sec", 0)
            
            # Calculate hit rate
            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            if keyspace_hits + keyspace_misses > 0:
                db_metrics["redis"]["hit_rate"] = keyspace_hits / (keyspace_hits + keyspace_misses)
            
            await r.close()
        except:
            pass
        
        return db_metrics
    
    async def check_agent_performance(self):
        """Check agent performance metrics"""
        # This would connect to actual agent monitoring
        # For now, return simulated data
        agent_metrics = {
            "active_agents": 5,
            "avg_response_time": 150.5,  # ms
            "messages_processed": 1234,
            "errors": 2,
            "agent_status": {
                "Solomon": {"status": "active", "cpu": 15.2, "memory": 256},
                "David": {"status": "active", "cpu": 12.8, "memory": 198},
                "Adam": {"status": "active", "cpu": 18.5, "memory": 312},
                "Eve": {"status": "idle", "cpu": 2.1, "memory": 128},
                "Bezalel": {"status": "active", "cpu": 25.3, "memory": 412}
            }
        }
        
        return agent_metrics
    
    def check_alerts(self, metrics):
        """Check for performance alerts"""
        alerts = []
        
        # CPU alert
        if metrics["cpu"]["percent"] > 80:
            alerts.append({
                "level": "warning",
                "message": f"High CPU usage: {metrics['cpu']['percent']:.1f}%",
                "timestamp": datetime.now()
            })
        
        # Memory alert
        if metrics["memory"]["percent"] > 85:
            alerts.append({
                "level": "critical",
                "message": f"High memory usage: {metrics['memory']['percent']:.1f}%",
                "timestamp": datetime.now()
            })
        
        # Disk I/O alert (if write is very high)
        if metrics["disk"]["write_bytes"] > 100 * 1024 * 1024:  # 100MB/s
            alerts.append({
                "level": "warning",
                "message": f"High disk write: {metrics['disk']['write_bytes'] / (1024**2):.1f} MB/s",
                "timestamp": datetime.now()
            })
        
        return alerts
    
    def create_dashboard_layout(self):
        """Create dashboard layout"""
        layout = Layout(name="root")
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split(
            Layout(name="system"),
            Layout(name="database")
        )
        
        layout["right"].split(
            Layout(name="servers"),
            Layout(name="agents")
        )
        
        return layout
    
    def create_system_table(self, metrics):
        """Create system metrics table"""
        table = Table(title="System Metrics", expand=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        # CPU
        cpu_status = "🟢" if metrics["cpu"]["percent"] < 70 else "🟡" if metrics["cpu"]["percent"] < 85 else "🔴"
        table.add_row(
            "CPU Usage",
            f"{metrics['cpu']['percent']:.1f}%",
            cpu_status
        )
        
        # Memory
        mem_status = "🟢" if metrics["memory"]["percent"] < 70 else "🟡" if metrics["memory"]["percent"] < 85 else "🔴"
        table.add_row(
            "Memory Usage",
            f"{metrics['memory']['percent']:.1f}% ({metrics['memory']['used']:.1f}GB used)",
            mem_status
        )
        
        # Disk I/O
        disk_read = metrics["disk"]["read_bytes"] / (1024**2)  # MB/s
        disk_write = metrics["disk"]["write_bytes"] / (1024**2)  # MB/s
        table.add_row(
            "Disk I/O",
            f"R: {disk_read:.1f} MB/s, W: {disk_write:.1f} MB/s",
            "🟢"
        )
        
        # Network
        net_in = metrics["network"]["bytes_recv"] / (1024**2)  # MB/s
        net_out = metrics["network"]["bytes_sent"] / (1024**2)  # MB/s
        table.add_row(
            "Network I/O",
            f"In: {net_in:.1f} MB/s, Out: {net_out:.1f} MB/s",
            "🟢"
        )
        
        return table
    
    def create_server_table(self, server_status):
        """Create MCP server status table"""
        table = Table(title="MCP Server Status", expand=True)
        table.add_column("Server", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Response Time", style="yellow")
        
        for name, status in server_status.items():
            status_icon = "🟢" if status["status"] == "healthy" else "🔴"
            response_time = f"{status['response_time']:.1f}ms" if status['response_time'] else "N/A"
            
            table.add_row(
                name,
                f"{status_icon} {status['status']}",
                response_time
            )
        
        return table
    
    def create_database_table(self, db_metrics):
        """Create database metrics table"""
        table = Table(title="Database Performance", expand=True)
        table.add_column("Database", style="cyan")
        table.add_column("Metric", style="green")
        table.add_column("Value", style="yellow")
        
        # PostgreSQL
        table.add_row(
            "PostgreSQL",
            "Connections",
            str(db_metrics["postgresql"]["connections"])
        )
        table.add_row(
            "",
            "Cache Hit Ratio",
            f"{db_metrics['postgresql']['cache_hit_ratio']*100:.1f}%"
        )
        
        # Redis
        table.add_row(
            "Redis",
            "Connected Clients",
            str(db_metrics["redis"]["connected_clients"])
        )
        table.add_row(
            "",
            "Memory Usage",
            f"{db_metrics['redis']['used_memory']:.1f} MB"
        )
        table.add_row(
            "",
            "Ops/sec",
            str(db_metrics["redis"]["ops_per_sec"])
        )
        
        return table
    
    def create_agent_table(self, agent_metrics):
        """Create agent performance table"""
        table = Table(title="Agent Performance", expand=True)
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("CPU %", style="yellow")
        table.add_column("Memory MB", style="yellow")
        
        for agent, metrics in agent_metrics["agent_status"].items():
            status_icon = "🟢" if metrics["status"] == "active" else "🟡"
            table.add_row(
                agent,
                f"{status_icon} {metrics['status']}",
                f"{metrics['cpu']:.1f}",
                str(metrics["memory"])
            )
        
        return table
    
    async def update_dashboard(self, layout):
        """Update dashboard with latest metrics"""
        # Collect all metrics
        system_metrics = await self.collect_system_metrics()
        server_status = await self.check_mcp_servers()
        db_metrics = await self.check_database_performance()
        agent_metrics = await self.check_agent_performance()
        
        # Check for alerts
        new_alerts = self.check_alerts(system_metrics)
        self.alerts.extend(new_alerts)
        
        # Update history
        self.metrics_history["cpu"].append(system_metrics["cpu"]["percent"])
        self.metrics_history["memory"].append(system_metrics["memory"]["percent"])
        
        # Update layout
        layout["header"].update(
            Panel(
                f"[bold]BoarderframeOS Performance Monitor[/bold] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style="blue"
            )
        )
        
        layout["system"].update(self.create_system_table(system_metrics))
        layout["servers"].update(self.create_server_table(server_status))
        layout["database"].update(self.create_database_table(db_metrics))
        layout["agents"].update(self.create_agent_table(agent_metrics))
        
        # Footer with alerts
        alert_text = "No alerts" if not self.alerts else f"{len(self.alerts)} alerts"
        layout["footer"].update(
            Panel(
                f"Press 'q' to quit | 's' to save snapshot | {alert_text}",
                style="dim"
            )
        )
    
    async def save_snapshot(self):
        """Save performance snapshot"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "metrics_history": {
                "cpu": list(self.metrics_history["cpu"]),
                "memory": list(self.metrics_history["memory"])
            },
            "alerts": [
                {
                    "level": alert["level"],
                    "message": alert["message"],
                    "timestamp": alert["timestamp"].isoformat()
                }
                for alert in self.alerts[-10:]  # Last 10 alerts
            ]
        }
        
        snapshot_path = f"performance/snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("performance", exist_ok=True)
        
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        self.console.print(f"[green]Snapshot saved to {snapshot_path}[/green]")
    
    async def run_monitor(self):
        """Run the performance monitor"""
        self.console.print("[bold green]Starting BoarderframeOS Performance Monitor...[/bold green]")
        
        layout = self.create_dashboard_layout()
        
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while self.monitoring:
                try:
                    await self.update_dashboard(layout)
                    await asyncio.sleep(1)
                    
                    # Check for keyboard input (non-blocking)
                    # In a real implementation, you'd use a proper async input handler
                    
                except KeyboardInterrupt:
                    self.monitoring = False
                except Exception as e:
                    self.console.print(f"[red]Error: {e}[/red]")
                    await asyncio.sleep(1)
        
        self.console.print("[bold green]Performance monitor stopped.[/bold green]")


async def main():
    """Main entry point"""
    monitor = PerformanceMonitor()
    
    try:
        await monitor.run_monitor()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        await monitor.save_snapshot()


if __name__ == "__main__":
    asyncio.run(main())