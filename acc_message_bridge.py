#!/usr/bin/env python3
"""
ACC Message Bridge
This bridges ACC messages to agents running in separate processes
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

from core.acc_client import ACCClient
from core.message_bus import message_bus, AgentMessage, MessageType


class ACCMessageBridge:
    """Bridges messages between ACC and local message bus"""
    
    def __init__(self):
        self.acc_client = ACCClient("message_bridge", "localhost:8890")
        self.running = False
        self.processed_messages = set()
        
    async def start(self):
        """Start the bridge"""
        print("🌉 Starting ACC Message Bridge")
        
        # Start local message bus
        if not message_bus.running:
            await message_bus.start()
            print("✅ Started local message bus")
            
        # Connect to ACC
        if await self.acc_client.connect():
            print("✅ Connected to ACC")
            self.running = True
            
            # Start polling for ACC messages
            asyncio.create_task(self._poll_acc_messages())
            
            # Start forwarding local messages to ACC
            asyncio.create_task(self._forward_to_acc())
            
            return True
        else:
            print("❌ Failed to connect to ACC")
            return False
            
    async def _poll_acc_messages(self):
        """Poll ACC for new messages and forward to local agents"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            while self.running:
                try:
                    # Get recent messages from ACC
                    response = await client.get(
                        "http://localhost:8890/api/messages",
                        params={"limit": 20}
                    )
                    
                    if response.status_code == 200:
                        messages = response.json()
                        
                        for msg in messages:
                            msg_id = msg.get("id")
                            
                            # Skip if already processed
                            if msg_id in self.processed_messages:
                                continue
                                
                            to_agent = msg.get("to_agent")
                            
                            # Check if this agent is registered locally
                            if to_agent and to_agent in message_bus.agent_queues:
                                print(f"🌉 Forwarding message {msg_id} to {to_agent}")
                                
                                # Convert ACC message to AgentMessage
                                agent_msg = AgentMessage(
                                    from_agent=msg.get("from_agent", "user"),
                                    to_agent=to_agent,
                                    message_type=MessageType.TASK_REQUEST,
                                    content={
                                        "type": "user_chat",
                                        "message": msg.get("content", {}).get("text", "")
                                    },
                                    correlation_id=msg_id,
                                    requires_response=True
                                )
                                
                                # Send via local message bus
                                await message_bus.send_message(agent_msg)
                                self.processed_messages.add(msg_id)
                                
                except Exception as e:
                    print(f"❌ Error polling ACC: {e}")
                    
                await asyncio.sleep(1)  # Poll every second
                
    async def _forward_to_acc(self):
        """Forward responses from local agents to ACC"""
        # Register as a relay agent
        await message_bus.register_agent("acc_relay")
        
        while self.running:
            try:
                # Get messages for relay
                messages = await message_bus.get_messages("acc_relay", timeout=1.0)
                
                for msg in messages:
                    if msg.message_type == MessageType.TASK_RESPONSE:
                        print(f"🌉 Forwarding response from {msg.from_agent} to ACC")
                        
                        # Send to ACC
                        await self.acc_client.send_message(
                            msg.from_agent,
                            msg.content.get("response", ""),
                            msg.correlation_id
                        )
                        
            except Exception as e:
                print(f"❌ Error forwarding to ACC: {e}")
                
            await asyncio.sleep(0.1)
            
    async def stop(self):
        """Stop the bridge"""
        self.running = False
        await self.acc_client.disconnect()
        print("🌉 ACC Message Bridge stopped")


async def main():
    """Run the message bridge"""
    bridge = ACCMessageBridge()
    
    try:
        if await bridge.start():
            print("🌉 Bridge is running. Press Ctrl+C to stop.")
            
            # Keep running
            while bridge.running:
                await asyncio.sleep(1)
        else:
            print("❌ Failed to start bridge")
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down bridge...")
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())