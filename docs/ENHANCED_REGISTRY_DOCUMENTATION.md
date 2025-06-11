# BoarderframeOS Enhanced Registry System Documentation

## Overview

The Enhanced Registry System is a comprehensive, production-ready service discovery and management platform for BoarderframeOS. It provides real-time tracking, health monitoring, and coordination for all system components including AI agents, leaders, departments, divisions, databases, and servers.

## Table of Contents

1. [Architecture](#architecture)
2. [Features](#features)
3. [Components](#components)
4. [API Reference](#api-reference)
5. [Client Usage](#client-usage)
6. [Event System](#event-system)
7. [Database Schema](#database-schema)
8. [Deployment](#deployment)
9. [Monitoring](#monitoring)
10. [Best Practices](#best-practices)

## Architecture

### Technology Stack

- **Backend**: FastAPI with async Python
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis for real-time events and caching
- **Real-time**: WebSockets for live updates
- **Protocols**: REST API and WebSocket connections

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Enhanced Registry System                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   FastAPI   │  │  PostgreSQL  │  │      Redis       │  │
│  │   Server    │  │   Database   │  │  Event Streams   │  │
│  │  (Port 8100) │  │  (Port 5434) │  │   (Port 6379)   │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │            │
│  ┌──────┴─────────────────┴────────────────────┴────────┐  │
│  │              Registry Core Engine                     │  │
│  │  - Entity Management                                  │  │
│  │  - Health Monitoring                                  │  │
│  │  - Event Processing                                   │  │
│  │  - Service Discovery                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │  REST API    │  │   WebSocket    │  │  Background   │  │
│  │  Endpoints   │  │   Connections  │  │    Tasks      │  │
│  └──────────────┘  └────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Core Features

1. **Unified Registry**
   - Single source of truth for all system components
   - Support for agents, leaders, departments, divisions, databases, and servers
   - Flexible metadata storage with JSONB

2. **Real-time Updates**
   - WebSocket connections for live notifications
   - Redis Streams for event broadcasting
   - Pub/Sub pattern for immediate updates

3. **Health Monitoring**
   - Automatic heartbeat tracking
   - Health score calculations
   - Cascading health impact analysis
   - Service dependency tracking

4. **Service Discovery**
   - Capability-based discovery
   - Tag and metadata filtering
   - Department/division hierarchy navigation
   - Load-balanced service selection

5. **Performance Optimization**
   - Connection pooling (15-50 connections)
   - In-memory caching with TTL
   - Query optimization with indexes
   - Batch operations support

### Advanced Features

1. **Event System**
   - Comprehensive event logging
   - Event subscriptions
   - Correlation tracking
   - Audit trail

2. **Organizational Management**
   - Department hierarchy
   - Leadership tiers
   - Agent assignments
   - Division structure

3. **Metrics and Analytics**
   - Real-time statistics
   - Performance metrics
   - Historical data tracking
   - Custom metric support

4. **High Availability**
   - Retry logic
   - Circuit breakers
   - Graceful degradation
   - Health-based routing

## Components

### 1. Enhanced Registry System (`enhanced_registry_system.py`)

The main registry service providing:

- **FastAPI Application**: REST API and WebSocket server
- **Entity Management**: CRUD operations for all entity types
- **Event Processing**: Real-time event handling and distribution
- **Background Tasks**: Health monitoring, cache cleanup, metrics collection
- **WebSocket Handler**: Live connection management

### 2. Registry Client (`registry_client.py`)

High-level client library featuring:

- **Type-safe Methods**: Dedicated methods for each entity type
- **Automatic Heartbeat**: Manages heartbeats for registered entities
- **Event Subscriptions**: WebSocket-based event listening
- **Connection Pooling**: Efficient HTTP session management
- **Local Caching**: Reduces API calls with smart caching

### 3. Database Schema

PostgreSQL tables:
- `agent_registry`: Agents and leaders
- `server_registry`: All server types
- `department_registry`: Department information
- `database_registry`: Database connections
- `divisions`: Division hierarchy
- `registry_event_log`: Event history
- `service_dependencies`: Dependency tracking
- `registry_metrics`: Performance metrics

## API Reference

### Base URL

```
http://localhost:8100
```

### Authentication

Currently no authentication required (add as needed for production).

### Endpoints

#### Health Check

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "health_score": 100.0,
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "cache": "enabled",
    "websockets": "3 connected"
  },
  "entities": {
    "total": 145,
    "healthy": 130,
    "warning": 10,
    "critical": 5,
    "online": 125
  }
}
```

#### Register Entity

```http
POST /register/{entity_type}
Content-Type: application/json

{
  "name": "CustomerAnalyzer",
  "capabilities": ["analyze", "report", "predict"],
  "llm_model": "gpt-4",
  "department_id": "sales-dept-id"
}
```

#### Discover Entities

```http
GET /discover/{entity_type}?status=online&capability=analyze&limit=10
```

Parameters:
- `status`: Filter by service status
- `capability`: Filter by capability
- `tag`: Filter by tag
- `department_id`: Filter by department
- `division_id`: Filter by division
- `limit`: Maximum results (default: 100)
- `offset`: Pagination offset

#### Get Entity

```http
GET /entity/{entity_id}
```

#### Update Entity

```http
PUT /entity/{entity_id}
Content-Type: application/json

{
  "status": "online",
  "health_score": 95.0,
  "metadata": {
    "version": "1.2.0"
  }
}
```

#### Send Heartbeat

```http
POST /entity/{entity_id}/heartbeat
```

#### Unregister Entity

```http
DELETE /entity/{entity_id}
```

#### Assign Agent to Department

```http
POST /assign/agent/{agent_id}/department/{department_id}
```

#### Get Organizational Hierarchy

```http
GET /hierarchy/divisions
```

#### Get Statistics

```http
GET /statistics
```

### WebSocket Interface

Connect to: `ws://localhost:8100/ws`

#### Subscribe to Events

```json
{
  "command": "subscribe",
  "entity_types": ["agent", "server"]
}
```

#### Ping/Pong

```json
{
  "command": "ping"
}
```

## Client Usage

### Basic Registration

```python
from core.registry_client import RegistryClient, ServerType

async def register_my_agent():
    async with RegistryClient() as client:
        # Register an agent
        agent = await client.register_agent(
            name="DataProcessor",
            capabilities=["process", "transform", "validate"],
            department_id="analytics-dept",
            llm_model="gpt-4",
            metadata={"version": "2.0.0"}
        )
        print(f"Registered agent: {agent.id}")

        # Register a server
        server = await client.register_server(
            name="Analytics API",
            server_type=ServerType.BUSINESS_SERVICE,
            host="localhost",
            port=8080,
            endpoints=[
                {"path": "/analyze", "method": "POST"},
                {"path": "/report", "method": "GET"}
            ]
        )
        print(f"Registered server: {server.id}")
```

### Service Discovery

```python
async def find_analytics_agents():
    async with RegistryClient() as client:
        # Find agents with specific capability
        agents = await client.discover_agents(
            capability="analyze",
            status=ServiceStatus.ONLINE,
            department_id="analytics-dept"
        )

        # Select best agent based on load
        best_agent = min(agents, key=lambda a: a.current_load)
        return best_agent
```

### Event Subscriptions

```python
async def monitor_registry_events():
    async with RegistryClient() as client:
        # Define event handler
        async def on_agent_registered(event: RegistryEvent):
            print(f"New agent registered: {event.data['name']}")

        # Subscribe to events
        client.on_event(EventType.REGISTERED, on_agent_registered)
        await client.subscribe_to_events(
            event_types=[EventType.REGISTERED, EventType.STATUS_CHANGED],
            entity_types=[RegistryType.AGENT]
        )

        # Keep listening
        await asyncio.sleep(3600)
```

### With BaseAgent Integration

```python
from core.base_agent import BaseAgent
from core.registry_client import RegistryClient

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.registry_client = None
        self.registry_entry = None

    async def initialize(self):
        await super().initialize()

        # Create registry client
        self.registry_client = RegistryClient()
        await self.registry_client.connect()

        # Register this agent
        self.registry_entry = await self.registry_client.register_agent(
            name=self.name,
            agent_id=str(self.id),
            capabilities=self.capabilities,
            department_id=self.department_id,
            metadata={
                "agent_type": self.__class__.__name__,
                "version": self.version
            }
        )

    async def shutdown(self):
        # Unregister from registry
        if self.registry_client and self.registry_entry:
            await self.registry_client.unregister(self.registry_entry.id)
            await self.registry_client.disconnect()

        await super().shutdown()
```

## Event System

### Event Types

- `REGISTERED`: New entity registered
- `UNREGISTERED`: Entity removed
- `STATUS_CHANGED`: Status update
- `HEARTBEAT`: Heartbeat received
- `HEALTH_CHANGED`: Health score changed
- `CAPABILITY_ADDED`: New capability added
- `CAPABILITY_REMOVED`: Capability removed
- `ASSIGNMENT_CHANGED`: Department/division assignment changed
- `METRIC_UPDATED`: Metrics updated

### Event Structure

```json
{
  "id": "event-uuid",
  "event_type": "STATUS_CHANGED",
  "entity_id": "agent-uuid",
  "entity_type": "agent",
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "registry",
  "data": {
    "old_status": "offline",
    "new_status": "online"
  },
  "correlation_id": "correlation-uuid"
}
```

### Redis Streams

Events are published to Redis Streams for durability and fanout:

- Stream: `registry:events`
- Channel: `registry:events:{entity_type}`

## Database Schema

### Key Tables

#### agent_registry
- Stores agents and leaders
- Tracks capabilities, health, and assignments
- Supports leadership-specific fields

#### server_registry
- All server types (Core, MCP, Business)
- Endpoints and API information
- Performance metrics

#### database_registry
- Database connections
- Performance and storage metrics
- Replication status

#### service_dependencies
- Tracks dependencies between services
- Health impact calculations
- Circuit breaker thresholds

### Indexes

Optimized indexes for:
- Entity lookups by ID
- Status and health queries
- Capability searches
- Department/division filtering
- Event correlation
- Timestamp-based queries

## Deployment

### Prerequisites

1. PostgreSQL 13+ with uuid-ossp extension
2. Redis 6.0+
3. Python 3.11+
4. Docker (optional)

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://boarderframe:boarderframe@localhost:5434/boarderframeos

# Redis
REDIS_URL=redis://localhost:6379

# Registry Settings
REGISTRY_HOST=0.0.0.0
REGISTRY_PORT=8100
ENABLE_CACHING=true
CACHE_TTL=300
ENABLE_WEBSOCKETS=true
ENABLE_AUDIT_LOG=true
```

### Running the Registry

#### Standalone

```bash
python -m core.enhanced_registry_system
```

#### With Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY core/enhanced_registry_system.py .
COPY core/registry_client.py .

CMD ["python", "-m", "enhanced_registry_system"]
```

#### Integration with startup.py

The registry is automatically started when running:

```bash
python startup.py
```

### Database Migrations

Run the migration to set up enhanced registry tables:

```bash
psql -U boarderframe -d boarderframeos -f migrations/006_enhanced_registry_tables.sql
```

## Monitoring

### Health Checks

Monitor registry health via:

```bash
curl http://localhost:8100/health
```

### Metrics Endpoint

Get detailed metrics:

```bash
curl http://localhost:8100/metrics
```

### Prometheus Integration

The registry exposes metrics in Prometheus format at `/metrics`.

### Logging

- All operations logged with appropriate levels
- Structured logging with JSON format
- Correlation IDs for request tracing

## Best Practices

### 1. Registration

- Always provide meaningful names and descriptions
- Include all relevant capabilities
- Set appropriate metadata
- Use consistent naming conventions

### 2. Health Management

- Implement proper heartbeat intervals (30-60 seconds)
- Handle heartbeat failures gracefully
- Monitor health scores
- Set up alerts for critical health

### 3. Service Discovery

- Use capability-based discovery
- Filter by health score for reliability
- Implement load balancing logic
- Cache discovery results appropriately

### 4. Event Handling

- Subscribe only to needed events
- Implement idempotent event handlers
- Use correlation IDs for tracking
- Handle WebSocket reconnections

### 5. Performance

- Use batch operations when possible
- Enable caching for read-heavy workloads
- Monitor connection pool usage
- Set appropriate timeouts

### 6. Error Handling

- Implement retry logic with backoff
- Log errors with context
- Use circuit breakers for dependencies
- Provide fallback mechanisms

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if registry service is running
   - Verify port 8100 is not blocked
   - Check PostgreSQL and Redis connections

2. **Slow Performance**
   - Monitor database query performance
   - Check connection pool exhaustion
   - Review cache hit rates
   - Analyze event queue size

3. **Missing Heartbeats**
   - Verify network connectivity
   - Check heartbeat interval settings
   - Review agent logs for errors
   - Monitor WebSocket connections

4. **Event Delivery Issues**
   - Check Redis connection
   - Verify WebSocket subscriptions
   - Review event handler errors
   - Monitor event queue backlog

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Diagnostics

Run comprehensive diagnostics:

```bash
curl http://localhost:8100/health | jq '.'
curl http://localhost:8100/metrics | jq '.'
curl http://localhost:8100/statistics | jq '.'
```

## Future Enhancements

1. **Security**
   - JWT authentication
   - Role-based access control
   - API key management
   - Encryption at rest

2. **Scalability**
   - Horizontal scaling with load balancer
   - Read replicas for discovery
   - Partitioned event streams
   - Distributed caching

3. **Features**
   - GraphQL API
   - gRPC support
   - Kubernetes operator
   - Service mesh integration

4. **Monitoring**
   - OpenTelemetry integration
   - Custom dashboards
   - SLA tracking
   - Anomaly detection
