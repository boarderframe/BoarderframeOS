"""
MCP-UI Framework Core
Comprehensive infrastructure for building MCP servers with UI capabilities
"""

from .base_server import MCPServer, MCPServerConfig
from .protocol import (
    MCPUIResource,
    MCPUIResponse,
    MCPUIIntent,
    MCPUIProtocol,
    ResourceType,
    IntentType
)
from .communication import (
    MessageBus,
    PostMessageHandler,
    EventEmitter,
    MessageType
)
from .security import (
    SecurityConfig,
    SecurityManager,
    TokenBudget,
    RateLimiter,
    ContentValidator
)
from .state import (
    StateManager,
    StateStore,
    StateEvent,
    StateSnapshot
)

__version__ = "1.0.0"

__all__ = [
    # Server
    "MCPServer",
    "MCPServerConfig",
    
    # Protocol
    "MCPUIResource",
    "MCPUIResponse",
    "MCPUIIntent",
    "MCPUIProtocol",
    "ResourceType",
    "IntentType",
    
    # Communication
    "MessageBus",
    "PostMessageHandler",
    "EventEmitter",
    "MessageType",
    
    # Security
    "SecurityConfig",
    "SecurityManager",
    "TokenBudget",
    "RateLimiter",
    "ContentValidator",
    
    # State
    "StateManager",
    "StateStore",
    "StateEvent",
    "StateSnapshot",
]