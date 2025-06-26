#!/usr/bin/env python3
"""
Enhanced ACC Message Handler - Fixes bidirectional message flow
This module patches the ACC to properly handle agent responses
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from core.message_bus import AgentMessage, MessageType, message_bus


class ACCMessageHandlerFix:
    """Enhanced message handling for ACC"""
    
    def __init__(self, acc_instance):
        self.acc = acc_instance
        self.pending_responses = {}  # correlation_id -> websocket connection
        
    async def enhanced_handle_send_message(self, message, connection_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced message handling with response tracking"""
        # Generate message ID
        message_id = str(uuid.uuid4())
        
        # Track who sent this message for response routing
        if connection_id and connection_id in self.acc.websocket_connections:
            self.pending_responses[message_id] = self.acc.websocket_connections[connection_id]
        
        # Determine sender
        sender = "user"
        
        # Prepare message data for storage
        message_data = {
            "id": message_id,
            "from_agent": sender,
            "to_agent": message.to_agent,
            "channel_id": message.channel,
            "content": {"text": message.content},
            "format": message.format.value,
            "attachments": message.attachments,
            "thread_id": message.thread_id,
            "mentions": message.mentions,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in database
        await self.acc.store_message(message_data)
        
        # Route message
        if message.to_agent:
            # Direct message - send via message bus
            agent_msg = AgentMessage(
                from_agent=sender,
                to_agent=message.to_agent,
                message_type=MessageType.TASK_REQUEST,
                content={"type": "user_chat", "message": message.content},
                correlation_id=message_id,
                requires_response=True
            )
            
            print(f"🚀 ACC: Sending message to {message.to_agent} via message bus (correlation_id: {message_id})")
            success = await message_bus.send_message(agent_msg)
            
            if success:
                print(f"✅ ACC: Message successfully queued for {message.to_agent}")
            else:
                print(f"❌ ACC: Failed to queue message for {message.to_agent}")
                
            # Also notify via WebSocket if agent is connected
            await self.acc.send_to_agent_websockets(message.to_agent, {
                "type": "message",
                "data": message_data
            })
        
        return {"success": True, "message_id": message_id}
    
    async def enhanced_handle_message_bus_message(self, message: AgentMessage):
        """Enhanced handler for messages from the message bus"""
        print(f"📨 ACC: Received message bus message - type: {message.message_type}, from: {message.from_agent}, to: {message.to_agent}")
        
        # Check if this is a response to a user message
        if message.message_type == MessageType.TASK_RESPONSE and message.correlation_id:
            print(f"📬 ACC: Processing response with correlation_id: {message.correlation_id}")
            
            # Convert to ACC format
            acc_message = {
                "id": message.correlation_id,  # Use correlation ID to match original
                "from_agent": message.from_agent,
                "to_agent": "user",  # Response goes back to user
                "content": {"text": message.content.get("response", str(message.content))},
                "timestamp": message.timestamp.isoformat(),
                "type": "agent_response",
                "correlation_id": message.correlation_id
            }
            
            # Store in database
            await self.acc.store_message(acc_message)
            
            # Send to WebSocket if we have a pending connection
            if message.correlation_id in self.pending_responses:
                ws = self.pending_responses[message.correlation_id]
                try:
                    await ws.send_json({
                        "type": "message",
                        "data": acc_message
                    })
                    print(f"✅ ACC: Sent response to WebSocket client")
                except Exception as e:
                    print(f"❌ ACC: Failed to send to WebSocket: {e}")
                finally:
                    # Clean up
                    del self.pending_responses[message.correlation_id]
            else:
                print(f"⚠️ ACC: No pending WebSocket connection for correlation_id: {message.correlation_id}")
                
                # Broadcast to all connections as fallback
                for conn_id, ws in self.acc.websocket_connections.items():
                    try:
                        await ws.send_json({
                            "type": "message",
                            "data": acc_message
                        })
                    except:
                        pass
        
        # Also handle the original logic for other message types
        else:
            # Convert message bus message to ACC format
            acc_message = {
                "id": str(uuid.uuid4()),
                "from_agent": message.from_agent,
                "to_agent": message.to_agent,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "type": message.message_type.value,
                "correlation_id": message.correlation_id
            }
            
            # Store in database
            await self.acc.store_message(acc_message)
            
            # Broadcast to relevant WebSocket connections
            if message.to_agent:
                await self.acc.send_to_agent_websockets(message.to_agent, {
                    "type": "message",
                    "data": acc_message
                })
            else:
                channel = message.content.get("channel", "general")
                await self.acc.broadcast_to_channel(channel, {
                    "type": "message",
                    "data": acc_message
                })


async def apply_acc_message_handler_fix(acc_instance):
    """Apply the message handler fix to an ACC instance"""
    import uuid  # Import needed for message ID generation
    
    # Create the fix handler
    fix_handler = ACCMessageHandlerFix(acc_instance)
    
    # Store original handlers
    acc_instance._original_handle_send_message = acc_instance.handle_send_message
    acc_instance._original_handle_message_bus_message = acc_instance.handle_message_bus_message
    
    # Replace with enhanced handlers
    acc_instance.handle_send_message = fix_handler.enhanced_handle_send_message
    acc_instance.handle_message_bus_message = fix_handler.enhanced_handle_message_bus_message
    
    # Also ensure ACC properly subscribes to response messages
    await message_bus.subscribe_to_topic("acc_system", "task_responses")
    
    print("✅ ACC message handler fix applied successfully")
    return fix_handler


if __name__ == "__main__":
    print("This module should be imported and applied to an ACC instance")