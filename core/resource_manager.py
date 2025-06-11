"""
Resource Management System - BoarderframeOS
Monitor and manage compute resources (CPU, Memory, GPU) for all agents
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psutil

try:
    import nvidia_ml_py3 as nvml
    HAS_NVIDIA = True
except ImportError:
    HAS_NVIDIA = False

from .agent_registry import AgentDiscoveryInfo, agent_registry
from .message_bus import AgentMessage, MessagePriority, MessageType, message_bus

logger = logging.getLogger("resource_manager")

class ResourceType(Enum):
    """Types of resources managed"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"

class ResourceAlert(Enum):
    """Resource alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class ResourceLimit:
    """Resource limits for agents"""
    cpu_percent: float = 100.0  # CPU percentage limit
    memory_mb: float = 8192.0   # Memory limit in MB
    gpu_percent: float = 100.0  # GPU percentage limit
    disk_mb: float = 10240.0    # Disk usage limit in MB
    network_mbps: float = 1000.0  # Network bandwidth limit

@dataclass
class ResourceUsage:
    """Current resource usage"""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    gpu_percent: float = 0.0
    gpu_memory_mb: float = 0.0
    disk_mb: float = 0.0
    network_mbps: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "memory_percent": self.memory_percent,
            "gpu_percent": self.gpu_percent,
            "gpu_memory_mb": self.gpu_memory_mb,
            "disk_mb": self.disk_mb,
            "network_mbps": self.network_mbps,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class SystemResources:
    """System-wide resource information"""
    cpu_cores: int
    cpu_frequency_mhz: float
    memory_total_mb: float
    memory_available_mb: float
    gpu_count: int = 0
    gpu_total_memory_mb: float = 0.0
    disk_total_mb: float = 0.0
    disk_available_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_frequency_mhz": self.cpu_frequency_mhz,
            "memory_total_mb": self.memory_total_mb,
            "memory_available_mb": self.memory_available_mb,
            "gpu_count": self.gpu_count,
            "gpu_total_memory_mb": self.gpu_total_memory_mb,
            "disk_total_mb": self.disk_total_mb,
            "disk_available_mb": self.disk_available_mb
        }

class ResourceManager:
    """Centralized resource management for all agents"""

    def __init__(self):
        self.agent_limits: Dict[str, ResourceLimit] = {}
        self.agent_usage: Dict[str, ResourceUsage] = {}
        self.usage_history: Dict[str, List[ResourceUsage]] = {}
        self.system_resources: Optional[SystemResources] = None
        self.alert_thresholds = {
            ResourceAlert.WARNING: 0.80,
            ResourceAlert.CRITICAL: 0.95
        }
        self.running = False
        self.history_retention_hours = 24

        # Initialize NVIDIA GPU support if available
        self.gpu_initialized = False
        if HAS_NVIDIA:
            try:
                nvml.nvmlInit()
                self.gpu_initialized = True
                logger.info("NVIDIA GPU monitoring initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize NVIDIA GPU monitoring: {e}")

    async def start(self):
        """Start the resource manager"""
        self.running = True
        logger.info("Resource Manager started")

        # Get system resource information
        await self._detect_system_resources()

        # Start monitoring tasks
        asyncio.create_task(self._monitor_system_resources())
        asyncio.create_task(self._monitor_agent_resources())
        asyncio.create_task(self._cleanup_history())
        asyncio.create_task(self._alert_monitor())

        # Subscribe to agent events
        await message_bus.subscribe_to_topic("resource_manager", "system_events")

    async def stop(self):
        """Stop the resource manager"""
        self.running = False
        logger.info("Resource Manager stopped")

    async def _detect_system_resources(self):
        """Detect available system resources"""
        try:
            # CPU information
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            cpu_frequency = cpu_freq.current if cpu_freq else 0.0

            # Memory information
            memory = psutil.virtual_memory()
            memory_total = memory.total / 1024 / 1024  # Convert to MB
            memory_available = memory.available / 1024 / 1024

            # Disk information
            disk = psutil.disk_usage('/')
            disk_total = disk.total / 1024 / 1024  # Convert to MB
            disk_available = disk.free / 1024 / 1024

            # GPU information
            gpu_count = 0
            gpu_total_memory = 0.0

            if self.gpu_initialized:
                try:
                    gpu_count = nvml.nvmlDeviceGetCount()
                    for i in range(gpu_count):
                        handle = nvml.nvmlDeviceGetHandleByIndex(i)
                        memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_total_memory += memory_info.total / 1024 / 1024  # Convert to MB
                except Exception as e:
                    logger.warning(f"Error getting GPU information: {e}")

            self.system_resources = SystemResources(
                cpu_cores=cpu_count,
                cpu_frequency_mhz=cpu_frequency,
                memory_total_mb=memory_total,
                memory_available_mb=memory_available,
                gpu_count=gpu_count,
                gpu_total_memory_mb=gpu_total_memory,
                disk_total_mb=disk_total,
                disk_available_mb=disk_available
            )

            logger.info(f"System resources detected: {cpu_count} CPU cores, "
                       f"{memory_total:.0f}MB RAM, {gpu_count} GPUs")

        except Exception as e:
            logger.error(f"Failed to detect system resources: {e}")

    def set_agent_limits(self, agent_id: str, limits: ResourceLimit):
        """Set resource limits for an agent"""
        self.agent_limits[agent_id] = limits
        logger.info(f"Set resource limits for agent {agent_id}")

    def get_agent_limits(self, agent_id: str) -> ResourceLimit:
        """Get resource limits for an agent"""
        return self.agent_limits.get(agent_id, ResourceLimit())

    def get_agent_usage(self, agent_id: str) -> Optional[ResourceUsage]:
        """Get current resource usage for an agent"""
        return self.agent_usage.get(agent_id)

    def get_system_usage(self) -> ResourceUsage:
        """Get current system-wide resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_used_mb = (memory.total - memory.available) / 1024 / 1024
            memory_percent = memory.percent

            # GPU usage
            gpu_percent = 0.0
            gpu_memory_mb = 0.0

            if self.gpu_initialized:
                try:
                    gpu_count = nvml.nvmlDeviceGetCount()
                    total_gpu_util = 0.0
                    total_gpu_memory = 0.0

                    for i in range(gpu_count):
                        handle = nvml.nvmlDeviceGetHandleByIndex(i)
                        util = nvml.nvmlDeviceGetUtilizationRates(handle)
                        memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)

                        total_gpu_util += util.gpu
                        total_gpu_memory += memory_info.used / 1024 / 1024

                    gpu_percent = total_gpu_util / max(gpu_count, 1)
                    gpu_memory_mb = total_gpu_memory

                except Exception as e:
                    logger.debug(f"Error getting GPU usage: {e}")

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_used_mb = (disk.total - disk.free) / 1024 / 1024

            return ResourceUsage(
                cpu_percent=cpu_percent,
                memory_mb=memory_used_mb,
                memory_percent=memory_percent,
                gpu_percent=gpu_percent,
                gpu_memory_mb=gpu_memory_mb,
                disk_mb=disk_used_mb,
                network_mbps=0.0,  # TODO: Implement network monitoring
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error getting system usage: {e}")
            return ResourceUsage()

    def get_agent_resource_history(self, agent_id: str, hours: int = 1) -> List[ResourceUsage]:
        """Get resource usage history for an agent"""
        if agent_id not in self.usage_history:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            usage for usage in self.usage_history[agent_id]
            if usage.timestamp >= cutoff_time
        ]

    def check_resource_violations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Check if an agent is violating resource limits"""
        violations = []

        if agent_id not in self.agent_usage or agent_id not in self.agent_limits:
            return violations

        usage = self.agent_usage[agent_id]
        limits = self.agent_limits[agent_id]

        # Check CPU limit
        if usage.cpu_percent > limits.cpu_percent:
            violations.append({
                "resource": ResourceType.CPU.value,
                "usage": usage.cpu_percent,
                "limit": limits.cpu_percent,
                "violation_percent": (usage.cpu_percent / limits.cpu_percent) * 100
            })

        # Check memory limit
        if usage.memory_mb > limits.memory_mb:
            violations.append({
                "resource": ResourceType.MEMORY.value,
                "usage": usage.memory_mb,
                "limit": limits.memory_mb,
                "violation_percent": (usage.memory_mb / limits.memory_mb) * 100
            })

        # Check GPU limit
        if usage.gpu_percent > limits.gpu_percent:
            violations.append({
                "resource": ResourceType.GPU.value,
                "usage": usage.gpu_percent,
                "limit": limits.gpu_percent,
                "violation_percent": (usage.gpu_percent / limits.gpu_percent) * 100
            })

        return violations

    def get_resource_recommendations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get resource optimization recommendations for an agent"""
        recommendations = []

        if agent_id not in self.usage_history:
            return recommendations

        # Analyze recent usage patterns
        recent_usage = self.get_agent_resource_history(agent_id, hours=6)
        if not recent_usage:
            return recommendations

        # Calculate averages
        avg_cpu = sum(u.cpu_percent for u in recent_usage) / len(recent_usage)
        avg_memory = sum(u.memory_mb for u in recent_usage) / len(recent_usage)
        avg_gpu = sum(u.gpu_percent for u in recent_usage) / len(recent_usage)

        limits = self.get_agent_limits(agent_id)

        # CPU recommendations
        if avg_cpu < limits.cpu_percent * 0.5:
            recommendations.append({
                "resource": ResourceType.CPU.value,
                "type": "reduce_limit",
                "current_limit": limits.cpu_percent,
                "suggested_limit": max(avg_cpu * 1.5, 10.0),
                "reason": "Low CPU utilization detected"
            })
        elif avg_cpu > limits.cpu_percent * 0.9:
            recommendations.append({
                "resource": ResourceType.CPU.value,
                "type": "increase_limit",
                "current_limit": limits.cpu_percent,
                "suggested_limit": min(avg_cpu * 1.2, 100.0),
                "reason": "High CPU utilization detected"
            })

        # Memory recommendations
        if avg_memory < limits.memory_mb * 0.5:
            recommendations.append({
                "resource": ResourceType.MEMORY.value,
                "type": "reduce_limit",
                "current_limit": limits.memory_mb,
                "suggested_limit": max(avg_memory * 1.5, 512.0),
                "reason": "Low memory utilization detected"
            })
        elif avg_memory > limits.memory_mb * 0.9:
            recommendations.append({
                "resource": ResourceType.MEMORY.value,
                "type": "increase_limit",
                "current_limit": limits.memory_mb,
                "suggested_limit": avg_memory * 1.2,
                "reason": "High memory utilization detected"
            })

        return recommendations

    async def _monitor_system_resources(self):
        """Monitor system-wide resource usage"""
        while self.running:
            try:
                system_usage = self.get_system_usage()

                # Broadcast system resource update
                await message_bus.broadcast(AgentMessage(
                    from_agent="resource_manager",
                    to_agent="system",
                    message_type=MessageType.STATUS_UPDATE,
                    content={
                        "event": "system_resources_update",
                        "usage": system_usage.to_dict(),
                        "resources": self.system_resources.to_dict() if self.system_resources else {}
                    }
                ), topic="system_events")

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"System resource monitoring error: {e}")
                await asyncio.sleep(30)

    async def _monitor_agent_resources(self):
        """Monitor resource usage for all registered agents"""
        while self.running:
            try:
                for agent_id in list(agent_registry.agents.keys()):
                    agent_info = agent_registry.get_agent(agent_id)
                    if not agent_info or not agent_info.pid:
                        continue

                    try:
                        # Get process information
                        process = psutil.Process(agent_info.pid)

                        # CPU usage
                        cpu_percent = process.cpu_percent()

                        # Memory usage
                        memory_info = process.memory_info()
                        memory_mb = memory_info.rss / 1024 / 1024

                        # GPU usage (if available and agent uses GPU)
                        gpu_percent = 0.0
                        gpu_memory_mb = 0.0
                        # TODO: Implement per-process GPU monitoring

                        # Create usage record
                        usage = ResourceUsage(
                            cpu_percent=cpu_percent,
                            memory_mb=memory_mb,
                            memory_percent=(memory_mb / self.system_resources.memory_total_mb * 100) if self.system_resources else 0,
                            gpu_percent=gpu_percent,
                            gpu_memory_mb=gpu_memory_mb,
                            disk_mb=0.0,  # TODO: Implement disk monitoring
                            network_mbps=0.0,  # TODO: Implement network monitoring
                            timestamp=datetime.now()
                        )

                        # Store current usage
                        self.agent_usage[agent_id] = usage

                        # Store in history
                        if agent_id not in self.usage_history:
                            self.usage_history[agent_id] = []
                        self.usage_history[agent_id].append(usage)

                        # Update agent registry with metrics
                        await agent_registry.update_agent_heartbeat(agent_id, {
                            "cpu_usage": cpu_percent,
                            "memory_usage_mb": memory_mb,
                            "gpu_usage": gpu_percent
                        })

                    except psutil.NoSuchProcess:
                        # Process no longer exists
                        logger.warning(f"Process for agent {agent_id} no longer exists")
                        if agent_id in self.agent_usage:
                            del self.agent_usage[agent_id]
                    except Exception as e:
                        logger.debug(f"Error monitoring agent {agent_id}: {e}")

                await asyncio.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"Agent resource monitoring error: {e}")
                await asyncio.sleep(10)

    async def _cleanup_history(self):
        """Clean up old resource usage history"""
        while self.running:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)

                for agent_id in list(self.usage_history.keys()):
                    history = self.usage_history[agent_id]
                    cleaned_history = [
                        usage for usage in history
                        if usage.timestamp >= cutoff_time
                    ]
                    self.usage_history[agent_id] = cleaned_history

                await asyncio.sleep(3600)  # Clean up every hour

            except Exception as e:
                logger.error(f"History cleanup error: {e}")
                await asyncio.sleep(3600)

    async def _alert_monitor(self):
        """Monitor for resource alerts"""
        while self.running:
            try:
                # Check system-wide resource usage
                system_usage = self.get_system_usage()

                if self.system_resources:
                    # Check system memory usage
                    memory_usage_percent = (system_usage.memory_mb / self.system_resources.memory_total_mb) * 100

                    if memory_usage_percent > self.alert_thresholds[ResourceAlert.CRITICAL] * 100:
                        await self._send_alert(ResourceAlert.CRITICAL, ResourceType.MEMORY,
                                             f"System memory usage at {memory_usage_percent:.1f}%")
                    elif memory_usage_percent > self.alert_thresholds[ResourceAlert.WARNING] * 100:
                        await self._send_alert(ResourceAlert.WARNING, ResourceType.MEMORY,
                                             f"System memory usage at {memory_usage_percent:.1f}%")

                # Check individual agent violations
                for agent_id in self.agent_usage.keys():
                    violations = self.check_resource_violations(agent_id)
                    for violation in violations:
                        if violation['violation_percent'] > self.alert_thresholds[ResourceAlert.CRITICAL] * 100:
                            await self._send_alert(ResourceAlert.CRITICAL, ResourceType(violation['resource']),
                                                 f"Agent {agent_id} exceeding {violation['resource']} limit: "
                                                 f"{violation['usage']:.1f} > {violation['limit']:.1f}")

                await asyncio.sleep(60)  # Check alerts every minute

            except Exception as e:
                logger.error(f"Alert monitoring error: {e}")
                await asyncio.sleep(60)

    async def _send_alert(self, level: ResourceAlert, resource_type: ResourceType, message: str):
        """Send a resource alert"""
        await message_bus.broadcast(AgentMessage(
            from_agent="resource_manager",
            to_agent="system",
            message_type=MessageType.ALERT,
            content={
                "alert_level": level.value,
                "resource_type": resource_type.value,
                "message": message,
                "timestamp": datetime.now().isoformat()
            },
            priority=MessagePriority.HIGH if level == ResourceAlert.CRITICAL else MessagePriority.NORMAL
        ), topic="system_alerts")

        logger.warning(f"Resource alert ({level.value}): {message}")

# Global resource manager instance
resource_manager = ResourceManager()
