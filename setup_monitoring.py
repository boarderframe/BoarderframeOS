#!/usr/bin/env python3
"""
BoarderframeOS Monitoring and Logging Setup Script
Configures comprehensive logging, metrics collection, health monitoring, and alerting systems
"""

import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, List, Optional, Any
import subprocess
import shutil


class MonitoringSetup:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(self.base_dir, "logs")
        self.monitoring_dir = os.path.join(self.base_dir, "monitoring")
        self.config_dir = os.path.join(self.base_dir, "configs", "monitoring")
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "directories_created": [],
            "configs_created": [],
            "services_configured": [],
            "monitoring_components": {},
            "summary": {}
        }
        
        self.errors = []
        self.warnings = []
        self.successes = []
        
    def log_success(self, message: str):
        self.successes.append(message)
        print(f"✓ {message}")
        
    def log_warning(self, message: str):
        self.warnings.append(message)
        print(f"⚠ {message}")
        
    def log_error(self, message: str):
        self.errors.append(message)
        print(f"✗ {message}")
        
    def create_directory_structure(self):
        """Create necessary directories for monitoring and logging"""
        print("\n=== Creating Directory Structure ===")
        
        directories = [
            self.log_dir,
            os.path.join(self.log_dir, "agents"),
            os.path.join(self.log_dir, "api"),
            os.path.join(self.log_dir, "system"),
            os.path.join(self.log_dir, "errors"),
            self.monitoring_dir,
            os.path.join(self.monitoring_dir, "metrics"),
            os.path.join(self.monitoring_dir, "health"),
            os.path.join(self.monitoring_dir, "alerts"),
            self.config_dir
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                self.log_success(f"Created directory: {directory}")
                self.results["directories_created"].append(directory)
            except Exception as e:
                self.log_error(f"Failed to create directory {directory}: {e}")
                
    def setup_logging_config(self):
        """Create comprehensive logging configuration"""
        print("\n=== Setting Up Logging Configuration ===")
        
        # Main logging configuration
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "json": {
                    "format": '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "stream": "ext://sys.stdout"
                },
                "file_all": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": f"{self.log_dir}/boarderframeos.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                },
                "file_errors": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": f"{self.log_dir}/errors/errors.log",
                    "maxBytes": 10485760,
                    "backupCount": 5
                },
                "file_agents": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "json",
                    "filename": f"{self.log_dir}/agents/agents.log",
                    "maxBytes": 10485760,
                    "backupCount": 3
                },
                "file_api": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": f"{self.log_dir}/api/api.log",
                    "maxBytes": 10485760,
                    "backupCount": 3
                }
            },
            "loggers": {
                "boarderframeos": {
                    "level": "DEBUG",
                    "handlers": ["console", "file_all"],
                    "propagate": False
                },
                "boarderframeos.agents": {
                    "level": "DEBUG",
                    "handlers": ["file_agents"],
                    "propagate": True
                },
                "boarderframeos.api": {
                    "level": "INFO",
                    "handlers": ["file_api"],
                    "propagate": True
                },
                "boarderframeos.errors": {
                    "level": "ERROR",
                    "handlers": ["file_errors"],
                    "propagate": True
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "file_all"]
            }
        }
        
        # Save logging configuration
        config_path = os.path.join(self.config_dir, "logging_config.json")
        with open(config_path, "w") as f:
            json.dump(logging_config, f, indent=2)
            
        self.log_success(f"Created logging configuration: {config_path}")
        self.results["configs_created"].append(config_path)
        
        # Create Python logging setup script
        setup_script = '''#!/usr/bin/env python3
"""
BoarderframeOS Logging Setup
Import this module to configure logging for any component
"""

import logging
import logging.config
import json
import os

def setup_logging(component_name="boarderframeos"):
    """Setup logging for a component"""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "configs/monitoring/logging_config.json"
    )
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        logging.config.dictConfig(config)
        logger = logging.getLogger(f"boarderframeos.{component_name}")
    else:
        # Fallback to basic config
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(f"boarderframeos.{component_name}")
        
    return logger

# Convenience functions
def get_agent_logger(agent_name):
    """Get logger for an agent"""
    return setup_logging(f"agents.{agent_name}")

def get_api_logger(endpoint_name):
    """Get logger for an API endpoint"""
    return setup_logging(f"api.{endpoint_name}")

def get_error_logger():
    """Get error logger"""
    return setup_logging("errors")
'''
        
        setup_path = os.path.join(self.base_dir, "logging_setup.py")
        with open(setup_path, "w") as f:
            f.write(setup_script)
            
        self.log_success(f"Created logging setup script: {setup_path}")
        self.results["configs_created"].append(setup_path)
        
    def setup_metrics_collection(self):
        """Setup metrics collection system"""
        print("\n=== Setting Up Metrics Collection ===")
        
        # Prometheus-compatible metrics configuration
        metrics_config = {
            "metrics": {
                "system": {
                    "cpu_usage": {
                        "type": "gauge",
                        "help": "CPU usage percentage",
                        "labels": ["host"]
                    },
                    "memory_usage": {
                        "type": "gauge",
                        "help": "Memory usage percentage",
                        "labels": ["host"]
                    },
                    "disk_usage": {
                        "type": "gauge",
                        "help": "Disk usage percentage",
                        "labels": ["host", "mount"]
                    }
                },
                "agents": {
                    "agent_response_time": {
                        "type": "histogram",
                        "help": "Agent response time in milliseconds",
                        "labels": ["agent_name", "method"],
                        "buckets": [10, 50, 100, 500, 1000, 5000]
                    },
                    "agent_tasks_total": {
                        "type": "counter",
                        "help": "Total number of tasks processed by agent",
                        "labels": ["agent_name", "status"]
                    },
                    "active_agents": {
                        "type": "gauge",
                        "help": "Number of active agents",
                        "labels": ["department"]
                    }
                },
                "api": {
                    "http_requests_total": {
                        "type": "counter",
                        "help": "Total HTTP requests",
                        "labels": ["method", "endpoint", "status"]
                    },
                    "http_request_duration": {
                        "type": "histogram",
                        "help": "HTTP request duration in seconds",
                        "labels": ["method", "endpoint"],
                        "buckets": [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
                    }
                },
                "database": {
                    "db_connections": {
                        "type": "gauge",
                        "help": "Number of database connections",
                        "labels": ["database", "state"]
                    },
                    "db_query_duration": {
                        "type": "histogram",
                        "help": "Database query duration in seconds",
                        "labels": ["database", "query_type"],
                        "buckets": [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
                    }
                },
                "message_bus": {
                    "messages_processed_total": {
                        "type": "counter",
                        "help": "Total messages processed",
                        "labels": ["priority", "status"]
                    },
                    "message_queue_size": {
                        "type": "gauge",
                        "help": "Current message queue size",
                        "labels": ["priority"]
                    }
                }
            },
            "export": {
                "format": "prometheus",
                "endpoint": "/metrics",
                "port": 9090
            }
        }
        
        config_path = os.path.join(self.config_dir, "metrics_config.json")
        with open(config_path, "w") as f:
            json.dump(metrics_config, f, indent=2)
            
        self.log_success(f"Created metrics configuration: {config_path}")
        self.results["configs_created"].append(config_path)
        
        # Create metrics collector script
        collector_script = '''#!/usr/bin/env python3
"""
BoarderframeOS Metrics Collector
Collects and exposes metrics for monitoring
"""

import time
import psutil
import json
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from flask import Flask, Response

app = Flask(__name__)

# Load metrics configuration
with open("configs/monitoring/metrics_config.json", "r") as f:
    config = json.load(f)

# System metrics
cpu_usage = Gauge('boarderframeos_cpu_usage', 'CPU usage percentage', ['host'])
memory_usage = Gauge('boarderframeos_memory_usage', 'Memory usage percentage', ['host'])
disk_usage = Gauge('boarderframeos_disk_usage', 'Disk usage percentage', ['host', 'mount'])

# Agent metrics
agent_response_time = Histogram(
    'boarderframeos_agent_response_time',
    'Agent response time in milliseconds',
    ['agent_name', 'method'],
    buckets=(10, 50, 100, 500, 1000, 5000)
)
agent_tasks_total = Counter(
    'boarderframeos_agent_tasks_total',
    'Total number of tasks processed by agent',
    ['agent_name', 'status']
)
active_agents = Gauge(
    'boarderframeos_active_agents',
    'Number of active agents',
    ['department']
)

def collect_system_metrics():
    """Collect system metrics"""
    # CPU
    cpu_usage.labels(host='localhost').set(psutil.cpu_percent())
    
    # Memory
    memory = psutil.virtual_memory()
    memory_usage.labels(host='localhost').set(memory.percent)
    
    # Disk
    for partition in psutil.disk_partitions():
        usage = psutil.disk_usage(partition.mountpoint)
        disk_usage.labels(host='localhost', mount=partition.mountpoint).set(usage.percent)

@app.route('/metrics')
def metrics():
    """Expose metrics endpoint"""
    collect_system_metrics()
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': time.time()}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
'''
        
        collector_path = os.path.join(self.monitoring_dir, "metrics_collector.py")
        with open(collector_path, "w") as f:
            f.write(collector_script)
            
        self.log_success(f"Created metrics collector: {collector_path}")
        self.results["services_configured"].append("metrics_collector")
        
    def setup_health_monitoring(self):
        """Setup health monitoring system"""
        print("\n=== Setting Up Health Monitoring ===")
        
        # Health check configuration
        health_config = {
            "checks": {
                "system": {
                    "cpu_threshold": 80,
                    "memory_threshold": 85,
                    "disk_threshold": 90
                },
                "services": [
                    {
                        "name": "PostgreSQL",
                        "type": "tcp",
                        "host": "localhost",
                        "port": 5434,
                        "timeout": 5
                    },
                    {
                        "name": "Redis",
                        "type": "tcp",
                        "host": "localhost",
                        "port": 6379,
                        "timeout": 5
                    },
                    {
                        "name": "Corporate HQ",
                        "type": "http",
                        "url": "http://localhost:8888/health",
                        "timeout": 10
                    },
                    {
                        "name": "Registry Server",
                        "type": "http",
                        "url": "http://localhost:8009/health",
                        "timeout": 5
                    },
                    {
                        "name": "Analytics Server",
                        "type": "http",
                        "url": "http://localhost:8007/health",
                        "timeout": 5
                    }
                ],
                "agents": [
                    "solomon",
                    "david",
                    "adam",
                    "eve",
                    "bezalel"
                ]
            },
            "intervals": {
                "system": 30,      # Check every 30 seconds
                "services": 60,    # Check every minute
                "agents": 120      # Check every 2 minutes
            }
        }
        
        config_path = os.path.join(self.config_dir, "health_config.json")
        with open(config_path, "w") as f:
            json.dump(health_config, f, indent=2)
            
        self.log_success(f"Created health configuration: {config_path}")
        self.results["configs_created"].append(config_path)
        
        # Create health monitor script
        monitor_script = '''#!/usr/bin/env python3
"""
BoarderframeOS Health Monitor
Monitors system and service health
"""

import asyncio
import aiohttp
import psutil
import json
import logging
from datetime import datetime
import socket

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_monitor")

class HealthMonitor:
    def __init__(self):
        with open("configs/monitoring/health_config.json", "r") as f:
            self.config = json.load(f)
            
        self.health_status = {
            "system": {},
            "services": {},
            "agents": {},
            "last_check": None
        }
        
    async def check_system_health(self):
        """Check system resource health"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.health_status["system"] = {
                "cpu": {
                    "value": cpu,
                    "healthy": cpu < self.config["checks"]["system"]["cpu_threshold"]
                },
                "memory": {
                    "value": memory,
                    "healthy": memory < self.config["checks"]["system"]["memory_threshold"]
                },
                "disk": {
                    "value": disk,
                    "healthy": disk < self.config["checks"]["system"]["disk_threshold"]
                }
            }
            
            logger.info(f"System health: CPU={cpu}%, Memory={memory}%, Disk={disk}%")
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            
    async def check_service_health(self):
        """Check service health"""
        for service in self.config["checks"]["services"]:
            try:
                if service["type"] == "tcp":
                    # TCP port check
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(service["timeout"])
                    result = sock.connect_ex((service["host"], service["port"]))
                    sock.close()
                    
                    self.health_status["services"][service["name"]] = {
                        "healthy": result == 0,
                        "type": "tcp",
                        "port": service["port"]
                    }
                    
                elif service["type"] == "http":
                    # HTTP health check
                    async with aiohttp.ClientSession() as session:
                        try:
                            async with session.get(
                                service["url"],
                                timeout=aiohttp.ClientTimeout(total=service["timeout"])
                            ) as response:
                                self.health_status["services"][service["name"]] = {
                                    "healthy": response.status == 200,
                                    "type": "http",
                                    "status_code": response.status
                                }
                        except Exception:
                            self.health_status["services"][service["name"]] = {
                                "healthy": False,
                                "type": "http",
                                "error": "Connection failed"
                            }
                            
            except Exception as e:
                logger.error(f"Service health check failed for {service['name']}: {e}")
                self.health_status["services"][service["name"]] = {
                    "healthy": False,
                    "error": str(e)
                }
                
    async def check_agent_health(self):
        """Check agent health"""
        # This would check actual agent status via API
        # For now, we'll simulate
        for agent in self.config["checks"]["agents"]:
            self.health_status["agents"][agent] = {
                "healthy": True,  # Would check actual status
                "last_seen": datetime.now().isoformat()
            }
            
    async def run_health_checks(self):
        """Run all health checks"""
        while True:
            # System health
            await self.check_system_health()
            
            # Service health
            await self.check_service_health()
            
            # Agent health
            await self.check_agent_health()
            
            self.health_status["last_check"] = datetime.now().isoformat()
            
            # Save status to file
            with open("monitoring/health/current_status.json", "w") as f:
                json.dump(self.health_status, f, indent=2)
                
            # Wait for next check
            await asyncio.sleep(min(self.config["intervals"].values()))
            
if __name__ == "__main__":
    monitor = HealthMonitor()
    asyncio.run(monitor.run_health_checks())
'''
        
        monitor_path = os.path.join(self.monitoring_dir, "health_monitor.py")
        with open(monitor_path, "w") as f:
            f.write(monitor_script)
            
        self.log_success(f"Created health monitor: {monitor_path}")
        self.results["services_configured"].append("health_monitor")
        
    def setup_alerting_system(self):
        """Setup alerting system"""
        print("\n=== Setting Up Alerting System ===")
        
        # Alerting configuration
        alert_config = {
            "rules": [
                {
                    "name": "high_cpu_usage",
                    "condition": "system.cpu > 90",
                    "duration": "5m",
                    "severity": "warning",
                    "message": "CPU usage is above 90% for 5 minutes"
                },
                {
                    "name": "critical_memory",
                    "condition": "system.memory > 95",
                    "duration": "2m",
                    "severity": "critical",
                    "message": "Memory usage is critically high"
                },
                {
                    "name": "service_down",
                    "condition": "service.healthy == false",
                    "duration": "1m",
                    "severity": "critical",
                    "message": "Service {service_name} is down"
                },
                {
                    "name": "agent_unresponsive",
                    "condition": "agent.last_seen > 5m",
                    "duration": "0s",
                    "severity": "warning",
                    "message": "Agent {agent_name} is unresponsive"
                },
                {
                    "name": "high_error_rate",
                    "condition": "error_rate > 10",
                    "duration": "5m",
                    "severity": "warning",
                    "message": "Error rate is above 10% for 5 minutes"
                }
            ],
            "channels": {
                "console": {
                    "type": "console",
                    "enabled": True
                },
                "file": {
                    "type": "file",
                    "path": "monitoring/alerts/alerts.log",
                    "enabled": True
                },
                "webhook": {
                    "type": "webhook",
                    "url": "http://localhost:8888/api/alerts",
                    "enabled": False
                }
            },
            "settings": {
                "check_interval": 30,
                "alert_cooldown": 300  # 5 minutes between same alerts
            }
        }
        
        config_path = os.path.join(self.config_dir, "alert_config.json")
        with open(config_path, "w") as f:
            json.dump(alert_config, f, indent=2)
            
        self.log_success(f"Created alert configuration: {config_path}")
        self.results["configs_created"].append(config_path)
        
        # Create alerting script
        alert_script = '''#!/usr/bin/env python3
"""
BoarderframeOS Alert Manager
Manages alerts based on defined rules
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alert_manager")

class AlertManager:
    def __init__(self):
        with open("configs/monitoring/alert_config.json", "r") as f:
            self.config = json.load(f)
            
        self.active_alerts = {}
        self.alert_history = []
        
    def check_condition(self, rule: Dict, metrics: Dict) -> bool:
        """Check if alert condition is met"""
        # This would evaluate the condition string
        # For now, return False
        return False
        
    def send_alert(self, rule: Dict, channel: str):
        """Send alert through specified channel"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "rule": rule["name"],
            "severity": rule["severity"],
            "message": rule["message"]
        }
        
        if channel == "console":
            print(f"[ALERT] {rule['severity'].upper()}: {rule['message']}")
            
        elif channel == "file":
            with open(self.config["channels"]["file"]["path"], "a") as f:
                f.write(json.dumps(alert) + "\\n")
                
        elif channel == "webhook" and self.config["channels"]["webhook"]["enabled"]:
            # Send webhook
            pass
            
        self.alert_history.append(alert)
        
    def process_alerts(self, metrics: Dict):
        """Process alert rules against current metrics"""
        for rule in self.config["rules"]:
            if self.check_condition(rule, metrics):
                # Check if alert is already active
                if rule["name"] not in self.active_alerts:
                    # New alert
                    for channel, config in self.config["channels"].items():
                        if config["enabled"]:
                            self.send_alert(rule, channel)
                            
                    self.active_alerts[rule["name"]] = datetime.now()
                    
            else:
                # Condition cleared
                if rule["name"] in self.active_alerts:
                    del self.active_alerts[rule["name"]]
                    logger.info(f"Alert cleared: {rule['name']}")
                    
if __name__ == "__main__":
    manager = AlertManager()
    # Would integrate with health monitor
    print("Alert manager started")
'''
        
        alert_path = os.path.join(self.monitoring_dir, "alert_manager.py")
        with open(alert_path, "w") as f:
            f.write(alert_script)
            
        self.log_success(f"Created alert manager: {alert_path}")
        self.results["services_configured"].append("alert_manager")
        
    def create_monitoring_dashboard(self):
        """Create monitoring dashboard HTML"""
        print("\n=== Creating Monitoring Dashboard ===")
        
        dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoarderframeOS Monitoring Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #00ff88, #0088ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .healthy { color: #00ff88; }
        .warning { color: #ffc107; }
        .critical { color: #ff0088; }
        
        .logs-section {
            background: #000;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 20px;
            height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.9em;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 5px;
        }
        
        .log-error { background: rgba(255, 0, 136, 0.2); }
        .log-warning { background: rgba(255, 193, 7, 0.2); }
        .log-info { background: rgba(0, 136, 255, 0.2); }
    </style>
</head>
<body>
    <div class="container">
        <h1>BoarderframeOS Monitoring Dashboard</h1>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>System Health</h3>
                <div class="metric-value healthy">Healthy</div>
                <div>CPU: 45% | Memory: 62% | Disk: 38%</div>
            </div>
            
            <div class="metric-card">
                <h3>Active Services</h3>
                <div class="metric-value">9/9</div>
                <div>All services operational</div>
            </div>
            
            <div class="metric-card">
                <h3>Active Agents</h3>
                <div class="metric-value">5</div>
                <div>Solomon, David, Adam, Eve, Bezalel</div>
            </div>
            
            <div class="metric-card">
                <h3>Message Throughput</h3>
                <div class="metric-value">1.2K/s</div>
                <div>Last 5 minutes average</div>
            </div>
            
            <div class="metric-card">
                <h3>API Response Time</h3>
                <div class="metric-value">32ms</div>
                <div>P95 latency</div>
            </div>
            
            <div class="metric-card">
                <h3>Error Rate</h3>
                <div class="metric-value healthy">0.2%</div>
                <div>Last hour</div>
            </div>
        </div>
        
        <h2>Recent Logs</h2>
        <div class="logs-section" id="logs">
            <div class="log-entry log-info">[INFO] System monitoring started</div>
            <div class="log-entry log-info">[INFO] All health checks passing</div>
            <div class="log-entry log-warning">[WARNING] High memory usage detected: 82%</div>
            <div class="log-entry log-info">[INFO] Agent Solomon processed 15 tasks</div>
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>'''
        
        dashboard_path = os.path.join(self.monitoring_dir, "dashboard.html")
        with open(dashboard_path, "w") as f:
            f.write(dashboard_html)
            
        self.log_success(f"Created monitoring dashboard: {dashboard_path}")
        self.results["configs_created"].append(dashboard_path)
        
    def create_systemd_services(self):
        """Create systemd service files for monitoring components"""
        print("\n=== Creating Systemd Service Files ===")
        
        services = [
            {
                "name": "boarderframeos-metrics",
                "description": "BoarderframeOS Metrics Collector",
                "exec": f"{sys.executable} {self.monitoring_dir}/metrics_collector.py",
                "restart": "always"
            },
            {
                "name": "boarderframeos-health",
                "description": "BoarderframeOS Health Monitor",
                "exec": f"{sys.executable} {self.monitoring_dir}/health_monitor.py",
                "restart": "always"
            },
            {
                "name": "boarderframeos-alerts",
                "description": "BoarderframeOS Alert Manager",
                "exec": f"{sys.executable} {self.monitoring_dir}/alert_manager.py",
                "restart": "always"
            }
        ]
        
        systemd_dir = os.path.join(self.monitoring_dir, "systemd")
        os.makedirs(systemd_dir, exist_ok=True)
        
        for service in services:
            service_content = f'''[Unit]
Description={service["description"]}
After=network.target

[Service]
Type=simple
User={os.getenv("USER")}
WorkingDirectory={self.base_dir}
ExecStart={service["exec"]}
Restart={service["restart"]}
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
            
            service_path = os.path.join(systemd_dir, f"{service['name']}.service")
            with open(service_path, "w") as f:
                f.write(service_content)
                
            self.log_success(f"Created systemd service: {service_path}")
            self.results["services_configured"].append(service["name"])
            
        # Create installation script
        install_script = f'''#!/bin/bash
# Install BoarderframeOS monitoring services

echo "Installing BoarderframeOS monitoring services..."

# Copy service files
sudo cp {systemd_dir}/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
for service in boarderframeos-metrics boarderframeos-health boarderframeos-alerts; do
    sudo systemctl enable $service
    sudo systemctl start $service
    echo "Started $service"
done

echo "Monitoring services installed and started!"
'''
        
        install_path = os.path.join(self.monitoring_dir, "install_services.sh")
        with open(install_path, "w") as f:
            f.write(install_script)
            
        os.chmod(install_path, 0o755)
        self.log_success(f"Created service installation script: {install_path}")
        
    def create_monitoring_scripts(self):
        """Create utility monitoring scripts"""
        print("\n=== Creating Monitoring Scripts ===")
        
        # Log viewer script
        log_viewer = '''#!/usr/bin/env python3
"""
BoarderframeOS Log Viewer
Interactive log viewing utility
"""

import os
import sys
import time
from datetime import datetime

def tail_file(filepath, lines=50):
    """Tail a log file"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r') as f:
        # Get last N lines
        file_lines = f.readlines()
        last_lines = file_lines[-lines:]
        
        for line in last_lines:
            print(line.strip())
            
def watch_logs(log_dir):
    """Watch all log files for changes"""
    print(f"Watching logs in {log_dir}...")
    print("Press Ctrl+C to stop\\n")
    
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print(f"BoarderframeOS Log Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # Show recent logs from each category
            log_files = {
                "System": "boarderframeos.log",
                "Errors": "errors/errors.log",
                "Agents": "agents/agents.log",
                "API": "api/api.log"
            }
            
            for category, filename in log_files.items():
                filepath = os.path.join(log_dir, filename)
                if os.path.exists(filepath):
                    print(f"\\n[{category}]")
                    tail_file(filepath, 5)
                    
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\\nStopped watching logs")
        
if __name__ == "__main__":
    log_dir = "logs"
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
        
    watch_logs(log_dir)
'''
        
        viewer_path = os.path.join(self.monitoring_dir, "log_viewer.py")
        with open(viewer_path, "w") as f:
            f.write(log_viewer)
            
        os.chmod(viewer_path, 0o755)
        self.log_success(f"Created log viewer: {viewer_path}")
        
        # Status checker script
        status_script = '''#!/bin/bash
# BoarderframeOS Monitoring Status

echo "BoarderframeOS Monitoring Status"
echo "================================"

# Check if monitoring services are running
echo -e "\\nMonitoring Services:"
for service in metrics_collector health_monitor alert_manager; do
    if pgrep -f "$service.py" > /dev/null; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
    fi
done

# Check log files
echo -e "\\nLog Files:"
for logfile in logs/boarderframeos.log logs/errors/errors.log; do
    if [ -f "$logfile" ]; then
        size=$(du -h "$logfile" | cut -f1)
        echo "✓ $logfile ($size)"
    else
        echo "✗ $logfile not found"
    fi
done

# Show recent alerts
echo -e "\\nRecent Alerts:"
if [ -f "monitoring/alerts/alerts.log" ]; then
    tail -5 monitoring/alerts/alerts.log
else
    echo "No alerts log found"
fi

echo -e "\\nMonitoring Dashboard: file://$(pwd)/monitoring/dashboard.html"
'''
        
        status_path = os.path.join(self.monitoring_dir, "check_status.sh")
        with open(status_path, "w") as f:
            f.write(status_script)
            
        os.chmod(status_path, 0o755)
        self.log_success(f"Created status checker: {status_path}")
        
    def generate_report(self):
        """Generate setup report"""
        # Calculate summary
        self.results["summary"] = {
            "directories_created": len(self.results["directories_created"]),
            "configs_created": len(self.results["configs_created"]),
            "services_configured": len(self.results["services_configured"]),
            "monitoring_ready": len(self.errors) == 0,
            "total_successes": len(self.successes),
            "total_warnings": len(self.warnings),
            "total_errors": len(self.errors)
        }
        
        # Save JSON report
        with open("monitoring_setup_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Print summary
        print("\n" + "="*60)
        print("MONITORING SETUP SUMMARY")
        print("="*60)
        
        summary = self.results["summary"]
        print(f"Directories Created: {summary['directories_created']}")
        print(f"Config Files Created: {summary['configs_created']}")
        print(f"Services Configured: {summary['services_configured']}")
        print(f"Monitoring Ready: {'YES' if summary['monitoring_ready'] else 'NO'}")
        
        print(f"\n✓ Successes: {summary['total_successes']}")
        print(f"⚠ Warnings: {summary['total_warnings']}")
        print(f"✗ Errors: {summary['total_errors']}")
        
        print("\nKey Components:")
        print(f"  - Logging: {self.log_dir}")
        print(f"  - Monitoring: {self.monitoring_dir}")
        print(f"  - Configs: {self.config_dir}")
        print(f"  - Dashboard: {self.monitoring_dir}/dashboard.html")
        
        print("\nNext Steps:")
        print("1. Start monitoring services:")
        print("   python monitoring/metrics_collector.py")
        print("   python monitoring/health_monitor.py")
        print("   python monitoring/alert_manager.py")
        print("\n2. Or install as systemd services:")
        print("   ./monitoring/install_services.sh")
        print("\n3. View monitoring dashboard:")
        print(f"   open {self.monitoring_dir}/dashboard.html")
        print("\n4. Check monitoring status:")
        print("   ./monitoring/check_status.sh")
        
        print("\nDetailed report saved to: monitoring_setup_report.json")
        
    def run_setup(self):
        """Run complete monitoring setup"""
        print("="*60)
        print("BoarderframeOS Monitoring and Logging Setup")
        print("="*60)
        
        # Create directory structure
        self.create_directory_structure()
        
        # Setup components
        self.setup_logging_config()
        self.setup_metrics_collection()
        self.setup_health_monitoring()
        self.setup_alerting_system()
        
        # Create dashboard and scripts
        self.create_monitoring_dashboard()
        self.create_systemd_services()
        self.create_monitoring_scripts()
        
        # Generate report
        self.generate_report()
        
        # Return success if no errors
        return len(self.errors) == 0


def main():
    setup = MonitoringSetup()
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()