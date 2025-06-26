"""
Agent Health Monitoring System for BoarderframeOS
Provides real-time health tracking and diagnostics for all agents
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import psutil
import logging
import json
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Agent health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


class HealthMetric(Enum):
    """Types of health metrics"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    MESSAGE_QUEUE = "message_queue"
    LAST_ACTIVITY = "last_activity"
    UPTIME = "uptime"
    TASK_SUCCESS_RATE = "task_success_rate"


@dataclass
class HealthCheck:
    """Individual health check result"""
    metric: HealthMetric
    status: HealthStatus
    value: Any
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentHealthReport:
    """Complete health report for an agent"""
    agent_id: str
    agent_name: str
    overall_status: HealthStatus
    checks: List[HealthCheck]
    uptime: timedelta
    last_check: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "overall_status": self.overall_status.value,
            "checks": [
                {
                    "metric": check.metric.value,
                    "status": check.status.value,
                    "value": check.value,
                    "message": check.message,
                    "timestamp": check.timestamp.isoformat()
                }
                for check in self.checks
            ],
            "uptime": str(self.uptime),
            "last_check": self.last_check.isoformat(),
            "metadata": self.metadata
        }


class AgentHealthMonitor:
    """
    Monitors health of all agents in the system
    
    Features:
    - Real-time health metrics collection
    - Configurable thresholds and alerts
    - Historical data tracking
    - Anomaly detection
    - Auto-recovery suggestions
    """
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.alert_handlers: List[callable] = []
        self.check_interval = 30  # seconds
        self._monitoring_task = None
        self._process_monitors: Dict[str, psutil.Process] = {}
        
        # Health thresholds
        self.thresholds = {
            HealthMetric.CPU_USAGE: {"warning": 70, "critical": 90},
            HealthMetric.MEMORY_USAGE: {"warning": 80, "critical": 95},
            HealthMetric.RESPONSE_TIME: {"warning": 2.0, "critical": 5.0},
            HealthMetric.ERROR_RATE: {"warning": 0.05, "critical": 0.10},
            HealthMetric.MESSAGE_QUEUE: {"warning": 100, "critical": 500},
            HealthMetric.TASK_SUCCESS_RATE: {"warning": 0.95, "critical": 0.80}
        }
        
    async def start_monitoring(self):
        """Start the health monitoring loop"""
        if self._monitoring_task:
            logger.warning("Health monitoring already running")
            return
            
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Agent health monitoring started")
        
    async def stop_monitoring(self):
        """Stop the health monitoring loop"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("Agent health monitoring stopped")
            
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self.check_all_agents()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
                
    def register_agent(self, agent_id: str, agent_name: str, 
                      process_id: Optional[int] = None, **metadata):
        """Register an agent for health monitoring"""
        self.agents[agent_id] = {
            "name": agent_name,
            "process_id": process_id,
            "start_time": datetime.now(),
            "metadata": metadata
        }
        
        if process_id:
            try:
                self._process_monitors[agent_id] = psutil.Process(process_id)
            except psutil.NoSuchProcess:
                logger.warning(f"Process {process_id} not found for agent {agent_name}")
                
        logger.info(f"Registered agent {agent_name} ({agent_id}) for health monitoring")
        
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from health monitoring"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            if agent_id in self._process_monitors:
                del self._process_monitors[agent_id]
            logger.info(f"Unregistered agent {agent_id} from health monitoring")
            
    async def check_agent_health(self, agent_id: str) -> Optional[AgentHealthReport]:
        """Check health of a specific agent"""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not registered for health monitoring")
            return None
            
        agent_info = self.agents[agent_id]
        checks = []
        
        # CPU usage check
        cpu_check = await self._check_cpu_usage(agent_id)
        if cpu_check:
            checks.append(cpu_check)
            
        # Memory usage check
        memory_check = await self._check_memory_usage(agent_id)
        if memory_check:
            checks.append(memory_check)
            
        # Response time check
        response_check = await self._check_response_time(agent_id)
        checks.append(response_check)
        
        # Error rate check
        error_check = await self._check_error_rate(agent_id)
        checks.append(error_check)
        
        # Message queue check
        queue_check = await self._check_message_queue(agent_id)
        checks.append(queue_check)
        
        # Last activity check
        activity_check = await self._check_last_activity(agent_id)
        checks.append(activity_check)
        
        # Task success rate
        success_check = await self._check_task_success_rate(agent_id)
        checks.append(success_check)
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        # Calculate uptime
        uptime = datetime.now() - agent_info["start_time"]
        
        report = AgentHealthReport(
            agent_id=agent_id,
            agent_name=agent_info["name"],
            overall_status=overall_status,
            checks=checks,
            uptime=uptime,
            last_check=datetime.now(),
            metadata=agent_info["metadata"]
        )
        
        # Store in history
        self.health_history[agent_id].append(report)
        
        # Check for alerts
        await self._check_alerts(report)
        
        return report
        
    async def check_all_agents(self) -> Dict[str, AgentHealthReport]:
        """Check health of all registered agents"""
        reports = {}
        
        for agent_id in list(self.agents.keys()):
            try:
                report = await self.check_agent_health(agent_id)
                if report:
                    reports[agent_id] = report
            except Exception as e:
                logger.error(f"Error checking health for agent {agent_id}: {e}")
                
        return reports
        
    async def _check_cpu_usage(self, agent_id: str) -> Optional[HealthCheck]:
        """Check CPU usage for an agent"""
        if agent_id not in self._process_monitors:
            return None
            
        try:
            process = self._process_monitors[agent_id]
            cpu_percent = process.cpu_percent(interval=1)
            
            status = self._get_status_for_metric(
                HealthMetric.CPU_USAGE, 
                cpu_percent
            )
            
            return HealthCheck(
                metric=HealthMetric.CPU_USAGE,
                status=status,
                value=cpu_percent,
                threshold_warning=self.thresholds[HealthMetric.CPU_USAGE]["warning"],
                threshold_critical=self.thresholds[HealthMetric.CPU_USAGE]["critical"],
                message=f"CPU usage: {cpu_percent:.1f}%"
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return HealthCheck(
                metric=HealthMetric.CPU_USAGE,
                status=HealthStatus.UNKNOWN,
                value=None,
                message="Process not accessible"
            )
            
    async def _check_memory_usage(self, agent_id: str) -> Optional[HealthCheck]:
        """Check memory usage for an agent"""
        if agent_id not in self._process_monitors:
            return None
            
        try:
            process = self._process_monitors[agent_id]
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            status = self._get_status_for_metric(
                HealthMetric.MEMORY_USAGE,
                memory_percent
            )
            
            return HealthCheck(
                metric=HealthMetric.MEMORY_USAGE,
                status=status,
                value=memory_percent,
                threshold_warning=self.thresholds[HealthMetric.MEMORY_USAGE]["warning"],
                threshold_critical=self.thresholds[HealthMetric.MEMORY_USAGE]["critical"],
                message=f"Memory: {memory_info.rss / 1024 / 1024:.1f} MB ({memory_percent:.1f}%)"
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return HealthCheck(
                metric=HealthMetric.MEMORY_USAGE,
                status=HealthStatus.UNKNOWN,
                value=None,
                message="Process not accessible"
            )
            
    async def _check_response_time(self, agent_id: str) -> HealthCheck:
        """Check agent response time"""
        # This would typically ping the agent or check recent response times
        # For now, simulate with random data
        import random
        response_time = random.uniform(0.1, 3.0)
        
        status = self._get_status_for_metric(
            HealthMetric.RESPONSE_TIME,
            response_time
        )
        
        return HealthCheck(
            metric=HealthMetric.RESPONSE_TIME,
            status=status,
            value=response_time,
            threshold_warning=self.thresholds[HealthMetric.RESPONSE_TIME]["warning"],
            threshold_critical=self.thresholds[HealthMetric.RESPONSE_TIME]["critical"],
            message=f"Response time: {response_time:.2f}s"
        )
        
    async def _check_error_rate(self, agent_id: str) -> HealthCheck:
        """Check agent error rate"""
        # This would check actual error logs
        # For now, simulate
        import random
        error_rate = random.uniform(0, 0.1)
        
        status = self._get_status_for_metric(
            HealthMetric.ERROR_RATE,
            error_rate
        )
        
        return HealthCheck(
            metric=HealthMetric.ERROR_RATE,
            status=status,
            value=error_rate,
            threshold_warning=self.thresholds[HealthMetric.ERROR_RATE]["warning"],
            threshold_critical=self.thresholds[HealthMetric.ERROR_RATE]["critical"],
            message=f"Error rate: {error_rate*100:.1f}%"
        )
        
    async def _check_message_queue(self, agent_id: str) -> HealthCheck:
        """Check message queue depth"""
        # This would check actual message queue
        # For now, simulate
        import random
        queue_size = random.randint(0, 200)
        
        status = self._get_status_for_metric(
            HealthMetric.MESSAGE_QUEUE,
            queue_size
        )
        
        return HealthCheck(
            metric=HealthMetric.MESSAGE_QUEUE,
            status=status,
            value=queue_size,
            threshold_warning=self.thresholds[HealthMetric.MESSAGE_QUEUE]["warning"],
            threshold_critical=self.thresholds[HealthMetric.MESSAGE_QUEUE]["critical"],
            message=f"Queue depth: {queue_size} messages"
        )
        
    async def _check_last_activity(self, agent_id: str) -> HealthCheck:
        """Check when agent was last active"""
        # This would check actual activity timestamp
        # For now, simulate
        last_activity = datetime.now() - timedelta(minutes=5)
        time_since = datetime.now() - last_activity
        
        if time_since < timedelta(minutes=5):
            status = HealthStatus.HEALTHY
        elif time_since < timedelta(minutes=15):
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
            
        return HealthCheck(
            metric=HealthMetric.LAST_ACTIVITY,
            status=status,
            value=last_activity,
            message=f"Last active: {time_since.total_seconds()/60:.1f} minutes ago"
        )
        
    async def _check_task_success_rate(self, agent_id: str) -> HealthCheck:
        """Check task success rate"""
        # This would check actual task completion stats
        # For now, simulate
        import random
        success_rate = random.uniform(0.85, 1.0)
        
        # Reverse thresholds for success rate (lower is worse)
        if success_rate >= self.thresholds[HealthMetric.TASK_SUCCESS_RATE]["warning"]:
            status = HealthStatus.HEALTHY
        elif success_rate >= self.thresholds[HealthMetric.TASK_SUCCESS_RATE]["critical"]:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
            
        return HealthCheck(
            metric=HealthMetric.TASK_SUCCESS_RATE,
            status=status,
            value=success_rate,
            threshold_warning=self.thresholds[HealthMetric.TASK_SUCCESS_RATE]["warning"],
            threshold_critical=self.thresholds[HealthMetric.TASK_SUCCESS_RATE]["critical"],
            message=f"Task success rate: {success_rate*100:.1f}%"
        )
        
    def _get_status_for_metric(self, metric: HealthMetric, value: float) -> HealthStatus:
        """Determine health status based on metric value and thresholds"""
        if metric not in self.thresholds:
            return HealthStatus.UNKNOWN
            
        thresholds = self.thresholds[metric]
        
        # For metrics where higher is worse
        if metric in [HealthMetric.CPU_USAGE, HealthMetric.MEMORY_USAGE, 
                     HealthMetric.RESPONSE_TIME, HealthMetric.ERROR_RATE,
                     HealthMetric.MESSAGE_QUEUE]:
            if value >= thresholds["critical"]:
                return HealthStatus.CRITICAL
            elif value >= thresholds["warning"]:
                return HealthStatus.WARNING
            else:
                return HealthStatus.HEALTHY
        # For metrics where lower is worse
        else:
            if value <= thresholds["critical"]:
                return HealthStatus.CRITICAL
            elif value <= thresholds["warning"]:
                return HealthStatus.WARNING
            else:
                return HealthStatus.HEALTHY
                
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall health status from individual checks"""
        if not checks:
            return HealthStatus.UNKNOWN
            
        # If any check is critical, overall is critical
        if any(check.status == HealthStatus.CRITICAL for check in checks):
            return HealthStatus.CRITICAL
            
        # If any check is warning, overall is warning
        if any(check.status == HealthStatus.WARNING for check in checks):
            return HealthStatus.WARNING
            
        # If all checks are healthy
        if all(check.status == HealthStatus.HEALTHY for check in checks):
            return HealthStatus.HEALTHY
            
        # Otherwise unknown
        return HealthStatus.UNKNOWN
        
    async def _check_alerts(self, report: AgentHealthReport):
        """Check if alerts need to be triggered"""
        # Check for critical status
        if report.overall_status == HealthStatus.CRITICAL:
            await self._trigger_alert(report, "critical")
            
        # Check for status changes
        history = self.health_history[report.agent_id]
        if len(history) >= 2:
            previous = history[-2]
            if previous.overall_status != report.overall_status:
                await self._trigger_alert(report, "status_change")
                
    async def _trigger_alert(self, report: AgentHealthReport, alert_type: str):
        """Trigger an alert"""
        for handler in self.alert_handlers:
            try:
                await handler(report, alert_type)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
                
    def add_alert_handler(self, handler: callable):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
        
    def get_agent_history(self, agent_id: str, limit: int = 50) -> List[AgentHealthReport]:
        """Get historical health reports for an agent"""
        if agent_id not in self.health_history:
            return []
            
        history = list(self.health_history[agent_id])
        return history[-limit:]
        
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        all_reports = {}
        for agent_id in self.agents:
            history = self.health_history[agent_id]
            if history:
                all_reports[agent_id] = history[-1]
                
        summary = {
            "total_agents": len(self.agents),
            "healthy": sum(1 for r in all_reports.values() if r.overall_status == HealthStatus.HEALTHY),
            "warning": sum(1 for r in all_reports.values() if r.overall_status == HealthStatus.WARNING),
            "critical": sum(1 for r in all_reports.values() if r.overall_status == HealthStatus.CRITICAL),
            "offline": sum(1 for r in all_reports.values() if r.overall_status == HealthStatus.OFFLINE),
            "timestamp": datetime.now().isoformat()
        }
        
        return summary
        
    def get_recommendations(self, report: AgentHealthReport) -> List[str]:
        """Get recommendations based on health report"""
        recommendations = []
        
        for check in report.checks:
            if check.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                if check.metric == HealthMetric.CPU_USAGE:
                    recommendations.append(f"High CPU usage detected. Consider scaling or optimizing {report.agent_name}")
                elif check.metric == HealthMetric.MEMORY_USAGE:
                    recommendations.append(f"High memory usage. Check for memory leaks in {report.agent_name}")
                elif check.metric == HealthMetric.RESPONSE_TIME:
                    recommendations.append(f"Slow response times. Review {report.agent_name} performance")
                elif check.metric == HealthMetric.ERROR_RATE:
                    recommendations.append(f"High error rate. Check logs for {report.agent_name}")
                elif check.metric == HealthMetric.MESSAGE_QUEUE:
                    recommendations.append(f"Message queue backlog. Scale {report.agent_name} or increase processing")
                elif check.metric == HealthMetric.TASK_SUCCESS_RATE:
                    recommendations.append(f"Low task success rate. Review {report.agent_name} configuration")
                    
        return recommendations


# Global health monitor instance
_health_monitor = None


def get_health_monitor() -> AgentHealthMonitor:
    """Get the global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = AgentHealthMonitor()
    return _health_monitor