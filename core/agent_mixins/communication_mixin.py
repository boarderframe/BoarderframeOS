"""
CommunicationMixin - Message bus and inter-agent communication
Provides communication capabilities for agents
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime
import json
import uuid

from core.message_bus import (
    MessageBus, AgentMessage, MessageType, MessagePriority,
    send_task_request, broadcast_status, share_knowledge
)


class CommunicationMixin:
    """Inter-agent communication capabilities"""
    
    def __init__(self):
        """Initialize communication components"""
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.subscribed_topics: Set[str] = set()
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.communication_stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "broadcasts_sent": 0,
            "responses_sent": 0,
            "errors": 0
        }
        
        # Message processing configuration
        self.max_message_size = 1024 * 1024  # 1MB
        self.message_timeout = 30  # seconds
        self.batch_size = 10
        
    async def setup_communication(self, message_bus: MessageBus) -> None:
        """Setup communication with message bus"""
        self.message_bus = message_bus
        
        # Register with message bus
        await self.message_bus.register_agent(self.name)
        
        # Subscribe with default handler
        await self.message_bus.subscribe(self.name, self._handle_incoming_message)
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"Communication setup complete for {self.name}")
            
    async def send_message(
        self,
        to_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        requires_response: bool = False,
        timeout: Optional[float] = None
    ) -> Optional[AgentMessage]:
        """Send message to another agent"""
        # Validate message size
        if len(json.dumps(content)) > self.max_message_size:
            raise ValueError(f"Message exceeds maximum size of {self.max_message_size} bytes")
            
        # Create message
        correlation_id = str(uuid.uuid4())
        message = AgentMessage(
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            priority=priority,
            requires_response=requires_response,
            correlation_id=correlation_id,
            ttl_seconds=timeout or self.message_timeout
        )
        
        # Setup response handler if needed
        if requires_response:
            response_future = asyncio.Future()
            self.pending_responses[correlation_id] = response_future
            
        # Send message
        success = await self.message_bus.send_message(message)
        
        if success:
            self.communication_stats["messages_sent"] += 1
            
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"Sent {message_type.value} to {to_agent}")
                
            # Wait for response if required
            if requires_response:
                try:
                    response = await asyncio.wait_for(
                        response_future,
                        timeout=timeout or self.message_timeout
                    )
                    return response
                except asyncio.TimeoutError:
                    del self.pending_responses[correlation_id]
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.warning(f"Response timeout for message {correlation_id}")
                    return None
                    
        else:
            self.communication_stats["errors"] += 1
            if requires_response and correlation_id in self.pending_responses:
                del self.pending_responses[correlation_id]
                
        return None
        
    async def broadcast_message(
        self,
        message_type: MessageType,
        content: Dict[str, Any],
        topic: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> None:
        """Broadcast message to all agents or topic subscribers"""
        message = AgentMessage(
            from_agent=self.name,
            to_agent="*",
            message_type=message_type,
            content=content,
            priority=priority,
            requires_response=False
        )
        
        await self.message_bus.broadcast(message, topic)
        self.communication_stats["broadcasts_sent"] += 1
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.debug(f"Broadcast {message_type.value} to {'topic: ' + topic if topic else 'all agents'}")
            
    async def subscribe_to_topic(self, topic: str, handler: Optional[Callable] = None) -> None:
        """Subscribe to a message topic"""
        await self.message_bus.subscribe_to_topic(self.name, topic, handler)
        self.subscribed_topics.add(topic)
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"Subscribed to topic: {topic}")
            
    async def unsubscribe_from_topic(self, topic: str) -> None:
        """Unsubscribe from a message topic"""
        await self.message_bus.unsubscribe_from_topic(self.name, topic)
        self.subscribed_topics.discard(topic)
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"Unsubscribed from topic: {topic}")
            
    def register_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Register handler for specific message type"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
            
        self.message_handlers[message_type].append(handler)
        
    async def request_task(
        self,
        target_agent: str,
        task: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """Request a task from another agent"""
        response = await self.send_message(
            to_agent=target_agent,
            message_type=MessageType.TASK_REQUEST,
            content={"task": task},
            priority=priority,
            requires_response=True,
            timeout=timeout
        )
        
        if response:
            return response.content.get("result")
        return None
        
    async def share_knowledge_with_agents(
        self,
        knowledge: Dict[str, Any],
        topic: str
    ) -> None:
        """Share knowledge with other agents"""
        await share_knowledge(self.name, knowledge, topic)
        
    async def send_status_update(self, status: Dict[str, Any]) -> None:
        """Send status update to all agents"""
        await broadcast_status(self.name, status)
        
    async def _handle_incoming_message(self, message: AgentMessage) -> None:
        """Handle incoming message from message bus"""
        try:
            self.communication_stats["messages_received"] += 1
            
            # Add to processing queue
            await self.message_queue.put(message)
            
        except asyncio.QueueFull:
            self.communication_stats["errors"] += 1
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Message queue full, dropping message from {message.from_agent}")
                
    async def process_messages(self) -> None:
        """Process queued messages - should be called in agent's main loop"""
        messages_to_process = []
        
        # Get batch of messages
        for _ in range(min(self.batch_size, self.message_queue.qsize())):
            try:
                message = self.message_queue.get_nowait()
                messages_to_process.append(message)
            except asyncio.QueueEmpty:
                break
                
        # Process each message
        for message in messages_to_process:
            await self._process_single_message(message)
            
    async def _process_single_message(self, message: AgentMessage) -> None:
        """Process a single message"""
        try:
            # Check if it's a response to a pending request
            if message.message_type == MessageType.TASK_RESPONSE and message.correlation_id:
                if message.correlation_id in self.pending_responses:
                    future = self.pending_responses.pop(message.correlation_id)
                    if not future.done():
                        future.set_result(message)
                    return
                    
            # Call registered handlers
            handlers = self.message_handlers.get(message.message_type, [])
            
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.error(f"Error in message handler: {e}", exc_info=True)
                        
            # Send response if required
            if message.requires_response:
                await self._send_response(message)
                
        except Exception as e:
            self.communication_stats["errors"] += 1
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Error processing message: {e}", exc_info=True)
                
    async def _send_response(self, original_message: AgentMessage) -> None:
        """Send response to a message that requires it"""
        # Default response - can be overridden by handlers
        response_content = {
            "status": "acknowledged",
            "result": None,
            "timestamp": datetime.now().isoformat()
        }
        
        response = AgentMessage(
            from_agent=self.name,
            to_agent=original_message.from_agent,
            message_type=MessageType.TASK_RESPONSE,
            content=response_content,
            priority=original_message.priority,
            requires_response=False,
            correlation_id=original_message.correlation_id
        )
        
        await self.message_bus.send_message(response)
        self.communication_stats["responses_sent"] += 1
        
    async def cleanup_communication(self) -> None:
        """Cleanup communication resources"""
        # Cancel pending responses
        for future in self.pending_responses.values():
            if not future.done():
                future.cancel()
                
        self.pending_responses.clear()
        
        # Unregister from message bus
        if hasattr(self, 'message_bus'):
            await self.message_bus.unregister_agent(self.name)
            
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(f"Communication cleanup complete for {self.name}")
            
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics"""
        return {
            **self.communication_stats,
            "subscribed_topics": list(self.subscribed_topics),
            "pending_responses": len(self.pending_responses),
            "queue_size": self.message_queue.qsize()
        }