# BoarderframeOS

AI-Native Operating System with Corporate Headquarters (formerly BCC) - A distributed agent coordination system targeting $15K monthly revenue through 120+ specialized AI agents across 24 biblical-named departments.

## 🔧 System Status
**✅ FULLY OPERATIONAL** - All core components working with unified server status tracking, Docker-integrated PostgreSQL/Redis infrastructure, 6 MCP servers running, agents active, Corporate Headquarters dashboard operational with real-time metrics.

## 🗂️ Project Structure

```
BoarderframeOS/
├── agents/                 # Agent implementations
│   ├── david/             # David agent
│   ├── primordials/       # Core system agents (Adam, Eve, Bezalel)
│   └── solomon/           # Solomon agent
├── core/                  # Core framework components
│   ├── agent_controller.py
│   ├── message_bus.py
│   ├── llm_client.py
│   └── ...
├── mcp/                   # MCP server implementations
│   ├── registry_server.py
│   ├── filesystem_server.py
│   ├── database_server.py
│   └── llm_server.py
├── ui/                    # Legacy web interface components
├── corporate_headquarters.py  # Corporate Headquarters dashboard
├── startup.py             # Enhanced single entry point system boot
├── configs/               # Configuration files
├── data/                  # Database and data files
├── logs/                  # System logs
├── tools/                 # Command-line tools
│   ├── claude/           # Separate coding project
│   └── ctl/              # BoarderframeOS CLI tools
├── utils/                 # Utility functions
├── docs/                  # Documentation
├── scripts/               # Shell scripts
├── dev/                   # Development/test files
├── archive/               # Archived/unused files
└── templates/             # System templates
```

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** - Required for PostgreSQL/Redis infrastructure
- **Python 3.13+** - With virtual environment support

### Boot BoarderframeOS
```bash
python startup.py
```
This single command boots the complete system:
- 🏰 **BoarderframeOS System Boot** with beautiful terminal output
- 🐳 **Docker Infrastructure** - Automatically starts PostgreSQL (port 5434) and Redis containers
- 🗂️ **Registry System** - PostgreSQL-backed service discovery and agent registration
- 📡 **Message Bus** - SQLite-based agent communication system
- 🔌 **MCP Servers** (Registry, Filesystem, PostgreSQL Database, Payment, Analytics, Customer)
- 🤖 **AI Agents** (Solomon - Chief of Staff, David - CEO)
- 🎛️ **Corporate Headquarters** on http://localhost:8888
- 🌐 **Auto-opens browser** to Corporate Headquarters
- 💬 **Chat with agents** through the web interface

### Check System Status
```bash
python system_status.py
```

## 🔧 Components

### Infrastructure
- **PostgreSQL** (port 5434) - Primary database with pgvector for embeddings
- **Redis** (port 6379) - Caching and real-time messaging
- **Docker** - Containerized infrastructure management

### MCP Servers
- **Registry Server** (port 8000) - Service discovery and registration
- **Filesystem Server** (port 8001) - File operations and monitoring
- **PostgreSQL Database Server** (port 8010) - Primary database operations
- **Payment Server** (port 8006) - Revenue and billing management
- **Analytics Server** (port 8007) - System metrics and analytics
- **Customer Server** (port 8008) - Customer relationship management
- **Agent Cortex** (port 8889) - Intelligent model orchestration (replaces LLM Server)

### AI Agents
- **Solomon** - Chief of Staff AI (claude-3-5-sonnet-latest)
- **David** - CEO Agent (claude-3-5-sonnet-latest) 
- **Adam** - Agent Creator (future agent generation)
- **Eve** - Agent Development (future)

### Corporate Headquarters (formerly BCC)
- **Corporate HQ** (port 8888) - Real-time system monitoring and control with unified server status
- **Agent Chat** - Direct communication with Solomon, David, and other agents
- **Department Analytics** - 24 biblical-named departments with visual metrics
- **Real-time Status** - Accurate MCP server status, agent metrics, system health
- **HQ Metrics Layer** - Comprehensive metrics calculation and visualization
- **Auto-refreshes** every 30 seconds with real-time data

## 📋 Features

