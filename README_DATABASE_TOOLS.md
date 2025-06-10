# BoarderframeOS Database Management Tools

Complete guide to managing your PostgreSQL database with multiple interfaces and CLI tools.

## 🛠️ Available Tools

### **1. Web-Based Tools (Recommended)**

#### **pgAdmin 4** - Full-Featured PostgreSQL Admin
- **URL**: http://localhost:8080
- **Login**: admin@boarderframeos.local / admin_secure_2025
- **Features**: Complete database administration, query editor, visual schema browser

#### **Adminer** - Lightweight Database Manager  
- **URL**: http://localhost:8081
- **Login**: Server: `postgresql`, Username: `boarderframe`, Database: `boarderframeos`
- **Features**: Simple, fast interface for quick operations

#### **Redis Commander** - Redis Management
- **URL**: http://localhost:8082
- **Login**: admin / admin_secure_2025
- **Features**: Redis key browser, real-time monitoring, Streams viewer

### **2. Command Line Tools**

#### **Database CLI** (`./scripts/db`)
```bash
# Connect to database
./scripts/db connect

# Show status and stats
./scripts/db status

# List tables and schemas
./scripts/db tables
./scripts/db schema agents

# View data
./scripts/db agents
./scripts/db memories
./scripts/db count agent_memories

# Test vector operations
./scripts/db vector-test

# Database management
./scripts/db backup
./scripts/db restore backup_20250127.sql

# Launch web admin tools
./scripts/db admin
```

#### **Quick Query Tool** (`./scripts/db-query`)
```bash
# Execute quick SQL queries
./scripts/db-query "SELECT COUNT(*) FROM agents"
./scripts/db-query "SELECT name, department FROM agents WHERE status = 'active'"
./scripts/db-query "SELECT * FROM agent_memories ORDER BY created_at DESC LIMIT 5"
```

#### **Native PostgreSQL CLI**
```bash
# Direct psql connection
psql postgresql://boarderframe:boarderframe_secure_2025@localhost:5432/boarderframeos
```

---

## 🚀 Quick Start

### **Launch All Admin Tools**
```bash
# Start database infrastructure
docker-compose up -d postgresql redis

# Launch web admin interfaces
./scripts/db admin

# Access tools at:
# - pgAdmin: http://localhost:8080
# - Adminer: http://localhost:8081  
# - Redis Commander: http://localhost:8082
```

### **Connect via CLI**
```bash
# Interactive database session
./scripts/db connect

# Quick status check
./scripts/db status

# View all agents
./scripts/db agents
```

---

## 🔍 Common Operations

### **Exploring Data**

#### **List Tables and Row Counts**
```bash
./scripts/db tables
```

#### **View Table Schema**
```bash
./scripts/db schema agents
./scripts/db schema agent_memories
./scripts/db schema departments
```

#### **Check Data Counts**
```bash
./scripts/db count agents
./scripts/db count agent_memories
./scripts/db count tasks
```

### **Agent Operations**

#### **View All Agents**
```bash
./scripts/db agents
```

#### **Agent Memories**
```bash
# All memories
./scripts/db memories

# Memories for specific agent
./scripts/db memories "agent-uuid-here"
```

#### **Custom Queries**
```bash
# Active agents by department
./scripts/db-query "
    SELECT department, COUNT(*) as agent_count 
    FROM agents 
    WHERE status = 'active' 
    GROUP BY department
"

# Recent interactions
./scripts/db-query "
    SELECT 
        ai.interaction_type,
        a1.name as source_agent,
        a2.name as target_agent,
        ai.started_at
    FROM agent_interactions ai
    LEFT JOIN agents a1 ON ai.source_agent_id = a1.id
    LEFT JOIN agents a2 ON ai.target_agent_id = a2.id
    ORDER BY ai.started_at DESC
    LIMIT 10
"
```

### **Vector Operations**

#### **Test Vector Extension**
```bash
./scripts/db vector-test
```

#### **Vector Similarity Queries**
```sql
-- In pgAdmin or via db-query:
SELECT 
    content,
    1 - (embedding <=> '[0.1,0.2,0.3,...]'::vector) as similarity
FROM agent_memories
ORDER BY embedding <=> '[0.1,0.2,0.3,...]'::vector
LIMIT 10;
```

### **Performance Monitoring**

#### **Database Statistics**
```bash
./scripts/db status
```

#### **Table Sizes**
```bash
./scripts/db-query "
    SELECT 
        tablename,
        pg_size_pretty(pg_total_relation_size(tablename)) as size,
        pg_total_relation_size(tablename) as bytes
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(tablename) DESC
"
```

#### **Active Connections**
```bash
./scripts/db-query "
    SELECT 
        datname,
        numbackends as connections,
        xact_commit as commits,
        xact_rollback as rollbacks
    FROM pg_stat_database 
    WHERE datname = 'boarderframeos'
"
```

---

## 💾 Backup and Recovery

### **Create Backups**
```bash
# Automatic timestamped backup
./scripts/db backup

# Manual backup with custom name
pg_dump -h localhost -p 5432 -U boarderframe boarderframeos > my_backup.sql
```

