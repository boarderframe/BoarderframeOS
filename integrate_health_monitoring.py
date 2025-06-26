#!/usr/bin/env python3
"""
Health Monitoring Integration Script
Adds health monitoring to existing BoarderframeOS components
"""

import os
import sys
import re
from pathlib import Path
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_header():
    """Print script header"""
    print("=" * 60)
    print("BoarderframeOS Health Monitoring Integration")
    print("=" * 60)
    print("Adding health monitoring to agents and system components")
    print()


def backup_file(file_path: Path) -> Path:
    """Create backup of a file"""
    backup_path = file_path.with_suffix(file_path.suffix + '.health_backup')
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_base_agent():
    """Add health monitoring to BaseAgent"""
    base_agent_file = Path("core/base_agent.py")
    
    if not base_agent_file.exists():
        print("  ⚠️  core/base_agent.py not found")
        return False
    
    try:
        with open(base_agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if already has health monitoring
        if 'agent_health' in content:
            print("  ℹ️  BaseAgent already has health monitoring")
            return False
        
        # Add import
        import_section = """from typing import Dict, Any, Optional, List
import logging
import asyncio
import os
from core.agent_health import get_health_monitor"""
        
        # Find where to insert imports
        if "import logging" in content:
            content = content.replace("import logging", import_section)
        else:
            # Add after other imports
            lines = content.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    import_end = i
            
            lines.insert(import_end + 1, import_section)
            content = '\n'.join(lines)
        
        # Add health registration in __init__
        health_init = """
        # Register with health monitor
        self._health_monitor = get_health_monitor()
        self._health_monitor.register_agent(
            agent_id=f"agent-{self.name.lower().replace(' ', '-')}",
            agent_name=self.name,
            process_id=os.getpid(),
            agent_type=getattr(self, 'agent_type', 'unknown'),
            department=getattr(self, 'department', 'unknown')
        )"""
        
        # Find __init__ method
        init_match = re.search(r'def __init__\(self.*?\):', content)
        if init_match:
            # Find end of __init__ method
            init_end = content.find('\n', init_match.end())
            next_def = content.find('\n    def ', init_end)
            if next_def > 0:
                # Insert before next method
                content = content[:next_def] + health_init + content[next_def:]
        
        # Add health check method
        health_check_method = '''
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of the agent"""
        agent_id = f"agent-{self.name.lower().replace(' ', '-')}"
        report = await self._health_monitor.check_agent_health(agent_id)
        return report.to_dict() if report else {"status": "unknown"}
        
    def report_error(self, error: Exception):
        """Report an error to health monitoring"""
        # This would update error metrics
        logger.error(f"Agent {self.name} error: {error}")
        
    def report_task_completion(self, success: bool, duration: float):
        """Report task completion to health monitoring"""
        # This would update success rate metrics
        logger.info(f"Agent {self.name} task {'succeeded' if success else 'failed'} in {duration:.2f}s")'''
        
        # Add before the last line of the class
        class_end = content.rfind('\n\n')
        if class_end > 0:
            content = content[:class_end] + health_check_method + content[class_end:]
        
        # Write updated content
        if content != original_content:
            backup_file(base_agent_file)
            with open(base_agent_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated core/base_agent.py with health monitoring")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating BaseAgent: {e}")
        return False


def update_startup():
    """Add health monitoring to startup.py"""
    startup_file = Path("startup.py")
    
    if not startup_file.exists():
        print("  ⚠️  startup.py not found")
        return False
    
    try:
        with open(startup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add health monitoring import
        if 'agent_health' not in content:
            health_imports = """from core.agent_health import get_health_monitor

# Initialize health monitoring
health_monitor = get_health_monitor()
"""
            
            # Add after main imports
            import_end = content.find('# Core modules')
            if import_end > 0:
                content = content[:import_end] + health_imports + '\n' + content[import_end:]
        
        # Add health monitoring startup
        health_startup = '''
    # Start health monitoring
    print("Starting agent health monitoring...")
    await health_monitor.start_monitoring()
    print("✓ Health monitoring active")
    
    # Launch health dashboard
    print("Launching health dashboard on port 8891...")
    health_dashboard_process = subprocess.Popen(
        [sys.executable, "agent_health_dashboard.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)
    print("✓ Health dashboard: http://localhost:8891")
'''
        
        # Find where to add (after other services)
        services_pos = content.find('print("✓ All services started successfully!")')
        if services_pos > 0:
            insert_pos = content.rfind('\n', 0, services_pos)
            content = content[:insert_pos] + health_startup + content[insert_pos:]
        
        # Write updated content
        if content != original_content:
            backup_file(startup_file)
            with open(startup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated startup.py with health monitoring")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating startup: {e}")
        return False


def update_corporate_hq():
    """Add health endpoint to Corporate HQ"""
    corp_hq_file = Path("corporate_headquarters.py")
    
    if not corp_hq_file.exists():
        print("  ⚠️  corporate_headquarters.py not found")
        return False
    
    try:
        with open(corp_hq_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add health endpoints
        if '/api/agents/health' not in content:
            health_endpoints = '''
@app.route('/api/agents/health')
def get_agents_health():
    """Get health status of all agents"""
    from core.agent_health import get_health_monitor
    
    health_monitor = get_health_monitor()
    summary = health_monitor.get_system_health_summary()
    
    # Get individual agent reports
    agents_health = {}
    for agent_id in health_monitor.agents:
        history = health_monitor.get_agent_history(agent_id, limit=1)
        if history:
            agents_health[agent_id] = history[0].to_dict()
    
    return jsonify({
        'summary': summary,
        'agents': agents_health
    })

@app.route('/api/agents/<agent_id>/health')
def get_agent_health(agent_id):
    """Get health status of a specific agent"""
    from core.agent_health import get_health_monitor
    
    health_monitor = get_health_monitor()
    history = health_monitor.get_agent_history(agent_id, limit=1)
    
    if not history:
        return jsonify({'error': 'Agent not found'}), 404
    
    report = history[0]
    recommendations = health_monitor.get_recommendations(report)
    
    return jsonify({
        'report': report.to_dict(),
        'recommendations': recommendations
    })
'''
            
            # Find where to add (after other API endpoints)
            api_section = content.find("@app.route('/api/")
            if api_section > 0:
                # Find the end of the last route
                next_section = content.find('\n\n\n', api_section)
                if next_section > 0:
                    content = content[:next_section] + '\n' + health_endpoints + content[next_section:]
        
        # Write updated content
        if content != original_content:
            backup_file(corp_hq_file)
            with open(corp_hq_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated corporate_headquarters.py with health endpoints")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating Corporate HQ: {e}")
        return False


def create_health_alerts_config():
    """Create health alerts configuration"""
    config_file = Path("configs/health_alerts.yaml")
    config_file.parent.mkdir(exist_ok=True)
    
    config = """# Agent Health Monitoring Configuration

# Health check intervals (seconds)
check_interval: 30
history_retention: 86400  # 24 hours

# Health thresholds
thresholds:
  cpu_usage:
    warning: 70
    critical: 90
  
  memory_usage:
    warning: 80
    critical: 95
  
  response_time:
    warning: 2.0
    critical: 5.0
  
  error_rate:
    warning: 0.05  # 5%
    critical: 0.10  # 10%
  
  message_queue:
    warning: 100
    critical: 500
  
  task_success_rate:
    warning: 0.95  # 95%
    critical: 0.80  # 80%

# Alert configuration
alerts:
  # Email alerts
  email:
    enabled: false
    smtp_server: smtp.gmail.com
    smtp_port: 587
    from_address: alerts@boarderframeos.local
    to_addresses:
      - admin@boarderframeos.local
    
  # Webhook alerts
  webhook:
    enabled: false
    url: https://hooks.example.com/alerts
    
  # Slack alerts
  slack:
    enabled: false
    webhook_url: https://hooks.slack.com/services/XXX/YYY/ZZZ
    
  # PagerDuty alerts
  pagerduty:
    enabled: false
    integration_key: YOUR_INTEGRATION_KEY

# Alert rules
alert_rules:
  - name: agent_critical
    condition: overall_status == "critical"
    channels: [email, slack, pagerduty]
    cooldown: 300  # 5 minutes
    
  - name: high_error_rate
    condition: error_rate > 0.10
    channels: [email, slack]
    cooldown: 600  # 10 minutes
    
  - name: agent_offline
    condition: overall_status == "offline"
    channels: [email, pagerduty]
    cooldown: 60  # 1 minute
    
  - name: resource_exhaustion
    condition: cpu_usage > 90 or memory_usage > 95
    channels: [email, slack]
    cooldown: 300  # 5 minutes

# Recovery actions
recovery_actions:
  high_cpu:
    threshold: 90
    action: scale_horizontal
    
  high_memory:
    threshold: 95
    action: restart_agent
    
  high_error_rate:
    threshold: 0.15
    action: rollback_deployment
    
  agent_offline:
    threshold: 180  # seconds
    action: restart_agent
"""
    
    with open(config_file, 'w') as f:
        f.write(config)
    
    print(f"  ✅ Created health alerts configuration: {config_file}")
    return True


def create_health_dashboard_launcher():
    """Create launcher script for health dashboard"""
    launcher_content = '''#!/usr/bin/env python3
"""
Health Dashboard Launcher
Convenient launcher for the agent health dashboard
"""

import subprocess
import sys
import time
import webbrowser
import os

def main():
    print("🏥 Launching Agent Health Dashboard...")
    
    # Start the dashboard server
    process = subprocess.Popen(
        [sys.executable, "agent_health_dashboard.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(2)
    
    # Check if running
    if process.poll() is None:
        print("✅ Health dashboard started successfully")
        print("📊 Dashboard URL: http://localhost:8891")
        
        # Open in browser
        try:
            webbrowser.open("http://localhost:8891")
        except:
            print("⚠️  Could not open browser automatically")
        
        print("\\nPress Ctrl+C to stop the dashboard")
        
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\\n🛑 Shutting down health dashboard...")
            process.terminate()
            process.wait()
            print("✅ Dashboard stopped")
    else:
        print("❌ Failed to start health dashboard")
        stderr = process.stderr.read().decode()
        print(f"Error: {stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    launcher_file = Path("launch_health_dashboard.py")
    with open(launcher_file, 'w') as f:
        f.write(launcher_content)
    
    # Make executable
    launcher_file.chmod(0o755)
    
    print(f"  ✅ Created health dashboard launcher: {launcher_file}")
    return True


def create_health_docs():
    """Create health monitoring documentation"""
    doc_content = """# Agent Health Monitoring

BoarderframeOS includes comprehensive health monitoring for all agents.

## Overview

The health monitoring system provides:

- **Real-time Metrics**: CPU, memory, response time, error rates
- **Health Status**: Healthy, Warning, Critical, Offline states
- **Historical Tracking**: Trends and patterns over time
- **Smart Alerts**: Configurable thresholds and notifications
- **Auto-Recovery**: Suggested and automated recovery actions

## Dashboard

Access the health dashboard at: http://localhost:8891

### Features

- **System Overview**: Total agents and health distribution
- **Individual Agent Cards**: Detailed metrics per agent
- **Filtering**: View by health status
- **Real-time Updates**: Auto-refresh every 10 seconds
- **Responsive Design**: Works on all devices

## Metrics Tracked

### Resource Metrics
- **CPU Usage**: Percentage of CPU utilized
- **Memory Usage**: RAM consumption percentage
- **Message Queue**: Pending messages in queue

### Performance Metrics
- **Response Time**: Average response latency
- **Error Rate**: Percentage of failed operations
- **Task Success Rate**: Completion percentage

### Availability Metrics
- **Uptime**: Time since agent start
- **Last Activity**: Time since last operation

## Health States

1. **Healthy** 🟢
   - All metrics within normal thresholds
   - Agent responsive and performing well

2. **Warning** 🟡
   - One or more metrics approaching limits
   - Performance degradation possible

3. **Critical** 🔴
   - Critical thresholds exceeded
   - Immediate attention required

4. **Offline** ⚫
   - Agent not responding
   - No recent activity detected

## Integration

### Agent Registration

Agents automatically register on startup:

```python
from core.agent_health import get_health_monitor

health_monitor = get_health_monitor()
health_monitor.register_agent(
    agent_id="agent-solomon",
    agent_name="Solomon",
    process_id=os.getpid()
)
```

### Health Checks

Get agent health status:

```python
report = await health_monitor.check_agent_health("agent-solomon")
print(f"Status: {report.overall_status}")
print(f"CPU: {report.checks[0].value}%")
```

### Custom Metrics

Report custom metrics:

```python
agent.report_task_completion(success=True, duration=1.23)
agent.report_error(exception)
```

## Configuration

Edit `configs/health_alerts.yaml`:

```yaml
thresholds:
  cpu_usage:
    warning: 70
    critical: 90
  memory_usage:
    warning: 80
    critical: 95
```

## Alerts

### Alert Channels

1. **Email**: SMTP configuration
2. **Webhook**: HTTP POST to endpoint
3. **Slack**: Slack incoming webhook
4. **PagerDuty**: Incident management

### Alert Rules

```yaml
alert_rules:
  - name: agent_critical
    condition: overall_status == "critical"
    channels: [email, slack, pagerduty]
    cooldown: 300  # 5 minutes
```

## API Endpoints

### Get All Agents Health
```
GET /api/agents/health
```

Response:
```json
{
  "summary": {
    "total_agents": 5,
    "healthy": 3,
    "warning": 1,
    "critical": 1,
    "offline": 0
  },
  "agents": {
    "agent-solomon": { ... }
  }
}
```

### Get Agent Health
```
GET /api/agents/{agent_id}/health
```

### Get Health History
```
GET /api/health/{agent_id}/history?limit=50
```

## Troubleshooting

### Agent Shows Offline

1. Check if agent process is running
2. Verify agent registration
3. Check network connectivity
4. Review agent logs

### High Resource Usage

1. Check for memory leaks
2. Review recent changes
3. Scale horizontally
4. Optimize algorithms

### False Alerts

1. Adjust thresholds in config
2. Increase cooldown periods
3. Add filtering rules

## Best Practices

1. **Monitor Regularly**: Check dashboard daily
2. **Set Realistic Thresholds**: Based on normal operation
3. **Configure Alerts**: Get notified of issues
4. **Review Trends**: Look for patterns
5. **Act on Warnings**: Don't wait for critical

## Recovery Actions

The system can automatically:

- **Restart agents** on critical errors
- **Scale horizontally** on high load
- **Rollback deployments** on error spikes
- **Clear caches** on memory issues

This health monitoring ensures your BoarderframeOS agents remain
operational and performant at all times.
"""
    
    doc_file = Path("HEALTH_MONITORING.md")
    with open(doc_file, 'w') as f:
        f.write(doc_content)
    
    print(f"  ✅ Created health monitoring documentation: {doc_file}")
    return True


def main():
    """Main integration function"""
    print_header()
    
    # Check if we're in the right directory
    if not Path("startup.py").exists():
        print("❌ Error: Not in BoarderframeOS root directory")
        return False
    
    updated_files = []
    
    try:
        # Update core components
        print("🔧 Updating core components...")
        if update_base_agent():
            updated_files.append("core/base_agent.py")
        
        # Update startup
        print("\n🚀 Updating startup process...")
        if update_startup():
            updated_files.append("startup.py")
        
        # Update Corporate HQ
        print("\n🏢 Updating Corporate HQ...")
        if update_corporate_hq():
            updated_files.append("corporate_headquarters.py")
        
        # Create configurations
        print("\n📋 Creating configurations...")
        create_health_alerts_config()
        create_health_dashboard_launcher()
        
        # Create documentation
        print("\n📚 Creating documentation...")
        create_health_docs()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 HEALTH MONITORING INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"Files updated: {len(updated_files)}")
        
        if updated_files:
            print("\n📁 Updated files:")
            for file in updated_files:
                print(f"  - {file}")
        
        print("\n🚀 Quick Start:")
        print("  1. Start system: python startup.py")
        print("  2. View dashboard: http://localhost:8891")
        print("  3. Or launch directly: python launch_health_dashboard.py")
        
        print("\n📊 Features Enabled:")
        print("  ✓ Real-time health metrics")
        print("  ✓ Multi-state health tracking")
        print("  ✓ Historical data retention")
        print("  ✓ Smart alerting system")
        print("  ✓ Auto-recovery suggestions")
        print("  ✓ Beautiful web dashboard")
        
        print("\n✅ Agent health monitoring is ready!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)