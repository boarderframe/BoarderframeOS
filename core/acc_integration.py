"""
ACC Integration for BaseAgent
Allows agents to communicate through the Agent Communication Center
"""

import asyncio
from typing import Optional, Dict, Any
from .acc_client import ACCClient
from .message_bus import AgentMessage, MessageType


class ACCIntegrationMixin:
    """Mixin to add ACC integration to agents"""
    
    def __init__(self):
        self.acc_client: Optional[ACCClient] = None
        self.use_acc = False
        
    async def connect_to_acc(self, acc_url: str = "localhost:8890"):
        """Connect this agent to the ACC"""
        try:
            self.acc_client = ACCClient(self.config.name, acc_url)
            
            # Set message handler
            self.acc_client.set_message_handler(self._handle_acc_message)
            
            # Connect
            if await self.acc_client.connect():
                self.use_acc = True
                self.log(f"Connected to ACC at {acc_url}")
                return True
            else:
                self.log("Failed to connect to ACC", level="warning")
                return False
                
        except Exception as e:
            self.log(f"Error connecting to ACC: {e}", level="error")
            return False
            
    async def disconnect_from_acc(self):
        """Disconnect from ACC"""
        if self.acc_client:
            await self.acc_client.disconnect()
            self.use_acc = False
            self.log("Disconnected from ACC")
            
    async def _handle_acc_message(self, message_data: Dict[str, Any]):
        """Handle messages received from ACC"""
        # Convert ACC message to AgentMessage format
        agent_msg = AgentMessage(
            from_agent=message_data.get("from_agent", "unknown"),
            to_agent=self.config.name,
            message_type=MessageType.TASK_REQUEST,
            content=message_data.get("content", {}),
            correlation_id=message_data.get("correlation_id"),
            requires_response=True
        )
        
        # Add to message queue for processing
        await self.message_queue.put(agent_msg)
        
    async def send_acc_response(self, to_agent: str, response: str, correlation_id: Optional[str] = None):
        """Send a response through ACC"""
        if self.acc_client and self.use_acc:
            await self.acc_client.send_message(to_agent, response, correlation_id)
        else:
            self.log("ACC not connected, cannot send response", level="warning")


def create_acc_enabled_agent(agent_class):
    """Factory function to create an ACC-enabled agent class"""
    
    class ACCEnabledAgent(agent_class, ACCIntegrationMixin):
        def __init__(self, config):
            agent_class.__init__(self, config)
            ACCIntegrationMixin.__init__(self)
            
        async def run(self):
            """Enhanced run method that connects to ACC first"""
            # Try to connect to ACC
            await self.connect_to_acc()
            
            # Run the original agent logic
            await agent_class.run(self)
            
        async def _process_messages(self, messages):
            """Enhanced message processing that handles ACC responses"""
            for message in messages:
                try:
                    # Process the message normally
                    await agent_class._process_messages(self, [message])
                    
                    # If from ACC and requires response, send through ACC
                    if self.use_acc and message.requires_response and hasattr(message, 'correlation_id'):
                        if message.content.get("type") == "user_chat":
                            # Get response from handle_user_chat
                            user_message = message.content.get("message", "")
                            response = await self.handle_user_chat(user_message)
                            
                            # Send via ACC
                            await self.send_acc_response(
                                message.from_agent,
                                response,
                                message.correlation_id
                            )
                            
                except Exception as e:
                    self.log(f"Error processing ACC message: {e}", level="error")
                    
        async def terminate(self):
            """Enhanced terminate that disconnects from ACC"""
            await self.disconnect_from_acc()
            await agent_class.terminate(self)
    
    return ACCEnabledAgent