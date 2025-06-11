# 🚀 BoarderframeOS Quick Start

## Prerequisites

- **Docker Desktop** - Must be running for PostgreSQL/Redis infrastructure
- **Python 3.13+** - With virtual environment support

## Single Command Boot

BoarderframeOS now boots with a single command:

```bash
cd /Users/cosburn/BoarderframeOS
python startup.py
```

## What Happens

This single command boots the complete BoarderframeOS system:

- 🏰 **System Boot** with beautiful terminal output and status tracking
- 🐳 **Docker Infrastructure** - Auto-starts PostgreSQL (port 5434) and Redis containers
- 🗂️ **Registry System** - PostgreSQL-backed service discovery and agent registration
- 📡 **Message Bus** - SQLite-based agent communication system
- 🔌 **MCP Servers** launch (Registry, Filesystem, PostgreSQL Database, Payment, Analytics, Customer)
- 🧠 **Agent Cortex** initializes for intelligent model orchestration (port 8889)
- 📊 **HQ Metrics Layer** starts for comprehensive system tracking
- 🤖 **AI Agents** initialize (Solomon - Chief of Staff, David - CEO)
- 🎛️ **Corporate Headquarters** starts on port 8888
- 🌐 **Auto-opens browser** to Corporate Headquarters dashboard
- 💬 **Agent Chat** ready for immediate use

## Corporate Headquarters URL

**http://localhost:8888**

## What You Can Do

1. **Chat with AI Agents**: Direct communication with Solomon (Chief of Staff) and David (CEO)
2. **Monitor System**: Real-time status of all MCP servers and agents
3. **View Departments**: Analytics for 24 biblical-named departments
4. **Check Health**: Live monitoring of all infrastructure components

## Alternative Start Methods

```bash
# Via shell script
./scripts/start

# Via bash script with message
./scripts/start.sh
```

## Stop the System

Press **Ctrl+C** in the terminal to gracefully shutdown all components.

## Check System Status

```bash
python system_status.py
```

## Troubleshooting

### If startup fails:

1. **Check Docker**: Ensure Docker Desktop is running
2. **Check ports**: PostgreSQL uses port 5434 (not 5432) to avoid conflicts
3. **Check logs**: Look in `logs/` directory for detailed error messages
4. **Manual health check**: `curl http://localhost:8000/health`

### Common Issues:

- **"Registry system failed"**: Start Docker Desktop and retry
- **Port conflicts**: Check for services using ports 5434, 8000-8010, 8888, or 8889
- **Python dependencies**: Ensure using Python 3.13+ with virtual environment
- **Server status issues**: Fixed in latest version - all UI components show unified status

---

**The simplest way:** Just run `python startup.py` and BoarderframeOS boots completely!
