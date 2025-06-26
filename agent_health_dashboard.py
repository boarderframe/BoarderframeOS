#!/usr/bin/env python3
"""
Agent Health Dashboard Server
Real-time web dashboard for agent health monitoring
"""

from flask import Flask, render_template_string, jsonify, request
import asyncio
from datetime import datetime, timedelta
import json
import threading
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent_health import get_health_monitor, HealthStatus, AgentHealthReport

app = Flask(__name__)

# Dashboard HTML template
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Health Dashboard - BoarderframeOS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            overflow-x: hidden;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
            padding: 20px 40px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.5);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(45deg, #4CAF50, #2196F3, #FF5722);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        /* Summary Cards */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 20px 40px;
        }
        
        .summary-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .summary-value {
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .summary-label {
            color: #888;
            font-size: 0.9em;
        }
        
        /* Agent Grid */
        .agents-container {
            padding: 20px 40px;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .agent-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .agent-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: #4CAF50;
        }
        
        .agent-card.warning::before { background: #FFC107; }
        .agent-card.critical::before { background: #F44336; }
        .agent-card.offline::before { background: #757575; }
        
        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .agent-name {
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-healthy { background: #4CAF50; color: white; }
        .status-warning { background: #FFC107; color: #333; }
        .status-critical { background: #F44336; color: white; }
        .status-offline { background: #757575; color: white; }
        
        /* Metrics */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 5px;
        }
        
        .metric-label {
            color: #aaa;
            font-size: 0.9em;
        }
        
        .metric-value {
            font-weight: 600;
        }
        
        /* Progress Bars */
        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
            margin: 5px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: #4CAF50;
            transition: width 0.3s ease;
        }
        
        .progress-fill.warning { background: #FFC107; }
        .progress-fill.critical { background: #F44336; }
        
        /* Charts */
        .chart-container {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            height: 150px;
        }
        
        /* Recommendations */
        .recommendations {
            background: rgba(33, 150, 243, 0.1);
            border: 1px solid rgba(33, 150, 243, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
        }
        
        .recommendations h3 {
            color: #2196F3;
            margin-bottom: 10px;
        }
        
        .recommendation-item {
            padding: 5px 0;
            font-size: 0.9em;
        }
        
        /* Animations */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .updating {
            animation: pulse 2s infinite;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .agents-grid {
                grid-template-columns: 1fr;
            }
            
            .summary-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        /* Filters */
        .filters {
            padding: 0 40px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            color: #e0e0e0;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .filter-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .filter-btn.active {
            background: #2196F3;
            border-color: #2196F3;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Agent Health Dashboard</h1>
        <p>Real-time monitoring of BoarderframeOS agents</p>
        <p style="margin-top: 10px; color: #888;">Last updated: <span id="lastUpdate">-</span></p>
    </div>
    
    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-label">Total Agents</div>
            <div class="summary-value" id="totalAgents">0</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Healthy</div>
            <div class="summary-value" style="color: #4CAF50;" id="healthyAgents">0</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Warning</div>
            <div class="summary-value" style="color: #FFC107;" id="warningAgents">0</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Critical</div>
            <div class="summary-value" style="color: #F44336;" id="criticalAgents">0</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Offline</div>
            <div class="summary-value" style="color: #757575;" id="offlineAgents">0</div>
        </div>
    </div>
    
    <div class="filters">
        <button class="filter-btn active" onclick="filterAgents('all')">All Agents</button>
        <button class="filter-btn" onclick="filterAgents('healthy')">Healthy</button>
        <button class="filter-btn" onclick="filterAgents('warning')">Warning</button>
        <button class="filter-btn" onclick="filterAgents('critical')">Critical</button>
        <button class="filter-btn" onclick="filterAgents('offline')">Offline</button>
    </div>
    
    <div class="agents-container">
        <h2>Agent Status</h2>
        <div class="agents-grid" id="agentsGrid">
            <!-- Agent cards will be inserted here -->
        </div>
    </div>
    
    <script>
        let currentFilter = 'all';
        let healthData = {};
        
        async function fetchHealthData() {
            try {
                const response = await fetch('/api/health/all');
                const data = await response.json();
                healthData = data;
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to fetch health data:', error);
            }
        }
        
        function updateDashboard(data) {
            // Update summary
            document.getElementById('totalAgents').textContent = data.summary.total_agents;
            document.getElementById('healthyAgents').textContent = data.summary.healthy;
            document.getElementById('warningAgents').textContent = data.summary.warning;
            document.getElementById('criticalAgents').textContent = data.summary.critical;
            document.getElementById('offlineAgents').textContent = data.summary.offline;
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            
            // Update agent cards
            const grid = document.getElementById('agentsGrid');
            grid.innerHTML = '';
            
            Object.entries(data.agents).forEach(([agentId, report]) => {
                if (currentFilter !== 'all' && report.overall_status !== currentFilter) {
                    return;
                }
                
                const card = createAgentCard(report);
                grid.appendChild(card);
            });
        }
        
        function createAgentCard(report) {
            const card = document.createElement('div');
            card.className = `agent-card ${report.overall_status}`;
            
            const metricsHtml = report.checks.map(check => {
                const progressClass = check.status === 'critical' ? 'critical' : 
                                    check.status === 'warning' ? 'warning' : '';
                                    
                let progressWidth = 0;
                if (check.metric === 'cpu_usage' || check.metric === 'memory_usage') {
                    progressWidth = check.value || 0;
                } else if (check.metric === 'error_rate') {
                    progressWidth = (check.value || 0) * 100;
                } else if (check.metric === 'task_success_rate') {
                    progressWidth = (check.value || 0) * 100;
                }
                
                return `
                    <div class="metric-item">
                        <span class="metric-label">${formatMetricName(check.metric)}</span>
                        <span class="metric-value">${formatMetricValue(check)}</span>
                    </div>
                    ${(check.metric === 'cpu_usage' || check.metric === 'memory_usage') ? `
                        <div class="progress-bar">
                            <div class="progress-fill ${progressClass}" style="width: ${progressWidth}%"></div>
                        </div>
                    ` : ''}
                `;
            }).join('');
            
            card.innerHTML = `
                <div class="agent-header">
                    <div class="agent-name">${report.agent_name}</div>
                    <div class="status-badge status-${report.overall_status}">${report.overall_status}</div>
                </div>
                
                <div class="metrics-grid">
                    ${metricsHtml}
                </div>
                
                <div style="margin-top: 10px; color: #888; font-size: 0.9em;">
                    Uptime: ${report.uptime}
                </div>
            `;
            
            return card;
        }
        
        function formatMetricName(metric) {
            return metric.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
        }
        
        function formatMetricValue(check) {
            if (check.value === null || check.value === undefined) {
                return 'N/A';
            }
            
            switch (check.metric) {
                case 'cpu_usage':
                case 'memory_usage':
                    return `${check.value.toFixed(1)}%`;
                case 'response_time':
                    return `${check.value.toFixed(2)}s`;
                case 'error_rate':
                case 'task_success_rate':
                    return `${(check.value * 100).toFixed(1)}%`;
                case 'message_queue':
                    return check.value;
                case 'last_activity':
                    return check.message || 'Unknown';
                default:
                    return check.value;
            }
        }
        
        function filterAgents(status) {
            currentFilter = status;
            
            // Update filter buttons
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Re-render with filter
            updateDashboard(healthData);
        }
        
        // Initial load
        fetchHealthData();
        
        // Auto-refresh every 10 seconds
        setInterval(fetchHealthData, 10000);
    </script>
</body>
</html>'''

@app.route('/')
def dashboard():
    """Serve the health dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/health/all')
def get_all_health():
    """Get health data for all agents"""
    health_monitor = get_health_monitor()
    
    # Get current health reports
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    reports = loop.run_until_complete(health_monitor.check_all_agents())
    
    # Convert to JSON-serializable format
    agents_data = {}
    for agent_id, report in reports.items():
        agents_data[agent_id] = report.to_dict()
    
    # Get system summary
    summary = health_monitor.get_system_health_summary()
    
    return jsonify({
        "agents": agents_data,
        "summary": summary,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health/<agent_id>')
def get_agent_health(agent_id):
    """Get health data for a specific agent"""
    health_monitor = get_health_monitor()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    report = loop.run_until_complete(health_monitor.check_agent_health(agent_id))
    
    if not report:
        return jsonify({"error": "Agent not found"}), 404
    
    # Get recommendations
    recommendations = health_monitor.get_recommendations(report)
    
    return jsonify({
        "report": report.to_dict(),
        "recommendations": recommendations,
        "history": [r.to_dict() for r in health_monitor.get_agent_history(agent_id, limit=20)]
    })

@app.route('/api/health/<agent_id>/history')
def get_agent_history(agent_id):
    """Get health history for an agent"""
    health_monitor = get_health_monitor()
    limit = int(request.args.get('limit', 50))
    
    history = health_monitor.get_agent_history(agent_id, limit=limit)
    
    return jsonify({
        "agent_id": agent_id,
        "history": [report.to_dict() for report in history]
    })

@app.route('/api/alerts', methods=['POST'])
def set_alert_webhook():
    """Set webhook for health alerts"""
    data = request.json
    webhook_url = data.get('webhook_url')
    
    if not webhook_url:
        return jsonify({"error": "webhook_url required"}), 400
    
    # In a real implementation, this would configure alert webhooks
    return jsonify({"status": "Alert webhook configured"})


def start_monitoring():
    """Start the health monitoring in background"""
    health_monitor = get_health_monitor()
    
    # Register some test agents
    health_monitor.register_agent("agent-solomon", "Solomon", os.getpid())
    health_monitor.register_agent("agent-david", "David", os.getpid())
    health_monitor.register_agent("agent-adam", "Adam", os.getpid())
    health_monitor.register_agent("agent-eve", "Eve", os.getpid())
    health_monitor.register_agent("agent-bezalel", "Bezalel", os.getpid())
    
    # Start monitoring
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(health_monitor.start_monitoring())


if __name__ == '__main__':
    # Start monitoring in background thread
    monitor_thread = threading.Thread(target=start_monitoring, daemon=True)
    monitor_thread.start()
    
    # Start Flask app
    print("🏥 Agent Health Dashboard starting on http://localhost:8891")
    app.run(host='0.0.0.0', port=8891, debug=False)