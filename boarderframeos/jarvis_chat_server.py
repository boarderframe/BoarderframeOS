#!/usr/bin/env python3
"""
Jarvis Chat Server - Modern Web UI for Jarvis Claude Agent
FastAPI server with WebSocket support for real-time chat
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.jarvis_claude import JarvisClaude
from core.base_agent import AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis_chat")

class JarvisChatServer:
    """Chat server for Jarvis with WebSocket support"""
    
    def __init__(self):
        self.app = FastAPI(title="Jarvis Chat Interface", version="1.0.0")
        self.active_connections: List[WebSocket] = []
        self.jarvis_agent: Optional[JarvisClaude] = None
        self.chat_history: List[Dict] = []
        
        # Setup routes
        self.setup_routes()
        
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_chat_interface():
            """Serve the main chat interface"""
            return self.get_chat_html()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "jarvis_active": self.jarvis_agent is not None,
                "active_connections": len(self.active_connections),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time chat"""
            await self.connect(websocket)
            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Process the message
                    await self.handle_message(websocket, message_data)
                    
            except WebSocketDisconnect:
                await self.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await self.disconnect(websocket)
    
    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Initialize Jarvis if not already running
        if not self.jarvis_agent:
            await self.initialize_jarvis()
        
        # Send welcome message and chat history
        await self.send_to_connection(websocket, {
            "type": "system",
            "message": "Connected to Jarvis! Claude 4 Opus is ready to assist you.",
            "timestamp": datetime.now().isoformat(),
            "history": self.chat_history[-10:]  # Last 10 messages
        })
        
        logger.info(f"New connection established. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Connection closed. Remaining: {len(self.active_connections)}")
    
    async def initialize_jarvis(self):
        """Initialize Jarvis Claude agent"""
        try:
            # Check for API key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.error("ANTHROPIC_API_KEY not set")
                return False
            
            # Create Jarvis config for chat mode
            config = AgentConfig(
                name="jarvis-chat",
                role="ai-assistant-chat", 
                goals=[
                    "Provide helpful assistance through chat interface",
                    "Answer questions with Claude 4's enhanced reasoning",
                    "Help with analysis, planning, and problem-solving",
                    "Maintain context across chat conversations",
                    "Be conversational and engaging while remaining professional"
                ],
                tools=["filesystem"],
                zone="executive",
                model="claude-opus-4-20250514",
                temperature=0.4  # Balanced for conversation
            )
            
            self.jarvis_agent = JarvisClaude(config)
            logger.info("Jarvis Claude agent initialized for chat")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Jarvis: {e}")
            return False
    
    async def handle_message(self, websocket: WebSocket, message_data: Dict):
        """Process incoming chat messages"""
        try:
            user_message = message_data.get("message", "").strip()
            if not user_message:
                return
            
            # Add user message to history
            user_msg = {
                "type": "user",
                "message": user_message,
                "timestamp": datetime.now().isoformat()
            }
            self.chat_history.append(user_msg)
            
            # Broadcast user message to all connections
            await self.broadcast_message(user_msg)
            
            # Send typing indicator
            await self.broadcast_message({
                "type": "typing",
                "message": "Jarvis is thinking...",
                "timestamp": datetime.now().isoformat()
            })
            
            # Get response from Jarvis
            if self.jarvis_agent:
                # Create context for Jarvis
                context = {
                    "current_time": datetime.now().isoformat(),
                    "chat_mode": True,
                    "user_message": user_message,
                    "recent_messages": self.chat_history[-5:],  # Last 5 for context
                    "available_tools": ["filesystem"],
                    "active_tasks": 0,
                    "message_queue_size": 0
                }
                
                # Generate response using Jarvis
                jarvis_thought = await self.jarvis_agent.think(context)
                
                # Create response message
                jarvis_msg = {
                    "type": "jarvis",
                    "message": jarvis_thought,
                    "timestamp": datetime.now().isoformat()
                }
                self.chat_history.append(jarvis_msg)
                
                # Broadcast Jarvis response
                await self.broadcast_message(jarvis_msg)
                
            else:
                # Fallback if Jarvis not available
                error_msg = {
                    "type": "error",
                    "message": "Jarvis is not available. Please check API key configuration.",
                    "timestamp": datetime.now().isoformat()
                }
                await self.broadcast_message(error_msg)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            error_msg = {
                "type": "error",
                "message": f"Error processing message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            await self.send_to_connection(websocket, error_msg)
    
    async def send_to_connection(self, websocket: WebSocket, message: Dict):
        """Send message to specific connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending to connection: {e}")
    
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        # Remove failed connections
        failed_connections = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                failed_connections.append(websocket)
        
        # Clean up failed connections
        for websocket in failed_connections:
            await self.disconnect(websocket)
    
    def get_chat_html(self) -> str:
        """Generate the chat interface HTML"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis Chat - BoarderframeOS</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            width: 95%;
            max-width: 800px;
            height: 90vh;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        
        .chat-header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .chat-header .subtitle {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .connection-status {
            position: absolute;
            top: 15px;
            right: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #27ae60;
            box-shadow: 0 0 10px rgba(39, 174, 96, 0.5);
        }
        
        .connection-status.disconnected {
            background: #e74c3c;
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            scroll-behavior: smooth;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message.jarvis {
            justify-content: flex-start;
        }
        
        .message.system {
            justify-content: center;
        }
        
        .message.typing {
            justify-content: flex-start;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.4;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.jarvis .message-content {
            background: #f8f9fa;
            color: #2c3e50;
            border: 1px solid #e9ecef;
            border-bottom-left-radius: 4px;
        }
        
        .message.system .message-content {
            background: rgba(52, 152, 219, 0.1);
            color: #3498db;
            font-style: italic;
            border-radius: 10px;
            font-size: 14px;
        }
        
        .message.typing .message-content {
            background: #e9ecef;
            color: #6c757d;
            font-style: italic;
        }
        
        .message.error .message-content {
            background: rgba(231, 76, 60, 0.1);
            color: #e74c3c;
            border: 1px solid rgba(231, 76, 60, 0.3);
        }
        
        .avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            margin: 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
        }
        
        .message.user .avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            order: 2;
        }
        
        .message.jarvis .avatar {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
        }
        
        .timestamp {
            font-size: 11px;
            color: #999;
            margin-top: 4px;
            text-align: right;
        }
        
        .message.jarvis .timestamp {
            text-align: left;
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e9ecef;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        
        .message-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 16px;
            resize: none;
            max-height: 100px;
            min-height: 44px;
            outline: none;
            transition: border-color 0.3s ease;
        }
        
        .message-input:focus {
            border-color: #3498db;
        }
        
        .send-button {
            width: 44px;
            height: 44px;
            border: none;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s ease;
        }
        
        .send-button:hover {
            transform: scale(1.05);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: scale(1);
        }
        
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6c757d;
            animation: typingPulse 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        .typing-dot:nth-child(3) { animation-delay: 0s; }
        
        @keyframes typingPulse {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        @media (max-width: 600px) {
            .chat-container {
                width: 100%;
                height: 100vh;
                border-radius: 0;
            }
            
            .message-content {
                max-width: 85%;
            }
            
            .chat-header h1 {
                font-size: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="connection-status" id="connectionStatus"></div>
            <h1>🤖 Jarvis Chat</h1>
            <div class="subtitle">Powered by Claude 4 Opus • BoarderframeOS</div>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message system">
                <div class="message-content">
                    Connecting to Jarvis...
                </div>
            </div>
        </div>
        
        <div class="chat-input">
            <div class="input-container">
                <textarea 
                    id="messageInput" 
                    class="message-input" 
                    placeholder="Ask Jarvis anything..."
                    rows="1"
                ></textarea>
                <button id="sendButton" class="send-button" disabled>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z" />
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <script>
        class JarvisChat {
            constructor() {
                this.ws = null;
                this.messageInput = document.getElementById('messageInput');
                this.sendButton = document.getElementById('sendButton');
                this.chatMessages = document.getElementById('chatMessages');
                this.connectionStatus = document.getElementById('connectionStatus');
                
                this.setupEventListeners();
                this.connect();
            }
            
            setupEventListeners() {
                this.sendButton.addEventListener('click', () => this.sendMessage());
                
                this.messageInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });
                
                this.messageInput.addEventListener('input', () => {
                    this.autoResize();
                    this.updateSendButton();
                });
            }
            
            connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                try {
                    this.ws = new WebSocket(wsUrl);
                    
                    this.ws.onopen = () => {
                        console.log('Connected to Jarvis');
                        this.connectionStatus.classList.remove('disconnected');
                        this.updateSendButton();
                    };
                    
                    this.ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                    };
                    
                    this.ws.onclose = () => {
                        console.log('Disconnected from Jarvis');
                        this.connectionStatus.classList.add('disconnected');
                        this.updateSendButton();
                        
                        // Attempt to reconnect after 3 seconds
                        setTimeout(() => this.connect(), 3000);
                    };
                    
                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        this.connectionStatus.classList.add('disconnected');
                    };
                    
                } catch (error) {
                    console.error('Failed to connect:', error);
                    this.connectionStatus.classList.add('disconnected');
                }
            }
            
            handleMessage(data) {
                if (data.type === 'system') {
                    this.clearMessages();
                    this.addMessage('system', data.message, data.timestamp);
                    
                    // Load chat history if provided
                    if (data.history && data.history.length > 0) {
                        data.history.forEach(msg => {
                            this.addMessage(msg.type, msg.message, msg.timestamp);
                        });
                    }
                } else if (data.type === 'typing') {
                    this.removeTypingIndicator();
                    this.addTypingIndicator();
                } else {
                    this.removeTypingIndicator();
                    this.addMessage(data.type, data.message, data.timestamp);
                }
                
                this.scrollToBottom();
            }
            
            addMessage(type, message, timestamp) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                
                let avatar = '';
                if (type === 'user') {
                    avatar = '<div class="avatar">You</div>';
                } else if (type === 'jarvis') {
                    avatar = '<div class="avatar">J</div>';
                }
                
                const time = new Date(timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                messageDiv.innerHTML = `
                    ${avatar}
                    <div style="flex: 1;">
                        <div class="message-content">${this.escapeHtml(message)}</div>
                        <div class="timestamp">${time}</div>
                    </div>
                `;
                
                this.chatMessages.appendChild(messageDiv);
            }
            
            addTypingIndicator() {
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message typing typing-indicator-msg';
                typingDiv.innerHTML = `
                    <div class="avatar">J</div>
                    <div class="message-content">
                        <div class="typing-indicator">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                `;
                
                this.chatMessages.appendChild(typingDiv);
            }
            
            removeTypingIndicator() {
                const typing = this.chatMessages.querySelector('.typing-indicator-msg');
                if (typing) {
                    typing.remove();
                }
            }
            
            sendMessage() {
                const message = this.messageInput.value.trim();
                if (!message || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    return;
                }
                
                // Send message to server
                this.ws.send(JSON.stringify({
                    type: 'user_message',
                    message: message
                }));
                
                // Clear input
                this.messageInput.value = '';
                this.autoResize();
                this.updateSendButton();
                this.messageInput.focus();
            }
            
            clearMessages() {
                this.chatMessages.innerHTML = '';
            }
            
            scrollToBottom() {
                this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
            }
            
            autoResize() {
                this.messageInput.style.height = 'auto';
                this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 100) + 'px';
            }
            
            updateSendButton() {
                const hasText = this.messageInput.value.trim().length > 0;
                const isConnected = this.ws && this.ws.readyState === WebSocket.OPEN;
                this.sendButton.disabled = !hasText || !isConnected;
            }
            
            escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML.replace(/\\n/g, '<br>');
            }
        }
        
        // Initialize chat when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new JarvisChat();
        });
    </script>
</body>
</html>
        '''

# Create and run the server
def create_app():
    """Create FastAPI app instance"""
    return JarvisChatServer().app

def run_server():
    """Run the Jarvis chat server"""
    print("🚀 Starting Jarvis Chat Server")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return
    
    print(f"✅ API key configured: ...{api_key[-8:]}")
    print("🤖 Initializing Jarvis Claude agent...")
    print("🌐 Starting web server...")
    
    # Create server instance
    server = JarvisChatServer()
    
    # Run with uvicorn
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=8888,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    run_server()