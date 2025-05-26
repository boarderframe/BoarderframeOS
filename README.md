# BoarderframeOS - Clean & Organized

A distributed agent coordination system with MCP (Model Context Protocol) servers.

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
├── ui/                    # Web interface components
│   ├── templates/         # HTML templates
│   └── *.py              # Dashboard servers
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

### Start the System
```bash
python startup.py
```
This provides:
- ✅ Clean terminal output with emojis
- 🗄️ MCP server health checks
- 🤖 Agent status monitoring
- 📊 Auto-launching dashboard
- 🌐 Opens browser automatically

### Check System Status
```bash
python system_status.py
```

## 🔧 Components

### MCP Servers
- **Registry Server** (port 8000) - Agent registry and discovery
- **Filesystem Server** (port 8001) - File operations
- **Database Server** (port 8004) - Data persistence
- **LLM Server** (port 8005) - Language model interface

### Agents
- **Solomon** - Primary coordination agent
- **David** - Specialized task agent

### Dashboard
- **Dashboard** (port 8888) - Real-time system monitoring
- Shows startup status, agent health, MCP server status
- Auto-refreshes every 2 seconds

## 📋 Features

- **Clean Architecture**: Flat, organized folder structure
- **Health Monitoring**: Real-time status checks for all components
- **Enhanced Startup**: Beautiful terminal output with progress indicators
- **Web Dashboard**: Modern UI for system monitoring
- **Virtual Environment**: Isolated Python dependencies
- **Automatic Setup**: Dependency installation and environment setup

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

1. **Start the system**: `python startup.py`
2. **Check status**: `python system_status.py`
3. **Access dashboard**: http://localhost:8888
4. **View logs**: Check `logs/` directory

The system will automatically:
- Install required dependencies
- Start MCP servers with health checks
- Launch the dashboard
- Initialize agents
- Open the dashboard in your browser

## 🔍 Monitoring

- **Real-time status**: Dashboard shows live component status
- **Health checks**: Automatic monitoring of all services
- **Log aggregation**: Centralized logging in `logs/`
- **Process monitoring**: Agent and server process tracking