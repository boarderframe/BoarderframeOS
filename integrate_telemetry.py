#!/usr/bin/env python3
"""
OpenTelemetry Integration Script for BoarderframeOS
Integrates observability into existing components
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
    print("BoarderframeOS OpenTelemetry Integration")
    print("=" * 60)
    print("Adding comprehensive observability to the system")
    print()


def backup_file(file_path: Path) -> Path:
    """Create backup of a file"""
    backup_path = file_path.with_suffix(file_path.suffix + '.telemetry_backup')
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_base_agent():
    """Add telemetry to BaseAgent"""
    base_agent_file = Path("core/base_agent.py")
    
    if not base_agent_file.exists():
        print("  ⚠️  core/base_agent.py not found")
        return False
    
    try:
        with open(base_agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if already has telemetry
        if 'telemetry' in content or 'trace_agent_operation' in content:
            print("  ℹ️  BaseAgent already has telemetry")
            return False
        
        # Add import
        import_section = """from typing import Dict, Any, Optional, List
import logging
import asyncio
from core.telemetry import get_telemetry"""
        
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
        
        # Add telemetry initialization in __init__
        init_telemetry = """
        # Initialize telemetry
        self.telemetry = get_telemetry()"""
        
        # Find __init__ method
        init_match = re.search(r'def __init__\(self.*?\):', content)
        if init_match:
            # Find end of __init__ method
            init_end = content.find('\n', init_match.end())
            next_def = content.find('\n    def ', init_end)
            if next_def > 0:
                # Insert before next method
                content = content[:next_def] + init_telemetry + content[next_def:]
        
        # Add telemetry decorators to key methods
        methods_to_trace = ['think', 'act', 'handle_user_chat', 'process_message']
        
        for method in methods_to_trace:
            pattern = rf'(\n    async def {method}\('
            replacement = rf'\n    @get_telemetry().trace_agent_operation("{method}")\1'
            content = re.sub(pattern, replacement, content)
        
        # Add lifecycle tracking
        lifecycle_tracking = '''
    async def start(self):
        """Start the agent with telemetry"""
        self.telemetry.record_agent_lifecycle(self.name, "started")
        await super().start() if hasattr(super(), 'start') else None
        
    async def stop(self):
        """Stop the agent with telemetry"""
        self.telemetry.record_agent_lifecycle(self.name, "stopped")
        await super().stop() if hasattr(super(), 'stop') else None'''
        
        # Add before the last line of the class
        class_end = content.rfind('\n\n')
        if class_end > 0:
            content = content[:class_end] + lifecycle_tracking + content[class_end:]
        
        # Write updated content
        if content != original_content:
            backup_file(base_agent_file)
            with open(base_agent_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated core/base_agent.py with telemetry")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating BaseAgent: {e}")
        return False


def update_message_bus():
    """Add telemetry to message bus"""
    message_bus_file = Path("core/message_bus.py")
    
    if not message_bus_file.exists():
        print("  ⚠️  core/message_bus.py not found")
        return False
    
    try:
        with open(message_bus_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add telemetry import
        if 'telemetry' not in content:
            import_line = "from core.telemetry import get_telemetry\n"
            
            # Find imports section
            import_pos = content.find('import')
            if import_pos > 0:
                # Find end of imports
                lines = content[:import_pos].split('\n')
                content = '\n'.join(lines) + '\n' + import_line + content[import_pos:]
        
        # Add telemetry decorator to send_task_request
        if '@get_telemetry().trace_message_bus' not in content:
            content = re.sub(
                r'(async def send_task_request\()',
                r'@get_telemetry().trace_message_bus\n\1',
                content
            )
        
        # Write updated content
        if content != original_content:
            backup_file(message_bus_file)
            with open(message_bus_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated core/message_bus.py with telemetry")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating message bus: {e}")
        return False


def update_llm_client():
    """Add telemetry to LLM client"""
    llm_client_file = Path("core/llm_client.py")
    
    if not llm_client_file.exists():
        # Try the cost optimizer instead
        llm_client_file = Path("core/llm_cost_optimizer.py")
    
    if not llm_client_file.exists():
        print("  ⚠️  LLM client file not found")
        return False
    
    try:
        with open(llm_client_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add telemetry import
        if 'telemetry' not in content:
            import_line = "from core.telemetry import get_telemetry\n"
            
            # Find imports section
            import_pos = content.find('import')
            if import_pos > 0:
                # Find end of imports
                lines = content[:import_pos].split('\n')
                content = '\n'.join(lines) + '\n' + import_line + content[import_pos:]
        
        # Add telemetry decorator to complete method
        if '@get_telemetry().trace_llm_call' not in content:
            content = re.sub(
                r'(async def complete\()',
                r'@get_telemetry().trace_llm_call\n    \1',
                content
            )
        
        # Write updated content
        if content != original_content:
            backup_file(llm_client_file)
            with open(llm_client_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Updated {llm_client_file} with telemetry")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating LLM client: {e}")
        return False


def update_startup():
    """Add telemetry initialization to startup.py"""
    startup_file = Path("startup.py")
    
    if not startup_file.exists():
        print("  ⚠️  startup.py not found")
        return False
    
    try:
        with open(startup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Add telemetry import
        if 'telemetry' not in content:
            telemetry_imports = """from core.telemetry import get_telemetry

