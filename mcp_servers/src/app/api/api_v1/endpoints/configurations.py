"""
Configuration management API endpoints
"""
import logging
import json
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple file-based configuration storage for now
CONFIG_DIR = Path("config/servers")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def get_config_file(server_id: str) -> Path:
    """Get the configuration file path for a server."""
    return CONFIG_DIR / f"{server_id}.json"

def load_server_config(server_id: str) -> Dict[str, Any]:
    """Load server configuration from file."""
    config_file = get_config_file(server_id)
    if not config_file.exists():
        # Return default configuration
        return {
            "general": {
                "name": f"Server {server_id}",
                "description": "",
                "enabled": True,
                "server_type": "filesystem",
                "protocol": "stdio"
            },
            "command": {
                "executable": "python",
                "arguments": [],
                "working_directory": ""
            },
            "environment": {},
            "filesystem": {
                "allowed_directories": [],
                "blocked_directories": [],
                "read_only": False,
                "file_size_limit_mb": 100
            },
            "security": {
                "rate_limit_enabled": True,
                "requests_per_minute": 60,
                "max_token_budget": 10000,
                "blocked_commands": ["rm", "sudo", "chmod"]
            },
            "advanced": {
                "timeout_seconds": 30,
                "max_retries": 3,
                "log_level": "info"
            }
        }
    
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config for {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {str(e)}"
        )

def save_server_config(server_id: str, config: Dict[str, Any]) -> None:
    """Save server configuration to file."""
    config_file = get_config_file(server_id)
    
    # Add metadata
    config["_metadata"] = {
        "last_updated": datetime.now().isoformat(),
        "version": config.get("_metadata", {}).get("version", 0) + 1
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config for {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}"
        )

@router.get("/servers/{server_id}/config")
async def get_server_configuration(server_id: str) -> Dict[str, Any]:
    """Get configuration for a specific server."""
    try:
        config = load_server_config(server_id)
        return {
            "server_id": server_id,
            "config": config,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting config for {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration not found for server {server_id}"
        )

@router.put("/servers/{server_id}/config")
async def update_server_configuration(
    server_id: str, 
    config_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Update configuration for a specific server."""
    try:
        # Validate the configuration structure
        required_sections = ["general", "command", "environment", "filesystem", "security", "advanced"]
        for section in required_sections:
            if section not in config_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required configuration section: {section}"
                )
        
        # Save the configuration
        save_server_config(server_id, config_data)
        
        return {
            "server_id": server_id,
            "message": "Configuration updated successfully",
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config for {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.post("/servers/{server_id}/config/validate")
async def validate_server_configuration(
    server_id: str,
    config_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate a server configuration without saving it."""
    errors = []
    warnings = []
    
    try:
        # Basic validation
        if not config_data.get("general", {}).get("name"):
            errors.append("Server name is required")
        
        if not config_data.get("command", {}).get("executable"):
            errors.append("Executable command is required")
        
        # Filesystem validation
        fs_config = config_data.get("filesystem", {})
        allowed_dirs = fs_config.get("allowed_directories", [])
        blocked_dirs = fs_config.get("blocked_directories", [])
        
        for directory in allowed_dirs:
            if not os.path.exists(directory):
                warnings.append(f"Allowed directory does not exist: {directory}")
        
        # Security validation
        security_config = config_data.get("security", {})
        rate_limit = security_config.get("requests_per_minute", 60)
        if rate_limit > 1000:
            warnings.append("High rate limit may impact performance")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "server_id": server_id
        }
        
    except Exception as e:
        logger.error(f"Error validating config for {server_id}: {e}")
        return {
            "valid": False,
            "errors": [f"Validation failed: {str(e)}"],
            "warnings": warnings,
            "server_id": server_id
        }

@router.get("/servers/{server_id}/config/schema")
async def get_server_configuration_schema(server_id: str) -> Dict[str, Any]:
    """Get the configuration schema for a server type."""
    # Return a JSON schema for the configuration
    return {
        "type": "object",
        "required": ["general", "command", "environment", "filesystem", "security", "advanced"],
        "properties": {
            "general": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "description": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "server_type": {"type": "string", "enum": ["filesystem", "database", "http", "custom"]},
                    "protocol": {"type": "string", "enum": ["stdio", "http", "tcp"]}
                },
                "required": ["name", "server_type", "protocol"]
            },
            "command": {
                "type": "object",
                "properties": {
                    "executable": {"type": "string", "minLength": 1},
                    "arguments": {"type": "array", "items": {"type": "string"}},
                    "working_directory": {"type": "string"}
                },
                "required": ["executable"]
            },
            "environment": {
                "type": "object",
                "additionalProperties": {"type": "string"}
            },
            "filesystem": {
                "type": "object",
                "properties": {
                    "allowed_directories": {"type": "array", "items": {"type": "string"}},
                    "blocked_directories": {"type": "array", "items": {"type": "string"}},
                    "read_only": {"type": "boolean"},
                    "file_size_limit_mb": {"type": "number", "minimum": 1, "maximum": 1000}
                }
            },
            "security": {
                "type": "object",
                "properties": {
                    "rate_limit_enabled": {"type": "boolean"},
                    "requests_per_minute": {"type": "number", "minimum": 1, "maximum": 10000},
                    "max_token_budget": {"type": "number", "minimum": 100},
                    "blocked_commands": {"type": "array", "items": {"type": "string"}}
                }
            },
            "advanced": {
                "type": "object",
                "properties": {
                    "timeout_seconds": {"type": "number", "minimum": 1, "maximum": 300},
                    "max_retries": {"type": "number", "minimum": 0, "maximum": 10},
                    "log_level": {"type": "string", "enum": ["debug", "info", "warning", "error"]}
                }
            }
        }
    }