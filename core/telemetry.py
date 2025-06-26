"""
OpenTelemetry Integration for BoarderframeOS
Provides comprehensive observability for the distributed agent system
"""

import os
import sys
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from contextlib import contextmanager
import time
import logging
from datetime import datetime

# OpenTelemetry core components
from opentelemetry import trace, metrics, baggage
from opentelemetry.context import attach, detach
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.metrics import Meter, Counter, Histogram, UpDownCounter
from opentelemetry.propagate import inject, extract
from opentelemetry.trace.propagation import set_span_in_context

# OpenTelemetry SDK
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource

# OpenTelemetry exporters
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader

# Instrumentation libraries
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Semantic conventions
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)


class TelemetryManager:
    """
    Central manager for OpenTelemetry instrumentation
    
    Features:
    - Distributed tracing across agents
    - Metrics collection (latency, throughput, errors)
    - Custom spans for agent operations
    - Context propagation for async operations
    - Multiple exporter support (Console, Jaeger, OTLP, Prometheus)
    """
    
    def __init__(self, service_name: str = "boarderframeos"):
        self.service_name = service_name
        self.tracer_provider = None
        self.meter_provider = None
        self.tracer = None
        self.meter = None
        self._initialized = False
        
        # Metrics
        self.request_counter = None
        self.error_counter = None
        self.latency_histogram = None
        self.active_agents_gauge = None
        self.llm_cost_counter = None
        self.message_bus_counter = None
        
    def initialize(self, 
                  otlp_endpoint: Optional[str] = None,
                  jaeger_endpoint: Optional[str] = None,
                  prometheus_port: int = 9090,
                  enable_console: bool = False,
                  custom_attributes: Optional[Dict[str, Any]] = None):
        """Initialize OpenTelemetry with configured exporters"""
        
        if self._initialized:
            logger.warning("Telemetry already initialized")
            return
            
        # Create resource
        resource_attributes = {
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: "0.2.0",
            ResourceAttributes.SERVICE_INSTANCE_ID: os.getpid(),
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENVIRONMENT", "production"),
            "boarderframe.version": "0.2.0",
            "boarderframe.component": "telemetry"
        }
        
        if custom_attributes:
            resource_attributes.update(custom_attributes)
            
        resource = Resource.create(attributes=resource_attributes)
        
        # Initialize tracing
        self._init_tracing(resource, otlp_endpoint, jaeger_endpoint, enable_console)
        
        # Initialize metrics
        self._init_metrics(resource, otlp_endpoint, prometheus_port, enable_console)
        
        # Auto-instrument libraries
        self._auto_instrument()
        
        # Create custom metrics
        self._create_custom_metrics()
        
        self._initialized = True
        logger.info("Telemetry initialized successfully")
        
    def _init_tracing(self, resource: Resource, otlp_endpoint: Optional[str],
                     jaeger_endpoint: Optional[str], enable_console: bool):
        """Initialize tracing with exporters"""
        
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        
        # Add exporters
        if enable_console:
            console_exporter = ConsoleSpanExporter()
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
            
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=True  # Use secure=False for local development
            )
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
            
        if jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_endpoint.split(":")[0],
                agent_port=int(jaeger_endpoint.split(":")[1]) if ":" in jaeger_endpoint else 6831,
                collector_endpoint=None,  # Use agent endpoint
            )
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
            
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(
            instrumenting_module_name=__name__,
            instrumenting_library_version="1.0.0"
        )
        
    def _init_metrics(self, resource: Resource, otlp_endpoint: Optional[str],
                     prometheus_port: int, enable_console: bool):
        """Initialize metrics with exporters"""
        
        readers = []
        
        # Console exporter
        if enable_console:
            console_exporter = ConsoleMetricExporter()
            console_reader = PeriodicExportingMetricReader(
                exporter=console_exporter,
                export_interval_millis=10000  # 10 seconds
            )
            readers.append(console_reader)
            
        # OTLP exporter
        if otlp_endpoint:
            otlp_exporter = OTLPMetricExporter(
                endpoint=otlp_endpoint,
                insecure=True
            )
            otlp_reader = PeriodicExportingMetricReader(
                exporter=otlp_exporter,
                export_interval_millis=10000
            )
            readers.append(otlp_reader)
            
        # Prometheus exporter (pull-based)
        # Note: PrometheusMetricReader starts its own HTTP server on port 9090 by default
        # The port is not configurable in the current version
        prometheus_reader = PrometheusMetricReader()
        readers.append(prometheus_reader)
        
        # Create meter provider
        self.meter_provider = MeterProvider(
            resource=resource,
            metric_readers=readers
        )
        
        # Set global meter provider
        metrics.set_meter_provider(self.meter_provider)
        
        # Get meter
        self.meter = metrics.get_meter(
            name=__name__,
            version="1.0.0"
        )
        
    def _auto_instrument(self):
        """Auto-instrument common libraries"""
        
        # Instrument FastAPI
        try:
            FastAPIInstrumentor().instrument()
        except Exception as e:
            logger.debug(f"FastAPI instrumentation skipped: {e}")
            
        # Instrument Flask
        try:
            FlaskInstrumentor().instrument()
        except Exception as e:
            logger.debug(f"Flask instrumentation skipped: {e}")
            
        # Instrument HTTP clients
        HTTPXClientInstrumentor().instrument()
        
        # Instrument databases
        RedisInstrumentor().instrument()
        AsyncPGInstrumentor().instrument()
        Psycopg2Instrumentor().instrument()
        
        # Instrument logging
        LoggingInstrumentor().instrument(set_logging_format=True)
        
    def _create_custom_metrics(self):
        """Create custom metrics for BoarderframeOS"""
        
        # Request metrics
        self.request_counter = self.meter.create_counter(
            name="boarderframe.requests.total",
            description="Total number of requests",
            unit="1"
        )
        
        self.error_counter = self.meter.create_counter(
            name="boarderframe.errors.total",
            description="Total number of errors",
            unit="1"
        )
        
        self.latency_histogram = self.meter.create_histogram(
            name="boarderframe.request.duration",
            description="Request duration in seconds",
            unit="s"
        )
        
        # Agent metrics
        self.active_agents_gauge = self.meter.create_up_down_counter(
            name="boarderframe.agents.active",
            description="Number of active agents",
            unit="1"
        )
        
        # LLM metrics
        self.llm_cost_counter = self.meter.create_counter(
            name="boarderframe.llm.cost",
            description="LLM API costs in dollars",
            unit="USD"
        )
        
        # Message bus metrics
        self.message_bus_counter = self.meter.create_counter(
            name="boarderframe.messagebus.messages",
            description="Messages sent through the message bus",
            unit="1"
        )
        
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None,
             kind: trace.SpanKind = trace.SpanKind.INTERNAL):
        """Create a span context manager"""
        
        with self.tracer.start_as_current_span(
            name=name,
            attributes=attributes or {},
            kind=kind
        ) as span:
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
                
    def trace_agent_operation(self, operation: str):
        """Decorator for tracing agent operations"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                agent_name = "unknown"
                if args and hasattr(args[0], 'name'):
                    agent_name = args[0].name
                    
                attributes = {
                    "agent.name": agent_name,
                    "agent.operation": operation,
                    "agent.async": True
                }
                
                with self.span(f"agent.{operation}", attributes=attributes):
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        duration = time.time() - start_time
                        
                        # Record metrics
                        self.request_counter.add(1, {"agent": agent_name, "operation": operation})
                        self.latency_histogram.record(duration, {"agent": agent_name, "operation": operation})
                        
                        return result
                    except Exception as e:
                        self.error_counter.add(1, {"agent": agent_name, "operation": operation, "error": type(e).__name__})
                        raise
                        
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                agent_name = "unknown"
                if args and hasattr(args[0], 'name'):
                    agent_name = args[0].name
                    
                attributes = {
                    "agent.name": agent_name,
                    "agent.operation": operation,
                    "agent.async": False
                }
                
                with self.span(f"agent.{operation}", attributes=attributes):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        duration = time.time() - start_time
                        
                        # Record metrics
                        self.request_counter.add(1, {"agent": agent_name, "operation": operation})
                        self.latency_histogram.record(duration, {"agent": agent_name, "operation": operation})
                        
                        return result
                    except Exception as e:
                        self.error_counter.add(1, {"agent": agent_name, "operation": operation, "error": type(e).__name__})
                        raise
                        
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        return decorator
        
    def trace_llm_call(self, func: Callable) -> Callable:
        """Decorator for tracing LLM API calls"""
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            agent_name = kwargs.get("agent_name", "unknown")
            
            attributes = {
                "llm.model": model,
                "llm.agent": agent_name,
                "llm.prompt_length": len(kwargs.get("prompt", "")),
            }
            
            with self.span("llm.completion", attributes=attributes, kind=trace.SpanKind.CLIENT):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Extract cost if available
                    if hasattr(result, 'optimized_cost'):
                        self.llm_cost_counter.add(result.optimized_cost, {
                            "model": model,
                            "agent": agent_name
                        })
                        
                    # Record latency
                    self.latency_histogram.record(duration, {
                        "operation": "llm_call",
                        "model": model
                    })
                    
                    return result
                except Exception as e:
                    self.error_counter.add(1, {
                        "operation": "llm_call",
                        "model": model,
                        "error": type(e).__name__
                    })
                    raise
                    
        return wrapper
        
    def trace_message_bus(self, func: Callable) -> Callable:
        """Decorator for tracing message bus operations"""
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from_agent = kwargs.get("from_agent", "unknown")
            to_agent = kwargs.get("to_agent", "unknown")
            priority = kwargs.get("priority", "normal")
            
            attributes = {
                "messagebus.from": from_agent,
                "messagebus.to": to_agent,
                "messagebus.priority": priority
            }
            
            with self.span("messagebus.send", attributes=attributes):
                result = await func(*args, **kwargs)
                
                # Record metric
                self.message_bus_counter.add(1, {
                    "from": from_agent,
                    "to": to_agent,
                    "priority": priority
                })
                
                return result
                
        return wrapper
        
    def record_agent_lifecycle(self, agent_name: str, event: str):
        """Record agent lifecycle events"""
        
        current_span = trace.get_current_span()
        current_span.add_event(
            name=f"agent.{event}",
            attributes={
                "agent.name": agent_name,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Update active agents gauge
        if event == "started":
            self.active_agents_gauge.add(1, {"agent": agent_name})
        elif event == "stopped":
            self.active_agents_gauge.add(-1, {"agent": agent_name})
            
    def get_trace_context(self) -> Dict[str, Any]:
        """Get current trace context for propagation"""
        
        carrier = {}
        inject(carrier)
        return carrier
        
    def set_trace_context(self, carrier: Dict[str, Any]):
        """Set trace context from propagated data"""
        
        context = extract(carrier)
        token = attach(context)
        return token
        
    def create_child_span(self, name: str, parent_context: Optional[Dict[str, Any]] = None,
                         **kwargs) -> Span:
        """Create a child span with optional parent context"""
        
        if parent_context:
            token = self.set_trace_context(parent_context)
            
        span = self.tracer.start_span(name, **kwargs)
        
        if parent_context:
            detach(token)
            
        return span
        
    def add_baggage(self, key: str, value: str):
        """Add baggage for context propagation"""
        
        baggage.set_baggage(key, value)
        
    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage value"""
        
        return baggage.get_baggage(key)
        
    def shutdown(self):
        """Shutdown telemetry providers"""
        
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            
        if self.meter_provider:
            self.meter_provider.shutdown()
            
        self._initialized = False
        logger.info("Telemetry shut down")


# Global telemetry instance
_telemetry_manager = None


def get_telemetry() -> TelemetryManager:
    """Get the global telemetry manager instance"""
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager