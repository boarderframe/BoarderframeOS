#!/bin/bash

echo "🔍 Starting Open WebUI Debug Proxy"
echo "=================================="
echo ""
echo "📋 Setup Instructions:"
echo "1. Keep this terminal open"
echo "2. Open Open WebUI in your browser" 
echo "3. Go to Settings > Connections"
echo "4. Change OpenAI API Base URL to: http://localhost:8888"
echo "5. Make a request using the Kroger MCP tool"
echo "6. Watch this terminal for transformation detection"
echo ""
echo "⚠️  Note: This will proxy between Open WebUI and your MCP server"
echo "   MCP Server: http://localhost:9004"
echo "   Debug Proxy: http://localhost:8888"
echo ""
echo "🚀 Starting proxy..."
echo ""

cd "/Users/cosburn/MCP Servers"
python3 openwebui_debug.py