# BoarderframeOS UI Startup Guide

## 🚀 Quick Start

The UI server is now running! Access it at:

**📍 Main Dashboard: http://localhost:8080**

## 🎯 Current Status

✅ **UI Server Running** - Basic interface is live
⚠️ **Backend Pending** - Need to start the full system

## 🔧 To Enable Full Features

1. **Run the setup script:**
```bash
cd /Users/cosburn/BoarderframeOS/boarderframeos
python setup_boarderframeos.py
```

2. **Start the MCP servers:**
```bash
# In separate terminals or background:
python mcp/filesystem_server.py &
python mcp/database_server.py &
python mcp/llm_server.py &
python mcp/registry_server.py &
```

3. **Initialize the agent system:**
```bash
python startup.py
```

## 📱 Available Interfaces

- **Dashboard**: http://localhost:8080 - System overview
- **Health Check**: http://localhost:8080/health - Server status
- **API Status**: http://localhost:8080/api/status - Backend connectivity

## 🔄 Next Steps

1. The basic UI is working - you can see the dashboard
2. Solomon chat interface is ready (shows offline until backend starts)
3. System status cards show current state
4. Quick action buttons for system management

## 🛠️ Full System Architecture

Once you run the setup and start the backend:
- Solomon will come online for chat
- Agent monitoring will show live agents
- Real-time WebSocket updates
- Full orchestration visualization
- LLM activity monitoring

## 📞 Integration with Your Site

To integrate into your existing site:
1. The UI runs on port 8080
2. Can be proxied through your main site
3. WebSocket endpoints available for real-time data
4. REST API endpoints for system interaction

The foundation is ready - run the setup script to bring the full AI operating system online!
