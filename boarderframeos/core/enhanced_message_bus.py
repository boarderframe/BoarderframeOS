"""
Enhanced MessageBus - Advanced inter-agent communication system for BoarderframeOS
Provides improved routing, persistence, coordination patterns, and real-time monitoring
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import uuid
import weakref
from pathlib import Path

from .message_bus import MessagePriority, MessageType, AgentMessage

class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"

class RoutingStrategy(Enum):
    DIRECT = "direct"
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    CAPABILITY_BASED = "capability_based"
    CONTENT_BASED = "content_based"

@dataclass
class MessageMetrics:
    """Metrics for message delivery and processing"""
    sent_time: datetime
    delivered_time: Optional[datetime] = None
    acknowledged_time: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    retry_count: int = 0
    route_taken: List[str] = field(default_factory=list)

@dataclass
class EnhancedAgentMessage(AgentMessage):
    """Enhanced message with additional coordination features"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    routing_strategy: RoutingStrategy = RoutingStrategy.DIRECT
    required_capabilities: List[str] = field(default_factory=list)
    max_retries: int = 3
    metrics: MessageMetrics = field(default_factory=lambda: MessageMetrics(sent_time=datetime.now()))
    persistent: bool = False
    
class WorkflowStep:
    """Represents a step in an agent workflow"""
    def __init__(self, agent: str, action: str, input_data: Dict[str, Any], 
                 condition: Optional[Callable] = None):
        self.step_id = str(uuid.uuid4())
        self.agent = agent
        self.action = action
        self.input_data = input_data
        self.condition = condition
        self.status = "pending"
        self.result = None
        self.error = None

class AgentWorkflow:
    """Manages multi-agent workflows"""
    def __init__(self, workflow_id: str, steps: List[WorkflowStep]):
        self.workflow_id = workflow_id
        self.steps = steps
        self.current_step = 0
        self.status = "pending"
        self.created_at = datetime.now()
        self.completed_at = None

class AgentCircuitBreaker:
    """Circuit breaker pattern for agent communication"""
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        elif self.state == "open":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "half_open"
                return True
            return False
        else:  # half_open
            return True
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

