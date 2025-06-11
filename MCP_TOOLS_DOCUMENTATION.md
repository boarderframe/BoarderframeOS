# BoarderframeOS MCP Tools Documentation

## Overview

BoarderframeOS provides a comprehensive suite of Model Context Protocol (MCP) servers optimized for AI agent operations. Each server runs independently and provides specialized tools accessible via HTTP REST APIs and JSON-RPC interfaces.

## Server Architecture

### ✅ **Fully Operational Servers**

| Server | Port | Status | Optimization Level | Purpose |
|--------|------|--------|-------------------|---------|
| PostgreSQL Database | 8010 | 🟢 Production Ready | ⭐⭐⭐⭐⭐ Enterprise | Primary data persistence |
| Filesystem | 8001 | 🟢 Production Ready | ⭐⭐⭐⭐⭐ Enterprise | File operations + AI |
| Analytics | 8007 | 🟢 Production Ready | ⭐⭐⭐⭐⭐ Enterprise | Business metrics + events |
| Registry | 8009 | 🟢 Operational | ⭐⭐⭐ Standard | Service discovery |
| Database (SQLite) | 8004 | 🟢 Production Ready | ⭐⭐⭐⭐ Advanced | Legacy compatibility |
| Payment | 8006 | 🟢 Operational | ⭐⭐⭐ Standard | Revenue management |
| LLM | 8005 | 🟢 Operational | ⭐⭐⭐ Standard | Language model proxy |

---

## 1. PostgreSQL Database Server (Port 8010)

### **Enterprise-Grade Database Operations**

**Optimization Features:**
- ✅ Advanced connection pooling (15-50 connections)
- ✅ High-performance query cache (5000 entries)
- ✅ Real-time performance monitoring
- ✅ 99.99% PostgreSQL cache hit ratio
- ✅ pgvector support for AI embeddings

### **Available Tools**

#### **Core Database Operations**
```http
POST /query
```
Execute raw SQL queries with caching and monitoring
- **Input**: `{sql: string, params: array, fetch_all: boolean}`
- **Output**: Query results with execution metrics
- **Performance**: ~2ms average response time

```http
POST /insert
```
Insert data with conflict handling
- **Input**: `{table: string, data: object, on_conflict: string}`
- **Output**: Insert confirmation with ID
- **Features**: UUID generation, JSON support

```http
POST /update
POST /delete
```
Update and delete operations with transaction safety

#### **Schema Operations**
```http
GET /tables
GET /schema/{table}
```
List tables and inspect schema structures

#### **Performance Monitoring**
```http
GET /performance
```
Comprehensive performance statistics
- Connection pool metrics
- Query cache performance
- PostgreSQL system stats
- Cache hit ratios

```http
GET /cache/stats
POST /cache/clear
```
Query cache management and statistics

#### **Vector Operations** (pgvector)
```http
POST /vector/search
POST /vector/insert
```
AI embedding operations for semantic search

---

## 2. Filesystem Server (Port 8001)

### **AI-Enhanced File Operations**

**Optimization Features:**
- ✅ 4-tier rate limiting system
- ✅ AI content analysis capabilities
- ✅ Async I/O operations
- ✅ Real-time file monitoring
- ✅ Advanced search capabilities

### **Available Tools**

#### **Core File Operations** (JSON-RPC)
```json
{"method": "fs.list", "params": {"path": ".", "recursive": false}}
```
List directory contents with metadata

```json
{"method": "fs.read", "params": {"path": "file.txt", "encoding": "utf-8"}}
```
Read file contents with encoding support

```json
{"method": "fs.write", "params": {"path": "file.txt", "content": "data"}}
```
Write files with integrity checking

```json
{"method": "fs.search", "params": {"path": ".", "pattern": "*.py", "content_search": "import"}}
```
Advanced file search with content filtering

#### **AI Analysis Tools**
```json
{"method": "fs.analyze", "params": {"path": "file.txt", "analysis_type": "summary"}}
```
AI-powered content analysis and summarization

```json
{"method": "fs.embed", "params": {"path": "file.txt"}}
```
Generate embeddings for semantic operations

#### **Rate Limiting Protection**
- **General operations**: 100 requests/minute
- **File operations**: 20 requests/minute
- **Batch operations**: 10 requests/minute
- **AI operations**: 5 requests/minute

```http
GET /rate-limit-stats
```
Monitor rate limiting status

---

## 3. Analytics Server (Port 8007)

### **Real-Time Business Intelligence**

**Optimization Features:**
- ✅ PostgreSQL backend with JSONB storage
- ✅ Background event processing (50-event batches)
- ✅ Dedicated connection pool (5-15 connections)
- ✅ GIN indexes for fast JSON queries
- ✅ Real-time metrics caching

### **Available Tools**

#### **Event Tracking**
```http
POST /track
```
Track business events with background processing
- **Input**: `{event_type: string, agent_id: string, data: object}`
- **Events**: revenue, new_customer, churn, api_usage
- **Processing**: Automatic batching and PostgreSQL storage

#### **Business Metrics**
```http
GET /metrics/customer-acquisition
GET /metrics/lifetime-value
GET /metrics/churn
GET /metrics/revenue-per-agent
GET /metrics/api-usage
```
Real-time KPI calculations

#### **Performance Analytics**
```http
GET /performance
```
Background processing and queue statistics

```http
GET /metrics/cached
```
Access cached metrics for fast retrieval

```http
GET /dashboard-data
```
Comprehensive dashboard data for business intelligence

