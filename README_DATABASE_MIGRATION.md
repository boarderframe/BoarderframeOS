# Database MCP Server Migration Guide

This guide covers the migration from SQLite to PostgreSQL + pgvector for the BoarderframeOS Database MCP Server.

## 🔄 Migration Overview

### **Old SQLite Server** (`database_server.py`)
- **Database**: SQLite with individual files
- **Features**: Basic CRUD operations, limited scalability
- **Port**: 8004
- **Status**: Legacy, maintained for compatibility

### **New PostgreSQL Server** (`database_server_postgres.py`)
- **Database**: PostgreSQL 16 + pgvector extension
- **Features**: Enhanced CRUD, vector search, Redis events, connection pooling
- **Port**: 8005 (during transition)
- **Status**: Production-ready replacement

---

## 🚀 Quick Migration Steps

### **1. Start Infrastructure**
```bash
# Start PostgreSQL + Redis
docker-compose up -d postgresql redis

# Verify services
docker-compose ps
```

### **2. Test New PostgreSQL Server**
```bash
# Start the new PostgreSQL server
python mcp/start_postgres_server.py

# In another terminal, test the infrastructure
python test_infrastructure.py
```

### **3. Compare Servers Side by Side**
```bash
# Terminal 1: Start SQLite server (existing)
python mcp/database_server.py --port 8004

# Terminal 2: Start PostgreSQL server
python mcp/start_postgres_server.py --port 8005

# Terminal 3: Run comparison tests
python mcp/test_database_servers.py
```

### **4. Migrate Data (Optional)**
```bash
# Migrate existing SQLite data to PostgreSQL
python migrations/migrate_sqlite_to_postgres.py
```

### **5. Update Applications**
```bash
# Update MCP server references from :8004 to :8005
# Update database URLs in configuration files
# Test all agent integrations
```

---

## 🆕 Enhanced Features

### **Vector Operations**
```python
# Semantic similarity search
POST /vector-search
{
    "embedding": [0.1, 0.2, ...],  # 1536-dimensional vector
    "similarity_threshold": 0.8,
    "limit": 10,
    "agent_id": "optional-filter"
}
```

### **Memory Management**
```python
# Insert agent memory with automatic embedding
POST /memory
{
    "agent_id": "agent-uuid",
    "content": "Memory content here",
    "memory_type": "long_term",
    "importance": 0.9,
    "metadata": {"context": "conversation"}
}
```

### **Real-time Events**
```python
# Get recent database events from Redis Streams
GET /events?limit=10

# Events are automatically published for:
# - insert, update, delete operations
# - memory creation
# - agent interactions
```

### **Enhanced Health Monitoring**
```python
GET /health
{
    "status": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "pool_size": 20,
    "active_connections": 5
}
```

### **Performance Monitoring**
```python
# All responses include execution time
{
    "success": true,
    "data": {...},
    "execution_time_ms": 45.2,
    "rows_affected": 1
}
```

---

## 📊 API Comparison

| Feature | SQLite Server | PostgreSQL Server | Notes |
|---------|---------------|-------------------|-------|
| **Basic CRUD** | ✅ | ✅ | Enhanced with performance monitoring |
| **Raw SQL** | ✅ | ✅ | Added timeout and parameter validation |
| **Health Check** | ✅ | ✅ | Enhanced with connection pool stats |
| **Table Schema** | ✅ | ✅ | PostgreSQL-specific metadata |
| **Vector Search** | ❌ | ✅ | **New**: Semantic similarity search |
| **Memory Operations** | ❌ | ✅ | **New**: Agent memory management |
| **Real-time Events** | ❌ | ✅ | **New**: Redis Streams integration |
| **Connection Pooling** | ❌ | ✅ | **New**: Production-grade performance |
| **Performance Metrics** | ❌ | ✅ | **New**: Execution time tracking |
| **Event Auditing** | ❌ | ✅ | **New**: Change tracking |

---

## 🔧 Configuration

### **Environment Variables**
```bash
# PostgreSQL connection
DATABASE_URL=postgresql://boarderframe:password@localhost:5432/boarderframeos

# Redis connection
REDIS_URL=redis://localhost:6379

# Connection pool settings
DB_POOL_MIN_SIZE=10
DB_POOL_MAX_SIZE=20
```

### **Server Ports**
- **SQLite Server**: `http://localhost:8004` (legacy)
- **PostgreSQL Server**: `http://localhost:8005` (new)
- **After migration**: Move PostgreSQL server to port 8004

---

## 🧪 Testing and Validation

### **Individual Server Testing**
```bash
# Test PostgreSQL server
curl http://localhost:8005/health
curl -X POST http://localhost:8005/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 as test"}'

# Test vector search
curl -X POST http://localhost:8005/vector-search \
  -H "Content-Type: application/json" \
  -d '{"embedding": [0.1, 0.2, ...], "limit": 5}'
```