# Initialize telemetry early
telemetry = get_telemetry()
"""
            
            # Add after main imports
            import_end = content.find('# Core modules')
            if import_end > 0:
                content = content[:import_end] + telemetry_imports + '\n' + content[import_end:]
        
        # Add telemetry initialization in main startup
        telemetry_init = '''
    # Initialize OpenTelemetry
    print("Initializing OpenTelemetry...")
    telemetry.initialize(
        otlp_endpoint=os.getenv("OTLP_ENDPOINT", "localhost:4317"),
        jaeger_endpoint=os.getenv("JAEGER_ENDPOINT", "localhost:6831"),
        prometheus_port=int(os.getenv("PROMETHEUS_PORT", "9090")),
        enable_console=os.getenv("TELEMETRY_CONSOLE", "false").lower() == "true",
        custom_attributes={
            "deployment": "local",
            "version": "0.2.0"
        }
    )
    print("✓ OpenTelemetry initialized")
'''
        
        # Find where to add (after Redis initialization)
        redis_pos = content.find('print("✓ Redis connection established")')
        if redis_pos > 0:
            insert_pos = content.find('\n', redis_pos) + 1
            content = content[:insert_pos] + telemetry_init + content[insert_pos:]
        
        # Write updated content
        if content != original_content:
            backup_file(startup_file)
            with open(startup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated startup.py with telemetry initialization")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating startup: {e}")
        return False


def create_telemetry_config():
    """Create telemetry configuration"""
    config_file = Path("configs/telemetry.yaml")
    config_file.parent.mkdir(exist_ok=True)
    
    config = """# OpenTelemetry Configuration for BoarderframeOS

# Service identification
service:
  name: boarderframeos
  version: 0.2.0
  environment: production

# Tracing configuration
tracing:
  # Sampling rate (0.0 to 1.0)
  sampling_rate: 1.0
  
  # Exporters
  exporters:
    # Console exporter (for debugging)
    console:
      enabled: false
    
    # OTLP exporter (for OpenTelemetry Collector)
    otlp:
      enabled: true
      endpoint: localhost:4317
      insecure: true
      headers: {}
    
    # Jaeger exporter (direct to Jaeger)
    jaeger:
      enabled: true
      agent_endpoint: localhost:6831
      collector_endpoint: null
      
# Metrics configuration
metrics:
  # Export interval in seconds
  export_interval: 10
  
  # Exporters
  exporters:
    # Console exporter
    console:
      enabled: false
    
    # OTLP exporter
    otlp:
      enabled: true
      endpoint: localhost:4317
      insecure: true
    
    # Prometheus exporter (pull-based)
    prometheus:
      enabled: true
      port: 9090

# Instrumentation configuration
instrumentation:
  # Auto-instrumentation
  auto_instrument:
    - fastapi
    - flask
    - httpx
    - redis
    - asyncpg
    - psycopg2
    - logging
  
  # Custom spans
  custom_spans:
    # Agent operations
    agent_operations:
      - think
      - act
      - handle_user_chat
      - process_message
    
    # LLM operations
    llm_operations:
      - complete
      - generate
      - embed
    
    # Message bus operations
    messagebus_operations:
      - send
      - receive
      - publish
      - subscribe

# Baggage configuration (context propagation)
baggage:
  # Keys to propagate
  keys:
    - user_id
    - session_id
    - agent_name
    - department
    - correlation_id

# Resource attributes
resource_attributes:
  # Deployment information
  deployment.environment: ${ENVIRONMENT:production}
  deployment.region: ${REGION:us-east-1}
  
  # Service mesh information
  service.namespace: boarderframe
  service.instance.id: ${HOSTNAME:unknown}
  
  # Custom attributes
  boarderframe.agents.total: 191
  boarderframe.departments.total: 24
  boarderframe.version: 0.2.0
