# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## BoarderframeOS Architecture

BoarderframeOS is an AI business operating system that manages AI agents across distributed compute zones. The system is designed to run on DGX Spark hardware with 2000 TOPS compute power.

### Core Architecture

The system follows a layered architecture:
- **Core Layer**: Base agent framework, LLM client, and compute management
- **Agent Layer**: Individual AI agents (Jarvis, CEO, etc.) that inherit from BaseAgent
- **MCP Server Layer**: Model Context Protocol servers providing filesystem, git, and terminal access
- **Zone Layer**: Compute allocation and resource management
- **Control Layer**: `boarderctl` CLI and web interfaces

Key architectural relationships:
- Agents communicate with MCP servers via the MCP protocol
- Zones allocate compute resources (TOPS) to agents
- `boarderctl` manages the entire system through the boarderframe.yaml configuration
- LLMClient provides Claude 4 integration for agent intelligence

## Key Commands

### Development Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize BoarderframeOS
./boarderctl init
```

### Running the System
```bash
# Start all services (MCP servers + agents)
python startup.py

# Start Jarvis web chat interface
python jarvis_web_chat.py

# Start individual MCP servers
python mcp-servers/filesystem_server.py  # Port 8001
python mcp-servers/git_server.py         # Port 8002
python mcp-servers/terminal_server.py    # Port 8003
```

### Agent Management
```bash
# Create a new agent
./boarderctl agent create jarvis --type jarvis --zone executive

# List all agents
./boarderctl agent list

# Start/stop agents
./boarderctl agent start jarvis
./boarderctl agent stop jarvis
```

### Zone Management
```bash
# Create a compute zone
./boarderctl zone create executive --allocation 20 --type business-ops

# List zones
./boarderctl zone list
```

### Testing
```bash
# Run all tests (when implemented)
pytest

# Run specific test file
pytest tests/test_agent.py
```

## Key Configuration Files

### boarderframe.yaml
Central configuration storing:
- Agent definitions and status
- Zone allocations
- MCP server configurations
- Compute resource tracking (TOPS, memory)

### .env
Environment variables:
- `ANTHROPIC_API_KEY`: Required for Claude 4 integration

## LLM Integration

The system uses Claude 4 Opus by default, configured in `core/llm_client.py`:
- Model: `claude-opus-4-20250514`
- The LLMClient handles both Anthropic Claude and local Ollama models
- Agents use LLMClient for reasoning and decision-making

## MCP Server Security

All MCP servers implement security measures:
- **Filesystem**: Sandboxed to BoarderframeOS directory only
- **Git**: Requires authentication for remote operations
- **Terminal**: Whitelist-based command execution

## Web Interfaces

### Jarvis Web Chat (Port 8890)
Modern chat interface with:
- WebSocket-based real-time communication
- MCP server status monitoring
- Settings panel for model configuration
- Responsive design with mobile support

The UI tracks MCP server availability and shows tool indicators when servers are online.

## Agent Development

When creating new agents:
1. Inherit from `BaseAgent` in `core/base_agent.py`
2. Implement `think()` and `act()` methods
3. Use MCP clients for external operations
4. Register in boarderframe.yaml
5. Follow the sense-think-act loop pattern

## Important Notes

- The system is designed for DGX Spark hardware but runs on any Python 3.9+ environment
- All file operations through MCP servers are sandboxed for security
- Agents run asynchronously and communicate through structured protocols
- The warm-gradient UI theme is used throughout for a friendly experience