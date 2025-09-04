# MCP Server Process Monitoring Service

A comprehensive Python process monitoring service for MCP servers that provides real-time process monitoring, health checking, and resource tracking using `psutil`.

## 🎯 Features

- **Real-time Process Monitoring**: Continuous monitoring of CPU, memory, and other system resources
- **Process Health Assessment**: Automated health checks with configurable thresholds  
- **Performance Trends**: Historical data tracking and trend analysis
- **Alert System**: Configurable alerts for process health issues
- **Process Discovery**: Automatic discovery of MCP-related processes
- **Lifecycle Management**: Start, stop, restart processes with monitoring integration
- **Comprehensive Metrics**: Extended process metrics including I/O, threads, file descriptors

## 📁 File Structure

```
src/app/services/
├── process_monitor.py          # Core monitoring service
├── process_manager.py          # Process lifecycle management  
├── integration_example.py      # Integration example and usage patterns
└── __init__.py                # Service exports

tests/unit/
└── test_process_monitor.py     # Comprehensive test suite
```

## 🚀 Quick Start

### Basic Usage

```python
from app.services.process_monitor import ProcessMonitor

# Initialize monitor
monitor = ProcessMonitor(
    monitoring_interval=5.0,      # Monitor every 5 seconds
    health_check_interval=30.0,   # Health checks every 30 seconds
    enable_alerts=True            # Enable alerting
)

# Start monitoring system
await monitor.start_monitoring()

# Add a process to monitor
monitor.add_process('my_server', pid=12345)

# Get real-time metrics
metrics = monitor.get_process_metrics('my_server')
print(f"CPU: {metrics.cpu_percent}%, Memory: {metrics.memory_mb}MB")

# Check process health
health = monitor.get_process_health('my_server')
print(f"Healthy: {health.is_healthy}, Issues: {health.issues}")

# Stop monitoring
await monitor.stop_monitoring()
```

### Integrated Service Usage

```python
from app.services.integration_example import MCPProcessService

# Initialize integrated service
service = MCPProcessService()
await service.start_service()

# Start an MCP server with monitoring
result = await service.start_mcp_server(
    server_id='my_mcp_server',
    name='My MCP Server',
    command=['python', '-m', 'my_mcp_server'],
    working_directory='/path/to/server'
)

# Get comprehensive status with real metrics
status = service.get_server_status('my_mcp_server')
print(f"Status: {status['status']}")
print(f"CPU: {status['metrics']['cpu_percent']}%")
print(f"Memory: {status['metrics']['memory_mb']}MB")
print(f"Health: {'Healthy' if status['health']['is_healthy'] else 'Issues'}")

# Stop server and monitoring
await service.stop_mcp_server('my_mcp_server')
await service.stop_service()
```

## 📊 Metrics Collected

### Basic Metrics (ProcessMetrics)
- **CPU Usage**: Current CPU percentage
- **Memory Usage**: RSS memory in MB and percentage
- **Uptime**: Process uptime in seconds  
- **Status**: Process status (running, sleeping, etc.)
- **Threads**: Number of threads
- **File Descriptors**: Number of open file descriptors/handles

### Extended Metrics (ExtendedProcessMetrics)
- **CPU Times**: User and system CPU time
- **Memory Details**: RSS, VMS, shared memory
- **I/O Statistics**: Read/write counts and bytes
- **Context Switches**: Voluntary and involuntary
- **Process Info**: Command line, executable path, working directory
- **Relationships**: Parent PID, child PIDs
- **Network**: Open connections count
- **Files**: Open files count

### Health Metrics
- **Health Status**: Overall health assessment
- **Issues List**: Specific problems detected
- **Warning/Error Counts**: Severity categorization
- **Last Check Time**: When health was last assessed

### Performance Trends
- **CPU History**: Historical CPU usage data
- **Memory History**: Historical memory usage data  
- **Averages**: Average CPU and memory usage
- **Peaks**: Peak resource usage values

## 🔧 Configuration

### Alert Thresholds

```python
monitor.set_alert_threshold('cpu_percent', 80.0)      # CPU > 80%
monitor.set_alert_threshold('memory_percent', 85.0)   # Memory > 85%
monitor.set_alert_threshold('memory_mb', 1024.0)      # Memory > 1GB
monitor.set_alert_threshold('file_descriptors', 1000) # FDs > 1000
monitor.set_alert_threshold('thread_count', 100)      # Threads > 100
```

### Alert Callbacks

```python
def handle_alert(alert):
    print(f"ALERT: {alert.server_id} - {alert.message}")
    if alert.severity == 'critical':
        # Implement auto-restart logic
        pass

monitor.add_alert_callback(handle_alert)
```

### Monitoring Intervals

```python
monitor = ProcessMonitor(
    monitoring_interval=1.0,      # Fast monitoring (1s)
    health_check_interval=10.0,   # Frequent health checks (10s)
    trend_window_size=120,        # Keep 2 minutes of history
    enable_alerts=True
)
```

## 🔍 Process Discovery

Automatically discover MCP-related processes:

```python
# Discover existing MCP processes
discovered = await monitor.discover_mcp_processes()
for proc in discovered:
    print(f"Found: PID {proc['pid']} - {proc['name']} - {proc['cmdline']}")
    
    if not proc['is_monitored']:
        # Add to monitoring
        monitor.add_process(f"discovered_{proc['pid']}", proc['pid'])
```

## 📈 Health Assessment

The system automatically assesses process health based on:

