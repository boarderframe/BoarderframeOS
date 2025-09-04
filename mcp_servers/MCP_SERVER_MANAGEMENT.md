# MCP Server Management Guide

## 🚀 Quick Start

```bash
# Start all MCP servers
./start_all_mcp_servers.sh

# Check status
./status_mcp_servers.sh

# Stop all servers
./stop_all_mcp_servers.sh
```

## 📋 Available Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **MCP Client UI** | 5173 | Interactive web interface for MCP servers | http://localhost:5173 |
| **Simple Filesystem** | 9001 | Basic file operations | http://localhost:9001/health |
| **Advanced Filesystem** | 9002 | Enhanced file operations with browser | http://localhost:9002/health |
| **Playwright Server** | 9003 | Browser automation and web scraping | http://localhost:9003/health |
| **Kroger MCP Server** | 9004 | Grocery shopping API with cart management | http://localhost:9004/health |

## 🔧 Management Scripts

### `start_all_mcp_servers.sh`
- ✅ Starts all 4 MCP servers in background
- ✅ Checks if ports are already in use
- ✅ Creates log files in `./logs/` directory
- ✅ Performs health checks after startup
- ✅ Shows summary with URLs

### `stop_all_mcp_servers.sh`
- ✅ Gracefully stops all servers using PID files
- ✅ Falls back to port-based termination if needed
- ✅ Force kills if graceful shutdown fails
- ✅ Cleans up PID files
- ✅ Optional log cleanup with `--clean-logs`

### `status_mcp_servers.sh`
- ✅ Health check all servers
- ✅ Shows process information (PID, memory)
- ✅ Displays available tools count
- ✅ Shows version information
- ✅ Optional recent log entries with `--logs`

## 📁 File Structure

```
MCP Servers/
├── start_all_mcp_servers.sh    # Start all servers
├── stop_all_mcp_servers.sh     # Stop all servers  
├── status_mcp_servers.sh       # Check server status
├── logs/                       # Server log files
│   ├── simple_filesystem.log
│   ├── advanced_filesystem.log
│   ├── playwright.log
│   └── kroger_mcp.log
├── *.pid                       # Process ID files
├── simple_filesystem_server.py
├── advanced_filesystem_server.py
├── simple_playwright_server.py
├── kroger_mcp_server.py
└── .env                        # Environment configuration
```

## 🌐 API Documentation

Each server provides interactive API documentation:

- **Simple Filesystem**: http://localhost:9001/docs
- **Advanced Filesystem**: http://localhost:9002/docs  
- **Playwright Server**: http://localhost:9003/docs
- **Kroger MCP Server**: http://localhost:9004/docs

## 🔍 Monitoring

### Health Checks
```bash
curl http://localhost:9001/health  # Simple Filesystem
curl http://localhost:9002/health  # Advanced Filesystem
curl http://localhost:9003/health  # Playwright Server
curl http://localhost:9004/health  # Kroger MCP Server
```

### Log Monitoring
```bash
# View recent logs
./status_mcp_servers.sh --logs

# Follow specific server logs
tail -f logs/kroger_mcp.log
tail -f logs/playwright.log
```

## 🐛 Troubleshooting

### Server Won't Start
1. Check if port is already in use: `lsof -i :9001`
2. Check log files in `./logs/`
3. Verify Python environment and dependencies
4. Check `.env` file for required configuration

### Server Running But Not Responding
1. Check health endpoint: `curl http://localhost:9004/health`
2. Review recent log entries: `./status_mcp_servers.sh --logs`
3. Restart specific server: stop all, then start all

### Memory Issues
1. Check memory usage: `./status_mcp_servers.sh`
2. Restart servers if memory usage is high
3. Monitor logs for memory-related errors

## 🔧 Environment Setup

### Required Files
- `.env` - Contains Kroger API credentials and configuration
- `requirements.txt` - Python dependencies
- Individual server Python files

### Dependencies
```bash
pip install -r requirements.txt
```

## 💡 Development Tips

1. **Background Operation**: All servers run in background, logs are captured
2. **Hot Reload**: Kroger MCP server supports auto-reload on file changes
3. **PID Management**: Scripts track process IDs for clean shutdowns
4. **Port Management**: Automatic detection and handling of port conflicts
5. **Error Recovery**: Fallback mechanisms for graceful degradation

## 🚀 Production Considerations

- Use process managers like `supervisord` or `systemd` for production
- Implement proper logging rotation
- Set up monitoring and alerting
- Consider containerization with Docker for deployment
- Configure reverse proxy (nginx) for external access

---

**Quick Commands:**
- `./start_all_mcp_servers.sh` - Start everything
- `./status_mcp_servers.sh` - Check status
- `./stop_all_mcp_servers.sh` - Stop everything