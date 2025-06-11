#!/usr/bin/env python3
"""
Enhanced dashboard with Solomon chat interface
"""
import asyncio
import json
import logging
import os
import sys
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("chat_dashboard")


class ChatDashboardHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the chat dashboard"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/" or self.path == "/index.html":
            self.send_chat_dashboard()
        elif self.path == "/api/status":
            self.send_status_api()
        else:
            super().do_GET()

    def send_chat_dashboard(self):
        """Send the main chat dashboard HTML"""
        html_content = self.generate_dashboard_html()
        html_bytes = html_content.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(html_bytes)

    def send_status_api(self):
        """Send JSON status response"""
        try:
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "solomon_chat": {
                    "websocket_url": "ws://localhost:8889",
                    "status": "available",
                },
                "services": {
                    "dashboard": {"status": "online", "port": 8888},
                    "chat_server": {"status": "online", "port": 8889},
                },
            }

            response = json.dumps(status_data, indent=2)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", len(response))
            self.end_headers()
            self.wfile.write(response.encode())

        except Exception as e:
            error_response = json.dumps({"error": str(e)})
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", len(error_response))
            self.end_headers()
            self.wfile.write(error_response.encode())

    def generate_dashboard_html(self):
        """Generate the complete dashboard HTML"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoarderframeOS - Solomon Chat Interface</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
            height: calc(100vh - 40px);
        }}
        .main-panel {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }}
        .chat-panel {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #ffd700, #ffff00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .solomon-avatar {{
            font-size: 4em;
            margin-bottom: 10px;
        }}
        .connection-status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 10px 0;
            font-weight: bold;
        }}
        .status-connected {{
            background: #10b981;
            color: white;
        }}
        .status-disconnected {{
            background: #ef4444;
            color: white;
        }}
        .status-connecting {{
            background: #f59e0b;
            color: white;
        }}
        .chat-messages {{
            flex: 1;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            overflow-y: auto;
            min-height: 400px;
            max-height: 500px;
        }}
        .message {{
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 10px;
            max-width: 80%;
        }}
        .message.user {{
            background: #3b82f6;
            margin-left: auto;
            text-align: right;
        }}
        .message.solomon {{
            background: #10b981;
            margin-right: auto;
        }}
        .message.system {{
            background: #6b7280;
            margin: 0 auto;
            text-align: center;
            max-width: 60%;
            font-style: italic;
        }}
        .message-header {{
            font-size: 0.8em;
            opacity: 0.8;
            margin-bottom: 5px;
        }}
        .message-content {{
            line-height: 1.4;
        }}
        .chat-input-container {{
            display: flex;
            gap: 10px;
        }}
        .chat-input {{
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            font-size: 1em;
        }}
        .chat-input::placeholder {{
            color: rgba(255, 255, 255, 0.7);
        }}
        .send-button {{
            padding: 12px 20px;
            background: #10b981;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }}
        .send-button:hover:not(:disabled) {{
            background: #059669;
        }}
        .send-button:disabled {{
            background: #6b7280;
            cursor: not-allowed;
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .status-card {{
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .status-indicator {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }}
        .indicator-online {{ background: #10b981; }}
        .indicator-offline {{ background: #ef4444; }}
        .indicator-warning {{ background: #f59e0b; }}
        .logs-container {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
            flex: 1;
            overflow-y: auto;
        }}
        .log-entry {{
            font-family: monospace;
            font-size: 0.9em;
            margin-bottom: 5px;
            opacity: 0.8;
        }}
        @media (max-width: 768px) {{
            .container {{
                grid-template-columns: 1fr;
                grid-template-rows: auto 1fr;
            }}
            .chat-panel {{
                order: -1;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="main-panel">
            <div class="header">
                <h1>BoarderframeOS</h1>
                <p>AI-Native Operating System</p>
            </div>

            <div class="status-grid">
                <div class="status-card">
                    <h3>🏛️ MCP Registry</h3>
                    <span class="status-indicator indicator-online"></span>
                    <span>Online (8000)</span>
                </div>
                <div class="status-card">
                    <h3>📁 Filesystem</h3>
                    <span class="status-indicator indicator-online"></span>
                    <span>Online (8001)</span>
                </div>
                <div class="status-card">
                    <h3>💾 Database</h3>
                    <span class="status-indicator indicator-online"></span>
                    <span>Online (8004)</span>
                </div>
                <div class="status-card">
                    <h3>🧠 LLM Server</h3>
                    <span class="status-indicator indicator-online"></span>
                    <span>Online (8005)</span>
                </div>
            </div>

            <div class="logs-container">
                <h3>System Logs</h3>
                <div id="system-logs">
                    <div class="log-entry">[INFO] All MCP services online</div>
                    <div class="log-entry">[INFO] Solomon agent active and monitoring</div>
                    <div class="log-entry">[INFO] WebSocket chat server ready</div>
                    <div class="log-entry">[INFO] Dashboard operational</div>
                </div>
            </div>
        </div>

        <div class="chat-panel">
            <div class="header">
                <div class="solomon-avatar">🤖</div>
                <h2>Solomon</h2>
                <p>Chief of Staff</p>
                <div id="connection-status" class="connection-status status-disconnected">
                    Connecting...
                </div>
                <button id="manual-connect" style="display:none; margin-top:10px; padding:8px 16px; background:#3b82f6; color:white; border:none; border-radius:5px; cursor:pointer;">
                    Manual Connect
                </button>
            </div>

            <div class="chat-messages" id="chat-messages">
                <div class="message system">
                    <div class="message-content">
                        Welcome to BoarderframeOS. Connecting to Solomon...
                    </div>
                </div>
            </div>

            <div class="chat-input-container">
                <input
                    type="text"
                    id="chat-input"
                    class="chat-input"
                    placeholder="Message Solomon..."
                    disabled
                >
                <button id="send-button" class="send-button" disabled>Send</button>
            </div>
        </div>
    </div>

    <script>
        class SolomonChat {{
            constructor() {{
                this.ws = null;
                this.connected = false;
                this.reconnectAttempts = 0;
                this.maxReconnectAttempts = 5;

                this.messagesContainer = document.getElementById('chat-messages');
                this.chatInput = document.getElementById('chat-input');
                this.sendButton = document.getElementById('send-button');
                this.connectionStatus = document.getElementById('connection-status');
                this.manualConnectBtn = document.getElementById('manual-connect');

                this.initEventListeners();

                // Try to connect after a short delay
                setTimeout(() => {{
                    console.log('Starting connection attempt...');
                    this.connect();
                }}, 1000);
            }}

            initEventListeners() {{
                this.sendButton.addEventListener('click', () => this.sendMessage());
                this.chatInput.addEventListener('keypress', (e) => {{
                    if (e.key === 'Enter' && !e.shiftKey) {{
                        e.preventDefault();
                        this.sendMessage();
                    }}
                }});

                // Manual connect button
                this.manualConnectBtn.addEventListener('click', () => {{
                    console.log('Manual connect button clicked');
                    this.manualConnectBtn.style.display = 'none';
                    this.connect();
                }});
            }}

            connect() {{
                this.updateConnectionStatus('connecting', 'Connecting...');
                console.log('Attempting to connect to WebSocket at ws://localhost:8889');

                try {{
                    this.ws = new WebSocket('ws://localhost:8889');
                    console.log('WebSocket object created');

                    this.ws.onopen = () => {{
                        console.log('WebSocket connection opened');
                        this.connected = true;
                        this.reconnectAttempts = 0;
                        this.updateConnectionStatus('connected', 'Connected');
                        this.enableInput();
                    }};

                    this.ws.onmessage = (event) => {{
                        try {{
                            const data = JSON.parse(event.data);
                            this.handleMessage(data);
                        }} catch (e) {{
                            console.error('Error parsing message:', e);
                        }}
                    }};

                    this.ws.onclose = () => {{
                        this.connected = false;
                        this.updateConnectionStatus('disconnected', 'Disconnected');
                        this.disableInput();
                        this.addSystemMessage('Connection lost. Attempting to reconnect...');
                        this.attemptReconnect();
                    }};

                    this.ws.onerror = (error) => {{
                        console.error('WebSocket error:', error);
                        console.log('WebSocket error details:', error);
                        this.addSystemMessage('Connection error occurred');
                    }};

                }} catch (error) {{
                    console.error('Failed to connect:', error);
                    this.updateConnectionStatus('disconnected', 'Connection failed');
                    this.attemptReconnect();
                }}
            }}

            attemptReconnect() {{
                if (this.reconnectAttempts < this.maxReconnectAttempts) {{
                    this.reconnectAttempts++;
                    setTimeout(() => {{
                        console.log(`Reconnect attempt ${{this.reconnectAttempts}}`);
                        this.connect();
                    }}, 2000 * this.reconnectAttempts);
                }} else {{
                    this.addSystemMessage('Failed to reconnect automatically.');
                    this.manualConnectBtn.style.display = 'inline-block';
                }}
            }}

            updateConnectionStatus(status, text) {{
                this.connectionStatus.textContent = text;
                this.connectionStatus.className = `connection-status status-${{status}}`;
            }}

            enableInput() {{
                this.chatInput.disabled = false;
                this.sendButton.disabled = false;
                this.chatInput.placeholder = 'Message Solomon...';
            }}

            disableInput() {{
                this.chatInput.disabled = true;
                this.sendButton.disabled = true;
                this.chatInput.placeholder = 'Disconnected...';
            }}

            sendMessage() {{
                const message = this.chatInput.value.trim();
                if (!message || !this.connected) return;

                this.ws.send(JSON.stringify({{
                    type: 'user_message',
                    message: message
                }}));

                this.chatInput.value = '';
            }}

            handleMessage(data) {{
                switch (data.type) {{
                    case 'user_message':
                        this.addMessage('user', data.message, data.timestamp);
                        break;
                    case 'solomon_response':
                        this.addMessage('solomon', data.content, data.timestamp);
                        break;
                    case 'system_message':
                        this.addSystemMessage(data.message);
                        break;
                    case 'error':
                        this.addSystemMessage(`Error: ${{data.message}}`);
                        break;
                }}
            }}

            addMessage(sender, content, timestamp) {{
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${{sender}}`;

                const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
                const senderName = sender === 'user' ? 'You' : 'Solomon';

                messageDiv.innerHTML = `
                    <div class="message-header">${{senderName}} • ${{time}}</div>
                    <div class="message-content">${{content}}</div>
                `;

                this.messagesContainer.appendChild(messageDiv);
                this.scrollToBottom();
            }}

            addSystemMessage(content) {{
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message system';
                messageDiv.innerHTML = `
                    <div class="message-content">${{content}}</div>
                `;

                this.messagesContainer.appendChild(messageDiv);
                this.scrollToBottom();
            }}

            scrollToBottom() {{
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }}
        }}

        // Initialize chat when page loads
        document.addEventListener('DOMContentLoaded', () => {{
            console.log('DOM content loaded, initializing Solomon chat...');
            window.solomonChat = new SolomonChat();
        }});

        // Also try on window load as backup
        window.addEventListener('load', () => {{
            if (!window.solomonChat) {{
                console.log('Window loaded, initializing Solomon chat as backup...');
                window.solomonChat = new SolomonChat();
            }}
        }});

        // Add some demo log entries periodically
        setInterval(() => {{
            const logs = document.getElementById('system-logs');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.textContent = `[${{timestamp}}] System monitoring active`;
            logs.appendChild(logEntry);

            // Keep only last 10 log entries
            while (logs.children.length > 10) {{
                logs.removeChild(logs.firstChild);
            }}
        }}, 30000);
    </script>
</body>
</html>"""


def start_dashboard_server(port: int = 8888):
    """Start the dashboard HTTP server"""
    server = HTTPServer(("localhost", port), ChatDashboardHandler)
    logger.info(f"Starting chat dashboard on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        start_dashboard_server()
    except KeyboardInterrupt:
        logger.info("Shutting down chat dashboard")
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