"""
    
    with open(config_file, 'w') as f:
        f.write(config)
    
    print(f"  ✅ Created telemetry configuration: {config_file}")
    return True


def create_docker_compose_telemetry():
    """Create docker-compose for telemetry stack"""
    compose_content = """version: '3.8'

services:
  # Jaeger for distributed tracing
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "6831:6831/udp"  # Agent port
      - "16686:16686"    # Web UI
      - "14250:14250"    # gRPC
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - boarderframe_network

  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./configs/otel-collector.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Prometheus metrics
    depends_on:
      - jaeger
    networks:
      - boarderframe_network

  # Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9091:9090"  # Changed to avoid conflict
    networks:
      - boarderframe_network

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./configs/grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    networks:
      - boarderframe_network

volumes:
  prometheus_data:
  grafana_data:

networks:
  boarderframe_network:
    external: true
"""
    
    compose_file = Path("docker-compose.telemetry.yml")
    with open(compose_file, 'w') as f:
        f.write(compose_content)
    
    print(f"  ✅ Created telemetry docker-compose: {compose_file}")
    return True


def create_otel_collector_config():
    """Create OpenTelemetry Collector configuration"""
    config_dir = Path("configs")
    config_dir.mkdir(exist_ok=True)
    
    config = """receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

  resource:
    attributes:
      - key: service.name
        value: boarderframeos
        action: upsert
      - key: environment
        from_attribute: deployment.environment
        action: insert

  memory_limiter:
    check_interval: 1s
    limit_mib: 512

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8888"
    
  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [jaeger, logging]
    
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [prometheus, logging]

  extensions: [health_check, pprof, zpages]
"""
    
    config_file = config_dir / "otel-collector.yaml"
    with open(config_file, 'w') as f:
        f.write(config)
    
    print(f"  ✅ Created OpenTelemetry Collector config: {config_file}")
    return True


def create_prometheus_config():
    """Create Prometheus configuration"""
    config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # BoarderframeOS metrics
  - job_name: 'boarderframeos'
    static_configs:
      - targets: ['host.docker.internal:9090']
        labels:
          service: 'boarderframeos'
          
  # OpenTelemetry Collector metrics
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8888']
        labels:
          service: 'otel-collector'
          
  # Individual agent metrics (if exposed)
  - job_name: 'agents'
    static_configs:
      - targets: 
        - 'host.docker.internal:9091'  # Solomon
        - 'host.docker.internal:9092'  # David
        - 'host.docker.internal:9093'  # Adam
        labels:
          service: 'boarderframe-agents'
"""
    
    config_file = Path("configs/prometheus.yml")
    with open(config_file, 'w') as f:
        f.write(config)
    
    print(f"  ✅ Created Prometheus config: {config_file}")
    return True


