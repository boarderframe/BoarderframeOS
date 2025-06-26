"""
Hot Reload Configuration Management
Dynamic configuration reloading without service restart
"""

import asyncio
import json
import yaml
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime
import logging
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)


@dataclass 
class ConfigVersion:
    """Track configuration versions"""
    file_path: str
    version: int
    checksum: str
    last_modified: datetime
    applied_at: Optional[datetime] = None
    rollback_data: Optional[Dict[str, Any]] = None


class ConfigFileHandler(FileSystemEventHandler):
    """Handle configuration file changes"""
    
    def __init__(self, config_manager: 'HotReloadConfigManager'):
        self.config_manager = config_manager
        self._pending_reloads = set()
        
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a config file
        if file_path.suffix in ['.json', '.yaml', '.yml', '.env']:
            logger.info(f"Config file modified: {file_path}")
            
            # Debounce rapid changes
            if str(file_path) not in self._pending_reloads:
                self._pending_reloads.add(str(file_path))
                asyncio.create_task(self._handle_reload(file_path))
                
    async def _handle_reload(self, file_path: Path):
        """Handle configuration reload with debouncing"""
        try:
            # Wait a bit for any rapid successive changes
            await asyncio.sleep(0.5)
            
            # Remove from pending
            self._pending_reloads.discard(str(file_path))
            
            # Trigger reload
            await self.config_manager.reload_config(str(file_path))
            
        except Exception as e:
            logger.error(f"Failed to reload config {file_path}: {e}")