### **Restore from Backup**
```bash
# Interactive restore (with confirmation)
./scripts/db restore backup_20250127_143022.sql

# Direct restore
psql -h localhost -p 5432 -U boarderframe boarderframeos < backup.sql
```

### **Reset Database** ⚠️
```bash
# Complete database reset (DESTRUCTIVE!)
./scripts/db reset
```

---

## 🌐 Web Interface Guide

### **pgAdmin 4** - Professional Database Administration

#### **Access & Login**
1. Navigate to http://localhost:8080
2. Login with:
   - **Email**: admin@boarderframeos.local  
   - **Password**: admin_secure_2025

#### **Key Features**
- **Query Tool**: SQL editor with syntax highlighting and execution plans
- **Schema Browser**: Visual exploration of tables, relationships, and indexes
- **Data Viewer**: Browse and edit table data with filtering and sorting
- **Backup/Restore**: GUI-based database backup and restore operations
- **User Management**: Database user and permission management
- **Performance Monitoring**: Real-time statistics and query performance analysis

#### **Useful Queries in pgAdmin**
```sql
-- Vector similarity search example
SELECT 
    id,
    content,
    memory_type,
    1 - (embedding <=> $1::vector) as similarity
FROM agent_memories
WHERE 1 - (embedding <=> $1::vector) > 0.8
ORDER BY embedding <=> $1::vector
LIMIT 10;

-- Agent activity analysis
SELECT 
    a.name,
    a.department,
    COUNT(ai.id) as interaction_count,
    MAX(ai.started_at) as last_interaction
FROM agents a
LEFT JOIN agent_interactions ai ON a.id = ai.source_agent_id
GROUP BY a.id, a.name, a.department
ORDER BY interaction_count DESC;
```

### **Adminer** - Lightweight Quick Access

#### **Access & Login**
1. Navigate to http://localhost:8081
2. Login with:
   - **System**: PostgreSQL
   - **Server**: postgresql
   - **Username**: boarderframe
   - **Password**: boarderframe_secure_2025
   - **Database**: boarderframeos

#### **Key Features**
- **Fast Table Browser**: Quick navigation through database structure
- **Simple Queries**: Basic SQL execution with results display
- **Data Export**: Export data in various formats (CSV, JSON, SQL)
- **Schema Comparison**: Compare database schemas
- **Quick Editing**: Inline table data editing

### **Redis Commander** - Redis Management

#### **Access & Login**
1. Navigate to http://localhost:8082
2. Login with:
   - **Username**: admin
   - **Password**: admin_secure_2025

#### **Key Features**
- **Key Browser**: Explore Redis keys and data structures
- **Streams Viewer**: Monitor Redis Streams for real-time events
- **Memory Usage**: Track Redis memory consumption
- **TTL Management**: View and manage key expiration times
- **CLI Interface**: Execute Redis commands directly

---

## 🔧 Troubleshooting

### **Connection Issues**

#### **PostgreSQL Not Accessible**
```bash
# Check if PostgreSQL is running
docker-compose ps postgresql

# Check PostgreSQL logs
docker-compose logs postgresql

# Test connection
pg_isready -h localhost -p 5432 -U boarderframe -d boarderframeos
```

#### **Web Interfaces Not Loading**
```bash
# Check if admin services are running
docker-compose --profile admin ps

# Restart admin services
docker-compose --profile admin restart

# Check port conflicts
netstat -tulpn | grep :8080
netstat -tulpn | grep :8081
netstat -tulpn | grep :8082
```

### **Performance Issues**

#### **Slow Queries**
```sql
-- Check slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

#### **Connection Pool Status**
```bash
# Check active connections
./scripts/db-query "
    SELECT 
        state,
        COUNT(*) as connection_count
    FROM pg_stat_activity
    WHERE datname = 'boarderframeos'
    GROUP BY state
"
```

### **Vector Operation Issues**

#### **pgvector Extension Problems**
```sql
-- Check if pgvector is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Test vector operations
SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector as distance;
```

#### **Vector Index Performance**
```sql
-- Check vector indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexdef LIKE '%vector%';
```

---

## 📚 Advanced Tips

### **Performance Optimization**
- Use pgAdmin's query planner to analyze slow queries
- Monitor connection pool usage with `./scripts/db status`
- Regular VACUUM and ANALYZE operations for table maintenance
- Use partial indexes for frequently filtered queries

### **Security Best Practices**
- Change default passwords in production
- Use SSL connections for remote access
- Implement row-level security for multi-tenant scenarios
- Regular backup testing and recovery procedures

### **Development Workflow**
- Use Adminer for quick data exploration
- Use pgAdmin for complex query development and debugging
- Use CLI tools for automated scripts and monitoring
- Use Redis Commander to monitor real-time agent communication

---

*This comprehensive toolset provides everything needed to effectively manage your BoarderframeOS PostgreSQL database, from quick CLI operations to advanced administrative tasks.*