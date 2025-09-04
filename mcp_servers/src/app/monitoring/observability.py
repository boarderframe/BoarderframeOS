"""
Comprehensive monitoring and observability for MCP Server Manager
Implements metrics collection, tracing, logging, and alerting
"""
import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum

from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Initialize logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: float
    name: str
    value: float
    tags: Dict[str, str]
    metric_type: MetricType


class MetricsCollector:
    """Centralized metrics collection"""
    
    def __init__(self, namespace: str = "mcp_server"):
        self.namespace = namespace
        self.registry = CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            f'{namespace}_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            f'{namespace}_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.response_size = Histogram(
            f'{namespace}_response_size_bytes',
            'Response size in bytes',
            ['method', 'endpoint'],
            buckets=[100, 1000, 10000, 100000, 1000000, 10000000],
            registry=self.registry
        )
        
        # System metrics
        self.active_connections = Gauge(
            f'{namespace}_active_connections',
            'Number of active connections',
            registry=self.registry
        )
        
        self.cache_hits = Counter(
            f'{namespace}_cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            f'{namespace}_cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_connections = Gauge(
            f'{namespace}_db_connections',
            'Database connection pool status',
            ['status'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            f'{namespace}_db_query_duration_seconds',
            'Database query duration',
            ['query_type'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )
        
        # MCP server metrics
        self.mcp_server_status = Gauge(
            f'{namespace}_mcp_server_status',
            'MCP server status (0=down, 1=up)',
            ['server_name'],
            registry=self.registry
        )
        
        self.mcp_server_latency = Histogram(
            f'{namespace}_mcp_server_latency_seconds',
            'MCP server response latency',
            ['server_name', 'operation'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
        
        # Custom metrics storage
        self.custom_metrics: Dict[str, Any] = {}
        
    def record_request(self, method: str, endpoint: str, status: int, duration: float, size: int):
        """Record HTTP request metrics"""
        self.request_count.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
        self.response_size.labels(method=method, endpoint=endpoint).observe(size)
        
    def record_cache(self, cache_type: str, hit: bool):
        """Record cache hit/miss"""
        if hit:
            self.cache_hits.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type).inc()
            
    def record_db_query(self, query_type: str, duration: float):
        """Record database query metrics"""
        self.db_query_duration.labels(query_type=query_type).observe(duration)
        
    def set_db_connections(self, active: int, idle: int, overflow: int):
        """Set database connection pool metrics"""
        self.db_connections.labels(status='active').set(active)
        self.db_connections.labels(status='idle').set(idle)
        self.db_connections.labels(status='overflow').set(overflow)
        
    def set_mcp_server_status(self, server_name: str, is_up: bool):
        """Set MCP server status"""
        self.mcp_server_status.labels(server_name=server_name).set(1 if is_up else 0)
        
    def record_mcp_latency(self, server_name: str, operation: str, latency: float):
        """Record MCP server operation latency"""
        self.mcp_server_latency.labels(server_name=server_name, operation=operation).observe(latency)
        
    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest(self.registry)


class TracingManager:
    """Distributed tracing management"""
    
    def __init__(self, service_name: str = "mcp-server-manager", otlp_endpoint: Optional[str] = None):
        self.service_name = service_name
        
        # Configure resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })
        
        # Setup tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter if configured
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            span_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
        trace.set_tracer_provider(self.tracer_provider)
        self.tracer = trace.get_tracer(__name__)
        
    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Create a new span for tracing"""
        span = self.tracer.start_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span
        
    def instrument_app(self, app):
        """Instrument FastAPI application"""
        FastAPIInstrumentor.instrument_app(app)
        
    def instrument_redis(self):
        """Instrument Redis client"""
        RedisInstrumentor().instrument()
        
    def instrument_sqlalchemy(self, engine):
        """Instrument SQLAlchemy engine"""
        SQLAlchemyInstrumentor().instrument(engine=engine)


class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, Dict] = {}
        self._running = False
        
    def register_check(self, name: str, check_func: Callable, interval: int = 30):
        """Register a health check"""
        self.checks[name] = {
            'func': check_func,
            'interval': interval,
            'last_check': 0
        }
        
    async def run_checks(self):
        """Run all registered health checks"""
        current_time = time.time()
        
        for name, check_info in self.checks.items():
            if current_time - check_info['last_check'] >= check_info['interval']:
                try:
                    is_healthy = await check_info['func']()
                    self.health_status[name] = {
                        'healthy': is_healthy,
                        'last_check': current_time,
                        'error': None
                    }
                except Exception as e:
                    self.health_status[name] = {
                        'healthy': False,
                        'last_check': current_time,
                        'error': str(e)
                    }
                check_info['last_check'] = current_time
                
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        self._running = True
        while self._running:
            await self.run_checks()
            await asyncio.sleep(10)  # Check every 10 seconds
            
    def stop_monitoring(self):
        """Stop health monitoring"""
        self._running = False
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        overall_healthy = all(
            status.get('healthy', False) 
            for status in self.health_status.values()
        )
        
        return {
            'healthy': overall_healthy,
            'checks': self.health_status,
            'timestamp': datetime.now().isoformat()
        }


class PerformanceAnalyzer:
    """Real-time performance analysis"""
    
    def __init__(self, window_size: int = 300):  # 5 minute window
        self.window_size = window_size
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.anomaly_thresholds: Dict[str, float] = {}
        
    def add_metric(self, metric: PerformanceMetric):
        """Add metric to analysis buffer"""
        key = f"{metric.name}:{json.dumps(metric.tags, sort_keys=True)}"
        self.metrics_buffer[key].append(metric)
        
    def set_anomaly_threshold(self, metric_name: str, threshold: float):
        """Set anomaly detection threshold"""
        self.anomaly_thresholds[metric_name] = threshold
        
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect performance anomalies"""
        anomalies = []
        
        for key, metrics in self.metrics_buffer.items():
            if len(metrics) < 10:  # Need minimum data points
                continue
                
            metric_name = metrics[0].name
            if metric_name not in self.anomaly_thresholds:
                continue
                
            values = [m.value for m in metrics]
            avg = sum(values) / len(values)
            std_dev = (sum((x - avg) ** 2 for x in values) / len(values)) ** 0.5
            
            # Check for values outside threshold standard deviations
            threshold = self.anomaly_thresholds[metric_name]
            for metric in metrics[-5:]:  # Check recent metrics
                if abs(metric.value - avg) > threshold * std_dev:
                    anomalies.append({
                        'metric': metric_name,
                        'value': metric.value,
                        'average': avg,
                        'std_dev': std_dev,
                        'timestamp': metric.timestamp,
                        'tags': metric.tags
                    })
                    
        return anomalies
        
    def get_statistics(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        all_values = []
        
        for key, metrics in self.metrics_buffer.items():
            if metrics and metrics[0].name == metric_name:
                all_values.extend([m.value for m in metrics])
                
        if not all_values:
            return {}
            
        all_values.sort()
        n = len(all_values)
        
        return {
            'count': n,
            'min': all_values[0],
            'max': all_values[-1],
            'mean': sum(all_values) / n,
            'median': all_values[n // 2],
            'p95': all_values[int(n * 0.95)],
            'p99': all_values[int(n * 0.99)]
        }


class AlertManager:
    """Alert management and notification"""
    
    def __init__(self):
        self.alert_rules: List[Dict] = []
        self.active_alerts: Dict[str, Dict] = {}
        self.alert_handlers: List[Callable] = []
        
    def add_rule(self, name: str, condition: Callable, severity: str = "warning"):
        """Add alert rule"""
        self.alert_rules.append({
            'name': name,
            'condition': condition,
            'severity': severity
        })
        
    def add_handler(self, handler: Callable):
        """Add alert handler (e.g., email, Slack)"""
        self.alert_handlers.append(handler)
        
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check alert conditions"""
        for rule in self.alert_rules:
            try:
                should_alert = await rule['condition'](metrics)
                
                if should_alert and rule['name'] not in self.active_alerts:
                    # New alert
                    alert = {
                        'name': rule['name'],
                        'severity': rule['severity'],
                        'triggered_at': datetime.now(),
                        'metrics': metrics
                    }
                    self.active_alerts[rule['name']] = alert
                    await self._send_alert(alert)
                    
                elif not should_alert and rule['name'] in self.active_alerts:
                    # Alert resolved
                    resolved_alert = self.active_alerts.pop(rule['name'])
                    resolved_alert['resolved_at'] = datetime.now()
                    await self._send_resolution(resolved_alert)
                    
            except Exception as e:
                logger.error(f"Error checking alert {rule['name']}: {e}")
                
    async def _send_alert(self, alert: Dict):
        """Send alert to all handlers"""
        for handler in self.alert_handlers:
            try:
                await handler(alert, is_resolution=False)
            except Exception as e:
                logger.error(f"Error sending alert: {e}")
                
    async def _send_resolution(self, alert: Dict):
        """Send alert resolution to all handlers"""
        for handler in self.alert_handlers:
            try:
                await handler(alert, is_resolution=True)
            except Exception as e:
                logger.error(f"Error sending resolution: {e}")


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request monitoring"""
    
    def __init__(self, app, metrics_collector: MetricsCollector):
        super().__init__(app)
        self.metrics = metrics_collector
        
    async def dispatch(self, request: Request, call_next):
        """Monitor request execution"""
        start_time = time.time()
        
        # Track active connections
        self.metrics.active_connections.inc()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Get response size
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
                
            # Record metrics
            self.metrics.record_request(
                method=request.method,
                endpoint=str(request.url.path),
                status=response.status_code,
                duration=duration,
                size=len(response_body)
            )
            
            # Add monitoring headers
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            response.headers["X-Server-Time"] = str(int(time.time()))
            
            # Return response with body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
        finally:
            self.metrics.active_connections.dec()


class DashboardData:
    """Real-time dashboard data provider"""
    
    def __init__(self, metrics: MetricsCollector, analyzer: PerformanceAnalyzer):
        self.metrics = metrics
        self.analyzer = analyzer
        
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for dashboard display"""
        return {
            'request_rate': self._calculate_rate('requests'),
            'error_rate': self._calculate_error_rate(),
            'response_time': self.analyzer.get_statistics('response_time'),
            'active_connections': self.metrics.active_connections._value.get(),
            'cache_hit_ratio': self._calculate_cache_hit_ratio(),
            'anomalies': self.analyzer.detect_anomalies(),
            'timestamp': datetime.now().isoformat()
        }
        
    def _calculate_rate(self, metric: str) -> float:
        """Calculate rate per second"""
        # Implementation depends on metric storage
        return 0.0
        
    def _calculate_error_rate(self) -> float:
        """Calculate error rate"""
        # Implementation depends on metric storage
        return 0.0
        
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        # Implementation depends on metric storage
        return 0.0