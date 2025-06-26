#!/usr/bin/env python3
"""
Governance Dashboard Server
Web interface for BoarderframeOS governance monitoring
"""

from flask import Flask, render_template_string, jsonify, request
import asyncio
from datetime import datetime, timedelta
import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.governance import get_governance_controller, ComplianceStatus, RiskLevel

app = Flask(__name__)

# Dashboard HTML template
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Governance Dashboard - BoarderframeOS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a0033 0%, #220044 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        
        /* Header */
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.3);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(45deg, #9b59b6, #3498db, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Compliance Score */
        .compliance-section {
            padding: 40px;
            text-align: center;
        }
        
        .compliance-score {
            display: inline-block;
            position: relative;
            width: 250px;
            height: 250px;
        }
        
        .score-circle {
            width: 100%;
            height: 100%;
            transform: rotate(-90deg);
        }
        
        .score-value {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 3em;
            font-weight: bold;
        }
        
        .compliance-status {
            margin-top: 20px;
            font-size: 1.5em;
            padding: 10px 30px;
            border-radius: 30px;
            display: inline-block;
        }
        
        .status-compliant { background: #27ae60; }
        .status-warning { background: #f39c12; }
        .status-non_compliant { background: #e74c3c; }
        
        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px 40px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.08);
        }
        
        .metric-card h3 {
            color: #9b59b6;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        /* Policy Table */
        .policy-section {
            padding: 20px 40px;
        }
        
        .policy-table {
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .policy-table th {
            background: rgba(155, 89, 182, 0.3);
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .policy-table td {
            padding: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .policy-table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        /* Violations */
        .violations-section {
            padding: 20px 40px;
        }
        
        .violation-item {
            background: rgba(231, 76, 60, 0.1);
            border: 1px solid rgba(231, 76, 60, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
        }
        
        .violation-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .severity-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .severity-CRITICAL { background: #e74c3c; }
        .severity-HIGH { background: #f39c12; }
        .severity-MEDIUM { background: #3498db; }
        .severity-LOW { background: #95a5a6; }
        
        /* Charts */
        .chart-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            height: 300px;
        }
        
        /* Recommendations */
        .recommendations {
            background: rgba(52, 152, 219, 0.1);
            border: 1px solid rgba(52, 152, 219, 0.3);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 40px;
        }
        
        .recommendations h3 {
            color: #3498db;
            margin-bottom: 15px;
        }
        
        .recommendation-item {
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .recommendation-item:last-child {
            border-bottom: none;
        }
        
        /* Refresh Button */
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #9b59b6;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 30px;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(155, 89, 182, 0.3);
            transition: all 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #8e44ad;
            transform: translateY(-2px);
        }
        
        /* Risk Level Colors */
        .risk-CRITICAL { color: #e74c3c; }
        .risk-HIGH { color: #f39c12; }
        .risk-MEDIUM { color: #3498db; }
        .risk-LOW { color: #2ecc71; }
        .risk-MINIMAL { color: #95a5a6; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Governance Dashboard</h1>
        <p>BoarderframeOS Policy Enforcement & Compliance Monitoring</p>
        <p style="margin-top: 10px; color: #888;">Last updated: <span id="lastUpdate">-</span></p>
    </div>
    
    <!-- Compliance Score -->
    <div class="compliance-section">
        <div class="compliance-score">
            <svg class="score-circle" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="8"/>
                <circle id="scoreProgress" cx="50" cy="50" r="45" fill="none" stroke="#9b59b6" stroke-width="8"
                        stroke-dasharray="283" stroke-dashoffset="283" stroke-linecap="round"/>
            </svg>
            <div class="score-value" id="complianceScore">0%</div>
        </div>
        <div class="compliance-status" id="complianceStatus">Loading...</div>
    </div>
    
    <!-- Metrics Grid -->
    <div class="metrics-grid">
        <div class="metric-card">
            <h3>Active Policies</h3>
            <div class="metric-value" id="activePolicies">0</div>
            <p>Total: <span id="totalPolicies">0</span></p>
        </div>
        
        <div class="metric-card">
            <h3>Recent Violations</h3>
            <div class="metric-value" id="recentViolations">0</div>
            <p>Unresolved: <span id="unresolvedViolations">0</span></p>
        </div>
        
        <div class="metric-card">
            <h3>Risk Level</h3>
            <div class="metric-value risk-MEDIUM" id="riskLevel">MEDIUM</div>
            <p>Based on current compliance</p>
        </div>
        
        <div class="metric-card">
            <h3>Audit Events</h3>
            <div class="metric-value" id="auditEvents">0</div>
            <p>Last 24 hours</p>
        </div>
    </div>
    
    <!-- Recommendations -->
    <div class="recommendations" id="recommendationsSection" style="display: none;">
        <h3>💡 Recommendations</h3>
        <div id="recommendationsList"></div>
    </div>
    
    <!-- Policy Breakdown -->
    <div class="policy-section">
        <h2>Policy Overview</h2>
        <div class="chart-container">
            <canvas id="policyChart"></canvas>
        </div>
        
        <h3 style="margin-top: 30px;">Active Policies</h3>
        <table class="policy-table">
            <thead>
                <tr>
                    <th>Policy Name</th>
                    <th>Type</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="policyTableBody">
                <!-- Policies will be inserted here -->
            </tbody>
        </table>
    </div>
    
    <!-- Recent Violations -->
    <div class="violations-section">
        <h2>Recent Violations</h2>
        <div id="violationsList">
            <!-- Violations will be inserted here -->
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let policyChart = null;
        
        async function fetchGovernanceData() {
            try {
                const response = await fetch('/api/governance/status');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to fetch governance data:', error);
            }
        }
        
        function updateDashboard(data) {
            // Update timestamp
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
            
            // Update compliance score
            const score = data.compliance_score;
            document.getElementById('complianceScore').textContent = score.toFixed(1) + '%';
            
            // Animate score circle
            const circle = document.getElementById('scoreProgress');
            const circumference = 283;
            const offset = circumference - (score / 100) * circumference;
            circle.style.strokeDashoffset = offset;
            
            // Update compliance status
            const statusElement = document.getElementById('complianceStatus');
            statusElement.textContent = data.compliance_status.replace('_', ' ').toUpperCase();
            statusElement.className = 'compliance-status status-' + data.compliance_status;
            
            // Update metrics
            document.getElementById('activePolicies').textContent = data.active_policies;
            document.getElementById('totalPolicies').textContent = data.total_policies;
            document.getElementById('recentViolations').textContent = data.recent_violations;
            document.getElementById('unresolvedViolations').textContent = data.unresolved_violations;
            
            // Update risk level
            const riskElement = document.getElementById('riskLevel');
            riskElement.textContent = data.risk_level;
            riskElement.className = 'metric-value risk-' + data.risk_level;
            
            document.getElementById('auditEvents').textContent = data.audit_events_24h;
            
            // Update recommendations
            if (data.recommendations && data.recommendations.length > 0) {
                document.getElementById('recommendationsSection').style.display = 'block';
                const recList = document.getElementById('recommendationsList');
                recList.innerHTML = data.recommendations.map(rec => 
                    `<div class="recommendation-item">• ${rec}</div>`
                ).join('');
            }
            
            // Update policy table
            updatePolicyTable(data.policies);
            
            // Update violations
            updateViolations(data.violations);
            
            // Update charts
            updatePolicyChart(data.policy_breakdown);
        }
        
        function updatePolicyTable(policies) {
            const tbody = document.getElementById('policyTableBody');
            tbody.innerHTML = '';
            
            policies.forEach(policy => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${policy.name}</td>
                    <td>${policy.type}</td>
                    <td>${policy.priority}</td>
                    <td>${policy.enabled ? '✅ Enabled' : '❌ Disabled'}</td>
                    <td>${policy.actions.join(', ')}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function updateViolations(violations) {
            const container = document.getElementById('violationsList');
            container.innerHTML = '';
            
            if (violations.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #888;">No recent violations</p>';
                return;
            }
            
            violations.forEach(violation => {
                const item = document.createElement('div');
                item.className = 'violation-item';
                item.innerHTML = `
                    <div class="violation-header">
                        <div>
                            <strong>${violation.policy_name}</strong>
                            <br>
                            <small>${violation.entity_type}: ${violation.entity_id}</small>
                        </div>
                        <span class="severity-badge severity-${violation.severity}">${violation.severity}</span>
                    </div>
                    <p>${violation.description}</p>
                    <small>Time: ${new Date(violation.timestamp).toLocaleString()}</small>
                    ${violation.resolved ? '<br><small>✅ Resolved: ' + violation.resolution + '</small>' : ''}
                `;
                container.appendChild(item);
            });
        }
        
        function updatePolicyChart(breakdown) {
            const ctx = document.getElementById('policyChart').getContext('2d');
            
            if (policyChart) {
                policyChart.destroy();
            }
            
            const data = {
                labels: Object.keys(breakdown.by_type || {}),
                datasets: [{
                    label: 'Policies by Type',
                    data: Object.values(breakdown.by_type || {}),
                    backgroundColor: [
                        'rgba(155, 89, 182, 0.8)',
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ],
                    borderWidth: 0
                }]
            };
            
            policyChart = new Chart(ctx, {
                type: 'doughnut',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: '#e0e0e0'
                            }
                        }
                    }
                }
            });
        }
        
        function refreshDashboard() {
            fetchGovernanceData();
        }
        
        // Initial load
        fetchGovernanceData();
        
        // Auto-refresh every 30 seconds
        setInterval(fetchGovernanceData, 30000);
    </script>
</body>
</html>'''

@app.route('/')
def dashboard():
    """Serve the governance dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/governance/status')
def get_governance_status():
    """Get current governance status"""
    governance = get_governance_controller()
    
    # Generate compliance report
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    report = loop.run_until_complete(governance.generate_compliance_report())
    
    # Get recent violations
    recent_violations = [
        v for v in governance.violations
        if datetime.now() - v.timestamp < timedelta(hours=24)
    ]
    
    # Sort and limit violations
    recent_violations = sorted(
        recent_violations, 
        key=lambda x: x.timestamp, 
        reverse=True
    )[:10]
    
    # Get audit events from last 24 hours
    audit_events_24h = len([
        e for e in governance.audit_trail
        if datetime.now() - e.timestamp < timedelta(hours=24)
    ])
    
    # Prepare policy data
    policies = []
    for p in sorted(governance.policies.values(), key=lambda x: x.priority):
        policies.append({
            'id': p.id,
            'name': p.name,
            'type': p.type.value,
            'priority': p.priority,
            'enabled': p.enabled,
            'actions': [a.value for a in p.actions]
        })
    
    # Prepare violation data
    violations_data = []
    for v in recent_violations:
        violations_data.append({
            'id': v.id,
            'policy_name': v.policy_name,
            'entity_type': v.entity_type,
            'entity_id': v.entity_id,
            'severity': v.severity.name,
            'description': v.description,
            'timestamp': v.timestamp.isoformat(),
            'resolved': v.resolved,
            'resolution': v.resolution
        })
    
    return jsonify({
        'compliance_score': report.compliance_score,
        'compliance_status': report.status.value,
        'risk_level': report.risk_level.name,
        'total_policies': report.total_policies,
        'active_policies': report.active_policies,
        'recent_violations': report.violations_count,
        'unresolved_violations': len([v for v in recent_violations if not v.resolved]),
        'audit_events_24h': audit_events_24h,
        'recommendations': report.recommendations,
        'policies': policies,
        'violations': violations_data,
        'policy_breakdown': report.details.get('policy_breakdown', {}),
        'violation_trends': report.details.get('violation_trends', {}),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/governance/evaluate', methods=['POST'])
def evaluate_action():
    """Evaluate an action against policies"""
    governance = get_governance_controller()
    
    action_context = request.json
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    action, policies = loop.run_until_complete(
        governance.evaluate_action(action_context)
    )
    
    return jsonify({
        'action': action.value,
        'policies_applied': [p.name for p in policies]
    })

@app.route('/api/governance/policies')
def get_policies():
    """Get all policies"""
    governance = get_governance_controller()
    
    policies = []
    for p in governance.policies.values():
        policies.append({
            'id': p.id,
            'name': p.name,
            'type': p.type.value,
            'description': p.description,
            'enabled': p.enabled,
            'priority': p.priority,
            'rules': p.rules,
            'actions': [a.value for a in p.actions],
            'created_at': p.created_at.isoformat(),
            'updated_at': p.updated_at.isoformat()
        })
    
    return jsonify(policies)


if __name__ == '__main__':
    print("🏛️ Governance Dashboard starting on http://localhost:8892")
    app.run(host='0.0.0.0', port=8892, debug=False)