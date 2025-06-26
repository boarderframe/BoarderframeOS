"""
Blue-Green Hot Reload System for BoarderframeOS
Zero-downtime agent and configuration reloading
"""

import asyncio
import importlib
import sys
import os
import time
import hashlib
import pickle
from typing import Dict, Any, Optional, List, Tuple, Type
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DeploymentState(Enum):
    """Deployment environment states"""
    BLUE = "blue"
    GREEN = "green"
    TRANSITIONING = "transitioning"
    FAILED = "failed"


@dataclass
class ModuleVersion:
    """Tracks module version information"""
    module_name: str
    file_path: str
    last_modified: float
    checksum: str
    version: int = 1
    loaded_at: Optional[datetime] = None
    instance_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class ReloadMetrics:
    """Metrics for reload operations"""
    total_reloads: int = 0
    successful_reloads: int = 0
    failed_reloads: int = 0
    average_reload_time: float = 0.0
    last_reload_time: Optional[datetime] = None
    reload_times: List[float] = field(default_factory=list)
    
    def add_reload_time(self, duration: float):
        """Add a reload time measurement"""
        self.reload_times.append(duration)
        if len(self.reload_times) > 100:  # Keep last 100 measurements
            self.reload_times.pop(0)
        self.average_reload_time = sum(self.reload_times) / len(self.reload_times)