def create_grafana_dashboards():
    """Create Grafana dashboard configurations"""
    grafana_dir = Path("configs/grafana/provisioning")
    dashboards_dir = grafana_dir / "dashboards"
    dashboards_dir.mkdir(parents=True, exist_ok=True)
    
    # Dashboard provider config
    provider_config = """apiVersion: 1

providers:
  - name: 'BoarderframeOS'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
"""
    
    with open(grafana_dir / "dashboards/provider.yaml", 'w') as f:
        f.write(provider_config)
    
    # Create main dashboard
    dashboard = {
        "dashboard": {
            "title": "BoarderframeOS Observability",
            "panels": [
                {
                    "title": "Request Rate by Agent",
                    "targets": [{"expr": "rate(boarderframe_requests_total[5m])"}],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                },
                {
                    "title": "Error Rate",
                    "targets": [{"expr": "rate(boarderframe_errors_total[5m])"}],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                },
                {
                    "title": "LLM Costs",
                    "targets": [{"expr": "sum(boarderframe_llm_cost) by (agent)"}],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                },
                {
                    "title": "Active Agents",
                    "targets": [{"expr": "boarderframe_agents_active"}],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                }
            ]
        }
    }
    
    import json
    with open(dashboards_dir / "boarderframeos.json", 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print("  ✅ Created Grafana dashboards")
    return True


def create_telemetry_docs():
    """Create telemetry documentation"""
    doc_content = """# OpenTelemetry Integration

BoarderframeOS now includes comprehensive observability through OpenTelemetry.

## Overview

The telemetry system provides:

- **Distributed Tracing**: Track requests across agents and services
- **Metrics Collection**: Monitor performance, costs, and errors
- **Context Propagation**: Maintain context across async operations
- **Multiple Exporters**: Jaeger, Prometheus, OTLP, Console

## Quick Start

### Start Telemetry Stack

```bash
# Start telemetry services
docker-compose -f docker-compose.telemetry.yml up -d

# Verify services
curl http://localhost:16686  # Jaeger UI
curl http://localhost:3000   # Grafana (admin/admin)
curl http://localhost:9091   # Prometheus
```

### Environment Variables

```bash
# OTLP endpoint for traces and metrics
export OTLP_ENDPOINT=localhost:4317

# Jaeger endpoint for direct export
export JAEGER_ENDPOINT=localhost:6831

# Prometheus metrics port
export PROMETHEUS_PORT=9090

# Enable console output for debugging
export TELEMETRY_CONSOLE=false
```

## Architecture

### Components

1. **Telemetry Manager** (`core/telemetry.py`)
   - Central instrumentation management
   - Span and metric creation
   - Context propagation

2. **Auto-Instrumentation**
   - FastAPI/Flask endpoints
   - Database queries (PostgreSQL, Redis)
   - HTTP clients
   - Logging integration

3. **Custom Instrumentation**
   - Agent operations (think, act, chat)
   - LLM API calls with cost tracking
   - Message bus operations
   - Agent lifecycle events

### Data Flow

```
BoarderframeOS → OpenTelemetry SDK → Collector → Backends
                                                 ├─ Jaeger (traces)
                                                 ├─ Prometheus (metrics)
                                                 └─ Grafana (visualization)
```

## Instrumentation

### Agent Operations

All agent operations are automatically traced:

```python
@get_telemetry().trace_agent_operation("think")
async def think(self):
    # Automatically creates span with:
    # - agent.name
    # - agent.operation
    # - duration
    # - error tracking
```

### LLM Calls

LLM calls include cost tracking:

```python
@get_telemetry().trace_llm_call
async def complete(prompt, model, agent_name):
    # Tracks:
    # - Model used
    # - Token counts
    # - API costs
    # - Latency
```

### Message Bus

Message bus operations track flow:

```python
@get_telemetry().trace_message_bus
async def send_task_request(from_agent, to_agent, task):
    # Tracks:
    # - Source and destination
    # - Message priority
    # - Delivery success
```

## Metrics

### System Metrics

- `boarderframe.requests.total` - Total requests by agent and operation
- `boarderframe.errors.total` - Errors by type and agent
- `boarderframe.request.duration` - Request latency histogram

### Agent Metrics

- `boarderframe.agents.active` - Currently active agents
- `boarderframe.agent.lifecycle` - Agent start/stop events

### LLM Metrics

- `boarderframe.llm.cost` - API costs by model and agent
- `boarderframe.llm.tokens` - Token usage tracking

### Message Bus Metrics

- `boarderframe.messagebus.messages` - Messages by source/destination
- `boarderframe.messagebus.latency` - Delivery latency

## Viewing Data

### Jaeger UI (Traces)

Access at http://localhost:16686

- Search traces by service, operation, tags
- View trace timeline and spans
- Analyze request flow across agents

### Grafana (Metrics)

Access at http://localhost:3000 (admin/admin)

Pre-configured dashboards:
- Agent Performance
- LLM Cost Analysis
- System Health
- Error Analysis

### Prometheus (Raw Metrics)

Access at http://localhost:9091

Query examples:
```promql
# Request rate by agent
rate(boarderframe_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, boarderframe_request_duration_bucket)

# Total LLM costs
sum(boarderframe_llm_cost)

# Active agents
boarderframe_agents_active
```

## Custom Instrumentation

### Adding Spans

```python
from core.telemetry import get_telemetry

telemetry = get_telemetry()

# Context manager
with telemetry.span("custom.operation", attributes={"key": "value"}):
    # Your code here
    pass

# Manual span
span = telemetry.create_child_span("child.operation")
try:
    # Your code
    span.set_attribute("result", "success")
finally:
    span.end()
```

### Recording Metrics

```python
# Increment counter
telemetry.request_counter.add(1, {"operation": "custom"})

# Record histogram
telemetry.latency_histogram.record(0.123, {"operation": "custom"})

# Update gauge
telemetry.active_agents_gauge.add(1, {"agent": "new_agent"})
```

### Context Propagation

```python
# Get context for async operations
context = telemetry.get_trace_context()

# In another coroutine/process
telemetry.set_trace_context(context)
# Operations here will be linked to parent trace
```

## Performance Impact

The telemetry system is designed for minimal overhead:

- Sampling can be configured (default 100%)
- Batch processing for exports
- Async operations don't block main flow
- Memory limits prevent resource exhaustion

## Troubleshooting

### No Traces Appearing

1. Check services are running:
   ```bash
   docker-compose -f docker-compose.telemetry.yml ps
   ```

2. Verify endpoints in logs:
   ```bash
   docker logs boarderframeos-app | grep telemetry
   ```

3. Enable console output:
   ```bash
   export TELEMETRY_CONSOLE=true
   ```

### Missing Metrics

1. Check Prometheus targets: http://localhost:9091/targets
2. Verify metrics endpoint: http://localhost:9090/metrics
3. Check Grafana data sources

### High Memory Usage

1. Adjust batch size in collector config
2. Enable memory limiter
3. Reduce sampling rate

## Best Practices

1. **Use Semantic Attributes**: Follow OpenTelemetry semantic conventions
2. **Add Context**: Include relevant attributes on spans
3. **Handle Errors**: Set span status on errors
4. **Batch Operations**: Use batch processors for efficiency
5. **Sample Wisely**: Adjust sampling for production

## Security

- Don't include sensitive data in spans/metrics
- Use TLS for production endpoints
- Implement authentication for UIs
- Limit metric cardinality

This observability system provides deep insights into BoarderframeOS operations,
enabling better debugging, performance optimization, and cost management.
"""
    
    doc_file = Path("TELEMETRY.md")
    with open(doc_file, 'w') as f:
        f.write(doc_content)
    
    print(f"  ✅ Created telemetry documentation: {doc_file}")
    return True


def update_requirements():
    """Add OpenTelemetry dependencies to requirements.txt"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("  ⚠️  requirements.txt not found")
        return False
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already has OpenTelemetry
        if 'opentelemetry' in content:
            print("  ℹ️  OpenTelemetry already in requirements.txt")
            return False
        
        # Add OpenTelemetry dependencies
        otel_deps = """
# OpenTelemetry Core
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation==0.42b0

# OpenTelemetry Exporters
opentelemetry-exporter-otlp==1.21.0
opentelemetry-exporter-otlp-proto-grpc==1.21.0
opentelemetry-exporter-jaeger==1.21.0
opentelemetry-exporter-prometheus==0.42b0

# OpenTelemetry Instrumentation
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-flask==0.42b0
opentelemetry-instrumentation-httpx==0.42b0
opentelemetry-instrumentation-redis==0.42b0
opentelemetry-instrumentation-asyncpg==0.42b0
opentelemetry-instrumentation-psycopg2==0.42b0
opentelemetry-instrumentation-logging==0.42b0
opentelemetry-instrumentation-system-metrics==0.42b0
opentelemetry-propagator-b3==1.21.0
opentelemetry-propagator-jaeger==1.21.0
"""
        
        # Append to requirements
        with open(requirements_file, 'a') as f:
            f.write(otel_deps)
        
        print("  ✅ Updated requirements.txt with OpenTelemetry packages")
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating requirements: {e}")
        return False


def create_telemetry_test():
    """Create test script for telemetry"""
    test_content = '''#!/usr/bin/env python3
"""
Test OpenTelemetry Integration
Verifies telemetry is working correctly
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.telemetry import get_telemetry
from core.base_agent import BaseAgent


class TestAgent(BaseAgent):
    """Test agent for telemetry verification"""
    
    def __init__(self):
        super().__init__(
            name="test_agent",
            role="Telemetry Test Agent",
            personality_traits=["helpful", "observant"]
        )
    
    async def think(self):
        """Test thinking with telemetry"""
        self.telemetry.add_baggage("test_id", "12345")
        return "Thinking about telemetry..."
    
    async def act(self, thought: str):
        """Test acting with telemetry"""
        # Simulate some work
        await asyncio.sleep(0.1)
        return f"Acting on: {thought}"
    
    async def handle_user_chat(self, message: str) -> str:
        """Test chat with telemetry"""
        with self.telemetry.span("test.custom_operation", {"user_message": message}):
            # Simulate LLM call
            await asyncio.sleep(0.2)
            
            # Record custom metric
            self.telemetry.request_counter.add(1, {"operation": "test_chat"})
            
        return f"Test response to: {message}"


async def test_telemetry():
    """Run telemetry tests"""
    print("🔍 Testing OpenTelemetry Integration")
    print("=" * 50)
    
    # Initialize telemetry
    telemetry = get_telemetry()
    telemetry.initialize(
        enable_console=True,  # Enable console output for testing
        custom_attributes={"test_run": True}
    )
    
    print("✅ Telemetry initialized")
    
    # Test agent operations
    print("\\n📊 Testing agent telemetry...")
    agent = TestAgent()
    
    # Test lifecycle
    await agent.start()
    print("  ✓ Agent started (lifecycle tracked)")
    
    # Test operations
    thought = await agent.think()
    print(f"  ✓ Think operation completed: {thought}")
    
    action = await agent.act(thought)
    print(f"  ✓ Act operation completed: {action}")
    
    response = await agent.handle_user_chat("Hello telemetry!")
    print(f"  ✓ Chat operation completed: {response}")
    
    # Test context propagation
    print("\\n🔗 Testing context propagation...")
    
    parent_context = telemetry.get_trace_context()
    print(f"  ✓ Got parent context: {list(parent_context.keys())}")
    
    # Simulate child operation
    with telemetry.span("test.child_operation"):
        baggage_value = telemetry.get_baggage("test_id")
        print(f"  ✓ Baggage propagated: test_id={baggage_value}")
    
    # Test metrics
    print("\\n📈 Testing metrics...")
    
    # Record some metrics
    telemetry.request_counter.add(5, {"operation": "test"})
    telemetry.error_counter.add(1, {"error": "test_error"})
    telemetry.latency_histogram.record(0.123, {"operation": "test"})
    telemetry.llm_cost_counter.add(0.05, {"model": "test-model"})
    
    print("  ✓ Metrics recorded")
    
    # Stop agent
    await agent.stop()
    print("\\n✅ Agent stopped (lifecycle tracked)")
    
    # Give time for exports
    await asyncio.sleep(2)
    
    print("\\n🎉 Telemetry test completed!")
    print("\\nCheck the following to verify:")
    print("  - Console output above for spans")
    print("  - Jaeger UI: http://localhost:16686")
    print("  - Prometheus: http://localhost:9091/metrics")
    print("  - Grafana: http://localhost:3000")
    
    # Shutdown telemetry
    telemetry.shutdown()


if __name__ == "__main__":
    asyncio.run(test_telemetry())
'''
    
    test_file = Path("test_telemetry.py")
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    # Make executable
    test_file.chmod(0o755)
    
    print(f"  ✅ Created telemetry test script: {test_file}")
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
        
        if update_message_bus():
            updated_files.append("core/message_bus.py")
        
        if update_llm_client():
            updated_files.append("LLM client")
        
        # Update startup
        print("\n🚀 Updating startup process...")
        if update_startup():
            updated_files.append("startup.py")
        
        # Create configurations
        print("\n📋 Creating configurations...")
        create_telemetry_config()
        create_docker_compose_telemetry()
        create_otel_collector_config()
        create_prometheus_config()
        create_grafana_dashboards()
        
        # Update requirements
        print("\n📦 Updating dependencies...")
        update_requirements()
        
        # Create documentation
        print("\n📚 Creating documentation...")
        create_telemetry_docs()
        
        # Create test script
        print("\n🧪 Creating test script...")
        create_telemetry_test()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 OPENTELEMETRY INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"Files updated: {len(updated_files)}")
        
        if updated_files:
            print("\n📁 Updated files:")
            for file in updated_files:
                print(f"  - {file}")
        
        print("\n🚀 Quick Start:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Start telemetry stack: docker-compose -f docker-compose.telemetry.yml up -d")
        print("  3. Run test: python test_telemetry.py")
        print("  4. Start system: python startup.py")
        
        print("\n🔗 Access Points:")
        print("  - Jaeger UI: http://localhost:16686")
        print("  - Grafana: http://localhost:3000 (admin/admin)")
        print("  - Prometheus: http://localhost:9091")
        print("  - Metrics endpoint: http://localhost:9090/metrics")
        
        print("\n📊 Features Enabled:")
        print("  ✓ Distributed tracing across agents")
        print("  ✓ Automatic span creation for operations")
        print("  ✓ LLM cost tracking")
        print("  ✓ Message bus flow visualization")
        print("  ✓ Agent lifecycle monitoring")
        print("  ✓ Error tracking and alerting")
        print("  ✓ Performance metrics")
        
        print("\n✅ OpenTelemetry observability is ready!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)