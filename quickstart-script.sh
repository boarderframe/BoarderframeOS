#!/bin/bash
# BoarderframeOS Quick Start
# Get your AI empire running in 5 minutes

set -e

echo "🚀 BoarderframeOS Quick Start"
echo "============================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create project structure
echo "📁 Creating project structure..."
mkdir -p boarderframeos/{core,agents,zones,mcp-servers,ui,data,logs}
cd boarderframeos

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
cat > requirements.txt << EOF
fastapi==0.109.0
uvicorn==0.25.0
typer==0.9.0
rich==13.7.0
pydantic==2.5.3
httpx==0.26.0
pyyaml==6.0.1
websockets==12.0
asyncio==3.4.3
pytest==7.4.4
pytest-asyncio==0.23.3
EOF

pip install -r requirements.txt

# Copy the boarderctl script
echo "🔧 Installing boarderctl..."
cat > boarderctl << 'EOF'
#!/usr/bin/env python3
# Copy the full boarderctl code here
# [The artifact content from boarderctl-implementation would go here]
EOF

chmod +x boarderctl

# Copy the base agent framework
echo "🤖 Installing agent framework..."
mkdir -p core
# Copy the base_agent.py content here
# [The artifact content from base-agent-framework would go here]

# Create a simple MCP filesystem server
echo "🔌 Creating MCP filesystem server..."
cat > mcp-servers/filesystem_server.py << 'EOF'
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json

app = FastAPI()

class FileOperation(BaseModel):
    method: str
    params: dict

@app.post("/rpc")
async def handle_rpc(operation: FileOperation):
    if operation.method == "filesystem.read_file":
        path = Path(operation.params['path'])
        if path.exists() and path.is_file():
            return {"result": path.read_text()}
        return {"error": "File not found"}
    
    elif operation.method == "filesystem.write_file":
        path = Path(operation.params['path'])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(operation.params['content'])
        return {"result": "success"}
    
    elif operation.method == "filesystem.list_directory":
        path = Path(operation.params['path'])
        if path.exists() and path.is_dir():
            files = [str(f) for f in path.iterdir()]
            return {"result": {"files": files}}
        return {"error": "Directory not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
EOF

# Create first agent template
echo "👤 Creating your first agent (Jarvis)..."
cat > agents/jarvis_template.py << 'EOF'
from core.base_agent import BaseAgent, AgentConfig
import asyncio

class Jarvis(BaseAgent):
    """Your AI Chief of Staff"""
    
    async def think(self, context):
        # Simulate thinking
        thought = f"Analyzing {len(context.get('recent_memories', []))} recent memories..."
        return thought
    
    async def act(self, thought, context):
        # Simulate action
        result = {"status": "success", "action": "analyzed", "thought": thought}
        return result

if __name__ == "__main__":
    config = AgentConfig(
        name="jarvis",
        role="chief-of-staff",
        goals=["Manage other agents", "Optimize system performance"],
        tools=["filesystem", "git"],
        zone="executive"
    )
    
    agent = Jarvis(config)
    asyncio.run(agent.run())
EOF

# Create startup script
echo "🚀 Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash
# Start BoarderframeOS

echo "Starting BoarderframeOS..."

# Activate virtual environment
source venv/bin/activate

# Start MCP servers in background
echo "Starting MCP servers..."
python mcp-servers/filesystem_server.py &
MCP_PID=$!

# Wait for servers to start
sleep 2

# Initialize system if needed
if [ ! -f "boarderframe.yaml" ]; then
    echo "Initializing BoarderframeOS..."
    ./boarderctl init
fi

# Show status
./boarderctl status

echo ""
echo "BoarderframeOS is ready!"
echo "Try these commands:"
echo "  ./boarderctl zone create executive"
echo "  ./boarderctl agent create jarvis"
echo "  ./boarderctl agent start jarvis"
echo ""
echo "Press Ctrl+C to stop"

# Keep running
wait $MCP_PID
EOF

chmod +x start.sh

# Create initial config
echo "⚙️ Initializing BoarderframeOS..."
./boarderctl init

# Final instructions
echo ""
echo "✅ BoarderframeOS Quick Start Complete!"
echo ""
echo "📚 Next Steps:"
echo "1. Start the system:    ./start.sh"
echo "2. Create a zone:       ./boarderctl zone create executive"
echo "3. Create Jarvis:       ./boarderctl agent create jarvis"
echo "4. Start Jarvis:        ./boarderctl agent start jarvis"
echo ""
echo "📖 Documentation:       https://boarderframeos.ai/docs"
echo "💬 Discord:            https://discord.gg/boarderframe"
echo ""
echo "🚀 Ready to build your billion-dollar AI company!"