class HotReloadConfigManager:
    """
    Manages hot reloading of configuration files
    
    Features:
    - Watch configuration files for changes
    - Validate before applying
    - Rollback on failure
    - Version tracking
    - Change notifications
    """
    
    def __init__(self):
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.config_versions: Dict[str, ConfigVersion] = {}
        self.validators: Dict[str, Callable] = {}
        self.change_callbacks: Dict[str, List[Callable]] = {}
        self.watched_files: List[str] = []
        self._observer = None
        self._config_cache: Dict[str, Any] = {}
        
    async def start(self):
        """Start configuration file watching"""
        logger.info("Starting hot reload config manager")
        
        # Set up file watcher
        self._observer = Observer()
        handler = ConfigFileHandler(self)
        
        # Watch config directories
        config_dirs = ["configs/", ".", "settings/"]
        
        for config_dir in config_dirs:
            if Path(config_dir).exists():
                self._observer.schedule(handler, config_dir, recursive=True)
                logger.info(f"Watching config directory: {config_dir}")
                
        self._observer.start()
        
        # Load initial configurations
        await self._load_initial_configs()
        
    async def stop(self):
        """Stop configuration file watching"""
        logger.info("Stopping hot reload config manager")
        
        if self._observer:
            self._observer.stop()
            self._observer.join()
            
    async def _load_initial_configs(self):
        """Load initial configuration files"""
        config_patterns = [
            "boarderframe.yaml",
            "configs/**/*.json",
            "configs/**/*.yaml",
            "settings.json",
            ".env"
        ]
        
        for pattern in config_patterns:
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    await self.load_config(str(file_path))
                    
    async def load_config(self, file_path: str) -> bool:
        """Load a configuration file"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.error(f"Config file not found: {file_path}")
                return False
                
            # Read file content
            content = path.read_text()
            
            # Parse based on file type
            if path.suffix == '.json':
                config_data = json.loads(content)
            elif path.suffix in ['.yaml', '.yml']:
                config_data = yaml.safe_load(content)
            elif path.suffix == '.env' or path.name == '.env':
                config_data = self._parse_env_file(content)
            else:
                logger.warning(f"Unknown config file type: {file_path}")
                return False
                
            # Store configuration
            self.configs[file_path] = config_data
            self._update_cache(file_path, config_data)
            
            # Track version
            import hashlib
            checksum = hashlib.md5(content.encode()).hexdigest()
            
            if file_path in self.config_versions:
                version = self.config_versions[file_path]
                version.version += 1
                version.checksum = checksum
                version.last_modified = datetime.now()
            else:
                self.config_versions[file_path] = ConfigVersion(
                    file_path=file_path,
                    version=1,
                    checksum=checksum,
                    last_modified=datetime.now()
                )
                
            # Add to watched files
            if file_path not in self.watched_files:
                self.watched_files.append(file_path)
                
            logger.info(f"Loaded config: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config {file_path}: {e}")
            return False
            
    async def reload_config(self, file_path: str) -> bool:
        """Reload a configuration file with validation"""
        logger.info(f"Reloading config: {file_path}")
        
        try:
            # Save current config for rollback
            current_config = self.configs.get(file_path, {}).copy()
            current_version = self.config_versions.get(file_path)
            
            # Load new configuration
            success = await self.load_config(file_path)
            
            if not success:
                return False
                
            # Get new config
            new_config = self.configs[file_path]
            
            # Validate if validator exists
            if file_path in self.validators:
                validator = self.validators[file_path]
                
                try:
                    is_valid = await self._run_validator(validator, new_config)
                    
                    if not is_valid:
                        logger.error(f"Validation failed for {file_path}, rolling back")
                        self.configs[file_path] = current_config
                        self.config_versions[file_path] = current_version
                        return False
                        
                except Exception as e:
                    logger.error(f"Validator error for {file_path}: {e}, rolling back")
                    self.configs[file_path] = current_config
                    self.config_versions[file_path] = current_version
                    return False
                    
            # Store rollback data
            if file_path in self.config_versions:
                self.config_versions[file_path].rollback_data = current_config
                self.config_versions[file_path].applied_at = datetime.now()
                
            # Notify callbacks
            await self._notify_change_callbacks(file_path, new_config)
            
            logger.info(f"Successfully reloaded config: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload config {file_path}: {e}")
            return False
            
    def _parse_env_file(self, content: str) -> Dict[str, str]:
        """Parse .env file format"""
        config = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                    
                config[key] = value
                
        return config
        
    def _update_cache(self, file_path: str, config_data: Dict[str, Any]):
        """Update configuration cache"""
        # Flatten nested configs into cache
        if isinstance(config_data, dict):
            for key, value in config_data.items():
                cache_key = f"{file_path}:{key}"
                self._config_cache[cache_key] = value
                
                # Also store by just key for convenience
                self._config_cache[key] = value
                
    async def _run_validator(self, validator: Callable, config: Dict[str, Any]) -> bool:
        """Run configuration validator"""
        if asyncio.iscoroutinefunction(validator):
            return await validator(config)
        else:
            return validator(config)
            
    async def _notify_change_callbacks(self, file_path: str, new_config: Dict[str, Any]):
        """Notify registered callbacks of config changes"""
        callbacks = self.change_callbacks.get(file_path, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(file_path, new_config)
                else:
                    callback(file_path, new_config)
            except Exception as e:
                logger.error(f"Config change callback error: {e}")
                
    def register_validator(self, file_path: str, validator: Callable):
        """Register a validator for a config file"""
        self.validators[file_path] = validator
        
    def register_change_callback(self, file_path: str, callback: Callable):
        """Register a callback for config changes"""
        if file_path not in self.change_callbacks:
            self.change_callbacks[file_path] = []
        self.change_callbacks[file_path].append(callback)
        
    def get_config(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a file"""
        return self.configs.get(file_path)
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self._config_cache.get(key, default)
        
    def get_nested(self, path: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation"""
        # Example: get_nested("database.host") 
        parts = path.split('.')
        
        # Try direct cache lookup first
        if path in self._config_cache:
            return self._config_cache[path]
            
        # Try to find in configs
        for config in self.configs.values():
            value = config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break
                    
            if value is not None:
                return value
                
        return default
        
    def get_version(self, file_path: str) -> Optional[ConfigVersion]:
        """Get version info for a config file"""
        return self.config_versions.get(file_path)
        
    def rollback(self, file_path: str) -> bool:
        """Rollback configuration to previous version"""
        version = self.config_versions.get(file_path)
        
        if not version or not version.rollback_data:
            logger.error(f"No rollback data available for {file_path}")
            return False
            
        try:
            self.configs[file_path] = version.rollback_data
            self._update_cache(file_path, version.rollback_data)
            
            logger.info(f"Rolled back config: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed for {file_path}: {e}")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """Get hot reload config status"""
        return {
            "watched_files": len(self.watched_files),
            "loaded_configs": list(self.configs.keys()),
            "config_versions": {
                path: {
                    "version": version.version,
                    "last_modified": version.last_modified.isoformat(),
                    "applied_at": version.applied_at.isoformat() if version.applied_at else None
                }
                for path, version in self.config_versions.items()
            },
            "validators_registered": list(self.validators.keys()),
            "callbacks_registered": {
                path: len(callbacks) 
                for path, callbacks in self.change_callbacks.items()
            }
        }


# Global config manager instance
_config_manager = None


def get_config_manager() -> HotReloadConfigManager:
    """Get the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = HotReloadConfigManager()
    return _config_manager


def hot_config(key: str, default: Any = None) -> Any:
    """Get a hot-reloadable configuration value"""
    return get_config_manager().get(key, default)