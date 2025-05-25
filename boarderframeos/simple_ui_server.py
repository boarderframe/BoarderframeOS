#!/usr/bin/env python3
"""
Simplified UI server that works without complex imports
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="BoarderframeOS Simple UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple HTML template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <nav class="bg-gray-800 p-4">
        <h1 class="text-2xl font-bold text-blue-400">BoarderframeOS Dashboard</h1>
    </nav>
    
    <div class="container mx-auto p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-gray-800 p-6 rounded-lg">
                <h3 class="text-lg font-semibold mb-2">System Status</h3>
                <div class="text-green-400">✓ UI Server Online</div>
                <div class="text-yellow-400">⚠ Backend Pending</div>
            </div>
            <div class="bg-gray-800 p-6 rounded-lg">
                <h3 class="text-lg font-semibold mb-2">Core Agents</h3>
                <div class="space-y-1">
                    <div>Solomon: <span class="text-red-400">Offline</span></div>
                    <div>David: <span class="text-red-400">Offline</span></div>
                    <div>Adam: <span class="text-red-400">Offline</span></div>
                </div>
            </div>
            <div class="bg-gray-800 p-6 rounded-lg">
                <h3 class="text-lg font-semibold mb-2">Quick Actions</h3>
                <button onclick="startSystem()" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded mr-2">Start System</button>
                <button onclick="runSetup()" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">Run Setup</button>
            </div>
        </div>
        
        <div class="bg-gray-800 p-6 rounded-lg">
            <h3 class="text-lg font-semibold mb-4">Solomon Chat Interface</h3>
            <div id="chat-container" class="bg-gray-900 p-4 rounded mb-4 h-64 overflow-y-auto">
                <div class="text-gray-400">Solomon is offline. Start the system to begin chatting.</div>
            </div>
            <div class="flex space-x-2">
                <input id="message-input" type="text" placeholder="Message Solomon..." 
                       class="flex-1 bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white">
                <button onclick="sendMessage()" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">Send</button>
            </div>
        </div>
        
        <div class="mt-6 bg-gray-800 p-6 rounded-lg">
            <h3 class="text-lg font-semibold mb-4">System Setup Instructions</h3>
            <div class="space-y-2 text-sm">
                <div>1. Run the setup script: <code class="bg-gray-700 px-2 py-1 rounded">python setup_boarderframeos.py</code></div>
                <div>2. Start MCP servers: <code class="bg-gray-700 px-2 py-1 rounded">python mcp/server_launcher.py</code></div>
                <div>3. Initialize agents: <code class="bg-gray-700 px-2 py-1 rounded">python startup.py</code></div>
            </div>
        </div>
    </div>
    
    <script>
        function startSystem() {
            alert('System startup will be implemented once backend is running');
        }
        
        function runSetup() {
            alert('Run: python setup_boarderframeos.py');
        }
        
        function sendMessage() {
            const input = document.getElementById('message-input');
            const chat = document.getElementById('chat-container');
            
            if (input.value.trim()) {
                chat.innerHTML += '<div class="mb-2"><span class="text-blue-400">You:</span> ' + input.value + '</div>';
                chat.innerHTML += '<div class="mb-2"><span class="text-purple-400">Solomon:</span> I am not yet online. Please start the system first.</div>';
                input.value = '';
                chat.scrollTop = chat.scrollHeight;
            }
        }
        
        // Allow Enter key to send message
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/status")
async def get_status():
    return {
        "ui_server": "online",
        "backend_status": "not_connected",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Simple BoarderframeOS UI...")
    print("📍 Dashboard: http://localhost:8080")
    print("🔧 This is a basic UI. Run the full setup to enable all features.")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8080)