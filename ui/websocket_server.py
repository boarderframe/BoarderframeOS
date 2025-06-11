"""
WebSocket Server for BoarderframeOS UI
Provides real-time updates to the web interface
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set

import websockets

from ..core.base_agent import AgentState
from ..core.message_bus import AgentMessage, MessageType, message_bus

logger = logging.getLogger("websocket_server")


@dataclass
class UIEvent:
    """Event to be sent to UI clients"""

    event_type: str
    data: Dict
    timestamp: str = None
    id: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class WebSocketServer:
    """WebSocket server for real-time UI updates"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.agent_states: Dict[str, Dict] = {}
        self.solomon_conversations: List[Dict] = []
        self.system_metrics: Dict = {}
        self.server_id = "websocket_server"

    async def start(self):
        """Start the WebSocket server"""
        # Subscribe to message bus
        await message_bus.subscribe(self.server_id, self._handle_message_bus_event)

        # Start background tasks
        asyncio.create_task(self._broadcast_heartbeat())
        asyncio.create_task(self._collect_system_metrics())

        # Start WebSocket server
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        await websockets.serve(self.handle_client, self.host, self.port)

    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connections"""
        self.clients.add(websocket)
        logger.info(f"New client connected from {websocket.remote_address}")

        try:
            # Send initial state
            await self._send_initial_state(websocket)

            # Handle incoming messages
            async for message in websocket:
                await self._handle_client_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.remove(websocket)

    async def _send_initial_state(self, websocket):
        """Send initial system state to new client"""
        initial_event = UIEvent(
            event_type="initial_state",
            data={
                "agent_states": self.agent_states,
                "solomon_conversations": self.solomon_conversations[
                    -50:
                ],  # Last 50 messages
                "system_metrics": self.system_metrics,
            },
        )
        await websocket.send(initial_event.to_json())

    async def _handle_client_message(self, websocket, message):
        """Handle messages from UI clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "solomon_message":
                # Forward message to Solomon
                await self._forward_to_solomon(data.get("content"), websocket)

            elif message_type == "control_command":
                # Handle agent control commands
                await self._handle_control_command(data, websocket)

            elif message_type == "request_update":
                # Send current state
                await self._send_initial_state(websocket)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def _forward_to_solomon(self, content: str, websocket):
        """Forward user message to Solomon"""
        # Create message for Solomon
        solomon_message = AgentMessage(
            from_agent="user",
            to_agent="solomon",
            message_type=MessageType.TASK_REQUEST,
            data={
                "task_type": "conversation",
                "message": content,
                "channel": "web_ui",
                "session_id": str(websocket.remote_address),
            },
        )

        # Send via message bus
        await message_bus.send_direct(solomon_message)

        # Add to conversation history
        self.solomon_conversations.append(
            {
                "role": "user",
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Broadcast update
        await self.broadcast_event(
            UIEvent(
                event_type="solomon_conversation",
                data={"role": "user", "content": content},
            )
        )

    async def _handle_control_command(self, data: Dict, websocket):
        """Handle agent control commands from UI"""
        command = data.get("command")
        agent_id = data.get("agent_id")

        control_message = AgentMessage(
            from_agent="ui_control",
            to_agent="orchestrator",
            message_type=MessageType.CONTROL,
            data={
                "command": command,
                "agent_id": agent_id,
                "params": data.get("params", {}),
            },
        )

        await message_bus.send_direct(control_message)

    async def _handle_message_bus_event(self, message: AgentMessage):
        """Handle events from the message bus"""
        try:
            # Agent state updates
            if message.message_type == MessageType.STATUS_UPDATE:
                await self._handle_agent_status_update(message)

            # Solomon responses
            elif (
                message.from_agent == "solomon"
                and message.message_type == MessageType.TASK_RESPONSE
            ):
                await self._handle_solomon_response(message)

            # Agent lifecycle events
            elif message.message_type == MessageType.LIFECYCLE:
                await self._handle_lifecycle_event(message)

            # Performance metrics
            elif message.message_type == MessageType.METRICS:
                await self._handle_metrics_update(message)

        except Exception as e:
            logger.error(f"Error handling message bus event: {e}")

    async def _handle_agent_status_update(self, message: AgentMessage):
        """Handle agent status updates"""
        agent_id = message.from_agent
        status_data = message.data

        if agent_id not in self.agent_states:
            self.agent_states[agent_id] = {}

        self.agent_states[agent_id].update(
            {
                "status": status_data.get("status", "unknown"),
                "state": status_data.get("state", AgentState.IDLE.value),
                "last_update": datetime.now().isoformat(),
                "metrics": status_data.get("metrics", {}),
            }
        )

        # Broadcast update
        await self.broadcast_event(
            UIEvent(
                event_type="agent_status_update",
                data={"agent_id": agent_id, "status": self.agent_states[agent_id]},
            )
        )

    async def _handle_solomon_response(self, message: AgentMessage):
        """Handle Solomon's responses"""
        response_content = message.data.get("response", "")

        # Add to conversation history
        self.solomon_conversations.append(
            {
                "role": "solomon",
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Broadcast to UI
        await self.broadcast_event(
            UIEvent(
                event_type="solomon_conversation",
                data={"role": "solomon", "content": response_content},
            )
        )

    async def _handle_lifecycle_event(self, message: AgentMessage):
        """Handle agent lifecycle events (birth, evolution, death)"""
        event_data = message.data
        lifecycle_type = event_data.get("lifecycle_type")

        event_mapping = {
            "agent_created": "agent_birth",
            "agent_evolved": "agent_evolution",
            "agent_terminated": "agent_death",
            "agent_started": "agent_awakening",
        }

        ui_event_type = event_mapping.get(lifecycle_type, "agent_lifecycle")

        await self.broadcast_event(UIEvent(event_type=ui_event_type, data=event_data))

    async def _handle_metrics_update(self, message: AgentMessage):
        """Handle system metrics updates"""
        metrics = message.data
        self.system_metrics.update(metrics)

        await self.broadcast_event(UIEvent(event_type="metrics_update", data=metrics))

    async def broadcast_event(self, event: UIEvent):
        """Broadcast event to all connected clients"""
        if self.clients:
            message = event.to_json()
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True,
            )

    async def _broadcast_heartbeat(self):
        """Send periodic heartbeat to keep connections alive"""
        while True:
            try:
                await self.broadcast_event(
                    UIEvent(
                        event_type="heartbeat",
                        data={"server_time": datetime.now().isoformat()},
                    )
                )
                await asyncio.sleep(30)  # Every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self):
        """Collect and broadcast system metrics"""
        while True:
            try:
                # Request metrics from orchestrator
                metrics_request = AgentMessage(
                    from_agent=self.server_id,
                    to_agent="orchestrator",
                    message_type=MessageType.INFO_REQUEST,
                    data={"request": "system_status"},
                )
                await message_bus.send_direct(metrics_request)

                await asyncio.sleep(5)  # Every 5 seconds
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10)


# Global WebSocket server instance
ws_server = WebSocketServer()

# Export
__all__ = ["WebSocketServer", "ws_server", "UIEvent"]
