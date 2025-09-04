"""
Configuration management schemas for MCP servers
"""
from datetime import datetime
from typing import Dict, Optional, Any, List
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
import json


class ConfigurationType(str, Enum):
    """Types of configuration."""
    SYSTEM = "SYSTEM"
    SERVER = "SERVER"
    USER = "USER"
    ENVIRONMENT = "ENVIRONMENT"
    SECURITY = "SECURITY"
    LOGGING = "LOGGING"
    MONITORING = "MONITORING"


class ConfigurationStatus(str, Enum):
    """Status of configuration."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class ServerType(str, Enum):
    """MCP Server types with different configuration schemas."""
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"


# JSON Schema definitions for different server types
FILESYSTEM_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "allowed_directories": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of directories the server can access"
        },
        "blocked_paths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Paths that should be blocked from access"
        },
        "file_size_limit_mb": {
            "type": "integer",
            "minimum": 1,
            "maximum": 1000,
            "description": "Maximum file size in MB"
        },
        "max_directory_depth": {
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
            "description": "Maximum depth for directory traversal"
        },
        "permissions": {
            "type": "object",
            "properties": {
                "read": {"type": "boolean"},
                "write": {"type": "boolean"},
                "delete": {"type": "boolean"},
                "execute": {"type": "boolean"}
            }
        },
        "file_type_filters": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Allowed file extensions (e.g., ['.txt', '.json'])"
        }
    },
    "required": ["allowed_directories", "permissions"]
}

DATABASE_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "connection_string": {
            "type": "string",
            "description": "Database connection string (encrypted)"
        },
        "database_type": {
            "type": "string",
            "enum": ["postgresql", "mysql", "sqlite", "mongodb"],
            "description": "Type of database"
        },
        "pool_size": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Connection pool size"
        },
        "timeout_seconds": {
            "type": "integer",
            "minimum": 1,
            "maximum": 300,
            "description": "Query timeout in seconds"
        },
        "allowed_operations": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"]
            }
        },
        "allowed_tables": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tables the server can access"
        },
        "query_limits": {
            "type": "object",
            "properties": {
                "max_rows": {"type": "integer", "minimum": 1},
                "max_execution_time_ms": {"type": "integer", "minimum": 100}
            }
        }
    },
    "required": ["connection_string", "database_type", "allowed_operations"]
}

API_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "base_url": {
            "type": "string",
            "format": "uri",
            "description": "Base URL for the API"
        },
        "auth_type": {
            "type": "string",
            "enum": ["none", "api_key", "oauth2", "jwt", "basic"],
            "description": "Authentication type"
        },
        "auth_config": {
            "type": "object",
            "description": "Authentication configuration (encrypted)"
        },
        "allowed_endpoints": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Allowed API endpoints"
        },
        "rate_limits": {
            "type": "object",
            "properties": {
                "requests_per_minute": {"type": "integer", "minimum": 1},
                "concurrent_requests": {"type": "integer", "minimum": 1}
            }
        },
        "timeout_seconds": {
            "type": "integer",
            "minimum": 1,
            "maximum": 300
        },
        "retry_config": {
            "type": "object",
            "properties": {
                "max_retries": {"type": "integer", "minimum": 0, "maximum": 10},
                "retry_delay_ms": {"type": "integer", "minimum": 100}
            }
        },
        "headers": {
            "type": "object",
            "description": "Default headers to include in requests"
        }
    },
    "required": ["base_url", "auth_type"]
}


class ConfigurationBase(BaseModel):
    """Base configuration schema."""
    name: str = Field(..., min_length=1, max_length=255)
    key: str = Field(..., min_length=1, max_length=255, regex="^[a-zA-Z0-9_.-]+$")
    config_type: ConfigurationType
    value: Dict[str, Any]
    default_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    validation_schema: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    is_required: bool = False
    is_secret: bool = False
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}


class ConfigurationCreate(ConfigurationBase):
    """Schema for creating configuration."""
    mcp_server_id: Optional[int] = None
    user_id: Optional[int] = None
    environment_id: Optional[int] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    
    @root_validator
    def validate_scope(cls, values):
        """Ensure configuration has proper scope."""
        server_id = values.get('mcp_server_id')
        user_id = values.get('user_id')
        
        # At least one scope should be defined for non-system configs
        config_type = values.get('config_type')
        if config_type != ConfigurationType.SYSTEM:
            if not server_id and not user_id:
                raise ValueError('Configuration must be scoped to either a server or user')
        
        return values


class ConfigurationUpdate(BaseModel):
    """Schema for updating configuration."""
    value: Optional[Dict[str, Any]] = None
    default_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    validation_schema: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    is_required: Optional[bool] = None
    is_secret: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    change_reason: Optional[str] = None


class Configuration(ConfigurationBase):
    """Schema for configuration response."""
    id: int
    mcp_server_id: Optional[int] = None
    user_id: Optional[int] = None
    environment_id: Optional[int] = None
    status: ConfigurationStatus
    version: int
    parent_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by_id: int
    
    class Config:
        orm_mode = True


class ConfigurationValidation(BaseModel):
    """Schema for configuration validation request."""
    server_type: ServerType
    config: Dict[str, Any]
    
    @validator('config')
    def validate_config_not_empty(cls, v):
        if not v:
            raise ValueError('Configuration cannot be empty')
        return v


class ConfigurationValidationResponse(BaseModel):
    """Schema for configuration validation response."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    sanitized_config: Optional[Dict[str, Any]] = None


class ServerConfigurationSchema(BaseModel):
    """Schema for server-specific configuration."""
    server_type: ServerType
    schema: Dict[str, Any]
    example: Dict[str, Any]
    description: str
    
    @classmethod
    def get_schema_for_type(cls, server_type: ServerType) -> Dict[str, Any]:
        """Get JSON schema for a specific server type."""
        schemas = {
            ServerType.FILESYSTEM: FILESYSTEM_CONFIG_SCHEMA,
            ServerType.DATABASE: DATABASE_CONFIG_SCHEMA,
            ServerType.API: API_CONFIG_SCHEMA,
            ServerType.CUSTOM: {"type": "object", "additionalProperties": True}
        }
        return schemas.get(server_type, schemas[ServerType.CUSTOM])


class ConfigurationHistory(BaseModel):
    """Schema for configuration history."""
    id: int
    configuration_id: int
    action: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None
    changed_by_id: int
    change_reason: Optional[str] = None
    changed_at: datetime
    
    class Config:
        orm_mode = True


class ConfigurationBackup(BaseModel):
    """Schema for configuration backup/restore."""
    configurations: List[Configuration]
    timestamp: datetime
    description: Optional[str] = None
    created_by: str
    
    
class ConfigurationRollback(BaseModel):
    """Schema for configuration rollback request."""
    configuration_id: int
    target_version: int
    reason: str