#!/usr/bin/env python3
"""
Simple Jarvis Chat Server - Working version
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_client import LLMClient, CLAUDE_OPUS_CONFIG

app = FastAPI()
connections: List[WebSocket] = []
chat_history = []

# Initialize Claude client
claude_client = None

@app.on_event("startup")
async def startup():
    global claude_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        claude_client = LLMClient(CLAUDE_OPUS_CONFIG)
        print("✅ Claude client initialized")
    else:
        print("❌ No API key found")

@app.get("/", response_class=HTMLResponse)
async def get_chat():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Jarvis Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
        .messages { height: 400px; overflow-y: auto; padding: 20px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
        .user { background: #3498db; color: white; margin-left: 20%; }
        .jarvis { background: #ecf0f1; color: #2c3e50; margin-right: 20%; }
        .system { background: #e8f5e8; color: #27ae60; text-align: center; font-style: italic; }
        .input-area { padding: 20px; border-top: 1px solid #bdc3c7; }
        .input-group { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 10px; border: 1px solid #bdc3c7; border-radius: 5px; }
        button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #2980b9; }
        .status { position: absolute; top: 20px; right: 20px; width: 10px; height: 10px; border-radius: 50%; }
        .connected { background: #27ae60; }
        .disconnected { background: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="status" id="status"></div>
            <h1>🤖 Jarvis Chat</h1>
            <p>Powered by Claude 4 Opus</p>
        </div>
        <div class="messages" id="messages">
            <div class="message system">Connecting to Jarvis...</div>
        </div>
        <div class="input-area">
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Ask Jarvis anything..." disabled>
                <button onclick="sendMessage()" id="sendBtn" disabled>Send</button>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        const messages = document.getElementById('messages');
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const status = document.getElementById('status');

        function connect() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                status.className = 'status connected';
                input.disabled = false;
                sendBtn.disabled = false;
                addMessage('system', 'Connected to Jarvis!');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage(data.type, data.message);
            };
            
            ws.onclose = function() {
                status.className = 'status disconnected';
                input.disabled = true;
                sendBtn.disabled = true;
                addMessage('system', 'Disconnected. Reconnecting...');
                setTimeout(connect, 3000);
            };
        }

        function addMessage(type, message) {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.textContent = message;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        function sendMessage() {
            const message = input.value.trim();
            if (message && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({message: message}));
                addMessage('user', message);
                input.value = '';
            }
        }

        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });

        connect();
    </script>
</body>
</html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            if user_message and claude_client:
                # Create simple prompt for Jarvis
                prompt = f"""You are Jarvis, an AI assistant. Respond helpfully and conversationally to this message: {user_message}

Be friendly, concise, and helpful. You're powered by Claude 4 and part of BoarderframeOS."""
                
                try:
                    response = await claude_client.generate(prompt)
                    await websocket.send_text(json.dumps({
                        "type": "jarvis",
                        "message": response
                    }))
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "jarvis", 
                        "message": f"Sorry, I'm having trouble thinking right now: {str(e)}"
                    }))
            else:
                await websocket.send_text(json.dumps({
                    "type": "jarvis",
                    "message": "I'm not properly configured. Please check the API key."
                }))
                
    except WebSocketDisconnect:
        connections.remove(websocket)

if __name__ == "__main__":
    print("🚀 Starting Simple Jarvis Chat")
    print("=" * 40)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        exit(1)
    
    print(f"✅ API key: ...{api_key[-8:]}")
    print("🌐 Server starting on http://localhost:8889")
    
    uvicorn.run(app, host="0.0.0.0", port=8889, log_level="warning")