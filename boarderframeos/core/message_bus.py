"""
MessageBus - Inter-agent communication system for BoarderframeOS
Enables agents to coordinate and share information
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class MessageType(Enum):
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    RESOURCE_REQUEST = "resource_request"
    KNOWLEDGE_SHARE = "knowledge_share"
    COORDINATION = "coordination"
    ALERT = "alert"

@dataclass
class AgentMessage:
    """Message passed between agents"""
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    correlation_id: Optional[str] = None
    ttl_seconds: Optional[int] = None  # Time to live

class MessageBus:
    """Central message routing system for all agents"""
    
    def __init__(self):
        self.subscribers: Dict[str, Dict[str, List[Callable]]] = defaultdict(lambda: defaultdict(list))
        self.agent_queues: Dict[str, asyncio.Queue] = {}
        self.topic_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.message_history: List[AgentMessage] = []
        self.logger = logging.getLogger("MessageBus")
        self.running = False
        self._task = None
        
    async def start(self):
        """Start the message bus"""
        self.running = True
        self._task = asyncio.create_task(self._process_messages())
        self.logger.info("MessageBus started")
        
    async def stop(self):
        """Stop the message bus"""
        self.running = False
        if self._task:
            await self._task
        self.logger.info("MessageBus stopped")
        
    async def register_agent(self, agent_name: str, queue_size: int = 100):
        """Register an agent with the message bus"""
        if agent_name not in self.agent_queues:
            self.agent_queues[agent_name] = asyncio.Queue(maxsize=queue_size)
            self.logger.info(f"Registered agent: {agent_name}")
            
    async def unregister_agent(self, agent_name: str):
        """Unregister an agent from the message bus"""
        if agent_name in self.agent_queues:
            del self.agent_queues[agent_name]
            # Remove from all topic subscriptions
            for topic in self.topic_subscribers:
                self.topic_subscribers[topic].discard(agent_name)
            self.logger.info(f"Unregistered agent: {agent_name}")
            
    async def subscribe_to_topic(self, agent_name: str, topic: str, callback: Optional[Callable] = None):
        """Subscribe an agent to a topic"""
        self.topic_subscribers[topic].add(agent_name)
        if callback:
            self.subscribers[agent_name][topic].append(callback)
        self.logger.info(f"Agent {agent_name} subscribed to topic: {topic}")
        
    async def unsubscribe_from_topic(self, agent_name: str, topic: str):
        """Unsubscribe an agent from a topic"""
        self.topic_subscribers[topic].discard(agent_name)
        if topic in self.subscribers[agent_name]:
            del self.subscribers[agent_name][topic]
        self.logger.info(f"Agent {agent_name} unsubscribed from topic: {topic}")
    
    async def subscribe(self, agent_name: str, callback: Callable):
        """Subscribe an agent to receive all messages with a callback"""
        await self.register_agent(agent_name)
        self.subscribers[agent_name]['default'] = [callback]
        self.logger.info(f"Agent {agent_name} subscribed with default callback")
        
    async def send_message(self, message: AgentMessage):
        """Send a message to a specific agent"""
        if message.to_agent not in self.agent_queues:
            self.logger.warning(f"Agent {message.to_agent} not registered")
            return False
            
        try:
            # Add to recipient's queue
            await self.agent_queues[message.to_agent].put(message)
            
            # Store in history
            self.message_history.append(message)
            if len(self.message_history) > 1000:  # Keep last 1000 messages
                self.message_history = self.message_history[-1000:]
                
            self.logger.debug(f"Message sent from {message.from_agent} to {message.to_agent}")
            return True
            
        except asyncio.QueueFull:
            self.logger.error(f"Queue full for agent {message.to_agent}")
            return False
            
    async def broadcast(self, message: AgentMessage, topic: Optional[str] = None):
        """Broadcast a message to all agents or topic subscribers"""
        if topic:
            # Send to topic subscribers only
            recipients = self.topic_subscribers.get(topic, set())
        else:
            # Send to all agents except sender
            recipients = set(self.agent_queues.keys()) - {message.from_agent}
            
        tasks = []
        for agent_name in recipients:
            if agent_name in self.agent_queues:
                msg_copy = AgentMessage(
                    from_agent=message.from_agent,
                    to_agent=agent_name,
                    message_type=message.message_type,
                    content=message.content.copy(),
                    priority=message.priority,
                    timestamp=message.timestamp,
                    requires_response=message.requires_response,
                    correlation_id=message.correlation_id,
                    ttl_seconds=message.ttl_seconds
                )
                tasks.append(self.send_message(msg_copy))
                
        await asyncio.gather(*tasks)
        self.logger.info(f"Broadcast from {message.from_agent} to {len(recipients)} agents")
        
    async def route_to_agent(self, to_agent: str, message: AgentMessage):
        """Route a message to a specific agent"""
        message.to_agent = to_agent
        await self.send_message(message)
        
    async def get_messages(self, agent_name: str, timeout: Optional[float] = None) -> List[AgentMessage]:
        """Get all pending messages for an agent"""
        if agent_name not in self.agent_queues:
            return []
            
        messages = []
        queue = self.agent_queues[agent_name]
        
        try:
            # Get all messages without blocking
            while not queue.empty():
                msg = await asyncio.wait_for(queue.get(), timeout=timeout or 0.1)
                
                # Check TTL
                if msg.ttl_seconds:
                    elapsed = (datetime.now() - msg.timestamp).total_seconds()
                    if elapsed < msg.ttl_seconds:
                        messages.append(msg)
                    else:
                        self.logger.debug(f"Message expired: {msg.correlation_id}")
                else:
                    messages.append(msg)
                    
        except asyncio.TimeoutError:
            pass
            
        return messages
        
    async def wait_for_response(self, correlation_id: str, timeout: float = 30.0) -> Optional[AgentMessage]:
        """Wait for a response message with a specific correlation ID"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # Check recent messages
            for msg in reversed(self.message_history):
                if msg.correlation_id == correlation_id and msg.message_type == MessageType.TASK_RESPONSE:
                    return msg
                    
            await asyncio.sleep(0.1)
            
        return None
        
    async def _process_messages(self):
        """Background task to process messages and callbacks"""
        while self.running:
            try:
                # Process any callbacks
                for agent_name, topics in self.subscribers.items():
                    if agent_name in self.agent_queues:
                        messages = await self.get_messages(agent_name, timeout=0.1)
                        
                        for message in messages:
                            # Check if agent has callbacks for this message type
                            topic = message.message_type.value
                            if topic in topics:
                                for callback in topics[topic]:
                                    try:
                                        await callback(message)
                                    except Exception as e:
                                        self.logger.error(f"Callback error: {e}")
                                        
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
                
    def get_message_stats(self) -> Dict[str, Any]:
        """Get statistics about message bus usage"""
        stats = {
            "total_agents": len(self.agent_queues),
            "total_topics": len(self.topic_subscribers),
            "message_history_size": len(self.message_history),
            "queue_sizes": {},
            "topic_subscribers": {}
        }
        
        for agent_name, queue in self.agent_queues.items():
            stats["queue_sizes"][agent_name] = queue.qsize()
            
        for topic, subscribers in self.topic_subscribers.items():
            stats["topic_subscribers"][topic] = len(subscribers)
            
        return stats

