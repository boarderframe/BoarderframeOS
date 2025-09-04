"""
MCP Server schemas
"""
from datetime import datetime
from typing import Dict, Optional, Any, List
from enum import Enum

from pydantic import BaseModel, validator


class MCPServerStatus(str, Enum):
    """MCP Server status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class MCPServerBase(BaseModel):
    """Base MCP Server schema."""
    name: str
    description: Optional[str] = None
    host: str = "localhost"
    port: int
    protocol: str = "stdio"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    config: Optional[Dict[str, Any]] = None
    
    @validator('port')
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class MCPServerCreate(MCPServerBase):
    """Schema for creating MCP server."""
    pass


class MCPServerUpdate(BaseModel):
    """Schema for updating MCP server."""
    name: Optional[str] = None
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    config: Optional[Dict[str, Any]] = None
    
    @validator('port')
    def validate_port(cls, v):
        if v is not None and not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class MCPServer(MCPServerBase):
    """Schema for MCP server response."""
    id: int
    status: MCPServerStatus
    created_at: datetime
    updated_at: datetime
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True


class MCPServerHealth(BaseModel):
    """Schema for MCP server health status."""
    server_id: int
    status: MCPServerStatus
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    last_check: datetime


class ProcessMetrics(BaseModel):
    """Schema for process metrics."""
    pid: int
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float
    status: str
    num_threads: int
    num_fds: int


class MCPServerWithMetrics(MCPServer):
    """Schema for MCP server response with real-time metrics."""
    server_id: Optional[str] = None  # The actual string ID used by the system
    working_directory: Optional[str] = None  # The working directory for the server
    process_id: Optional[int] = None
    metrics: Optional[ProcessMetrics] = None
    restart_count: int = 0
    start_time: Optional[datetime] = None
    last_error: Optional[str] = None


class MCPServerControl(BaseModel):
    """Schema for server control operations."""
    action: str  # start, stop, restart
    timeout: Optional[float] = 30.0
    force: Optional[bool] = False


class MCPServerControlResponse(BaseModel):
    """Schema for server control operation response."""
    server_id: str
    action: str
    success: bool
    message: str
    process_id: Optional[int] = None
    timestamp: datetime