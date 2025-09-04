"""
Configuration management service for MCP servers
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError
import copy
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.config import (
    ConfigurationModel,
    ConfigurationStatus,
    ConfigurationType,
    ConfigurationHistoryModel
)
from app.models.mcp_server import MCPServerModel
from app.schemas.configuration import (
    ConfigurationCreate,
    ConfigurationUpdate,
    ConfigurationValidation,
    ConfigurationValidationResponse,
    ServerType,
    ServerConfigurationSchema,
    ConfigurationRollback
)
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data


logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing MCP server configurations."""
    
    def __init__(self):
        self.sensitive_fields = [
            'password', 'secret', 'token', 'key', 'credential',
            'connection_string', 'database_url', 'api_key'
        ]
        self.blocked_paths = [
            '/etc/passwd', '/etc/shadow', '/etc/sudoers',
            '/root', '/sys', '/proc', '/.ssh', '/.env'
        ]
    
    async def create_configuration(
        self,
        db: Session,
        config: ConfigurationCreate,
        user_id: int
    ) -> ConfigurationModel:
        """Create a new configuration."""
        try:
            # Validate configuration if server-specific
            if config.mcp_server_id:
                server = db.query(MCPServerModel).filter(
                    MCPServerModel.id == config.mcp_server_id
                ).first()
                if not server:
                    raise ValueError(f"Server with ID {config.mcp_server_id} not found")
                
                # Validate against server type schema
                validation_result = await self.validate_configuration(
                    ServerType.FILESYSTEM,  # Get from server config
                    config.value
                )
                if not validation_result.is_valid:
                    raise ValueError(f"Configuration validation failed: {', '.join(validation_result.errors)}")
            
            # Encrypt sensitive data
            encrypted_value = await self._encrypt_sensitive_fields(config.value)
            
            # Create configuration
            db_config = ConfigurationModel(
                name=config.name,
                key=config.key,
                config_type=config.config_type,
                mcp_server_id=config.mcp_server_id,
                user_id=config.user_id,
                environment_id=config.environment_id,
                value=encrypted_value,
                default_value=config.default_value,
                description=config.description,
                validation_schema=config.validation_schema,
                constraints=config.constraints,
                is_required=config.is_required,
                is_secret=config.is_secret,
                status=ConfigurationStatus.DRAFT,
                version=1,
                tags=config.tags,
                metadata=config.metadata,
                effective_from=config.effective_from,
                effective_until=config.effective_until,
                created_by_id=user_id
            )
            
            db.add(db_config)
            db.commit()
            db.refresh(db_config)
            
            # Add to history
            await self._add_to_history(
                db, db_config.id, "CREATE", None, encrypted_value,
                user_id, "Configuration created"
            )
            
            logger.info(f"Configuration created: {db_config.key} (ID: {db_config.id})")
            return db_config
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating configuration: {str(e)}")
            raise
    
    async def get_configuration(
        self,
        db: Session,
        config_id: int,
        decrypt: bool = False
    ) -> Optional[ConfigurationModel]:
        """Get a configuration by ID."""
        config = db.query(ConfigurationModel).filter(
            ConfigurationModel.id == config_id
        ).first()
        
        if config and decrypt and config.is_secret:
            config.value = await self._decrypt_sensitive_fields(config.value)
        
        return config
    
    async def get_server_configuration(
        self,
        db: Session,
        server_id: int,
        decrypt: bool = False
    ) -> List[ConfigurationModel]:
        """Get all configurations for a specific server."""
        configs = db.query(ConfigurationModel).filter(
            and_(
                ConfigurationModel.mcp_server_id == server_id,
                ConfigurationModel.status == ConfigurationStatus.ACTIVE
            )
        ).all()
        
        if decrypt:
            for config in configs:
                if config.is_secret:
                    config.value = await self._decrypt_sensitive_fields(config.value)
        
        return configs
    
    async def update_configuration(
        self,
        db: Session,
        config_id: int,
        update_data: ConfigurationUpdate,
        user_id: int,
        create_version: bool = True
    ) -> ConfigurationModel:
        """Update a configuration."""
        try:
            config = await self.get_configuration(db, config_id)
            if not config:
                raise ValueError(f"Configuration with ID {config_id} not found")
            
            old_value = copy.deepcopy(config.value)
            
            if create_version and config.status == ConfigurationStatus.ACTIVE:
                # Create new version
                new_version = config.create_new_version(
                    update_data.value or config.value,
                    update_data.change_reason
                )
                new_version.created_by_id = user_id
                db.add(new_version)
                
                # Deactivate current version
                config.status = ConfigurationStatus.DEPRECATED
                db.add(config)
                
                db.commit()
                db.refresh(new_version)
                
                # Add to history
                await self._add_to_history(
                    db, new_version.id, "VERSION_UPDATE", old_value,
                    new_version.value, user_id, update_data.change_reason
                )
                
                return new_version
            else:
                # Direct update
                update_dict = update_data.dict(exclude_unset=True)
                
                if 'value' in update_dict:
                    # Validate new value
                    if config.mcp_server_id:
                        validation_result = await self.validate_configuration(
                            ServerType.FILESYSTEM,  # Get from server config
                            update_dict['value']
                        )
                        if not validation_result.is_valid:
                            raise ValueError(f"Configuration validation failed: {', '.join(validation_result.errors)}")
                    
                    # Encrypt sensitive data
                    update_dict['value'] = await self._encrypt_sensitive_fields(update_dict['value'])
                
                for field, value in update_dict.items():
                    setattr(config, field, value)
                
                db.add(config)
                db.commit()
                db.refresh(config)
                
                # Add to history
                await self._add_to_history(
                    db, config.id, "UPDATE", old_value,
                    config.value, user_id, update_data.change_reason
                )
                
                return config
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating configuration: {str(e)}")
            raise
    
    async def validate_configuration(
        self,
        server_type: ServerType,
        config: Dict[str, Any]
    ) -> ConfigurationValidationResponse:
        """Validate a configuration against its schema."""
        errors = []
        warnings = []
        sanitized_config = copy.deepcopy(config)
        
        try:
            # Get schema for server type
            schema = ServerConfigurationSchema.get_schema_for_type(server_type)
            
            # Validate against JSON schema
            validate(instance=config, schema=schema)
            
            # Additional validation based on server type
            if server_type == ServerType.FILESYSTEM:
                errors.extend(await self._validate_filesystem_config(config))
                sanitized_config = await self._sanitize_filesystem_config(config)
            elif server_type == ServerType.DATABASE:
                errors.extend(await self._validate_database_config(config))
                sanitized_config = await self._sanitize_database_config(config)
            elif server_type == ServerType.API:
                errors.extend(await self._validate_api_config(config))
                sanitized_config = await self._sanitize_api_config(config)
            
            # Check for security issues
            security_issues = await self._check_security_issues(config)
            if security_issues:
                warnings.extend(security_issues)
            
            is_valid = len(errors) == 0
            
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            is_valid = False
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            is_valid = False
        
        return ConfigurationValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_config=sanitized_config if is_valid else None
        )
    
    async def _validate_filesystem_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate filesystem-specific configuration."""
        errors = []
        
        # Check allowed directories
        allowed_dirs = config.get('allowed_directories', [])
        for dir_path in allowed_dirs:
            # Check for path traversal attempts
            if '..' in dir_path:
                errors.append(f"Path traversal detected in: {dir_path}")
            
            # Check against blocked paths
            for blocked in self.blocked_paths:
                if dir_path.startswith(blocked):
                    errors.append(f"Blocked path detected: {dir_path}")
            
            # Validate path exists
            path = Path(dir_path)
            if not path.exists():
                errors.append(f"Directory does not exist: {dir_path}")
            elif not path.is_dir():
                errors.append(f"Path is not a directory: {dir_path}")
        
        # Validate permissions
        permissions = config.get('permissions', {})
        if not any(permissions.values()):
            errors.append("At least one permission must be enabled")
        
        # Check file size limit
        file_size = config.get('file_size_limit_mb', 100)
        if file_size > 1000:
            errors.append("File size limit exceeds maximum (1000 MB)")
        
        return errors
    
    async def _validate_database_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate database-specific configuration."""
        errors = []
        
        # Check connection string format
        conn_str = config.get('connection_string', '')
        if not conn_str:
            errors.append("Connection string is required")
        elif 'password' in conn_str and not config.get('is_encrypted'):
            errors.append("Connection string contains unencrypted password")
        
        # Validate allowed operations
        allowed_ops = config.get('allowed_operations', [])
        if 'DROP' in allowed_ops and 'CREATE' not in allowed_ops:
            errors.append("DROP operation requires CREATE permission")
        
        # Check pool size
        pool_size = config.get('pool_size', 10)
        db_type = config.get('database_type', '')
        if db_type == 'sqlite' and pool_size > 1:
            errors.append("SQLite does not support connection pooling")
        
        return errors
    
    async def _validate_api_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate API-specific configuration."""
        errors = []
        
        # Validate base URL
        base_url = config.get('base_url', '')
        if not base_url.startswith(('http://', 'https://')):
            errors.append("Base URL must start with http:// or https://")
        
        # Check auth configuration
        auth_type = config.get('auth_type', 'none')
        auth_config = config.get('auth_config', {})
        
        if auth_type != 'none' and not auth_config:
            errors.append(f"Auth configuration required for {auth_type}")
        
        if auth_type == 'api_key' and 'key' not in auth_config:
            errors.append("API key required for api_key auth type")
        
        # Validate rate limits
        rate_limits = config.get('rate_limits', {})
        if rate_limits:
            rpm = rate_limits.get('requests_per_minute', 60)
            if rpm > 1000:
                errors.append("Rate limit exceeds maximum (1000 rpm)")
        
        return errors
    
    async def _sanitize_filesystem_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize filesystem configuration."""
        sanitized = copy.deepcopy(config)
        
        # Normalize paths
        if 'allowed_directories' in sanitized:
            sanitized['allowed_directories'] = [
                str(Path(p).resolve()) for p in sanitized['allowed_directories']
            ]
        
        # Set secure defaults
        if 'permissions' not in sanitized:
            sanitized['permissions'] = {
                'read': True,
                'write': False,
                'delete': False,
                'execute': False
            }
        
        return sanitized
    
    async def _sanitize_database_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize database configuration."""
        sanitized = copy.deepcopy(config)
        
        # Remove sensitive data from logs
        if 'connection_string' in sanitized:
            # Mark for encryption
            sanitized['_requires_encryption'] = True
        
        # Set secure defaults
        if 'timeout_seconds' not in sanitized:
            sanitized['timeout_seconds'] = 30
        
        if 'query_limits' not in sanitized:
            sanitized['query_limits'] = {
                'max_rows': 10000,
                'max_execution_time_ms': 30000
            }
        
        return sanitized
    
    async def _sanitize_api_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize API configuration."""
        sanitized = copy.deepcopy(config)
        
        # Ensure HTTPS for production
        if 'base_url' in sanitized:
            url = sanitized['base_url']
            if url.startswith('http://') and 'localhost' not in url:
                sanitized['base_url'] = url.replace('http://', 'https://')
        
        # Set secure defaults
        if 'timeout_seconds' not in sanitized:
            sanitized['timeout_seconds'] = 30
        
        if 'retry_config' not in sanitized:
            sanitized['retry_config'] = {
                'max_retries': 3,
                'retry_delay_ms': 1000
            }
        
        return sanitized
    
    async def _check_security_issues(self, config: Dict[str, Any]) -> List[str]:
        """Check for potential security issues in configuration."""
        warnings = []
        
        def check_dict(d: dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check for sensitive data in non-encrypted fields
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    if isinstance(value, str) and value and not value.startswith('encrypted:'):
                        warnings.append(f"Potential sensitive data in {current_path}")
                
                # Check for overly permissive settings
                if key == 'permissions' and isinstance(value, dict):
                    if value.get('execute') and value.get('write'):
                        warnings.append("Write + Execute permissions can be dangerous")
                
                # Recursively check nested dictionaries
                if isinstance(value, dict):
                    check_dict(value, current_path)
        
        check_dict(config)
        return warnings
    
    async def _encrypt_sensitive_fields(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in configuration."""
        encrypted = copy.deepcopy(config)
        
        def encrypt_dict(d: dict):
            for key, value in d.items():
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    if isinstance(value, str) and value:
                        # In production, use proper encryption
                        d[key] = f"encrypted:{value}"  # Placeholder
                elif isinstance(value, dict):
                    encrypt_dict(value)
        
        encrypt_dict(encrypted)
        return encrypted
    
    async def _decrypt_sensitive_fields(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in configuration."""
        decrypted = copy.deepcopy(config)
        
        def decrypt_dict(d: dict):
            for key, value in d.items():
                if isinstance(value, str) and value.startswith('encrypted:'):
                    # In production, use proper decryption
                    d[key] = value.replace('encrypted:', '')  # Placeholder
                elif isinstance(value, dict):
                    decrypt_dict(value)
        
        decrypt_dict(decrypted)
        return decrypted
    
    async def _add_to_history(
        self,
        db: Session,
        config_id: int,
        action: str,
        old_value: Optional[Dict[str, Any]],
        new_value: Optional[Dict[str, Any]],
        user_id: int,
        reason: Optional[str] = None
    ):
        """Add configuration change to history."""
        history = ConfigurationHistoryModel(
            configuration_id=config_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            changed_by_id=user_id,
            change_reason=reason,
            change_summary=f"{action} configuration {config_id}"
        )
        db.add(history)
        db.commit()
    
    async def apply_configuration(
        self,
        db: Session,
        server_id: int,
        config_id: int,
        restart_required: bool = False
    ) -> bool:
        """Apply a configuration to a running server."""
        try:
            # Get the configuration
            config = await self.get_configuration(db, config_id, decrypt=True)
            if not config:
                raise ValueError(f"Configuration {config_id} not found")
            
            # Get the server
            server = db.query(MCPServerModel).filter(
                MCPServerModel.id == server_id
            ).first()
            if not server:
                raise ValueError(f"Server {server_id} not found")
            
            # Update server configuration
            server.config = config.value
            db.add(server)
            
            # Activate the configuration
            config.status = ConfigurationStatus.ACTIVE
            db.add(config)
            
            db.commit()
            
            # Restart server if required
            if restart_required:
                # Import here to avoid circular dependency
                from app.services.process_manager import process_manager
                await process_manager.restart_server(str(server_id))
            
            logger.info(f"Configuration {config_id} applied to server {server_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error applying configuration: {str(e)}")
            return False
    
    async def rollback_configuration(
        self,
        db: Session,
        rollback_data: ConfigurationRollback,
        user_id: int
    ) -> ConfigurationModel:
        """Rollback a configuration to a previous version."""
        try:
            # Get the target version
            target_config = db.query(ConfigurationModel).filter(
                and_(
                    ConfigurationModel.id == rollback_data.configuration_id,
                    ConfigurationModel.version == rollback_data.target_version
                )
            ).first()
            
            if not target_config:
                raise ValueError(f"Target version {rollback_data.target_version} not found")
            
            # Create new version with old values
            new_config = target_config.create_new_version(
                target_config.value,
                f"Rollback to version {rollback_data.target_version}: {rollback_data.reason}"
            )
            new_config.created_by_id = user_id
            new_config.status = ConfigurationStatus.ACTIVE
            
            # Deactivate current active version
            current_active = db.query(ConfigurationModel).filter(
                and_(
                    ConfigurationModel.key == target_config.key,
                    ConfigurationModel.mcp_server_id == target_config.mcp_server_id,
                    ConfigurationModel.status == ConfigurationStatus.ACTIVE
                )
            ).first()
            
            if current_active:
                current_active.status = ConfigurationStatus.DEPRECATED
                db.add(current_active)
            
            db.add(new_config)
            db.commit()
            db.refresh(new_config)
            
            # Add to history
            await self._add_to_history(
                db, new_config.id, "ROLLBACK",
                current_active.value if current_active else None,
                new_config.value, user_id, rollback_data.reason
            )
            
            logger.info(f"Configuration rolled back to version {rollback_data.target_version}")
            return new_config
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error rolling back configuration: {str(e)}")
            raise


# Create singleton instance
configuration_service = ConfigurationService()