- **CPU Usage**: Alerts when CPU usage exceeds thresholds
- **Memory Usage**: Monitors both absolute and percentage memory usage
- **Process State**: Detects zombie, stopped, or dead processes
- **Resource Limits**: Tracks file descriptors and thread counts
- **Performance Trends**: Identifies degrading performance over time

Health levels:
- ✅ **Healthy**: All metrics within normal ranges
- ⚠️ **Warning**: Some metrics elevated but not critical
- ❌ **Error**: Critical issues detected requiring attention

## 🚨 Alert System

### Alert Types
- `high_cpu`: CPU usage above threshold
- `high_memory`: Memory usage above threshold  
- `process_health`: General health issues
- `resource_limit`: File descriptor/thread limits exceeded

### Alert Severities
- `info`: Informational alerts
- `warning`: Elevated metrics, monitoring required
- `error`: Significant issues, intervention recommended
- `critical`: Severe problems, immediate action required

### Managing Alerts

```python
# Get all alerts
alerts = monitor.get_alerts()

# Get alerts for specific server
server_alerts = monitor.get_alerts('my_server')

# Clear alerts
monitor.clear_alerts()           # Clear all
monitor.clear_alerts('my_server') # Clear for specific server
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Set Python path and run tests
PYTHONPATH=src python -m pytest tests/unit/test_process_monitor.py -v

# Run integration tests
PYTHONPATH=src python -c "
from app.services.integration_example import example_usage
import asyncio
asyncio.run(example_usage())
"
```

### Test Coverage

The test suite includes:
- Unit tests for all core functionality
- Mock-based testing for psutil integration
- Integration tests with real processes
- Health assessment validation
- Alert system testing
- Trend calculation verification
- Error handling and edge cases

## 🔧 Integration with Existing Code

### Replace Hardcoded Data

**Before** (hardcoded data):
```python
def get_server_metrics(server_id):
    return {
        'cpu_percent': 45.2,  # Fake data
        'memory_mb': 256.0,   # Fake data
        'status': 'running'   # Fake data
    }
```

**After** (real monitoring):
```python
def get_server_metrics(server_id):
    return process_monitor.get_process_metrics(server_id)
```

### API Integration

```python
from fastapi import APIRouter
from app.services import process_monitor

router = APIRouter()

@router.get("/servers/{server_id}/metrics")
async def get_server_metrics(server_id: str):
    metrics = process_monitor.get_process_metrics(server_id)
    if not metrics:
        raise HTTPException(404, "Server not found or not monitored")
    return metrics

@router.get("/servers/{server_id}/health")
async def get_server_health(server_id: str):
    health = process_monitor.get_process_health(server_id)
    if not health:
        raise HTTPException(404, "Server not found or not monitored") 
    return health

@router.get("/servers/{server_id}/alerts")
async def get_server_alerts(server_id: str):
    return process_monitor.get_alerts(server_id)
```

## 🏗️ Architecture

### Core Components

1. **ProcessMonitor**: Main monitoring service
   - Metrics collection using psutil
   - Health assessment and alerting
   - Process discovery and lifecycle tracking

2. **ProcessManager**: Process lifecycle management
   - Start, stop, restart processes
   - Process state management
   - Error handling and recovery

3. **MCPProcessService**: Integrated service
   - Combines monitoring and management
   - Provides unified API for MCP server operations
   - Handles alerts and auto-recovery

### Data Flow

```
Process → psutil → ProcessMonitor → Metrics/Health/Alerts
                                 ↓
API Endpoints ← MCPProcessService ← ProcessManager
```

## 🛡️ Error Handling

The service includes comprehensive error handling for:

- **Process Access Denied**: Graceful handling when process permissions are insufficient
- **Process Not Found**: Detection and cleanup of dead processes
- **Zombie Processes**: Identification and alerting for zombie states
- **Resource Exhaustion**: Monitoring and alerting for resource limits
- **Collection Failures**: Retry logic and fallback mechanisms

## 📋 Performance Considerations

- **Efficient Polling**: Configurable intervals to balance accuracy vs. performance
- **Memory Management**: Automatic cleanup of old trend data
- **CPU Usage**: Minimal overhead from monitoring itself
- **Scalability**: Can monitor dozens of processes simultaneously
- **Resource Limits**: Built-in protection against resource exhaustion

## 🔮 Future Enhancements

- **Metrics Persistence**: Store historical data in database
- **Grafana Integration**: Real-time dashboards and visualization
- **Machine Learning**: Predictive analytics for process behavior
- **Auto-scaling**: Automatic resource adjustment based on metrics
- **Custom Metrics**: Plugin system for domain-specific monitoring
- **Distributed Monitoring**: Multi-node process monitoring

## 📚 Dependencies

- **psutil**: Cross-platform process and system monitoring
- **asyncio**: Async/await support for concurrent monitoring
- **datetime**: Time handling and calculations
- **logging**: Comprehensive logging throughout the system
- **pydantic**: Data validation and serialization (for schemas)

## 🤝 Contributing

When extending the monitoring service:

1. **Add Tests**: Include comprehensive test coverage for new features
2. **Update Documentation**: Document new capabilities and configuration options
3. **Performance Testing**: Ensure new features don't impact monitoring performance
4. **Error Handling**: Include proper error handling and logging
5. **Backward Compatibility**: Maintain compatibility with existing integrations

---

This process monitoring service replaces hardcoded data with real, live process monitoring capabilities, providing comprehensive insights into MCP server performance and health.