#!/usr/bin/env python3
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
