# Folder Reorganization Summary

This document explains the reorganization of the BoarderframeOS folder structure for better organization and maintainability.

## Changes Made

### New Folder Structure

#### `/docs/` - Documentation
**Moved from root:**
- `AGENT_CONTROL_IMPLEMENTATION_SUMMARY.md`
- `QUICK_START.md`
- `README_COMMANDS.md`
- `UI_STARTUP_GUIDE.md`

#### `/scripts/` - Shell Scripts & Utilities
**Moved from root:**
- `chat.sh`
- `run_ui.sh`
- `start.sh`
- `update_dashboard.sh`
- `dashboard` (script)
- `start` (script)
- `status` (script)
- `stable` (script)
- `ui` (script)

#### `/dev/` - Development & Testing
**Moved from root:**
- `agent_control_demo.py`
- `debug_enum_issue.py`
- `debug_message_bus.py`
- `demo_enhanced_agent_coordination.py`
- `simple_agent_control_test.py`
- `simple_coordination_demo.py`
- `simple_demo_test.py`
- `simple_message_bus_test.py`
- `test_*.py` (all test files)
- `websocket_test.html`

#### `/archive/` - Old/Unused Files
**Moved from root:**
- `deploy_david_agent.py`
- `install_deps.py`
- `minimal_server.py`
- `persistent_ui.py`
- `quick_dashboard.py`
- `quick_ui.py`
- `simple_start.py`
- `stable_ui.py`
- `start_all.py`
- `start_complete_system.py` (old version)
- `start_solomon.py`
- `start_solomon_combined.py`
- `start_system_simple.py`
- `solomon_chat.html`
- `health_check.py` (duplicate)

**Moved from boarderframeos/:**
- `simple_ui_server.py`
- `startup.py`
- `start_ui.py`
- `start_agent.py`
- `run_agent.py`
- `setup_boarderframeos.py`
- `health_check_boarderframeos.py` (renamed from health_check.py)

### Removed Empty Folders
- `/agents/` (root)
- `/mcp-servers/` (root)
- `/zones/` (root)
- `/templates/` (root)
- `/boarderframeos/experiments/`
- `/boarderframeos/docs/`
- `/boarderframeos/memories/`
- `/boarderframeos/zones/`
- `/boarderframeos/venv/` (duplicate virtual environment)

### Cleaned Up
- Removed all `__pycache__` directories
- Removed all `.DS_Store` files
- Cleaned up duplicate virtual environments

## Current Active Files (Root)

### Main System Files
- `start_complete_system_enhanced.py` - Main startup script (MCP + Agents + Dashboard)
- `start_system_enhanced.py` - Enhanced agent coordination startup
- `enhanced_dashboard.py` - Web dashboard for system monitoring
- `system_status.py` - System health checker
- `boarderframe.yaml` - Main configuration file

### Configuration & Environment
- `.env` - Environment variables
- `.gitignore` - Git ignore rules
- `.venv/` - Python virtual environment
- `README.md` - Main documentation

### Core Package
- `boarderframeos/` - Main package with clean structure

### Data & Logs
- `configs/` - Configuration files
- `data/` - Data storage
- `logs/` - Log files

### Tools
- `tools/` - Development tools (kept as-is per user request)

## Benefits of Reorganization

1. **Clear separation of concerns** - Active vs archived vs development files
2. **Easier navigation** - Related files grouped together
3. **Reduced clutter** - Root directory only contains essential files
4. **Better maintainability** - Easier to find and manage files
5. **Documentation organization** - All docs in one place
6. **Script organization** - All shell scripts grouped together
7. **Development workflow** - Test/debug files separated from production
8. **Archive preservation** - Old files kept for reference but out of the way

## Usage

- **Main startup**: Use `python start_complete_system_enhanced.py`
- **Documentation**: Check `/docs/` folder
- **Shell scripts**: Use scripts from `/scripts/` folder
- **Development**: Use files in `/dev/` for testing
- **Reference**: Check `/archive/` for old implementations