class EnhancedMessageBus:
    """Enhanced message bus with advanced coordination capabilities"""
    
    def __init__(self, db_path: str = "data/message_bus.db"):
        # Core messaging
        self.subscribers: Dict[str, Dict[str, List[Callable]]] = defaultdict(lambda: defaultdict(list))
        self.agent_queues: Dict[str, asyncio.Queue] = {}
        self.topic_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.message_history: deque = deque(maxlen=10000)
        
        # Enhanced features
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_load: Dict[str, int] = defaultdict(int)
        self.circuit_breakers: Dict[str, AgentCircuitBreaker] = {}
        self.routing_strategies: Dict[str, RoutingStrategy] = {}
        self.active_workflows: Dict[str, AgentWorkflow] = {}
        self.conversation_contexts: Dict[str, List[str]] = defaultdict(list)
        self.conversation_messages: Dict[str, List[str]] = defaultdict(list)
        self.workflow_messages: Dict[str, List[str]] = defaultdict(list)
        
        # Monitoring and metrics
        self.message_metrics: Dict[str, MessageMetrics] = {}
        self.message_counter: int = 0
        self.routing_stats: Dict[RoutingStrategy, int] = defaultdict(int)
        self.agent_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.performance_data: deque = deque(maxlen=1000)
        
        # Persistence
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("EnhancedMessageBus")
        self.running = False
        self._tasks = []
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for message persistence"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    delivered_at TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    status TEXT NOT NULL,
                    conversation_id TEXT,
                    workflow_id TEXT,
                    retry_count INTEGER DEFAULT 0,
                    ttl_seconds INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_capabilities (
                    agent_name TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    updated_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (agent_name, capability)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    steps TEXT NOT NULL
                )
            """)
    
    async def start(self):
        """Start the enhanced message bus"""
        self.running = True
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._process_messages()),
            asyncio.create_task(self._monitor_performance()),
            asyncio.create_task(self._cleanup_expired_messages()),
            asyncio.create_task(self._process_workflows()),
            asyncio.create_task(self._health_check_agents())
        ]
        
        self.logger.info("Enhanced MessageBus started with advanced features")
    
    async def stop(self):
        """Stop the enhanced message bus"""
        self.running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self.logger.info("Enhanced MessageBus stopped")
    
    async def register_agent(self, agent_name: str, capabilities: List[str] = None, 
                           queue_size: int = 100, routing_strategy: RoutingStrategy = RoutingStrategy.DIRECT):
        """Register an agent with capabilities and routing preferences"""
        if agent_name not in self.agent_queues:
            self.agent_queues[agent_name] = asyncio.Queue(maxsize=queue_size)
            self.circuit_breakers[agent_name] = AgentCircuitBreaker()
            self.routing_strategies[agent_name] = routing_strategy
            
            if capabilities:
                self.agent_capabilities[agent_name] = set(capabilities)
                await self._persist_capabilities(agent_name, capabilities)
            
            self.logger.info(f"Registered agent: {agent_name} with capabilities: {capabilities}")
    
    async def _persist_capabilities(self, agent_name: str, capabilities: List):
        """Persist agent capabilities to database"""
        with sqlite3.connect(self.db_path) as conn:
            for capability in capabilities:
                # Convert enum to string value if needed
                cap_str = capability.value if hasattr(capability, 'value') else str(capability)
                conn.execute("""
                    INSERT OR REPLACE INTO agent_capabilities 
                    (agent_name, capability, updated_at) 
                    VALUES (?, ?, ?)
                """, (agent_name, cap_str, datetime.now()))
    
    async def send_enhanced_message(self, message: EnhancedAgentMessage) -> bool:
        """Send an enhanced message with advanced routing"""
        message.metrics.sent_time = datetime.now()
        self.message_counter += 1
        
        # Persist critical messages
        if message.persistent:
            await self._persist_message(message)
        
        # Apply routing strategy
        target_agents = await self._resolve_routing(message)
        
        if not target_agents:
            self.logger.warning(f"No target agents found for message {message.message_id}")
            return False
        
        success = False
        for agent_name in target_agents:
            if await self._deliver_to_agent(agent_name, message):
                success = True
                
        # Update conversation context
        if message.conversation_id:
            self.conversation_contexts[message.conversation_id].append(message.message_id)
        
        return success
    
    async def _resolve_routing(self, message: EnhancedAgentMessage) -> List[str]:
        """Resolve target agents based on routing strategy"""
        if message.routing_strategy == RoutingStrategy.DIRECT:
            return [message.to_agent] if message.to_agent in self.agent_queues else []
        
        elif message.routing_strategy == RoutingStrategy.CAPABILITY_BASED:
            return self._find_agents_by_capabilities(message.required_capabilities)
        
        elif message.routing_strategy == RoutingStrategy.LOAD_BALANCED:
            return self._find_least_loaded_agents(message.required_capabilities)
        
        elif message.routing_strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(message.required_capabilities)
        
        else:
            return [message.to_agent] if message.to_agent in self.agent_queues else []
    
    def _find_agents_by_capabilities(self, required_capabilities: List[str]) -> List[str]:
        """Find agents that have all required capabilities"""
        if not required_capabilities:
            return list(self.agent_queues.keys())
        
        capable_agents = []
        for agent_name, capabilities in self.agent_capabilities.items():
            if all(cap in capabilities for cap in required_capabilities):
                if self.circuit_breakers[agent_name].can_execute():
                    capable_agents.append(agent_name)
        
        return capable_agents
    
    def _find_least_loaded_agents(self, required_capabilities: List[str]) -> List[str]:
        """Find the least loaded agents with required capabilities"""
        capable_agents = self._find_agents_by_capabilities(required_capabilities)
        
        if not capable_agents:
            return []
        
        # Sort by current load
        return sorted(capable_agents, key=lambda agent: self.agent_load[agent])[:3]
    
    def _round_robin_selection(self, required_capabilities: List[str]) -> List[str]:
        """Round-robin selection among capable agents"""
        capable_agents = self._find_agents_by_capabilities(required_capabilities)
        
        if not capable_agents:
            return []
        
        # Simple round-robin based on message count
        total_messages = sum(len(self.conversation_contexts[conv]) for conv in self.conversation_contexts)
        selected_agent = capable_agents[total_messages % len(capable_agents)]
        return [selected_agent]
    
    async def _deliver_to_agent(self, agent_name: str, message: EnhancedAgentMessage) -> bool:
        """Deliver message to specific agent with circuit breaker protection"""
        if not self.circuit_breakers[agent_name].can_execute():
            self.logger.warning(f"Circuit breaker open for agent {agent_name}")
            return False
        
        try:
            # Update metrics
            self.agent_load[agent_name] += 1
            
            # Add to agent's queue
            await self.agent_queues[agent_name].put(message)
            
            # Update message status
            message.delivery_status = DeliveryStatus.DELIVERED
            message.metrics.delivered_time = datetime.now()
            message.metrics.route_taken.append(agent_name)
            
            # Store metrics
            self.message_metrics[message.message_id] = message.metrics
            
            # Record success
            self.circuit_breakers[agent_name].record_success()
            
            self.logger.debug(f"Message {message.message_id} delivered to {agent_name}")
            return True
            
        except asyncio.QueueFull:
            self.circuit_breakers[agent_name].record_failure()
            self.logger.error(f"Queue full for agent {agent_name}")
            return False
        except Exception as e:
            self.circuit_breakers[agent_name].record_failure()
            self.logger.error(f"Failed to deliver message to {agent_name}: {e}")
            return False
        finally:
            self.agent_load[agent_name] = max(0, self.agent_load[agent_name] - 1)
    
    async def _persist_message(self, message: EnhancedAgentMessage):
        """Persist message to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO messages 
                (message_id, from_agent, to_agent, message_type, content, priority, 
                 created_at, status, conversation_id, workflow_id, ttl_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.message_id, message.from_agent, message.to_agent,
                message.message_type.value, json.dumps(message.content),
                message.priority.value, message.timestamp, message.delivery_status.value,
                message.conversation_id, message.workflow_id, message.ttl_seconds
            ))
    
    async def create_workflow(self, workflow_id: str, steps: List[Dict[str, Any]]) -> str:
        """Create a new agent workflow"""
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                agent=step_data["agent"],
                action=step_data["action"],
                input_data=step_data.get("input_data", {}),
                condition=step_data.get("condition")
            )
            workflow_steps.append(step)
        
        workflow = AgentWorkflow(workflow_id, workflow_steps)
        self.active_workflows[workflow_id] = workflow
        
        # Persist workflow
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO workflows (workflow_id, status, created_at, steps)
                VALUES (?, ?, ?, ?)
            """, (workflow_id, "pending", datetime.now(), json.dumps(steps)))
        
        self.logger.info(f"Created workflow {workflow_id} with {len(steps)} steps")
        return workflow_id
    
    async def _process_workflows(self):
        """Background task to process active workflows"""
        while self.running:
            try:
                for workflow_id, workflow in list(self.active_workflows.items()):
                    if workflow.status == "pending" and workflow.current_step < len(workflow.steps):
                        current_step = workflow.steps[workflow.current_step]
                        
                        # Execute current step
                        if current_step.status == "pending":
                            await self._execute_workflow_step(workflow, current_step)
                        
                        # Check if step is complete
                        if current_step.status == "completed":
                            workflow.current_step += 1
                            
                            # Check if workflow is complete
                            if workflow.current_step >= len(workflow.steps):
                                workflow.status = "completed"
                                workflow.completed_at = datetime.now()
                                del self.active_workflows[workflow_id]
                                self.logger.info(f"Workflow {workflow_id} completed")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error processing workflows: {e}")
    
    async def _execute_workflow_step(self, workflow: AgentWorkflow, step: WorkflowStep):
        """Execute a single workflow step"""
        try:
            # Create message for the step
            message = EnhancedAgentMessage(
                from_agent="WorkflowOrchestrator",
                to_agent=step.agent,
                message_type=MessageType.TASK_REQUEST,
                content={
                    "action": step.action,
                    "input_data": step.input_data,
                    "step_id": step.step_id
                },
                workflow_id=workflow.workflow_id,
                routing_strategy=RoutingStrategy.CAPABILITY_BASED,
                required_capabilities=[step.action]
            )
            
            # Send message
            success = await self.send_enhanced_message(message)
            
            if success:
                step.status = "in_progress"
                self.logger.debug(f"Started workflow step {step.step_id}")
            else:
                step.status = "failed"
                step.error = "Failed to send message"
                
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            self.logger.error(f"Error executing workflow step {step.step_id}: {e}")
    
    async def _monitor_performance(self):
        """Monitor system performance and collect metrics"""
        while self.running:
            try:
                # Collect performance data
                performance_snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "total_agents": len(self.agent_queues),
                    "active_workflows": len(self.active_workflows),
                    "message_queue_sizes": {
                        agent: queue.qsize() for agent, queue in self.agent_queues.items()
                    },
                    "agent_loads": dict(self.agent_load),
                    "circuit_breaker_states": {
                        agent: cb.state for agent, cb in self.circuit_breakers.items()
                    }
                }
                
                self.performance_data.append(performance_snapshot)
                
                # Log performance summary every minute
                if len(self.performance_data) % 60 == 0:
                    avg_queue_size = sum(queue.qsize() for queue in self.agent_queues.values()) / len(self.agent_queues)
                    self.logger.info(f"Performance: {len(self.agent_queues)} agents, avg queue size: {avg_queue_size:.1f}")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error monitoring performance: {e}")
    
    async def _process_messages(self):
        """Enhanced message processing with retry logic"""
        while self.running:
            try:
                # Process message acknowledgments and retries
                for message_id, metrics in list(self.message_metrics.items()):
                    if metrics.retry_count > 0:
                        # Handle retry logic here
                        pass
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error processing messages: {e}")
    
    async def _cleanup_expired_messages(self):
        """Clean up expired messages and old data"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Clean up message metrics older than 24 hours
                expired_metrics = []
                for message_id, metrics in self.message_metrics.items():
                    if current_time - metrics.sent_time > timedelta(hours=24):
                        expired_metrics.append(message_id)
                
                for message_id in expired_metrics:
                    del self.message_metrics[message_id]
                
                # Clean up conversation contexts older than 7 days
                # (This would need more sophisticated logic in practice)
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                self.logger.error(f"Error cleaning up expired messages: {e}")
    
    async def _health_check_agents(self):
        """Perform health checks on registered agents"""
        while self.running:
            try:
                for agent_name in list(self.agent_queues.keys()):
                    # Simple health check - could be enhanced with ping messages
                    queue_size = self.agent_queues[agent_name].qsize()
                    
                    # Update agent metrics
                    self.agent_metrics[agent_name].update({
                        "last_health_check": datetime.now().isoformat(),
                        "queue_size": queue_size,
                        "circuit_breaker_state": self.circuit_breakers[agent_name].state
                    })
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error performing health checks: {e}")
    
    async def register_agent_capabilities(self, agent_name: str, capabilities: List):
        """Register capabilities for an agent"""
        # Convert enum values to strings if needed
        cap_strings = []
        for cap in capabilities:
            if hasattr(cap, 'value'):
                cap_strings.append(cap.value)
            else:
                cap_strings.append(str(cap))
        
        self.agent_capabilities[agent_name] = set(cap_strings)
        await self._persist_capabilities(agent_name, capabilities)
        self.logger.info(f"Registered capabilities for {agent_name}: {cap_strings}")
    
    async def discover_agents_by_capability(self, capability: str) -> List[str]:
        """Discover agents that have a specific capability"""
        agents = []
        for agent_name, agent_caps in self.agent_capabilities.items():
            if capability in agent_caps:
                agents.append(agent_name)
        return agents
    
    async def subscribe_to_topic(self, agent_name: str, topic: str):
        """Subscribe an agent to a topic"""
        self.topic_subscribers[topic].add(agent_name)
        self.logger.info(f"Agent {agent_name} subscribed to topic: {topic}")
    
    async def unsubscribe_from_topic(self, agent_name: str, topic: str):
        """Unsubscribe an agent from a topic"""
        self.topic_subscribers[topic].discard(agent_name)
        self.logger.info(f"Agent {agent_name} unsubscribed from topic: {topic}")
    
    def get_enhanced_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the message bus"""
        return {
            "basic_stats": {
                "total_agents": len(self.agent_queues),
                "active_workflows": len(self.active_workflows),
                "total_capabilities": sum(len(caps) for caps in self.agent_capabilities.values()),
                "message_history_size": len(self.message_history)
            },
            "performance_stats": {
                "average_queue_size": sum(q.qsize() for q in self.agent_queues.values()) / len(self.agent_queues) if self.agent_queues else 0,
                "total_agent_load": sum(self.agent_load.values()),
                "circuit_breakers_open": sum(1 for cb in self.circuit_breakers.values() if cb.state == "open")
            },
            "agent_capabilities": {
                agent: list(caps) for agent, caps in self.agent_capabilities.items()
            },
            "recent_performance": list(self.performance_data)[-10:] if self.performance_data else []
        }

    async def get_messages_for_agent(self, agent_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get message history for a specific agent"""
        try:
            if not self.db_path:
                return []
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT message_id, from_agent, to_agent, message_type, content, 
                           created_at, status, priority, conversation_id
                    FROM messages 
                    WHERE from_agent = ? OR to_agent = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (agent_name, agent_name, limit))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'message_id': row[0],
                        'from_agent': row[1],
                        'to_agent': row[2],
                        'message_type': row[3],
                        'content': json.loads(row[4]) if row[4] else {},
                        'timestamp': row[5],
                        'delivery_status': row[6],
                        'routing_strategy': 'direct',  # Default since not stored
                        'priority': row[7],
                        'conversation_id': row[8]
                    })
                
                return messages
                
        except Exception as e:
            self.logger.error(f"Error getting messages for agent {agent_name}: {e}")
            return []

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the message bus"""
        try:
            # Basic queue metrics
            queue_metrics = {}
            total_queue_size = 0
            for agent, queue in self.agent_queues.items():
                size = queue.qsize()
                queue_metrics[agent] = size
                total_queue_size += size
            
            avg_queue_size = total_queue_size / max(len(self.agent_queues), 1)
            
            # Message delivery metrics
            delivery_metrics = {
                'total_messages_sent': self.message_counter,
                'messages_in_queues': total_queue_size,
                'average_queue_size': avg_queue_size,
                'active_agents': len(self.agent_queues),
                'active_conversations': len(self.conversation_messages),
                'active_workflows': len(self.workflow_messages)
            }
            
            # Database metrics if available
            db_metrics = {}
            if self.db_path:
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        # Total messages in database
                        cursor.execute("SELECT COUNT(*) FROM messages")
                        db_metrics['total_persisted_messages'] = cursor.fetchone()[0]
                        
                        # Messages by status
                        cursor.execute("""
                            SELECT status, COUNT(*) 
                            FROM messages 
                            GROUP BY status
                        """)
                        status_counts = dict(cursor.fetchall())
                        db_metrics['message_status_distribution'] = status_counts
                        
                        # Recent message rate
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM messages 
                            WHERE datetime(created_at) >= datetime('now', '-1 hour')
                        """)
                        db_metrics['messages_last_hour'] = cursor.fetchone()[0]
                        
                except Exception as e:
                    self.logger.warning(f"Could not get database metrics: {e}")
            
            # Route performance
            route_metrics = {}
            for strategy in RoutingStrategy:
                route_metrics[strategy.value] = self.routing_stats.get(strategy, 0)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'delivery_metrics': delivery_metrics,
                'queue_metrics': queue_metrics,
                'database_metrics': db_metrics,
                'routing_metrics': route_metrics,
                'agent_capabilities': dict(self.agent_capabilities),
                'topic_subscriptions': {
                    topic: list(agents) for topic, agents in self.topic_subscribers.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'basic_metrics': {
                    'active_agents': len(self.agent_queues),
                    'total_queue_size': sum(q.qsize() for q in self.agent_queues.values())
                }
            }

