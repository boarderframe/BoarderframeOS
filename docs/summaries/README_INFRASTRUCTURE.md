# BoarderframeOS Infrastructure Setup

This guide covers the complete setup of the new PostgreSQL + pgvector + Redis infrastructure for BoarderframeOS.

## 🏗️ Architecture Overview

### **New Infrastructure Stack:**
- **PostgreSQL 16** with pgvector extension for unified data + vector storage
- **Redis 7** for caching and real-time messaging via Streams
- **Docker Compose** for simple, reliable deployment
- **Enhanced schemas** with proper indexing and performance optimization

### **Migration from SQLite:**
- Preserves existing agent memories and interactions
- Adds vector semantic search capabilities
- Consolidates multiple SQLite databases into unified PostgreSQL
- Maintains data integrity during transition

---

## 🚀 Quick Start

### **1. Prerequisites**
```bash
# Install Docker and Docker Compose
# Ensure you have Python 3.11+ installed
pip install -r requirements.txt
```

### **2. Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### **3. Start Infrastructure**
```bash
# Start PostgreSQL + Redis
docker-compose up -d postgresql redis

# Verify services are running
docker-compose ps
```

### **4. Initialize Database**
```bash
# The schema will be automatically created on first connection
# You can verify with:
docker-compose logs postgresql
```

### **5. Test Infrastructure**
```bash
# Run comprehensive test suite
python test_infrastructure.py
```

### **6. Migrate Existing Data (Optional)**
```bash
# Migrate from existing SQLite databases
python migrations/migrate_sqlite_to_postgres.py
```

---

## 📁 File Structure

```
BoarderframeOS/
├── docker-compose.yml           # Main infrastructure configuration
├── .env.example                 # Environment template
├── Dockerfile                   # Application container
├── requirements.txt             # Python dependencies
├── migrations/
│   ├── 001_initial_schema.sql   # Initial PostgreSQL schema
│   └── migrate_sqlite_to_postgres.py  # Data migration script
├── postgres-config/
│   ├── postgresql.conf          # PostgreSQL optimization
│   └── pg_hba.conf             # Authentication configuration
└── test_infrastructure.py      # Infrastructure testing suite
```

---

## 🗄️ Database Schema

### **Core Tables:**
- **`agents`** - Agent registry with hierarchy and capabilities
- **`agent_memories`** - Memory storage with vector embeddings (pgvector)
- **`agent_interactions`** - Inter-agent communication tracking
- **`departments`** - Department structure and configuration
- **`tasks`** - Task management and workflow coordination
- **`metrics`** - Performance and operational metrics

### **Vector Operations:**
```sql
-- Semantic similarity search
SELECT id, content, 1 - (embedding <=> $1) as similarity
FROM agent_memories
ORDER BY embedding <=> $1
LIMIT 10;

-- Custom similarity function
SELECT * FROM search_similar_memories(
    query_embedding := $1,
    similarity_threshold := 0.8,
    max_results := 5,
    agent_filter := $2
);
```

### **Business Tables:**
- **`customers`** - Customer management and subscriptions
- **`revenue_transactions`** - Revenue tracking
- **`api_usage`** - API usage for billing

---

## 🔧 Configuration

### **PostgreSQL Settings** (`postgres-config/postgresql.conf`):
- **Memory**: 256MB shared_buffers, 1GB effective_cache_size
- **Connections**: 200 max_connections
- **Logging**: Detailed query and performance logging
- **Extensions**: pgvector preloaded for vector operations

### **Redis Settings**:
- **Memory**: 512MB max with LRU eviction
- **Persistence**: AOF enabled for durability
- **Streams**: Configured for real-time messaging

### **Docker Compose Profiles**:
```bash
# Start core services only
docker-compose up -d postgresql redis

# Start with application container
docker-compose up -d

# Start with nginx proxy
docker-compose --profile nginx up -d
```

---

## 🧪 Testing and Verification

### **Infrastructure Test Suite** (`test_infrastructure.py`):
```bash
python test_infrastructure.py
```

**Tests Include:**
- PostgreSQL connection and extensions
- Redis connection and operations
- Schema verification and structure
- Vector operations and performance
- Redis Streams functionality
- Database performance benchmarks
- Memory usage analysis

