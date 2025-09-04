"""
Communication Infrastructure for MCP-UI
PostMessage handling, event system, and message bus
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime
from enum import Enum
import asyncio
import json
import logging
from collections import defaultdict
import uuid


# ============================================================================
# Message Types
# ============================================================================

class MessageType(str, Enum):
    """Standard message types"""
    INTENT = "intent"
    RESPONSE = "response"
    ERROR = "error"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    STATE_UPDATE = "state_update"
    COMMAND = "command"
    QUERY = "query"


# ============================================================================
# PostMessage Handler
# ============================================================================

class PostMessageHandler:
    """
    Handle PostMessage communication between UI components and server
    Implements secure message passing following browser postMessage API
    """
    
    def __init__(self, origin_whitelist: Optional[List[str]] = None):
        """
        Initialize PostMessage handler
        
        Args:
            origin_whitelist: List of allowed origins
        """
        self.origin_whitelist = origin_whitelist or ["*"]
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_handler(
        self,
        message_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    ):
        """
        Register message handler
        
        Args:
            message_type: Type of message to handle
            handler: Async handler function
        """
        self.message_handlers[message_type].append(handler)
        self.logger.debug(f"Registered handler for message type: {message_type}")
    
    async def handle_message(
        self,
        message: str,
        origin: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle incoming postMessage
        
        Args:
            message: Message content (JSON string)
            origin: Message origin
            
        Returns:
            Response data if applicable
        """
        # Validate origin
        if not self._validate_origin(origin):
            self.logger.warning(f"Invalid message origin: {origin}")
            return self._create_error_response("Invalid origin", "ORIGIN_ERROR")
        
        try:
            # Parse message
            data = json.loads(message)
            
            # Validate message structure
            if not self._validate_message_structure(data):
                return self._create_error_response("Invalid message structure", "STRUCTURE_ERROR")
            
            # Extract message details
            msg_id = data.get("id", str(uuid.uuid4()))
            msg_type = data.get("type", MessageType.INTENT)
            payload = data.get("payload", {})
            
            # Handle based on type
            if msg_type in self.message_handlers:
                responses = []
                for handler in self.message_handlers[msg_type]:
                    try:
                        response = await handler(payload)
                        if response:
                            responses.append(response)
                    except Exception as e:
                        self.logger.error(f"Handler error: {e}", exc_info=True)
                        responses.append(self._create_error_response(str(e), "HANDLER_ERROR"))
                
                # Combine responses
                if len(responses) == 1:
                    return self._create_response(msg_id, responses[0])
                elif responses:
                    return self._create_response(msg_id, {"results": responses})
                else:
                    return self._create_response(msg_id, {"status": "ok"})
            
            # Check for pending response
            if msg_id in self.pending_responses:
                future = self.pending_responses.pop(msg_id)
                future.set_result(payload)
                return None
            
            # No handler found
            return self._create_error_response(
                f"No handler for message type: {msg_type}",
                "NO_HANDLER"
            )
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON: {e}")
            return self._create_error_response("Invalid JSON", "JSON_ERROR")
        except Exception as e:
            self.logger.error(f"Message handling error: {e}", exc_info=True)
            return self._create_error_response(str(e), "INTERNAL_ERROR")
    
    async def send_message(
        self,
        target: str,
        message_type: str,
        payload: Dict[str, Any],
        wait_response: bool = False,
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send message to target
        
        Args:
            target: Target window/frame
            message_type: Type of message
            payload: Message payload
            wait_response: Wait for response
            timeout: Response timeout in seconds
            
        Returns:
            Response if wait_response is True
        """
        msg_id = str(uuid.uuid4())
        
        message = {
            "id": msg_id,
            "type": message_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
            "target": target
        }
        
        # Create JavaScript for posting message
        js_code = self._generate_post_message_js(message)
        
        if wait_response:
            # Create future for response
            future = asyncio.Future()
            self.pending_responses[msg_id] = future
            
            try:
                # Wait for response with timeout
                response = await asyncio.wait_for(future, timeout)
                return response
            except asyncio.TimeoutError:
                self.pending_responses.pop(msg_id, None)
                self.logger.warning(f"Message response timeout: {msg_id}")
                return None
            finally:
                self.pending_responses.pop(msg_id, None)
        
        return {"js": js_code}
    
    def _validate_origin(self, origin: str) -> bool:
        """Validate message origin"""
        if "*" in self.origin_whitelist:
            return True
        return origin in self.origin_whitelist
    
    def _validate_message_structure(self, data: Dict[str, Any]) -> bool:
        """Validate message has required fields"""
        return "type" in data or "id" in data
    
    def _create_response(self, msg_id: str, data: Any) -> Dict[str, Any]:
        """Create response message"""
        return {
            "id": msg_id,
            "type": MessageType.RESPONSE,
            "payload": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_error_response(self, error: str, code: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "type": MessageType.ERROR,
            "payload": {
                "error": error,
                "code": code
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_post_message_js(self, message: Dict[str, Any]) -> str:
        """Generate JavaScript code for posting message"""
        message_json = json.dumps(message)
        return f"""
        (function() {{
            const message = {message_json};
            const target = message.target || '*';
            
            // Post to parent if in iframe
            if (window.parent !== window) {{
                window.parent.postMessage(message, target);
            }}
            
            // Post to opener if popup
            if (window.opener) {{
                window.opener.postMessage(message, target);
            }}
            
            // Dispatch custom event for local handling
            window.dispatchEvent(new CustomEvent('mcp:message', {{
                detail: message
            }}));
        }})();
        """


# ============================================================================
# Event Emitter
# ============================================================================

class EventEmitter:
    """
    Event emitter for internal communication
    Implements Node.js-style event emitter pattern
    """
    
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.once_listeners: Dict[str, List[Callable]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def on(self, event: str, listener: Callable):
        """
        Add event listener
        
        Args:
            event: Event name
            listener: Event handler
        """
        self.listeners[event].append(listener)
    
    def once(self, event: str, listener: Callable):
        """
        Add one-time event listener
        
        Args:
            event: Event name
            listener: Event handler
        """
        self.once_listeners[event].append(listener)
    
    def off(self, event: str, listener: Callable):
        """
        Remove event listener
        
        Args:
            event: Event name
            listener: Event handler to remove
        """
        if event in self.listeners:
            try:
                self.listeners[event].remove(listener)
            except ValueError:
                pass
        
        if event in self.once_listeners:
            try:
                self.once_listeners[event].remove(listener)
            except ValueError:
                pass
    
    async def emit(self, event: str, *args, **kwargs):
        """
        Emit event
        
        Args:
            event: Event name
            *args: Event arguments
            **kwargs: Event keyword arguments
        """
        # Call regular listeners
        for listener in self.listeners.get(event, []):
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(*args, **kwargs)
                else:
                    listener(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Event listener error: {e}", exc_info=True)
        
        # Call once listeners
        once_listeners = self.once_listeners.pop(event, [])
        for listener in once_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(*args, **kwargs)
                else:
                    listener(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Once listener error: {e}", exc_info=True)
    
    def remove_all_listeners(self, event: Optional[str] = None):
        """
        Remove all listeners for event
        
        Args:
            event: Event name (all events if None)
        """
        if event:
            self.listeners.pop(event, None)
            self.once_listeners.pop(event, None)
        else:
            self.listeners.clear()
            self.once_listeners.clear()
    
    def listener_count(self, event: str) -> int:
        """Get listener count for event"""
        return len(self.listeners.get(event, [])) + len(self.once_listeners.get(event, []))


# ============================================================================
# Message Bus
# ============================================================================

class MessageBus:
    """
    Central message bus for component communication
    Implements pub/sub pattern with topic-based routing
    """
    
    def __init__(self):
        self.topics: Dict[str, List[Callable]] = defaultdict(list)
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.event_emitter = EventEmitter()
        self.post_message_handler = PostMessageHandler()
        self.logger = logging.getLogger(__name__)
        self._worker_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start message bus"""
        if self.running:
            return
        
        self.running = True
        self._worker_task = asyncio.create_task(self._process_messages())
        self.logger.info("Message bus started")
    
    async def stop(self):
        """Stop message bus"""
        self.running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Message bus stopped")
    
    async def close(self):
        """Close message bus and cleanup"""
        await self.stop()
        self.topics.clear()
        self.event_emitter.remove_all_listeners()
    
    def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Any]]
    ):
        """
        Subscribe to topic
        
        Args:
            topic: Topic pattern (supports wildcards)
            handler: Message handler
        """
        self.topics[topic].append(handler)
        self.logger.debug(f"Subscribed to topic: {topic}")
    
    def unsubscribe(self, topic: str, handler: Callable):
        """
        Unsubscribe from topic
        
        Args:
            topic: Topic pattern
            handler: Handler to remove
        """
        if topic in self.topics:
            try:
                self.topics[topic].remove(handler)
                self.logger.debug(f"Unsubscribed from topic: {topic}")
            except ValueError:
                pass
    
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        wait_response: bool = False,
        timeout: float = 30.0
    ) -> Optional[List[Any]]:
        """
        Publish message to topic
        
        Args:
            topic: Topic to publish to
            message: Message data
            wait_response: Wait for handler responses
            timeout: Response timeout
            
        Returns:
            Handler responses if wait_response is True
        """
        msg = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "wait_response": wait_response
        }
        
        if wait_response:
            # Create response future
            response_future = asyncio.Future()
            msg["response_future"] = response_future
            
            # Queue message
            await self.message_queue.put(msg)
            
            try:
                # Wait for response
                responses = await asyncio.wait_for(response_future, timeout)
                return responses
            except asyncio.TimeoutError:
                self.logger.warning(f"Message response timeout: {msg['id']}")
                return None
        else:
            # Fire and forget
            await self.message_queue.put(msg)
            return None
    
    async def _process_messages(self):
        """Process queued messages"""
        while self.running:
            try:
                # Get message with timeout to allow checking running status
                msg = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                # Find matching handlers
                handlers = self._find_handlers(msg["topic"])
                
                if handlers:
                    responses = []
                    
                    # Execute handlers
                    for handler in handlers:
                        try:
                            response = await handler(msg["message"])
                            if response:
                                responses.append(response)
                        except Exception as e:
                            self.logger.error(f"Handler error: {e}", exc_info=True)
                            responses.append({"error": str(e)})
                    
                    # Set response if waiting
                    if msg.get("wait_response") and "response_future" in msg:
                        msg["response_future"].set_result(responses)
                
                # Emit event
                await self.event_emitter.emit(
                    "message",
                    topic=msg["topic"],
                    message=msg["message"]
                )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Message processing error: {e}", exc_info=True)
    
    def _find_handlers(self, topic: str) -> List[Callable]:
        """Find handlers matching topic"""
        handlers = []
        
        for pattern, pattern_handlers in self.topics.items():
            if self._match_topic(pattern, topic):
                handlers.extend(pattern_handlers)
        
        return handlers
    
    def _match_topic(self, pattern: str, topic: str) -> bool:
        """
        Match topic against pattern
        Supports wildcards: * (single level), # (multi-level)
        """
        if pattern == topic:
            return True
        
        if pattern == "#":
            return True
        
        pattern_parts = pattern.split(".")
        topic_parts = topic.split(".")
        
        if len(pattern_parts) != len(topic_parts) and "#" not in pattern:
            return False
        
        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part == "#":
                return True
            
            if i >= len(topic_parts):
                return False
            
            if pattern_part != "*" and pattern_part != topic_parts[i]:
                return False
        
        return True