# Global enhanced message bus instance
enhanced_message_bus = EnhancedMessageBus()

# Convenience functions for enhanced messaging
async def send_workflow_request(initiator_agent: str, workflow_steps: List[Dict[str, Any]], 
                               workflow_id: Optional[str] = None) -> str:
    """Send a multi-agent workflow request"""
    if not workflow_id:
        workflow_id = f"workflow_{uuid.uuid4()}"
    
    return await enhanced_message_bus.create_workflow(workflow_id, workflow_steps)

async def send_capability_request(from_agent: str, required_capabilities: List[str], 
                                task_data: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
    """Send a task to agents with specific capabilities"""
    message = EnhancedAgentMessage(
        from_agent=from_agent,
        to_agent="",  # Will be resolved by routing
        message_type=MessageType.TASK_REQUEST,
        content=task_data,
        priority=priority,
        routing_strategy=RoutingStrategy.CAPABILITY_BASED,
        required_capabilities=required_capabilities,
        conversation_id=str(uuid.uuid4())
    )
    
    await enhanced_message_bus.send_enhanced_message(message)
    return message.conversation_id

async def broadcast_enhanced(from_agent: str, message_type: MessageType, content: Dict[str, Any], 
                           topic: Optional[str] = None, persistent: bool = False):
    """Enhanced broadcast with persistence option"""
    message = EnhancedAgentMessage(
        from_agent=from_agent,
        to_agent="*",
        message_type=message_type,
        content=content,
        routing_strategy=RoutingStrategy.DIRECT,
        persistent=persistent
    )
    
    # Broadcast to all agents in topic or all agents
    if topic and topic in enhanced_message_bus.topic_subscribers:
        for agent_name in enhanced_message_bus.topic_subscribers[topic]:
            agent_message = EnhancedAgentMessage(**asdict(message))
            agent_message.to_agent = agent_name
            await enhanced_message_bus.send_enhanced_message(agent_message)
    else:
        for agent_name in enhanced_message_bus.agent_queues:
            if agent_name != from_agent:
                agent_message = EnhancedAgentMessage(**asdict(message))
                agent_message.to_agent = agent_name
                await enhanced_message_bus.send_enhanced_message(agent_message)