### **Comparison Testing**
```bash
# Run comprehensive comparison
python mcp/test_database_servers.py

# Expected output:
# ✅ Health Check: Both passed
# ✅ Basic Queries: Both passed  
# 🆕 Vector Operations: PostgreSQL passed, SQLite failed
# 🆕 Memory Operations: PostgreSQL passed, SQLite failed
```

### **Performance Benchmarks**
Expected performance improvements:
- **Query speed**: 2-5x faster with connection pooling
- **Concurrent operations**: 10x better with PostgreSQL
- **Vector search**: New capability, <50ms response time
- **Memory usage**: More efficient with connection reuse

---

## 🔄 Migration Strategies

### **Strategy 1: Gradual Migration (Recommended)**
1. **Week 1**: Deploy PostgreSQL server on port 8005
2. **Week 2**: Test all integrations with new server
3. **Week 3**: Migrate data and update applications
4. **Week 4**: Switch port numbers and retire SQLite server

### **Strategy 2: Direct Replacement**
1. Stop SQLite server
2. Migrate data to PostgreSQL
3. Start PostgreSQL server on port 8004
4. Update all integrations immediately

### **Strategy 3: Dual Operation**
1. Run both servers indefinitely
2. Route new features to PostgreSQL server
3. Keep legacy operations on SQLite server
4. Gradual feature migration over time

---

## 🔍 Troubleshooting

### **Common Migration Issues**

#### **Connection Errors**
```bash
# Check PostgreSQL is running
docker-compose ps postgresql
docker-compose logs postgresql

# Test connection manually
psql postgresql://boarderframe:password@localhost:5432/boarderframeos
```

#### **Redis Connection Issues**
```bash
# Check Redis status
docker-compose ps redis
docker-compose exec redis redis-cli ping
```

#### **Performance Issues**
```bash
# Check connection pool status
curl http://localhost:8005/health

# Monitor query performance
curl http://localhost:8005/stats
```

#### **Vector Search Errors**
```sql
-- Verify pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check vector indexes
SELECT * FROM pg_indexes WHERE indexname LIKE '%embedding%';
```

### **Rollback Procedure**
If issues occur during migration:

1. **Stop PostgreSQL server**: `docker-compose stop postgresql`
2. **Restart SQLite server**: `python mcp/database_server.py`
3. **Update port references**: Change back to 8004
4. **Restore SQLite data**: From backup if needed

---

## 📈 Future Enhancements

### **Planned Features**
- **Automatic embedding generation** using OpenAI/local models
- **Advanced vector indexing** with HNSW for better performance
- **Cross-agent memory sharing** via semantic search
- **Real-time agent notifications** via Redis Streams
- **Metrics dashboard** for database performance monitoring
- **Automated backup and recovery** procedures

### **Integration Roadmap**
1. **Agent Memory Enhancement**: Automatic vector embedding for all agent memories
2. **Real-time Communication**: Redis Streams for live agent coordination
3. **Performance Optimization**: Query optimization and caching strategies
4. **Monitoring Dashboard**: Real-time database and agent metrics
5. **Backup Automation**: Scheduled backups with point-in-time recovery

---

## 📚 API Documentation

### **New Endpoints (PostgreSQL Server)**

#### **Vector Similarity Search**
```http
POST /vector-search
Content-Type: application/json

{
    "embedding": [0.1, 0.2, 0.3, ...],     // Required: 1536-dim vector
    "similarity_threshold": 0.8,            // Optional: min similarity
    "limit": 10,                            // Optional: max results
    "agent_id": "uuid",                     // Optional: filter by agent
    "memory_type": "long_term"              // Optional: filter by type
}
```

#### **Memory Management**
```http
POST /memory
Content-Type: application/json

{
    "agent_id": "agent-uuid",               // Required: agent identifier
    "content": "Memory content",            // Required: memory text
    "memory_type": "short_term",            // Optional: memory category
    "importance": 0.8,                      // Optional: 0.0-1.0 importance
    "embedding": [0.1, 0.2, ...],          // Optional: pre-computed vector
    "metadata": {"key": "value"},           // Optional: additional data
    "conversation_id": "conv-uuid",         // Optional: conversation link
    "workflow_id": "workflow-uuid"          // Optional: workflow link
}
```

#### **Event Streaming**
```http
GET /events?limit=10
```

#### **Enhanced Statistics**
```http
GET /stats
```

---

*This migration provides BoarderframeOS with enterprise-grade database capabilities, semantic search, and real-time coordination features while maintaining backward compatibility during the transition period.*