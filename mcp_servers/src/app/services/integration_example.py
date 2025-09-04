"""
Example of integrating ProcessMonitor with MCP services.

This demonstrates how to use the ProcessMonitor to replace hardcoded data
with real process monitoring capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from .process_monitor import ProcessMonitor, MonitoringAlert
from .process_manager import ProcessManager
from ..schemas.mcp_server import MCPServerStatus, ProcessMetrics


logger = logging.getLogger(__name__)


class MCPProcessService:
    """
    Integrated MCP Process Service combining monitoring and management.
    
    This service demonstrates how to use ProcessMonitor and ProcessManager
    together to provide comprehensive process lifecycle management with
    real-time monitoring capabilities.
    """
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.process_monitor = ProcessMonitor(
            monitoring_interval=5.0,
            health_check_interval=30.0,
            enable_alerts=True
        )
        
        # Set up alert handling
        self.process_monitor.add_alert_callback(self._handle_process_alert)
        
        # Configure alert thresholds
        self.process_monitor.set_alert_threshold('cpu_percent', 80.0)
        self.process_monitor.set_alert_threshold('memory_percent', 85.0)
        self.process_monitor.set_alert_threshold('memory_mb', 512.0)  # 512MB
    
    async def start_service(self):
        """Start the integrated service."""
        logger.info("Starting MCP Process Service")
        await self.process_monitor.start_monitoring()
        logger.info("MCP Process Service started")
    
    async def stop_service(self):
        """Stop the integrated service."""
        logger.info("Stopping MCP Process Service")
        await self.process_manager.shutdown()
        await self.process_monitor.stop_monitoring()
        logger.info("MCP Process Service stopped")
    
    async def start_mcp_server(
        self,
        server_id: str,
        name: str,
        command: List[str],
        working_directory: str = None,
        environment: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Start an MCP server with integrated monitoring.
        
        Args:
            server_id: Unique server identifier
            name: Human-readable server name
            command: Command to execute
            working_directory: Working directory for the process
            environment: Environment variables
            
        Returns:
            Dictionary with server status and initial metrics
        """
        try:
            # Start the process using ProcessManager
            process_info = await self.process_manager.start_server(
                server_id=server_id,
                name=name,
                command=command,
                working_directory=working_directory,
                environment=environment
            )
            
            # Add to monitoring if successful
            if process_info.pid and process_info.status == MCPServerStatus.ACTIVE:
                self.process_monitor.add_process(
                    server_id=server_id,
                    pid=process_info.pid,
                    start_time=process_info.start_time
                )
                
                logger.info(f"Started and monitoring MCP server '{name}' (PID: {process_info.pid})")
                
                # Return comprehensive status
                return {
                    'server_id': server_id,
                    'name': name,
                    'pid': process_info.pid,
                    'status': process_info.status.value,
                    'start_time': process_info.start_time,
                    'monitoring_enabled': True,
                    'metrics': self._get_current_metrics(server_id)
                }
            else:
                return {
                    'server_id': server_id,
                    'name': name,
                    'status': process_info.status.value,
                    'error': process_info.last_error,
                    'monitoring_enabled': False
                }
                
        except Exception as e:
            logger.error(f"Failed to start MCP server '{name}': {e}")
            return {
                'server_id': server_id,
                'name': name,
                'status': 'error',
                'error': str(e),
                'monitoring_enabled': False
            }
    
    async def stop_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """
        Stop an MCP server and remove from monitoring.
        
        Args:
            server_id: Server identifier to stop
            
        Returns:
            Dictionary with operation status
        """
        try:
            # Stop monitoring first
            self.process_monitor.remove_process(server_id)
            
            # Stop the process
            success = await self.process_manager.stop_server(server_id)
            
            return {
                'server_id': server_id,
                'success': success,
                'status': 'stopped' if success else 'error',
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop MCP server '{server_id}': {e}")
            return {
                'server_id': server_id,
                'success': False,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    async def restart_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """
        Restart an MCP server with monitoring.
        
        Args:
            server_id: Server identifier to restart
            
        Returns:
            Dictionary with restart status
        """
        try:
            # Get current process info
            process_info = self.process_manager.get_server_info(server_id)
            if not process_info:
                return {
                    'server_id': server_id,
                    'success': False,
                    'error': 'Server not found'
                }
            
            # Stop monitoring
            self.process_monitor.remove_process(server_id)
            
            # Restart process
            restarted_info = await self.process_manager.restart_server(server_id)
            
            # Resume monitoring
            if restarted_info.pid and restarted_info.status == MCPServerStatus.ACTIVE:
                self.process_monitor.add_process(
                    server_id=server_id,
                    pid=restarted_info.pid,
                    start_time=restarted_info.start_time
                )
            
            return {
                'server_id': server_id,
                'success': True,
                'pid': restarted_info.pid,
                'status': restarted_info.status.value,
                'restart_count': restarted_info.restart_count,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to restart MCP server '{server_id}': {e}")
            return {
                'server_id': server_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get comprehensive server status including real-time metrics.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Dictionary with complete server status
        """
        # Get process manager info
        process_info = self.process_manager.get_server_info(server_id)
        if not process_info:
            return {'error': 'Server not found'}
        
        # Get real-time metrics
        metrics = self.process_monitor.get_process_metrics(server_id)
        extended_metrics = self.process_monitor.get_extended_metrics(server_id)
        health = self.process_monitor.get_process_health(server_id)
        trends = self.process_monitor.get_process_trends(server_id)
        
        # Build comprehensive status
        status = {
            'server_id': server_id,
            'name': process_info.name,
            'pid': process_info.pid,
            'status': process_info.status.value,
            'start_time': process_info.start_time,
            'restart_count': process_info.restart_count,
            'command': process_info.command,
            'working_directory': process_info.working_directory,
            'is_running': self.process_monitor.is_process_running(server_id),
            'last_error': process_info.last_error
        }
        
        # Add metrics if available
        if metrics:
            status['metrics'] = {
                'pid': metrics.pid,
                'cpu_percent': metrics.cpu_percent,
                'memory_mb': metrics.memory_mb,
                'uptime_seconds': metrics.uptime_seconds,
                'status': metrics.status,
                'num_threads': metrics.num_threads,
                'num_fds': metrics.num_fds
            }
        
        # Add extended metrics if available
        if extended_metrics:
            status['extended_metrics'] = {
                'memory_percent': extended_metrics.memory_percent,
                'cpu_times_user': extended_metrics.cpu_times_user,
                'cpu_times_system': extended_metrics.cpu_times_system,
                'io_read_bytes': extended_metrics.io_read_bytes,
                'io_write_bytes': extended_metrics.io_write_bytes,
                'connections_count': extended_metrics.connections_count,
                'open_files_count': extended_metrics.open_files_count
            }
        
        # Add health information
        if health:
            status['health'] = {
                'is_healthy': health.is_healthy,
                'issues': health.issues,
                'warning_count': health.warning_count,
                'error_count': health.error_count,
                'last_check': health.last_check
            }
        
        # Add performance trends
        if trends:
            status['trends'] = {
                'avg_cpu': trends.avg_cpu,
                'avg_memory': trends.avg_memory,
                'peak_cpu': trends.peak_cpu,
                'peak_memory': trends.peak_memory,
                'samples': len(trends.cpu_history)
            }
        
        return status
    
    def list_all_servers(self) -> List[Dict[str, Any]]:
        """
        List all servers with their current status and metrics.
        
        Returns:
            List of server status dictionaries
        """
        servers = []
        for process_info in self.process_manager.list_servers():
            server_status = self.get_server_status(process_info.server_id)
            servers.append(server_status)
        
        return servers
    
    def get_server_alerts(self, server_id: str = None) -> List[Dict[str, Any]]:
        """
        Get monitoring alerts for servers.
        
        Args:
            server_id: Optional server to filter alerts for
            
        Returns:
            List of alert dictionaries
        """
        alerts = self.process_monitor.get_alerts(server_id)
        return [
            {
                'server_id': alert.server_id,
                'type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': alert.timestamp,
                'value': alert.value,
                'threshold': alert.threshold
            }
            for alert in alerts
        ]
    
    def clear_server_alerts(self, server_id: str = None):
        """Clear alerts for a server or all servers."""
        self.process_monitor.clear_alerts(server_id)
    
    async def discover_existing_processes(self) -> List[Dict[str, Any]]:
        """
        Discover existing MCP-related processes that could be managed.
        
        Returns:
            List of discovered process information
        """
        return await self.process_monitor.discover_mcp_processes()
    
    def _get_current_metrics(self, server_id: str) -> Dict[str, Any]:
        """Get current metrics for a server."""
        metrics = self.process_monitor.get_process_metrics(server_id)
        if metrics:
            return {
                'cpu_percent': metrics.cpu_percent,
                'memory_mb': metrics.memory_mb,
                'uptime_seconds': metrics.uptime_seconds,
                'num_threads': metrics.num_threads,
                'num_fds': metrics.num_fds
            }
        return {}
    
    def _handle_process_alert(self, alert: MonitoringAlert):
        """
        Handle process monitoring alerts.
        
        This method can be extended to implement automatic responses
        to process health issues, such as restarting unhealthy processes.
        """
        logger.warning(f"Process alert for {alert.server_id}: {alert.message}")
        
        # Example: Auto-restart on critical errors
        if alert.severity == 'critical' and alert.alert_type == 'process_health':
            logger.info(f"Critical process health issue detected for {alert.server_id}, "
                       "consider implementing auto-restart logic here")
            
            # Uncomment to enable auto-restart:
            # asyncio.create_task(self._auto_restart_server(alert.server_id))
    
    async def _auto_restart_server(self, server_id: str):
        """
        Automatically restart a server in response to health issues.
        
        Args:
            server_id: Server to restart
        """
        try:
            logger.info(f"Auto-restarting server {server_id} due to health issues")
            result = await self.restart_mcp_server(server_id)
            
            if result['success']:
                logger.info(f"Successfully auto-restarted server {server_id}")
            else:
                logger.error(f"Failed to auto-restart server {server_id}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error during auto-restart of server {server_id}: {e}")


# Example usage function
async def example_usage():
    """Example of how to use the integrated MCP Process Service."""
    service = MCPProcessService()
    
    try:
        # Start the service
        await service.start_service()
        
        # Start an MCP server (example)
        result = await service.start_mcp_server(
            server_id='example_server',
            name='Example MCP Server',
            command=['python', '-c', 'import time; time.sleep(60)'],
            working_directory='/tmp'
        )
        
        print(f"Server start result: {result}")
        
        # Wait a moment for metrics to be collected
        await asyncio.sleep(2)
        
        # Get server status with real metrics
        status = service.get_server_status('example_server')
        print(f"Server status: {status}")
        
        # Stop the server
        stop_result = await service.stop_mcp_server('example_server')
        print(f"Server stop result: {stop_result}")
        
    finally:
        # Clean up
        await service.stop_service()


if __name__ == '__main__':
    # Run the example
    asyncio.run(example_usage())