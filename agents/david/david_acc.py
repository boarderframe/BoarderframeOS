"""
David Agent with ACC Integration - BoarderframeOS
Enhanced version that connects to ACC via WebSocket for real-time communication
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.david.david import David as BaseDavid
from core.base_agent import AgentConfig
from core.acc_client import ACCClient
from core.message_bus import AgentMessage, MessageType


class DavidACC(BaseDavid):
    """
    David with ACC WebSocket integration
    """
    
    def __init__(self, config):
        """Initialize with ACC capabilities"""
        super().__init__(config)
        self.acc_client = None
        self.acc_connected = False
        
    async def connect_to_acc(self):
        """Connect to ACC via WebSocket"""
        try:
            self.acc_client = ACCClient(self.config.name, "localhost:8890")
            
            # Set up message handler
            self.acc_client.set_message_handler(self._handle_acc_message)
            
            # Connect
            if await self.acc_client.connect():
                self.acc_connected = True
                self.log("✅ Connected to ACC via WebSocket")
                return True
            else:
                self.log("❌ Failed to connect to ACC", level="warning")
                return False
                
        except Exception as e:
            self.log(f"❌ Error connecting to ACC: {e}", level="error")
            return False
            
    async def _handle_acc_message(self, message_data: Dict[str, Any]):
        """Handle messages received from ACC WebSocket"""
        self.log(f"📥 Received ACC message: {message_data}")
        
        # Convert to AgentMessage format for processing
        agent_msg = AgentMessage(
            from_agent=message_data.get("from_agent", "user"),
            to_agent=self.config.name,
            message_type=MessageType.TASK_REQUEST,
            content=message_data.get("content", {}),
            correlation_id=message_data.get("correlation_id"),
            requires_response=True
        )
        
        # Process the message
        if agent_msg.content.get("type") == "user_chat":
            user_message = agent_msg.content.get("message", "")
            response = await self.handle_user_chat(user_message)
            
            # Send response back via ACC
            if self.acc_connected and self.acc_client:
                await self.acc_client.send_message(
                    agent_msg.from_agent,
                    response,
                    agent_msg.correlation_id
                )
                self.log(f"📤 Sent response via ACC: {response[:100]}...")
                
    async def run(self):
        """Enhanced run method that connects to ACC first"""
        self.log(f"Starting {self.config.name} agent with ACC integration...")
        
        # Connect to ACC
        await self.connect_to_acc()
        
        # Start the base agent loop in parallel
        agent_task = asyncio.create_task(self._run_base_agent())
        
        try:
            # Keep both ACC connection and agent loop running
            await agent_task
        except Exception as e:
            self.log(f"Error in agent loop: {e}", level="error")
        finally:
            # Cleanup
            if self.acc_connected and self.acc_client:
                await self.acc_client.disconnect()
                self.log("Disconnected from ACC")
                
    async def _run_base_agent(self):
        """Run the base agent logic"""
        self.state = self.state.__class__.IDLE
        
        try:
            # Initial broadcast
            await self.broadcast_status()
            
            while self.active and self.state not in [
                self.state.__class__.TERMINATED,
                self.state.__class__.ERROR,
            ]:
                # Get context
                context = await self.get_context()
                
                # Check for new messages from message bus (legacy support)
                new_messages = context.get("new_messages", [])
                
                if new_messages or self.message_queue.qsize() > 0:
                    # Process with base agent logic
                    self.state = self.state.__class__.THINKING
                    thought = await self.think(context)
                    self.metrics["thoughts_processed"] += 1
                    
                    # Act
                    self.state = self.state.__class__.ACTING
                    result = await self.act(thought, context)
                    self.metrics["actions_taken"] += 1
                    
                    # Remember
                    self.memory.add(
                        {"thought": thought, "action": result, "context": context}
                    )
                    
                    # Process messages
                    await self._process_messages(new_messages)
                else:
                    # Idle state
                    self.state = self.state.__class__.IDLE
                    self.log("No tasks - remaining idle", level="debug")
                    
                # Periodic status broadcast
                if self.metrics["thoughts_processed"] % 50 == 0:
                    await self.broadcast_status()
                    
                # Wait before next iteration
                await asyncio.sleep(5)
                
        except Exception as e:
            self.state = self.state.__class__.ERROR
            self.metrics["errors"] += 1
            self.log(f"Error in main loop: {e}", level="error")
            raise


async def main():
    """Main entry point for ACC-enabled David"""
    config = AgentConfig(
        name="david",
        role="Chief Executive Officer",
        goals=[
            "Set strategic vision and direction for BoarderframeOS",
            "Ensure system achieves $15K monthly revenue target",
            "Make high-level architectural decisions",
            "Coordinate between departments and agents",
            "Maintain focus on scalability and growth",
        ],
        tools=[
            "mcp_filesystem",
            "mcp_database",
            "mcp_analytics", 
            "mcp_payment",
            "mcp_registry",
        ],
        zone="council",
        model="claude-3-5-sonnet-latest",
    )
    
    agent = DavidACC(config)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())