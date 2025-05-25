#!/usr/bin/env python3
"""
WebSocket server for real-time chat with Solomon
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
import websockets
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
    print(f"Loaded environment variables. API key present: {'ANTHROPIC_API_KEY' in os.environ}")
except ImportError:
    print("python-dotenv not installed, trying to load .env manually")
    env_file = Path(__file__).parent.parent.parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print(f"Manually loaded .env. API key present: {'ANTHROPIC_API_KEY' in os.environ}")
except Exception as e:
    print(f"Error loading environment: {e}")

from core.message_bus import message_bus, AgentMessage, MessageType, MessagePriority

logger = logging.getLogger("solomon_chat")

class SolomonChatServer:
    def __init__(self, port: int = 8889):
        self.port = port
        self.clients: Set = set()
        self.message_history: list = []
        self.registered_with_message_bus = False
        self.solomon_agent = None
        
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Don't send message history on connection to avoid triggering automatic responses
            
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def send_to_client(self, websocket, message: dict):
        """Send message to a specific client"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            self.clients.discard(websocket)
            
    async def broadcast_to_clients(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
            
        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > 100:
            self.message_history.pop(0)
            
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
                
        # Remove disconnected clients
        self.clients -= disconnected
        
    async def send_solomon_response(self, response_text: str):
        """Send a response from Solomon to all clients"""
        message = {
            "type": "solomon_response",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_clients(message)
        
    async def send_to_solomon(self, user_message: str) -> str:
        """Send message to Solomon via message bus"""
        try:
            # Register as web_ui agent if not already registered
            await self.register_with_message_bus()
            
            # Check if Solomon is registered  
            registered_agents = list(message_bus.agent_queues.keys())
            logger.info(f"Registered agents: {registered_agents}")
            if "Solomon" not in message_bus.agent_queues:
                logger.warning("Solomon not available - providing fallback response")
                # Send a mock response back to the client
                await self.send_solomon_response(f"Hello! I'm Solomon (offline mode). I received your message: '{user_message}'. I'm currently not fully operational due to missing API configuration, but the chat system is working! Once properly configured, I'll be able to provide full AI assistance.")
                return "Fallback response sent"
            
            # Create message for Solomon (case-sensitive)
            message = AgentMessage(
                from_agent="web_ui",
                to_agent="Solomon", 
                message_type=MessageType.TASK_REQUEST,
                content={"message": user_message},  # Wrap in dict to match Solomon's expectation
                priority=MessagePriority.NORMAL
            )
            
            # Send via message bus
            await message_bus.send_message(message)
            
            logger.info(f"Sent message to Solomon: {user_message}")
            return "Message sent to Solomon"
            
        except Exception as e:
            logger.error(f"Failed to send message to Solomon: {e}")
            return f"Error sending message: {str(e)}"
    
    async def register_with_message_bus(self):
        """Register this chat server with the message bus"""
        if self.registered_with_message_bus:
            return
            
        try:
            await message_bus.register_agent("web_ui")
            
            # Subscribe to responses from Solomon
            await message_bus.subscribe("web_ui", self.handle_solomon_response)
            
            self.registered_with_message_bus = True
            logger.info("Registered with message bus as 'web_ui'")
            
        except Exception as e:
            logger.error(f"Failed to register with message bus: {e}")
    
    async def handle_solomon_response(self, message: AgentMessage):
        """Handle responses from Solomon via message bus"""
        try:
            if message.from_agent == "Solomon" and message.to_agent == "web_ui":
                # Extract the actual response text
                response_text = message.content
                if isinstance(message.content, dict):
                    response_text = message.content.get("response", message.content.get("message", str(message.content)))
                
                # Forward Solomon's response to all connected clients
                response_msg = {
                    "type": "solomon_response",
                    "content": response_text,  # Use 'content' to match the JavaScript handler
                    "timestamp": datetime.now().isoformat(),
                    "sender": "solomon"
                }
                await self.broadcast_to_clients(response_msg)
                logger.info(f"Forwarded Solomon response to {len(self.clients)} clients")
                
        except Exception as e:
            logger.error(f"Error handling Solomon response: {e}")
            
    async def handle_client_message(self, websocket, message: str):
        """Handle incoming message from web client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "user_message":
                user_text = data.get("message", "")
                
                # Echo user message to all clients
                user_msg = {
                    "type": "user_message",
                    "message": user_text,
                    "timestamp": datetime.now().isoformat(),
                    "sender": "user"
                }
                await self.broadcast_to_clients(user_msg)
                
                # Send to Solomon (response will come back via message bus)
                await self.send_to_solomon(user_text)
                
                # Send acknowledgment that message was received
                ack_msg = {
                    "type": "system_message",
                    "message": "Message sent to Solomon...",
                    "timestamp": datetime.now().isoformat()
                }
                await self.broadcast_to_clients(ack_msg)
                
            elif message_type == "ping":
                await self.send_to_client(websocket, {"type": "pong", "timestamp": datetime.now().isoformat()})
                
        except json.JSONDecodeError:
            await self.send_to_client(websocket, {
                "type": "error", 
                "message": "Invalid JSON format"
            })
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.send_to_client(websocket, {
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
            
    async def websocket_handler(self, websocket, path: str = None):
        """Handle WebSocket connections"""
        await self.register_client(websocket)
        
        try:
            # Send welcome message
            await self.send_to_client(websocket, {
                "type": "system_message",
                "message": "Connected to Solomon chat interface",
                "timestamp": datetime.now().isoformat()
            })
            
            async for message in websocket:
                await self.handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def process_request(self, path, request_headers):
        """Handle HTTP requests that aren't WebSocket upgrades"""
        # Allow CORS for preflight requests
        origin = request_headers.get('Origin')
        if origin:
            return (
                200,
                [
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type'),
                    ('Content-Type', 'text/plain'),
                ],
                b'WebSocket endpoint - use ws:// protocol'
            )
        return None  # Let websockets handle it normally
            
    async def start_solomon_agent(self):
        """Start Solomon agent in the same process"""
        try:
            logger.info("Starting Solomon agent...")
            from agents.solomon.solomon import Solomon
            self.solomon_agent = Solomon()
            logger.info("Solomon agent started successfully")
            
            # Start Solomon's main loop
            asyncio.create_task(self.solomon_agent.run())
            
        except Exception as e:
            logger.error(f"Failed to start Solomon agent: {e}")
            self.solomon_agent = None
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting Solomon chat server on port {self.port}")
        
        # Start Solomon agent first
        await self.start_solomon_agent()
        
        # Register with message bus 
        await self.register_with_message_bus()
        
        server = await websockets.serve(
            self.websocket_handler,
            "localhost",  # Listen on localhost only
            self.port
        )
        
        logger.info(f"Solomon chat server running on ws://localhost:{self.port}")
        await server.wait_closed()

async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    chat_server = SolomonChatServer()
    
    try:
        await chat_server.start_server()
    except KeyboardInterrupt:
        logger.info("Shutting down Solomon chat server")
    except Exception as e:
        logger.error(f"Chat server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())