class HotReloadManager:
    """
    Manages blue-green hot reloading for agents and modules
    
    Features:
    - Zero-downtime reloading
    - Health checks before switching
    - Automatic rollback on failure
    - File change detection
    - Dependency tracking
    """
    
    def __init__(self, watch_paths: List[str] = None):
        self.watch_paths = watch_paths or ["agents/", "core/", "mcp/"]
        self.blue_modules: Dict[str, Any] = {}
        self.green_modules: Dict[str, Any] = {}
        self.current_state = DeploymentState.BLUE
        self.module_versions: Dict[str, ModuleVersion] = {}
        self.reload_callbacks: List[callable] = []
        self.metrics = ReloadMetrics()
        self._watch_task = None
        self._reload_lock = asyncio.Lock()
        self._dependency_graph: Dict[str, List[str]] = {}
        
    async def initialize(self):
        """Initialize the hot reload manager (alias for start)"""
        await self.start()
        
    async def start(self):
        """Start the hot reload manager"""
        logger.info("Starting hot reload manager")
        
        # Initialize module tracking
        self._scan_modules()
        
        # Start file watcher
        self._watch_task = asyncio.create_task(self._watch_files())
        
        logger.info(f"Hot reload manager started, watching: {self.watch_paths}")
        
    async def stop(self):
        """Stop the hot reload manager"""
        logger.info("Stopping hot reload manager")
        
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Hot reload manager stopped")
        
    def _scan_modules(self):
        """Scan and index all modules"""
        for watch_path in self.watch_paths:
            path = Path(watch_path)
            if not path.exists():
                continue
                
            for py_file in path.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                    
                module_name = self._path_to_module_name(py_file)
                if module_name:
                    self._track_module(module_name, str(py_file))
                    
    def _path_to_module_name(self, file_path: Path) -> Optional[str]:
        """Convert file path to module name"""
        try:
            # Remove .py extension
            path_str = str(file_path).replace(".py", "")
            
            # Convert path separators to dots
            module_name = path_str.replace(os.sep, ".")
            
            # Remove any leading dots
            module_name = module_name.lstrip(".")
            
            return module_name
            
        except Exception as e:
            logger.error(f"Failed to convert path {file_path} to module name: {e}")
            return None
            
    def _track_module(self, module_name: str, file_path: str):
        """Track a module for changes"""
        try:
            stat = os.stat(file_path)
            last_modified = stat.st_mtime
            
            # Calculate checksum
            with open(file_path, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()
                
            # Create or update module version
            if module_name in self.module_versions:
                version = self.module_versions[module_name]
                if version.checksum != checksum:
                    version.version += 1
                    version.checksum = checksum
                    version.last_modified = last_modified
            else:
                self.module_versions[module_name] = ModuleVersion(
                    module_name=module_name,
                    file_path=file_path,
                    last_modified=last_modified,
                    checksum=checksum
                )
                
        except Exception as e:
            logger.error(f"Failed to track module {module_name}: {e}")
            
    async def _watch_files(self):
        """Watch files for changes"""
        logger.info("Starting file watcher")
        check_interval = 2.0  # Check every 2 seconds
        
        while True:
            try:
                await asyncio.sleep(check_interval)
                
                # Check for changed modules
                changed_modules = []
                
                for module_name, version in self.module_versions.items():
                    try:
                        stat = os.stat(version.file_path)
                        
                        if stat.st_mtime > version.last_modified:
                            # File has been modified
                            with open(version.file_path, 'rb') as f:
                                new_checksum = hashlib.md5(f.read()).hexdigest()
                                
                            if new_checksum != version.checksum:
                                changed_modules.append(module_name)
                                logger.info(f"Detected change in module: {module_name}")
                                
                    except FileNotFoundError:
                        logger.warning(f"Module file not found: {version.file_path}")
                    except Exception as e:
                        logger.error(f"Error checking module {module_name}: {e}")
                        
                # Reload changed modules
                if changed_modules:
                    await self.reload_modules(changed_modules)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"File watcher error: {e}")
                await asyncio.sleep(5)  # Back off on error
                
    async def reload_modules(self, module_names: List[str]) -> bool:
        """Reload specified modules using blue-green deployment"""
        async with self._reload_lock:
            start_time = time.time()
            self.metrics.total_reloads += 1
            
            logger.info(f"Starting blue-green reload for modules: {module_names}")
            
            try:
                # Determine target environment
                target_env = DeploymentState.GREEN if self.current_state == DeploymentState.BLUE else DeploymentState.BLUE
                target_modules = self.green_modules if target_env == DeploymentState.GREEN else self.blue_modules
                
                # Update state
                self.current_state = DeploymentState.TRANSITIONING
                
                # Reload modules into target environment
                success = await self._reload_into_environment(module_names, target_modules)
                
                if not success:
                    logger.error("Module reload failed, rolling back")
                    self.current_state = DeploymentState.BLUE if target_env == DeploymentState.GREEN else DeploymentState.GREEN
                    self.metrics.failed_reloads += 1
                    return False
                    
                # Run health checks
                health_ok = await self._run_health_checks(target_modules)
                
                if not health_ok:
                    logger.error("Health checks failed, rolling back")
                    self.current_state = DeploymentState.BLUE if target_env == DeploymentState.GREEN else DeploymentState.GREEN
                    self.metrics.failed_reloads += 1
                    return False
                    
                # Switch to new environment
                logger.info(f"Switching from {self.current_state.value} to {target_env.value}")
                self.current_state = target_env
                
                # Notify callbacks
                await self._notify_reload_callbacks(module_names)
                
                # Update metrics
                reload_time = time.time() - start_time
                self.metrics.successful_reloads += 1
                self.metrics.add_reload_time(reload_time)
                self.metrics.last_reload_time = datetime.now()
                
                logger.info(f"Reload completed successfully in {reload_time:.2f}s")
                return True
                
            except Exception as e:
                logger.error(f"Reload failed with exception: {e}")
                self.current_state = DeploymentState.FAILED
                self.metrics.failed_reloads += 1
                return False
                
    async def _reload_into_environment(self, module_names: List[str], target_modules: Dict[str, Any]) -> bool:
        """Reload modules into target environment"""
        reload_errors = []
        
        # Sort modules by dependency order
        ordered_modules = self._order_by_dependencies(module_names)
        
        for module_name in ordered_modules:
            try:
                logger.debug(f"Reloading module: {module_name}")
                
                # Remove from sys.modules to force reload
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    
                # Import the module
                module = importlib.import_module(module_name)
                
                # Store in target environment
                target_modules[module_name] = module
                
                # Update tracking
                self._track_module(module_name, self.module_versions[module_name].file_path)
                self.module_versions[module_name].loaded_at = datetime.now()
                
            except Exception as e:
                error_msg = f"Failed to reload {module_name}: {e}"
                logger.error(error_msg)
                reload_errors.append(error_msg)
                
                # Update error tracking
                if module_name in self.module_versions:
                    self.module_versions[module_name].error_count += 1
                    self.module_versions[module_name].last_error = str(e)
                    
        return len(reload_errors) == 0
        
    def _order_by_dependencies(self, module_names: List[str]) -> List[str]:
        """Order modules by their dependencies"""
        # Simple implementation - can be enhanced with actual dependency analysis
        ordered = []
        
        # Core modules first
        core_modules = [m for m in module_names if m.startswith("core.")]
        other_modules = [m for m in module_names if not m.startswith("core.")]
        
        ordered.extend(sorted(core_modules))
        ordered.extend(sorted(other_modules))
        
        return ordered
        
    async def _run_health_checks(self, modules: Dict[str, Any]) -> bool:
        """Run health checks on reloaded modules"""
        logger.info("Running health checks on reloaded modules")
        
        health_results = []
        
        for module_name, module in modules.items():
            # Check for health check function
            if hasattr(module, 'health_check'):
                try:
                    result = await module.health_check()
                    health_results.append(result)
                    logger.debug(f"Health check for {module_name}: {result}")
                except Exception as e:
                    logger.error(f"Health check failed for {module_name}: {e}")
                    health_results.append(False)
                    
        # All health checks must pass
        return all(health_results) if health_results else True
        
    async def _notify_reload_callbacks(self, module_names: List[str]):
        """Notify registered callbacks about reload"""
        for callback in self.reload_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(module_names)
                else:
                    callback(module_names)
            except Exception as e:
                logger.error(f"Reload callback error: {e}")
                
    def register_reload_callback(self, callback: callable):
        """Register a callback for reload events"""
        self.reload_callbacks.append(callback)
        
    def get_module(self, module_name: str) -> Optional[Any]:
        """Get the current active module"""
        if self.current_state == DeploymentState.BLUE:
            return self.blue_modules.get(module_name)
        elif self.current_state == DeploymentState.GREEN:
            return self.green_modules.get(module_name)
        return None
        
    def get_module_version(self, module_name: str) -> Optional[ModuleVersion]:
        """Get version information for a module"""
        return self.module_versions.get(module_name)
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get reload metrics"""
        return {
            "current_state": self.current_state.value,
            "total_reloads": self.metrics.total_reloads,
            "successful_reloads": self.metrics.successful_reloads,
            "failed_reloads": self.metrics.failed_reloads,
            "average_reload_time": f"{self.metrics.average_reload_time:.2f}s",
            "last_reload_time": self.metrics.last_reload_time.isoformat() if self.metrics.last_reload_time else None,
            "tracked_modules": len(self.module_versions),
            "blue_modules": len(self.blue_modules),
            "green_modules": len(self.green_modules)
        }
        
    async def force_reload(self, module_name: str) -> bool:
        """Force reload a specific module"""
        if module_name not in self.module_versions:
            logger.error(f"Module {module_name} not tracked")
            return False
            
        return await self.reload_modules([module_name])
        
    @asynccontextmanager
    async def safe_reload_context(self):
        """Context manager for safe reloading operations"""
        original_state = self.current_state
        try:
            yield
        except Exception as e:
            logger.error(f"Error during reload context: {e}")
            # Attempt to restore original state
            self.current_state = original_state
            raise


# Global hot reload manager instance
_hot_reload_manager = None


def get_hot_reload_manager() -> HotReloadManager:
    """Get the global hot reload manager instance"""
    global _hot_reload_manager
    if _hot_reload_manager is None:
        _hot_reload_manager = HotReloadManager()
    return _hot_reload_manager


async def reload_module(module_name: str) -> bool:
    """Convenience function to reload a module"""
    manager = get_hot_reload_manager()
    return await manager.force_reload(module_name)