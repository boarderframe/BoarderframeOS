# Performance Optimization Guide

## Overview

BoarderframeOS includes comprehensive performance optimization tools to ensure optimal system performance, resource utilization, and response times.

## Quick Start

```bash
# Run all optimizations
./optimize_performance.py

# Optimize specific component
./optimize_performance.py --component database
./optimize_performance.py --component agents
./optimize_performance.py --component system

# Run optimizations and start monitor
./optimize_performance.py --monitor
```

## Performance Tools

### 1. Database Optimization (`performance/optimize_database.py`)

Optimizes PostgreSQL and SQLite performance:

- **Index Optimization**: Creates missing indexes, removes unused ones
- **Query Analysis**: Identifies and optimizes slow queries
- **Configuration Tuning**: Recommends optimal PostgreSQL settings
- **Maintenance**: Runs VACUUM and ANALYZE operations
- **Cache Optimization**: Improves cache hit ratios

**Features:**
- Automatic index creation for high-write columns
- Detection of sequential scans
- Memory configuration based on system resources
- SQLite WAL mode and pragma optimizations

### 2. Agent Optimization (`performance/optimize_agents.py`)

Optimizes agent performance and resource usage:

- **Memory Management**: Aggressive garbage collection, memory profiling
- **Message Processing**: Batching, compression, priority queues
- **Database Queries**: Connection pooling, query caching, prepared statements
- **LLM Optimization**: Response caching, token optimization, model routing
- **Concurrency**: Thread pool sizing, semaphore configuration

**Generated Configurations:**
- `performance/agent_optimization_config.json` - Complete optimization settings
- `performance/optimized_settings.py` - Python module with optimized constants

### 3. System Optimization (`performance/optimize_system.py`)

System-wide performance improvements:

- **Docker Resources**: Container CPU/memory limits
- **Network Settings**: TCP optimization, HTTP connection pooling
- **Redis Configuration**: Memory management, persistence settings
- **Python Runtime**: Optimization flags, memory settings
- **Bottleneck Analysis**: CPU, memory, disk I/O, network detection

**Generated Files:**
- `docker-compose.override.yml` - Docker resource limits
- `performance/nginx_optimized.conf` - Nginx reverse proxy config
- `performance/redis_optimized.conf` - Redis optimization settings
- `performance/optimized_startup.sh` - Optimized startup script

### 4. Performance Monitor (`performance/monitor_performance.py`)

Real-time performance monitoring dashboard:

- **System Metrics**: CPU, memory, disk I/O, network
- **MCP Server Health**: Status and response times
- **Database Performance**: Connections, cache hits, operations/sec
- **Agent Metrics**: CPU/memory per agent, response times
- **Alert System**: Automatic alerts for performance issues

**Features:**
- Rich terminal UI with live updates
- Performance history tracking
- Snapshot saving capability
- Alert notifications

## Optimization Areas

### Database Performance

```bash
# Run database optimization
./performance/optimize_database.py
```

**Optimizations Applied:**
- Index creation for frequently queried columns
- Removal of unused indexes
- VACUUM and ANALYZE for table maintenance
- Connection pool optimization
- Query cache configuration

### Agent Performance

```bash
# Run agent optimization
./performance/optimize_agents.py
```

**Optimizations Applied:**
- Memory usage reduction through GC tuning
- Message batching (50 messages, 100ms timeout)
- Message compression for payloads > 1KB
- LLM response caching (500 entries, 1hr TTL)
- Intelligent model routing based on query complexity

### System Resources

```bash
# Run system optimization
./performance/optimize_system.py
```

**Optimizations Applied:**
- Docker container resource limits
- TCP keepalive and nodelay settings
- Redis memory management and eviction policies
- Python runtime optimization flags
- File descriptor and process limits

## Performance Monitoring

### Real-time Dashboard

```bash
# Start performance monitor
./performance/monitor_performance.py
```

**Dashboard Sections:**
- System Metrics: CPU, memory, disk, network
- MCP Server Status: Health and response times
- Database Performance: PostgreSQL and Redis metrics
- Agent Performance: Per-agent resource usage

### Metrics Collection

The monitor tracks:
- CPU usage (overall and per-core)
- Memory usage and swap
- Disk I/O rates
- Network throughput
- Database connections and cache hits
- Agent response times
- MCP server health

## Configuration Files

### Optimized Settings Module

After running optimizations, use the generated settings:

```python
# In your code
from performance.optimized_settings import *

# Use optimized constants
message_batch_size = MESSAGE_BATCH_SIZE
db_pool_size = DB_POOL_MAX
cache_ttl = QUERY_CACHE_TTL
```

### Docker Compose Override

Apply Docker optimizations:

```bash
# Restart with optimized resources
docker-compose down
docker-compose up -d
```

### Redis Configuration

Apply Redis optimizations:

```bash
# Copy config to Redis
docker cp performance/redis_optimized.conf boarderframeos_redis:/usr/local/etc/redis/redis.conf
docker-compose restart redis
```

## Performance Best Practices

### 1. Regular Optimization

Run optimizations periodically:
- Database optimization: Weekly
- Agent optimization: After major changes
- System optimization: Monthly

### 2. Monitoring

- Keep performance monitor running during high load
- Save snapshots before and after changes
- Set up alerts for critical thresholds

### 3. Resource Allocation

- Allocate 25% of RAM to PostgreSQL shared_buffers
- Keep Redis memory under 50% of available RAM
- Limit concurrent agents based on CPU cores

### 4. Query Optimization

- Use indexes for frequently queried columns
- Batch database operations
- Enable query result caching
- Use prepared statements

### 5. Network Optimization

- Enable compression for large payloads
- Use connection pooling
- Implement request batching
- Set appropriate timeouts

## Troubleshooting

### High CPU Usage

1. Check agent CPU usage in monitor
2. Review slow queries in database
3. Reduce concurrent agent count
4. Enable CPU profiling

### High Memory Usage

1. Run memory optimization
2. Check for memory leaks
3. Reduce cache sizes
4. Enable aggressive GC

### Slow Response Times

1. Check database query performance
2. Review network latency
3. Enable response caching
4. Optimize LLM calls

### Database Performance Issues

1. Run VACUUM ANALYZE
2. Check index usage
3. Review connection pool settings
4. Monitor cache hit ratios

## Performance Targets

- **CPU Usage**: < 70% average
- **Memory Usage**: < 80% average
- **Database Cache Hit**: > 90%
- **Agent Response Time**: < 200ms average
- **MCP Server Response**: < 50ms
- **Message Processing**: > 1000 msg/sec

## Reporting

Performance reports are saved to:
- `performance/database_optimization_report.json`
- `performance/agent_optimization_config.json`
- `performance/system_optimization_report.json`
- `performance/optimization_dashboard.html`

View the dashboard:
```bash
open performance/optimization_dashboard.html
```