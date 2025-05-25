#!/usr/bin/env python3
"""
Simple HTTP-based chat dashboard (no WebSockets)
"""
import json
import logging
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.message_bus import message_bus, AgentMessage, MessageType, MessagePriority

logger = logging.getLogger("simple_chat_dashboard")

# Store messages in memory for this session
chat_messages = []
message_id_counter = 0

class SimpleChatHandler(SimpleHTTPRequestHandler):
    """HTTP handler for simple chat dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/" or self.path == "/index.html":
            self.send_chat_dashboard()
        elif self.path == "/api/messages":
            self.send_messages()
        elif self.path == "/api/status":
            self.send_status()
        else:
            super().do_GET()
            
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/api/send":
            self.handle_send_message()
        else:
            self.send_response(404)
            self.end_headers()
            
    def send_chat_dashboard(self):
        """Send the chat dashboard HTML"""
        html_content = self.generate_dashboard_html()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-length', len(html_content))
        self.end_headers()
        self.wfile.write(html_content.encode())
        
    def send_messages(self):
        """Send current messages as JSON"""
        response = json.dumps(chat_messages)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(response))
        self.end_headers()
        self.wfile.write(response.encode())
        
    def send_status(self):
        """Send status information"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "solomon_status": "active",
            "message_count": len(chat_messages)
        }
        response = json.dumps(status)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', len(response))
        self.end_headers()
        self.wfile.write(response.encode())
        
    def handle_send_message(self):
        """Handle sending a message"""
        global message_id_counter
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_message = data.get('message', '')
            if user_message:
                # Add user message
                message_id_counter += 1
                user_msg = {
                    "id": message_id_counter,
                    "type": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                }
                chat_messages.append(user_msg)
                
                # Generate Solomon's response
                message_id_counter += 1
                solomon_response = self.get_solomon_response(user_message)
                solomon_msg = {
                    "id": message_id_counter,
                    "type": "solomon",
                    "content": solomon_response,
                    "timestamp": datetime.now().isoformat()
                }
                chat_messages.append(solomon_msg)
                
                # Keep only last 50 messages
                if len(chat_messages) > 50:
                    chat_messages[:] = chat_messages[-50:]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            
    def get_solomon_response(self, user_message):
        """Generate a response from Solomon"""
        # For now, return a simulated response
        # In the full system, this would route through the message bus
        responses = [
            f"Thank you for your message: '{user_message}'. I am Solomon, your Chief of Staff.",
            "I understand your request. How may I assist you further?",
            "I'm here to help coordinate BoarderframeOS operations for you.",
            "Your message has been received. I'm processing your request.",
            "As your Chief of Staff, I'm ready to help with whatever you need."
        ]
        
        # Simple response selection based on message content
        if "hello" in user_message.lower():
            return "Hello! I'm Solomon, your Chief of Staff. Welcome to BoarderframeOS!"
        elif "help" in user_message.lower():
            return "I'm here to help! I can coordinate system operations, manage other agents, and assist with your business goals."
        elif "status" in user_message.lower():
            return "System status: All core services are online. Solomon agent active and monitoring."
        else:
            return f"I understand you said: '{user_message}'. I'm processing this and coordinating the appropriate response."
            
    def generate_dashboard_html(self):
        """Generate the complete dashboard HTML"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoarderframeOS - Solomon Chat</title>
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
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            height: calc(100vh - 40px);
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
        }}
        .solomon-avatar {{
            font-size: 3em;
            margin-bottom: 10px;
        }}
        .status {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            margin: 10px 0;
            font-weight: bold;
            background: #10b981;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>BoarderframeOS</h1>
            <div class="solomon-avatar">🤖</div>
            <h2>Solomon - Chief of Staff</h2>
            <div class="status">Connected & Ready</div>
        </div>
        
        <div class="chat-messages" id="chat-messages">
            <div class="message solomon">
                <div class="message-header">Solomon • Welcome</div>
                <div class="message-content">
                    Welcome to BoarderframeOS! I'm Solomon, your Chief of Staff. 
                    I'm here to help coordinate system operations and assist with your goals.
                    How may I help you today?
                </div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <input 
                type="text" 
                id="chat-input" 
                class="chat-input" 
                placeholder="Message Solomon..."
            >
            <button id="send-button" class="send-button">Send</button>
        </div>
    </div>

    <script>
        class SimpleChat {{
            constructor() {{
                this.messagesContainer = document.getElementById('chat-messages');
                this.chatInput = document.getElementById('chat-input');
                this.sendButton = document.getElementById('send-button');
                this.lastMessageId = 0;
                
                this.initEventListeners();
                this.startPolling();
            }}
            
            initEventListeners() {{
                this.sendButton.addEventListener('click', () => this.sendMessage());
                this.chatInput.addEventListener('keypress', (e) => {{
                    if (e.key === 'Enter') {{
                        e.preventDefault();
                        this.sendMessage();
                    }}
                }});
            }}
            
            async sendMessage() {{
                const message = this.chatInput.value.trim();
                if (!message) return;
                
                this.sendButton.disabled = true;
                this.chatInput.disabled = true;
                
                try {{
                    const response = await fetch('/api/send', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ message: message }})
                    }});
                    
                    if (response.ok) {{
                        this.chatInput.value = '';
                        await this.loadMessages();
                    }}
                }} catch (error) {{
                    console.error('Error sending message:', error);
                }} finally {{
                    this.sendButton.disabled = false;
                    this.chatInput.disabled = false;
                    this.chatInput.focus();
                }}
            }}
            
            async loadMessages() {{
                try {{
                    const response = await fetch('/api/messages');
                    const messages = await response.json();
                    
                    // Only add new messages
                    const newMessages = messages.filter(msg => msg.id > this.lastMessageId);
                    newMessages.forEach(msg => {{
                        this.addMessage(msg.type, msg.content, msg.timestamp);
                        this.lastMessageId = msg.id;
                    }});
                    
                }} catch (error) {{
                    console.error('Error loading messages:', error);
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
            
            scrollToBottom() {{
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            }}
            
            startPolling() {{
                // Poll for new messages every 2 seconds
                setInterval(() => {{
                    this.loadMessages();
                }}, 2000);
            }}
        }}
        
        // Initialize chat when page loads
        document.addEventListener('DOMContentLoaded', () => {{
            window.simpleChat = new SimpleChat();
            
            // Focus input
            document.getElementById('chat-input').focus();
        }});
    </script>
</body>
</html>"""

def start_simple_dashboard(port: int = 8890):
    """Start the simple chat dashboard"""
    server = HTTPServer(('localhost', port), SimpleChatHandler)
    logger.info(f"Starting simple chat dashboard on http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        start_simple_dashboard()
    except KeyboardInterrupt:
        logger.info("Shutting down simple chat dashboard")