# Global message bus instance
message_bus = MessageBus()

# Convenience functions
async def send_task_request(from_agent: str, to_agent: str, task: Dict[str, Any], 
                          priority: MessagePriority = MessagePriority.NORMAL) -> str:
    """Send a task request to another agent"""
    import uuid
    correlation_id = str(uuid.uuid4())
    
    message = AgentMessage(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=MessageType.TASK_REQUEST,
        content={"task": task},
        priority=priority,
        requires_response=True,
        correlation_id=correlation_id
    )
    
    await message_bus.send_message(message)
    return correlation_id

async def broadcast_status(agent_name: str, status: Dict[str, Any]):
    """Broadcast agent status update"""
    message = AgentMessage(
        from_agent=agent_name,
        to_agent="*",
        message_type=MessageType.STATUS_UPDATE,
        content=status,
        priority=MessagePriority.LOW
    )
    
    await message_bus.broadcast(message, topic="status_updates")

async def share_knowledge(from_agent: str, knowledge: Dict[str, Any], topic: str):
    """Share knowledge with agents subscribed to a topic"""
    message = AgentMessage(
        from_agent=from_agent,
        to_agent="*",
        message_type=MessageType.KNOWLEDGE_SHARE,
        content={"knowledge": knowledge, "topic": topic},
        priority=MessagePriority.NORMAL
    )
    
    await message_bus.broadcast(message, topic=topic)