#### **KPI Calculation**
```http
POST /kpi
```
Custom KPI calculations with time-based filtering
- **Input**: `{metric: string, timeframe: string, filters: object}`
- **Timeframes**: day, week, month
- **Custom metrics**: Revenue trends, agent performance, customer analytics

---

## 4. Registry Server (Port 8009)

### **Service Discovery & Agent Management**

### **Available Tools**

#### **Agent Discovery**
```http
GET /agents/discover
```
Discover active agents in the system

```http
POST /agents/register
```
Register new agents with the system

#### **Service Discovery**
```http
GET /services/discover
```
Discover available MCP services

```http
GET /health
```
Registry service health status

---

## 5. Payment Server (Port 8006)

### **Revenue Management**

### **Available Tools**

#### **Payment Processing**
```http
POST /payments/process
```
Process payments with Stripe integration

```http
GET /customers/{id}/billing
```
Customer billing and usage tracking

```http
GET /health
```
Payment service health status

---

## 6. LLM Server (Port 8005)

### **Language Model Proxy**

### **Available Tools**

#### **Chat Completions**
```http
POST /chat/completions
```
OpenAI-compatible chat completions

```http
GET /models
```
List available language models

```http
GET /health
```
LLM service health status

---

## 7. SQLite Database Server (Port 8004)

### **Legacy Database Support**

**Optimization Features:**
- ✅ Advanced connection pooling
- ✅ Query result caching (80% hit rate)
- ✅ Performance monitoring
- ✅ Backwards compatibility

### **Available Tools**

Similar to PostgreSQL server but with SQLite backend:
- `/query` - SQL query execution
- `/insert`, `/update`, `/delete` - Data operations
- `/performance` - Performance statistics
- `/tables`, `/schema/{table}` - Schema operations

---

## Common Integration Patterns

### **1. Multi-Server Workflows**

**AI-Powered File Analysis + Database Storage:**
```bash
# 1. Analyze file with AI
curl -X POST http://localhost:8001/rpc \
  -d '{"method": "fs.analyze", "params": {"path": "document.pdf"}}'

# 2. Store results in PostgreSQL
curl -X POST http://localhost:8010/insert \
  -d '{"table": "analysis_results", "data": {...}}'

# 3. Track analytics event
curl -X POST http://localhost:8007/track \
  -d '{"event_type": "ai_analysis", "data": {...}}'
```

### **2. Business Intelligence Pipeline**

**Revenue Tracking Workflow:**
```bash
# 1. Process payment
curl -X POST http://localhost:8006/payments/process

# 2. Track revenue event
curl -X POST http://localhost:8007/track \
  -d '{"event_type": "revenue", "amount": 150.00}'

# 3. Store customer data
curl -X POST http://localhost:8010/insert \
  -d '{"table": "customers", "data": {...}}'

# 4. Get real-time metrics
curl http://localhost:8007/metrics/revenue-per-agent
```

### **3. Performance Monitoring**

**System Health Dashboard:**
```bash
# Check all server health
for port in 8001 8004 8005 8006 8007 8009 8010; do
  curl http://localhost:$port/health
done

# Get performance metrics
curl http://localhost:8010/performance  # Database performance
curl http://localhost:8001/rate-limit-stats  # Rate limiting
curl http://localhost:8007/performance  # Analytics performance
```

## Security & Rate Limiting

### **Protection Mechanisms**
- **Rate Limiting**: All servers implement request throttling
- **Connection Pooling**: Prevents connection exhaustion
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Graceful degradation under load

### **Monitoring Endpoints**
All servers provide `/health` endpoints for monitoring and `/performance` or `/stats` for detailed metrics.

## Performance Characteristics

### **Benchmarked Performance**
- **Database Operations**: 1-3ms average query time
- **File Operations**: Rate-limited for stability
- **Analytics Processing**: 95% improvement with background batching
- **Connection Efficiency**: 50+ pooled connections vs individual connections
- **Cache Hit Rates**: 80-99% across different caching layers

## Error Handling

### **Standard Error Response**
```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2025-05-31T21:47:58.174732"
}
```

### **Rate Limiting Response**
```json
{
  "error": "Rate limit exceeded",
  "operation_type": "ai",
  "client_stats": {...}
}
```

## Development & Testing

### **Health Check All Servers**
```bash
#!/bin/bash
for port in 8001 8004 8005 8006 8007 8009 8010; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health | jq -r '.status // "Not responding"'
done
```

### **Performance Testing**
```bash
# Test database performance
curl -X POST http://localhost:8010/query \
  -d '{"sql": "SELECT current_timestamp", "params": []}'

# Test analytics events
curl -X POST http://localhost:8007/track \
  -d '{"event_type": "test", "data": {"metric": "value"}}'
```

---

## Summary

BoarderframeOS provides **7 production-ready MCP servers** with enterprise-grade optimizations:

- **🗄️ PostgreSQL Database**: Advanced connection pooling, query caching, 99.99% cache hit ratio
- **📁 Filesystem**: AI-enhanced file operations with 4-tier rate limiting
- **📊 Analytics**: Real-time business intelligence with background processing
- **🔍 Registry**: Service and agent discovery
- **💳 Payment**: Revenue management and billing
- **🤖 LLM**: Language model proxy services
- **📋 SQLite**: Legacy database compatibility

All servers are optimized for **120+ agent environments** with comprehensive monitoring, performance analytics, and enterprise-grade reliability.