### **Expected Performance:**
- **Vector Search**: <50ms for similarity queries
- **Database Queries**: >100 queries/second
- **Redis Operations**: >1000 ops/second
- **Memory Usage**: <500MB for connection pools

---

## 🔄 Migration Process

### **Automatic Migration** (`migrations/migrate_sqlite_to_postgres.py`):
1. **Exports** existing SQLite data with proper type conversion
2. **Transforms** data for PostgreSQL (UUIDs, JSON, timestamps)
3. **Imports** data preserving relationships and integrity
4. **Generates** vector embeddings for existing memories
5. **Verifies** migration with row count comparisons

### **Migration Tables:**
- ✅ `agents` - Agent registry with UUID conversion
- ✅ `agent_memories` - Memories with vector embedding generation
- ✅ `agent_interactions` - Communication history
- ✅ `tasks` - Task tracking with workflow support
- ✅ `metrics` - Performance metrics
- ✅ `customers` - Business data migration
- ✅ `revenue_transactions` - Revenue history

### **Manual Migration Steps:**
```bash
# 1. Backup existing SQLite databases
cp data/boarderframe.db data/boarderframe.db.backup

# 2. Start PostgreSQL
docker-compose up -d postgresql

# 3. Run migration script
python migrations/migrate_sqlite_to_postgres.py

# 4. Verify migration
python test_infrastructure.py
```

---

## 📊 Monitoring and Maintenance

### **Health Checks:**
```bash
# PostgreSQL health
docker-compose exec postgresql pg_isready -U boarderframe

# Redis health
docker-compose exec redis redis-cli ping

# Application health
curl http://localhost:8000/health
```

### **Performance Monitoring:**
```sql
-- Database statistics
SELECT * FROM pg_stat_database WHERE datname = 'boarderframeos';

-- Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public';

-- Vector index performance
SELECT * FROM pg_stat_user_indexes WHERE indexrelname LIKE '%embedding%';
```

### **Backup Strategy:**
```bash
# PostgreSQL backup
docker-compose exec postgresql pg_dump -U boarderframe boarderframeos > backup.sql

# Redis backup
docker-compose exec redis redis-cli BGSAVE
```

---

## 🔍 Troubleshooting

### **Common Issues:**

#### **PostgreSQL Connection Errors:**
```bash
# Check container status
docker-compose ps postgresql

# Check logs
docker-compose logs postgresql

# Verify network connectivity
docker-compose exec postgresql pg_isready
```

#### **pgvector Extension Issues:**
```sql
-- Verify extension is loaded
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check vector operations
SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector;
```

#### **Redis Connection Issues:**
```bash
# Check Redis status
docker-compose exec redis redis-cli info server

# Test basic operations
docker-compose exec redis redis-cli set test_key test_value
docker-compose exec redis redis-cli get test_key
```

#### **Performance Issues:**
- **Slow queries**: Check `postgresql.conf` settings and indexes
- **High memory usage**: Adjust `shared_buffers` and connection limits
- **Vector search slow**: Verify ivfflat indexes are created

### **Migration Issues:**
- **UUID conversion errors**: Check agent ID format in SQLite
- **Timestamp parsing**: Verify timestamp formats in source data
- **Foreign key violations**: Ensure parent records exist before children

---

## 🔗 Integration with BoarderframeOS

### **Environment Variables:**
```bash
DATABASE_URL=postgresql://boarderframe:password@localhost:5432/boarderframeos
REDIS_URL=redis://localhost:6379
```

### **Connection in Python:**
```python
import asyncpg
import aioredis

# PostgreSQL connection
conn = await asyncpg.connect(DATABASE_URL)

# Redis connection
redis = aioredis.from_url(REDIS_URL)
```

### **Next Steps:**
1. ✅ Infrastructure setup complete
2. 🔄 **Next**: Update database MCP server to use PostgreSQL
3. 🔄 **Next**: Migrate agents to use new database
4. 🔄 **Next**: Implement real-time features with Redis Streams

---

## 📚 Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Redis Documentation](https://redis.io/documentation)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

*This infrastructure provides the foundation for BoarderframeOS's next evolution with enhanced performance, scalability, and vector-powered semantic capabilities.*