- **AI-Native Operating System**: 120+ specialized agents across 24 departments
- **BoarderframeOS BCC**: Modern control center with agent chat capabilities
- **Message Bus Architecture**: Async communication with priorities and correlation IDs
- **MCP Integration**: Standardized tool communication ("USB-C for AI")
- **Biblical Hierarchy**: Strategic naming (Solomon → David → Adam/Eve → specialized agents)
- **Single Boot Command**: `python startup.py` starts everything
- **Real-time Monitoring**: Live status of all components
- **Agent Factory**: Future implementation - Adam will create new agents automatically
- **Revenue Focus**: Targeting $15K monthly through agent services
- **Docker Integration**: Automated PostgreSQL/Redis infrastructure management
- **Hybrid Architecture**: PostgreSQL for persistent data, SQLite for message bus
- **Health Monitoring**: Comprehensive system health checks and status reporting

## 🛠️ Development

### Directory Purpose
- **agents/**: Individual agent implementations
- **core/**: Shared framework components
- **mcp/**: MCP server implementations
- **ui/**: Web interface and dashboards
- **tools/claude/**: Independent coding project (keep separate)
- **tools/ctl/**: BoarderframeOS command-line utilities

### File Organization
- **docs/**: All documentation and guides
- **scripts/**: Shell scripts and utilities
- **dev/**: Test files and development utilities
- **archive/**: Old/unused files (kept for reference)

## 🧹 Recent Cleanup

The project structure has been flattened and organized:
- Removed redundant nested `boarderframeos/boarderframeos/` structure
- Merged common folders (tools, configs, data, logs)
- Preserved separate Claude project in `tools/claude/`
- Moved all documentation to `docs/`
- Archived unused files for reference

## 📝 Usage

1. **Boot BoarderframeOS**: `python startup.py`
2. **Access BCC**: http://localhost:8888 (opens automatically)
3. **Chat with agents**: Use the built-in chat interface in BCC
4. **Check status**: `python system_status.py`
5. **View logs**: Check `logs/` directory

## 🎛️ BoarderframeOS BCC Features

- **Agent Communication**: Direct chat with Solomon (Chief of Staff), David (CEO), and Adam (Agent Creator)
- **System Monitoring**: Real-time status of MCP servers, agents, and system metrics
- **Department Analytics**: Overview of 24 biblical-named departments
- **Message Bus Integration**: Real agent communication (not simulated)
- **Modern UI**: Dark theme with real-time updates
- **Service Health**: Live monitoring of all infrastructure components

## 🔍 Monitoring

- **Real-time status**: Dashboard shows live component status
- **Health checks**: Automatic monitoring of all services
- **Log aggregation**: Centralized logging in `logs/`
- **Process monitoring**: Agent and server process tracking

## 🔧 Troubleshooting

### Docker Issues
```bash
# Check Docker containers
docker ps

# Restart infrastructure
docker-compose down && docker-compose up -d

# Check PostgreSQL connection
docker exec boarderframeos_postgres psql -U boarderframe -d boarderframeos -c "SELECT current_user;"
```

### Port Conflicts
- **PostgreSQL**: Uses port 5434 (not standard 5432) to avoid conflicts
- **MCP Servers**: Use ports 8000-8010 (PostgreSQL DB server on 8010)
- **Corporate Headquarters**: Uses port 8888
- **Agent Cortex**: Uses port 8889

### System Status
```bash
# Check detailed system status
python system_status.py

# Check specific component logs
tail -f logs/[component].log

# Manual MCP server health check
curl http://localhost:8000/health
```

### Common Issues
1. **Docker not running**: Start Docker Desktop
2. **Port conflicts**: Check `lsof -i :5434` for PostgreSQL conflicts
3. **Python dependencies**: Ensure using Python 3.13+ with virtual environment
4. **aioredis compatibility**: Temporarily disabled due to Python 3.13 compatibility

## 🆕 Recent Improvements (January 2025)

### Server Status Unification
- Fixed server status inconsistencies across all UI components
- Implemented single source of truth for server status
- Corporate HQ now properly updates metrics layer with real-time status
- All UI components (header, welcome page, servers page) show consistent status

### Database Standardization
- Migrated from SQLite (port 8004) to PostgreSQL (port 8010) for all operations
- Fixed all database connection references throughout the codebase
- Improved performance with PostgreSQL-specific optimizations

### Agent Communication Fixes
- Fixed AgentMessage parameter error (changed 'data' to 'content')
- Improved message bus reliability and error handling
- Enhanced agent orchestrator with proper status tracking

### UI/UX Improvements
- Corporate Headquarters replaces BoarderframeOS BCC
- Added HQ Metrics Layer for comprehensive system visualization
- Enhanced dashboard with accurate real-time metrics
- Improved server status display with health indicators