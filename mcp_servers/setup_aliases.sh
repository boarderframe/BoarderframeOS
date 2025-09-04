#!/bin/bash

# Add convenient aliases for MCP server management

ALIAS_FILE="$HOME/.mcp_aliases"
SCRIPT_DIR="/Users/cosburn/MCP Servers"

cat > "$ALIAS_FILE" << 'EOF'
# MCP Server Management Aliases
alias mcp-start='cd "/Users/cosburn/MCP Servers" && ./start_servers.sh start'
alias mcp-stop='cd "/Users/cosburn/MCP Servers" && ./start_servers.sh stop'
alias mcp-restart='cd "/Users/cosburn/MCP Servers" && ./start_servers.sh restart'
alias mcp-status='cd "/Users/cosburn/MCP Servers" && ./start_servers.sh status'
alias mcp-logs='cd "/Users/cosburn/MCP Servers" && ./start_servers.sh logs'
alias mcp-ui='open http://localhost:3001'
alias mcp-api='open http://localhost:8000'
EOF

echo "Aliases created in $ALIAS_FILE"
echo
echo "Add this line to your ~/.bashrc or ~/.zshrc:"
echo "source $ALIAS_FILE"
echo
echo "Or run: echo 'source $ALIAS_FILE' >> ~/.zshrc"
echo
echo "Available commands after sourcing:"
echo "  mcp-start   - Start all MCP servers"
echo "  mcp-stop    - Stop all MCP servers"
echo "  mcp-restart - Restart all MCP servers"
echo "  mcp-status  - Show server status"
echo "  mcp-logs    - Show recent logs"
echo "  mcp-ui      - Open management UI"
echo "  mcp-api     - Open API documentation"