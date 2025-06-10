# 🏗️ BoarderframeOS Infrastructure

## 🏛️ Architecture Overview

BoarderframeOS uses a **hybrid architecture** with Docker-containerized databases and Python-based application services:

```
┌─────────────────────────────────────────────────────────┐
│                   BoarderframeOS                        │
├─────────────────────────────────────────────────────────┤
│  🎛️ BCC Dashboard (8888)                                │
├─────────────────────────────────────────────────────────┤
│  🤖 AI Agents: Solomon (CEO) + David (CTO)              │
├─────────────────────────────────────────────────────────┤
│  🔌 MCP Servers (8000-8009)                             │
│  ├── Registry (8000) - PostgreSQL                       │
│  ├── Filesystem (8001) - File Operations                │
│  ├── Database (8004) - SQLite                           │
│  ├── LLM (8005), Payment (8006), etc.                   │
├─────────────────────────────────────────────────────────┤
│  📡 Message Bus - SQLite                                │
├─────────────────────────────────────────────────────────┤
│  🐳 Docker Infrastructure                               │
│  ├── PostgreSQL (5434) + pgvector                       │
│  ├── Redis (6379)                                       │
│  ├── Adminer (8081) - DB Admin                          │
│  └── Redis Commander (8082) - Redis Admin               │
└─────────────────────────────────────────────────────────┘
```

## 🐳 Docker Infrastructure

### Containers

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| **boarderframeos_postgres** | pgvector/pgvector:pg16 | 5434→5432 | Primary database with vector embeddings |
| **boarderframeos_redis** | redis:7-alpine | 6379→6379 | Caching and real-time messaging |
| **boarderframeos_adminer** | adminer:latest | 8081→8080 | Database administration |
| **boarderframeos_redis_commander** | rediscommander:latest | 8082→8081 | Redis administration |

### Database Schema

PostgreSQL includes:
- **Agents table** - Agent registry with capabilities and status
- **Agent memories** - Vector embeddings for semantic search
- **Departments** - 24 biblical-named department structure
- **Tasks & workflows** - Task management and coordination
- **Metrics** - Performance and analytics tracking
- **Revenue tracking** - Customer and billing management
- **Message bus** - Inter-agent communication logs

### Port Strategy

- **PostgreSQL: 5434** (not 5432) to avoid conflicts with local installations
- **Redis: 6379** (standard port)
- **MCP Servers: 8000-8009** (Registry on 8000)
- **BCC Dashboard: 8888**

## 🔌 MCP Server Architecture

### Core Servers

| Server | Port | Backend | Purpose |
|--------|------|---------|---------|
| **Registry** | 8000 | PostgreSQL | Service discovery, agent registration |
| **Filesystem** | 8001 | Direct FS | File operations, monitoring |
| **Database** | 8004 | SQLite | General data persistence |

### Service Servers

| Server | Port | Purpose |
|--------|------|---------|
| **LLM** | 8005 | Language model interface |
| **Payment** | 8006 | Revenue and billing |
| **Analytics** | 8007 | System metrics |
| **Customer** | 8008 | CRM functionality |

## 🚀 Startup Sequence

The `startup.py` script follows this sequence:

1. **📦 Dependency Check** - Virtual environment and packages
2. **🐳 Docker Infrastructure** - Auto-starts containers if needed
3. **🗂️ Registry System** - PostgreSQL-backed service discovery
4. **📡 Message Bus** - SQLite-based communication
5. **🔌 MCP Servers** - All 7 servers in priority order
6. **🤖 Agents** - Solomon and David agents
7. **🎛️ BCC Dashboard** - Control center on port 8888

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
# Key settings
POSTGRES_PORT=5434
DATABASE_URL=postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos
REDIS_URL=redis://localhost:6379
```

### Docker Compose

The system uses `docker-compose.yml` for infrastructure:

```bash
# Start infrastructure
docker-compose up -d

# Stop infrastructure  
docker-compose down

# Check status
docker ps
```

## 📊 Health Monitoring

### System Status

```bash
# Comprehensive status check
python system_status.py

# Individual component health
curl http://localhost:8000/health  # Registry
curl http://localhost:8001/health  # Filesystem
curl http://localhost:8004/health  # Database
```

### Docker Health

```bash
# Container status
docker ps

# PostgreSQL connection test
docker exec boarderframeos_postgres psql -U boarderframe -d boarderframeos -c "SELECT current_user;"

# Redis connection test
docker exec boarderframeos_redis redis-cli ping
```

## 🔍 Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   # Start Docker Desktop
   open -a Docker
   ```

2. **Port conflicts**
   ```bash
   # Check what's using ports
   lsof -i :5434  # PostgreSQL
   lsof -i :8000  # Registry
   ```

3. **Database connection issues**
   ```bash
   # Reset Docker infrastructure
   docker-compose down && docker-compose up -d
   ```

4. **Python dependencies**
   ```bash
   # Ensure Python 3.13+
   python --version
   
   # Virtual environment
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

### Known Issues

- **aioredis compatibility**: Temporarily disabled due to Python 3.13 incompatibility
- **Registry fallback**: SQLite-based registry (port 8009) available as backup

## 🛡️ Security

### Database Security

- **Isolated containers** with custom network
- **Strong passwords** defined in environment
- **Local access only** (not exposed to internet)

### API Security

- **Internal communication** between MCP servers
- **Authentication** for admin interfaces
- **Rate limiting** on external endpoints

## 📈 Scalability

### Future Considerations

- **Redis clustering** for horizontal scaling
- **PostgreSQL read replicas** for query performance
- **Load balancing** for MCP servers
- **Kubernetes migration** for production deployment

---

**Status**: ✅ All infrastructure components operational and integrated with startup automation.