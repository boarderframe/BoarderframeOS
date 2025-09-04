"""
MCP Server Process Monitoring Service

A dedicated service for monitoring MCP server processes using psutil.
Provides real-time process monitoring, health checking, and resource tracking.
Replaces hardcoded data with actual process metrics.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

import psutil
from psutil import Process, NoSuchProcess, AccessDenied, ZombieProcess

from app.schemas.mcp_server import MCPServerStatus, ProcessMetrics


logger = logging.getLogger(__name__)


class ProcessState(str, Enum):
    """Extended process states for detailed monitoring."""
    RUNNING = "running"
    SLEEPING = "sleeping"
    DISK_SLEEP = "disk-sleep"
    STOPPED = "stopped"
    TRACING_STOP = "tracing-stop"
    ZOMBIE = "zombie"
    DEAD = "dead"
    WAKE_KILL = "wake-kill"
    WAKING = "waking"
    IDLE = "idle"
    LOCKED = "locked"
    WAITING = "waiting"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


@dataclass
class ProcessHealth:
    """Process health information."""
    is_healthy: bool
    issues: List[str] = field(default_factory=list)
    warning_count: int = 0
    error_count: int = 0
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessTrends:
    """Process performance trends over time."""
    cpu_history: List[float] = field(default_factory=list)
    memory_history: List[float] = field(default_factory=list)
    avg_cpu: float = 0.0
    avg_memory: float = 0.0
    peak_cpu: float = 0.0
    peak_memory: float = 0.0
    trend_window: int = 60  # Number of samples to keep


@dataclass
class ExtendedProcessMetrics:
    """Extended process metrics with additional monitoring data."""
    # Basic metrics (from schema)
    pid: int
    cpu_percent: float
    memory_mb: float
    uptime_seconds: float
    status: str
    num_threads: int
    num_fds: int
    
    # Extended metrics
    memory_percent: float
    cpu_times_user: float
    cpu_times_system: float
    memory_rss: int
    memory_vms: int
    memory_shared: int
    io_read_count: int
    io_write_count: int
    io_read_bytes: int
    io_write_bytes: int
    num_ctx_switches_voluntary: int
    num_ctx_switches_involuntary: int
    nice: int
    cmdline: List[str]
    exe: Optional[str]
    cwd: Optional[str]
    username: Optional[str]
    parent_pid: Optional[int]
    children_pids: List[int]
    open_files_count: int
    connections_count: int
    create_time: float
    
    # Health and trends
    health: ProcessHealth
    trends: ProcessTrends


@dataclass
class MonitoringAlert:
    """Monitoring alert information."""
    server_id: str
    alert_type: str
    severity: str  # info, warning, error, critical
    message: str
    timestamp: datetime
    value: Optional[float] = None
    threshold: Optional[float] = None


class ProcessMonitor:
    """
    Advanced process monitoring service for MCP servers.
    
    Features:
    - Real-time process metrics collection
    - Process health monitoring and alerts
    - Performance trend analysis
    - Resource usage tracking
    - Automated health checks
    - Process discovery and lifecycle tracking
    """
    
    def __init__(
        self,
        monitoring_interval: float = 5.0,
        health_check_interval: float = 30.0,
        trend_window_size: int = 60,
        enable_alerts: bool = True
    ):
        """
        Initialize the process monitor.
        
        Args:
            monitoring_interval: How often to collect metrics (seconds)
            health_check_interval: How often to run health checks (seconds)
            trend_window_size: Number of samples to keep for trends
            enable_alerts: Whether to enable alerting
        """
        self.monitoring_interval = monitoring_interval
        self.health_check_interval = health_check_interval
        self.trend_window_size = trend_window_size
        self.enable_alerts = enable_alerts
        
        # Monitored processes
        self._monitored_processes: Dict[str, int] = {}  # server_id -> pid
        self._process_metrics: Dict[str, ExtendedProcessMetrics] = {}
        self._process_start_times: Dict[str, datetime] = {}
        
        # Monitoring state
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Alert management
        self._alerts: List[MonitoringAlert] = []
        self._alert_callbacks: List[Callable[[MonitoringAlert], None]] = []
        self._alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'memory_mb': 1024.0,  # 1GB
            'file_descriptors': 1000,
            'thread_count': 100
        }
        
        # Process discovery
        self._discovered_processes: Set[int] = set()
        self._process_patterns: List[str] = ['python', 'node', 'mcp']
    
    async def start_monitoring(self):
        """Start the monitoring system."""
        logger.info("Starting process monitoring system")
        
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Discover existing processes
        await self._discover_processes()
        
        logger.info(f"Process monitoring started with interval {self.monitoring_interval}s")
    
    async def stop_monitoring(self):
        """Stop the monitoring system."""
        logger.info("Stopping process monitoring system")
        self._shutdown_event.set()
        
        # Cancel all monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        self._monitoring_tasks.clear()
        logger.info("Process monitoring stopped")
    
    def add_process(self, server_id: str, pid: int, start_time: Optional[datetime] = None):
        """
        Add a process to monitoring.
        
        Args:
            server_id: Unique identifier for the server
            pid: Process ID to monitor
            start_time: When the process was started
        """
        if not self._is_process_valid(pid):
            raise ValueError(f"Process {pid} is not valid or accessible")
        
        self._monitored_processes[server_id] = pid
        self._process_start_times[server_id] = start_time or datetime.now()
        
        # Start monitoring task for this process
        task = asyncio.create_task(self._monitor_process(server_id))
        self._monitoring_tasks[server_id] = task
        
        logger.info(f"Added process {pid} for server {server_id} to monitoring")
    
    def remove_process(self, server_id: str):
        """
        Remove a process from monitoring.
        
        Args:
            server_id: Server identifier to stop monitoring
        """
        if server_id in self._monitoring_tasks:
            self._monitoring_tasks[server_id].cancel()
            del self._monitoring_tasks[server_id]
        
        self._monitored_processes.pop(server_id, None)
        self._process_metrics.pop(server_id, None)
        self._process_start_times.pop(server_id, None)
        
        logger.info(f"Removed server {server_id} from monitoring")
    
    def get_process_metrics(self, server_id: str) -> Optional[ProcessMetrics]:
        """
        Get current process metrics for a server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            ProcessMetrics or None if not found/accessible
        """
        extended_metrics = self._process_metrics.get(server_id)
        if not extended_metrics:
            return None
        
        # Convert to schema format
        return ProcessMetrics(
            pid=extended_metrics.pid,
            cpu_percent=extended_metrics.cpu_percent,
            memory_mb=extended_metrics.memory_mb,
            uptime_seconds=extended_metrics.uptime_seconds,
            status=extended_metrics.status,
            num_threads=extended_metrics.num_threads,
            num_fds=extended_metrics.num_fds
        )
    
    def get_extended_metrics(self, server_id: str) -> Optional[ExtendedProcessMetrics]:
        """Get extended process metrics for a server."""
        return self._process_metrics.get(server_id)
    
    def get_all_metrics(self) -> Dict[str, ProcessMetrics]:
        """Get metrics for all monitored processes."""
        return {
            server_id: self.get_process_metrics(server_id)
            for server_id in self._monitored_processes
            if self.get_process_metrics(server_id) is not None
        }
    
    def is_process_running(self, server_id: str) -> bool:
        """Check if a monitored process is running."""
        pid = self._monitored_processes.get(server_id)
        if pid is None:
            return False
        return self._is_process_valid(pid)
    
    def get_process_health(self, server_id: str) -> Optional[ProcessHealth]:
        """Get health status for a process."""
        metrics = self._process_metrics.get(server_id)
        return metrics.health if metrics else None
    
    def get_process_trends(self, server_id: str) -> Optional[ProcessTrends]:
        """Get performance trends for a process."""
        metrics = self._process_metrics.get(server_id)
        return metrics.trends if metrics else None
    
    def get_alerts(self, server_id: Optional[str] = None) -> List[MonitoringAlert]:
        """Get monitoring alerts, optionally filtered by server."""
        if server_id:
            return [alert for alert in self._alerts if alert.server_id == server_id]
        return self._alerts.copy()
    
    def clear_alerts(self, server_id: Optional[str] = None):
        """Clear alerts, optionally for a specific server."""
        if server_id:
            self._alerts = [alert for alert in self._alerts if alert.server_id != server_id]
        else:
            self._alerts.clear()
    
    def add_alert_callback(self, callback: Callable[[MonitoringAlert], None]):
        """Add a callback function for new alerts."""
        self._alert_callbacks.append(callback)
    
    def set_alert_threshold(self, metric: str, value: float):
        """Set alert threshold for a metric."""
        self._alert_thresholds[metric] = value
    
    async def discover_mcp_processes(self) -> List[Dict[str, Any]]:
        """
        Discover running MCP-related processes.
        
        Returns:
            List of process information dictionaries
        """
        discovered = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                info = proc.info
                cmdline = info.get('cmdline', [])
                
                # Check if this looks like an MCP process
                if self._is_mcp_process(info['name'], cmdline):
                    proc_info = {
                        'pid': info['pid'],
                        'name': info['name'],
                        'cmdline': ' '.join(cmdline) if cmdline else '',
                        'create_time': datetime.fromtimestamp(info['create_time']),
                        'is_monitored': info['pid'] in self._monitored_processes.values()
                    }
                    discovered.append(proc_info)
                    
            except (NoSuchProcess, AccessDenied, ZombieProcess):
                continue
        
        return discovered
    
    # Private methods
    
    def _is_process_valid(self, pid: int) -> bool:
        """Check if a process is valid and accessible."""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (NoSuchProcess, AccessDenied, ZombieProcess):
            return False
    
    def _is_mcp_process(self, name: str, cmdline: List[str]) -> bool:
        """Check if a process appears to be MCP-related."""
        name_lower = name.lower()
        cmdline_str = ' '.join(cmdline).lower() if cmdline else ''
        
        # Check for common MCP patterns
        mcp_indicators = ['mcp', 'server', 'claude', 'anthropic']
        
        for indicator in mcp_indicators:
            if indicator in name_lower or indicator in cmdline_str:
                return True
        
        # Check for known process patterns
        for pattern in self._process_patterns:
            if pattern in name_lower:
                # Additional check for MCP in command line
                if 'mcp' in cmdline_str or 'server' in cmdline_str:
                    return True
        
        return False
    
    async def _discover_processes(self):
        """Discover and catalog existing processes."""
        try:
            discovered = await self.discover_mcp_processes()
            self._discovered_processes = {proc['pid'] for proc in discovered}
            logger.info(f"Discovered {len(discovered)} potential MCP processes")
        except Exception as e:
            logger.error(f"Error discovering processes: {e}")
    
    async def _monitor_process(self, server_id: str):
        """Monitor a single process."""
        logger.debug(f"Starting process monitoring for server {server_id}")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    pid = self._monitored_processes.get(server_id)
                    if pid is None:
                        break
                    
                    # Collect metrics
                    metrics = await self._collect_process_metrics(server_id, pid)
                    if metrics:
                        self._process_metrics[server_id] = metrics
                        
                        # Update trends
                        self._update_trends(metrics)
                        
                        # Check for alerts
                        if self.enable_alerts:
                            await self._check_alerts(server_id, metrics)
                    else:
                        # Process no longer accessible
                        logger.warning(f"Process {pid} for server {server_id} is no longer accessible")
                        break
                    
                    await asyncio.sleep(self.monitoring_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error monitoring process for server {server_id}: {e}")
                    await asyncio.sleep(self.monitoring_interval)
                    
        except Exception as e:
            logger.error(f"Critical error in process monitor for server {server_id}: {e}")
        
        logger.debug(f"Process monitoring stopped for server {server_id}")
    
    async def _collect_process_metrics(
        self, 
        server_id: str, 
        pid: int
    ) -> Optional[ExtendedProcessMetrics]:
        """Collect comprehensive metrics for a process."""
        try:
            process = psutil.Process(pid)
            
            # Basic metrics
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            uptime_seconds = time.time() - process.create_time()
            
            # CPU times
            cpu_times = process.cpu_times()
            cpu_times_user = cpu_times.user
            cpu_times_system = cpu_times.system
            
            # Memory details
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_rss = memory_info.rss
            memory_vms = memory_info.vms
            memory_shared = getattr(memory_info, 'shared', 0)
            
            # Process info
            status = process.status()
            num_threads = process.num_threads()
            nice = process.nice()
            cmdline = process.cmdline()
            create_time = process.create_time()
            
            # File descriptors/handles
            try:
                if hasattr(process, 'num_fds'):
                    num_fds = process.num_fds()
                else:
                    num_fds = process.num_handles()
            except (AccessDenied, AttributeError):
                num_fds = 0
            
            # I/O statistics
            try:
                io_counters = process.io_counters()
                io_read_count = io_counters.read_count
                io_write_count = io_counters.write_count
                io_read_bytes = io_counters.read_bytes
                io_write_bytes = io_counters.write_bytes
            except (AccessDenied, AttributeError):
                io_read_count = io_write_count = 0
                io_read_bytes = io_write_bytes = 0
            
            # Context switches
            try:
                ctx_switches = process.num_ctx_switches()
                num_ctx_switches_voluntary = ctx_switches.voluntary
                num_ctx_switches_involuntary = ctx_switches.involuntary
            except (AccessDenied, AttributeError):
                num_ctx_switches_voluntary = num_ctx_switches_involuntary = 0
            
            # Process details
            try:
                exe = process.exe()
                cwd = process.cwd()
                username = process.username()
            except (AccessDenied, AttributeError):
                exe = cwd = username = None
            
            # Parent and children
            try:
                parent_pid = process.ppid()
                children_pids = [child.pid for child in process.children()]
            except (AccessDenied, AttributeError):
                parent_pid = None
                children_pids = []
            
            # Open files and connections
            try:
                open_files_count = len(process.open_files())
            except (AccessDenied, AttributeError):
                open_files_count = 0
            
            try:
                connections_count = len(process.connections())
            except (AccessDenied, AttributeError):
                connections_count = 0
            
            # Health assessment
            health = self._assess_process_health(server_id, {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_mb': memory_mb,
                'num_fds': num_fds,
                'num_threads': num_threads,
                'status': status
            })
            
            # Trends (initialize if needed)
            existing_metrics = self._process_metrics.get(server_id)
            if existing_metrics and existing_metrics.trends:
                trends = existing_metrics.trends
            else:
                trends = ProcessTrends(trend_window=self.trend_window_size)
            
            return ExtendedProcessMetrics(
                pid=pid,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                uptime_seconds=uptime_seconds,
                status=status,
                num_threads=num_threads,
                num_fds=num_fds,
                memory_percent=memory_percent,
                cpu_times_user=cpu_times_user,
                cpu_times_system=cpu_times_system,
                memory_rss=memory_rss,
                memory_vms=memory_vms,
                memory_shared=memory_shared,
                io_read_count=io_read_count,
                io_write_count=io_write_count,
                io_read_bytes=io_read_bytes,
                io_write_bytes=io_write_bytes,
                num_ctx_switches_voluntary=num_ctx_switches_voluntary,
                num_ctx_switches_involuntary=num_ctx_switches_involuntary,
                nice=nice,
                cmdline=cmdline,
                exe=exe,
                cwd=cwd,
                username=username,
                parent_pid=parent_pid,
                children_pids=children_pids,
                open_files_count=open_files_count,
                connections_count=connections_count,
                create_time=create_time,
                health=health,
                trends=trends
            )
            
        except (NoSuchProcess, AccessDenied, ZombieProcess) as e:
            logger.warning(f"Cannot access process {pid} for server {server_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error collecting metrics for process {pid}: {e}")
            return None
    
    def _assess_process_health(self, server_id: str, metrics: Dict[str, Any]) -> ProcessHealth:
        """Assess the health of a process based on metrics."""
        issues = []
        warning_count = 0
        error_count = 0
        
        # Check CPU usage
        if metrics['cpu_percent'] > self._alert_thresholds.get('cpu_percent', 80):
            issues.append(f"High CPU usage: {metrics['cpu_percent']:.1f}%")
            if metrics['cpu_percent'] > 95:
                error_count += 1
            else:
                warning_count += 1
        
        # Check memory usage
        if metrics['memory_percent'] > self._alert_thresholds.get('memory_percent', 85):
            issues.append(f"High memory usage: {metrics['memory_percent']:.1f}%")
            if metrics['memory_percent'] > 95:
                error_count += 1
            else:
                warning_count += 1
        
        # Check file descriptors
        if metrics['num_fds'] > self._alert_thresholds.get('file_descriptors', 1000):
            issues.append(f"High file descriptor count: {metrics['num_fds']}")
            warning_count += 1
        
        # Check thread count
        if metrics['num_threads'] > self._alert_thresholds.get('thread_count', 100):
            issues.append(f"High thread count: {metrics['num_threads']}")
            warning_count += 1
        
        # Check process status
        if metrics['status'] in ['zombie', 'dead']:
            issues.append(f"Process is in bad state: {metrics['status']}")
            error_count += 1
        elif metrics['status'] in ['stopped', 'tracing-stop']:
            issues.append(f"Process is stopped: {metrics['status']}")
            warning_count += 1
        
        is_healthy = error_count == 0 and warning_count <= 2
        
        return ProcessHealth(
            is_healthy=is_healthy,
            issues=issues,
            warning_count=warning_count,
            error_count=error_count,
            last_check=datetime.now()
        )
    
    def _update_trends(self, metrics: ExtendedProcessMetrics):
        """Update performance trends for a process."""
        trends = metrics.trends
        
        # Add new data points
        trends.cpu_history.append(metrics.cpu_percent)
        trends.memory_history.append(metrics.memory_mb)
        
        # Trim to window size
        if len(trends.cpu_history) > trends.trend_window:
            trends.cpu_history.pop(0)
        if len(trends.memory_history) > trends.trend_window:
            trends.memory_history.pop(0)
        
        # Calculate averages and peaks
        if trends.cpu_history:
            trends.avg_cpu = sum(trends.cpu_history) / len(trends.cpu_history)
            trends.peak_cpu = max(trends.cpu_history)
        
        if trends.memory_history:
            trends.avg_memory = sum(trends.memory_history) / len(trends.memory_history)
            trends.peak_memory = max(trends.memory_history)
    
    async def _check_alerts(self, server_id: str, metrics: ExtendedProcessMetrics):
        """Check for alert conditions and generate alerts."""
        alerts_to_add = []
        
        # CPU alerts
        cpu_threshold = self._alert_thresholds.get('cpu_percent', 80)
        if metrics.cpu_percent > cpu_threshold:
            severity = 'critical' if metrics.cpu_percent > 95 else 'warning'
            alert = MonitoringAlert(
                server_id=server_id,
                alert_type='high_cpu',
                severity=severity,
                message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                timestamp=datetime.now(),
                value=metrics.cpu_percent,
                threshold=cpu_threshold
            )
            alerts_to_add.append(alert)
        
        # Memory alerts
        memory_threshold = self._alert_thresholds.get('memory_percent', 85)
        if metrics.memory_percent > memory_threshold:
            severity = 'critical' if metrics.memory_percent > 95 else 'warning'
            alert = MonitoringAlert(
                server_id=server_id,
                alert_type='high_memory',
                severity=severity,
                message=f"High memory usage: {metrics.memory_percent:.1f}%",
                timestamp=datetime.now(),
                value=metrics.memory_percent,
                threshold=memory_threshold
            )
            alerts_to_add.append(alert)
        
        # Process state alerts
        if not metrics.health.is_healthy:
            alert = MonitoringAlert(
                server_id=server_id,
                alert_type='process_health',
                severity='error' if metrics.health.error_count > 0 else 'warning',
                message=f"Process health issues: {', '.join(metrics.health.issues)}",
                timestamp=datetime.now()
            )
            alerts_to_add.append(alert)
        
        # Add alerts and notify callbacks
        for alert in alerts_to_add:
            self._alerts.append(alert)
            for callback in self._alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
        
        # Trim old alerts (keep last 1000)
        if len(self._alerts) > 1000:
            self._alerts = self._alerts[-1000:]
    
    async def _health_check_loop(self):
        """Background health check loop."""
        logger.debug("Starting health check loop")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Check all monitored processes
                    for server_id, pid in list(self._monitored_processes.items()):
                        if not self._is_process_valid(pid):
                            logger.warning(f"Process {pid} for server {server_id} is no longer valid")
                            # Could trigger auto-restart here if configured
                    
                    await asyncio.sleep(self.health_check_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in health check loop: {e}")
                    await asyncio.sleep(self.health_check_interval)
                    
        except Exception as e:
            logger.error(f"Critical error in health check loop: {e}")
        
        logger.debug("Health check loop stopped")


# Global process monitor instance
process_monitor = ProcessMonitor()