"""
Tests for the Process Monitor service.

Tests the process monitoring functionality including metrics collection,
health checking, alerts, and process lifecycle management.
"""

import asyncio
import os
import subprocess
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import pytest
import psutil
from psutil import NoSuchProcess, AccessDenied

from app.services.process_monitor import (
    ProcessMonitor,
    ProcessState,
    ProcessHealth,
    ProcessTrends,
    ExtendedProcessMetrics,
    MonitoringAlert
)
from app.schemas.mcp_server import ProcessMetrics


class TestProcessMonitor:
    """Test cases for ProcessMonitor class."""
    
    @pytest.fixture
    def monitor(self):
        """Create a ProcessMonitor instance for testing."""
        return ProcessMonitor(
            monitoring_interval=0.1,  # Fast for testing
            health_check_interval=0.5,
            trend_window_size=5,
            enable_alerts=True
        )
    
    @pytest.fixture
    def mock_process(self):
        """Create a mock psutil.Process object."""
        process = Mock(spec=psutil.Process)
        process.pid = 12345
        process.is_running.return_value = True
        process.cpu_percent.return_value = 25.5
        process.memory_percent.return_value = 45.2
        process.memory_info.return_value = Mock(
            rss=104857600,  # 100MB
            vms=209715200,  # 200MB
            shared=0
        )
        process.status.return_value = 'running'
        process.num_threads.return_value = 5
        process.num_fds.return_value = 20
        process.create_time.return_value = time.time() - 3600  # 1 hour ago
        process.cpu_times.return_value = Mock(user=10.5, system=2.3)
        process.nice.return_value = 0
        process.cmdline.return_value = ['python', '-m', 'mcp.server']
        process.exe.return_value = '/usr/bin/python'
        process.cwd.return_value = '/tmp'
        process.username.return_value = 'testuser'
        process.ppid.return_value = 1234
        process.children.return_value = []
        process.open_files.return_value = []
        process.connections.return_value = []
        process.io_counters.return_value = Mock(
            read_count=100,
            write_count=50,
            read_bytes=1024000,
            write_bytes=512000
        )
        process.num_ctx_switches.return_value = Mock(
            voluntary=1000,
            involuntary=50
        )
        return process
    
    @pytest.fixture
    def real_test_process(self):
        """Create a real test process for integration testing."""
        # Start a simple Python process that we can monitor
        proc = subprocess.Popen([
            'python', '-c', 'import time; time.sleep(10)'
        ])
        yield proc.pid
        
        # Clean up
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass
    
    def test_init(self, monitor):
        """Test ProcessMonitor initialization."""
        assert monitor.monitoring_interval == 0.1
        assert monitor.health_check_interval == 0.5
        assert monitor.trend_window_size == 5
        assert monitor.enable_alerts is True
        assert len(monitor._monitored_processes) == 0
        assert len(monitor._process_metrics) == 0
        assert len(monitor._alerts) == 0
    
    @patch('app.services.process_monitor.psutil.Process')
    def test_add_process_valid(self, mock_process_class, monitor, mock_process):
        """Test adding a valid process to monitoring."""
        mock_process_class.return_value = mock_process
        
        # Add process
        monitor.add_process('test_server', 12345)
        
        # Verify process was added
        assert 'test_server' in monitor._monitored_processes
        assert monitor._monitored_processes['test_server'] == 12345
        assert 'test_server' in monitor._process_start_times
        assert 'test_server' in monitor._monitoring_tasks
    
    @patch('app.services.process_monitor.psutil.Process')
    def test_add_process_invalid(self, mock_process_class, monitor):
        """Test adding an invalid process raises error."""
        mock_process = Mock()
        mock_process.is_running.side_effect = NoSuchProcess(12345)
        mock_process_class.side_effect = NoSuchProcess(12345)
        
        with pytest.raises(ValueError, match="Process 12345 is not valid"):
            monitor.add_process('test_server', 12345)
    
    def test_remove_process(self, monitor):
        """Test removing a process from monitoring."""
        # Add a mock task
        task = Mock(spec=asyncio.Task)
        monitor._monitoring_tasks['test_server'] = task
        monitor._monitored_processes['test_server'] = 12345
        monitor._process_metrics['test_server'] = Mock()
        monitor._process_start_times['test_server'] = datetime.now()
        
        # Remove process
        monitor.remove_process('test_server')
        
        # Verify removal
        task.cancel.assert_called_once()
        assert 'test_server' not in monitor._monitored_processes
        assert 'test_server' not in monitor._process_metrics
        assert 'test_server' not in monitor._process_start_times
        assert 'test_server' not in monitor._monitoring_tasks
    
    @patch('app.services.process_monitor.psutil.Process')
    def test_is_process_running_valid(self, mock_process_class, monitor, mock_process):
        """Test checking if a valid process is running."""
        mock_process_class.return_value = mock_process
        monitor._monitored_processes['test_server'] = 12345
        
        assert monitor.is_process_running('test_server') is True
    
    @patch('app.services.process_monitor.psutil.Process')
    def test_is_process_running_invalid(self, mock_process_class, monitor):
        """Test checking if an invalid process is running."""
        mock_process_class.side_effect = NoSuchProcess(12345)
        monitor._monitored_processes['test_server'] = 12345
        
        assert monitor.is_process_running('test_server') is False
    
    def test_is_process_running_not_monitored(self, monitor):
        """Test checking if a non-monitored process is running."""
        assert monitor.is_process_running('unknown_server') is False
    
    @patch('app.services.process_monitor.psutil.Process')
    async def test_collect_process_metrics(self, mock_process_class, monitor, mock_process):
        """Test collecting process metrics."""
        mock_process_class.return_value = mock_process
        
        # Collect metrics
        metrics = await monitor._collect_process_metrics('test_server', 12345)
        
        # Verify metrics
        assert metrics is not None
        assert metrics.pid == 12345
        assert metrics.cpu_percent == 25.5
        assert metrics.memory_percent == 45.2
        assert metrics.memory_mb == 100.0  # 104857600 / (1024*1024)
        assert metrics.status == 'running'
        assert metrics.num_threads == 5
        assert metrics.num_fds == 20
        assert metrics.cmdline == ['python', '-m', 'mcp.server']
        assert metrics.exe == '/usr/bin/python'
        assert metrics.cwd == '/tmp'
        assert metrics.username == 'testuser'
        assert isinstance(metrics.health, ProcessHealth)
        assert isinstance(metrics.trends, ProcessTrends)
    
    @patch('app.services.process_monitor.psutil.Process')
    async def test_collect_process_metrics_no_access(self, mock_process_class, monitor):
        """Test collecting metrics when process is not accessible."""
        mock_process_class.side_effect = AccessDenied()
        
        metrics = await monitor._collect_process_metrics('test_server', 12345)
        
        assert metrics is None
    
    def test_assess_process_health_healthy(self, monitor):
        """Test health assessment for a healthy process."""
        metrics = {
            'cpu_percent': 30.0,
            'memory_percent': 40.0,
            'memory_mb': 100.0,
            'num_fds': 50,
            'num_threads': 10,
            'status': 'running'
        }
        
        health = monitor._assess_process_health('test_server', metrics)
        
        assert health.is_healthy is True
        assert len(health.issues) == 0
        assert health.warning_count == 0
        assert health.error_count == 0
    
    def test_assess_process_health_high_cpu(self, monitor):
        """Test health assessment with high CPU usage."""
        metrics = {
            'cpu_percent': 90.0,  # Above default threshold of 80
            'memory_percent': 40.0,
            'memory_mb': 100.0,
            'num_fds': 50,
            'num_threads': 10,
            'status': 'running'
        }
        
        health = monitor._assess_process_health('test_server', metrics)
        
        assert health.is_healthy is False
        assert len(health.issues) == 1
        assert 'High CPU usage' in health.issues[0]
        assert health.warning_count == 1
        assert health.error_count == 0
    
    def test_assess_process_health_critical_memory(self, monitor):
        """Test health assessment with critical memory usage."""
        metrics = {
            'cpu_percent': 30.0,
            'memory_percent': 97.0,  # Critical level
            'memory_mb': 100.0,
            'num_fds': 50,
            'num_threads': 10,
            'status': 'running'
        }
        
        health = monitor._assess_process_health('test_server', metrics)
        
        assert health.is_healthy is False
        assert len(health.issues) == 1
        assert 'High memory usage' in health.issues[0]
        assert health.warning_count == 0
        assert health.error_count == 1
    
    def test_assess_process_health_zombie(self, monitor):
        """Test health assessment for zombie process."""
        metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_mb': 0.0,
            'num_fds': 0,
            'num_threads': 0,
            'status': 'zombie'
        }
        
        health = monitor._assess_process_health('test_server', metrics)
        
        assert health.is_healthy is False
        assert len(health.issues) == 1
        assert 'Process is in bad state: zombie' in health.issues[0]
        assert health.error_count == 1
    
    def test_update_trends(self, monitor):
        """Test updating performance trends."""
        # Create metrics with trends
        trends = ProcessTrends(trend_window=3)
        metrics = ExtendedProcessMetrics(
            pid=12345,
            cpu_percent=50.0,
            memory_mb=100.0,
            uptime_seconds=3600,
            status='running',
            num_threads=5,
            num_fds=20,
            memory_percent=45.0,
            cpu_times_user=10.0,
            cpu_times_system=2.0,
            memory_rss=104857600,
            memory_vms=209715200,
            memory_shared=0,
            io_read_count=100,
            io_write_count=50,
            io_read_bytes=1024000,
            io_write_bytes=512000,
            num_ctx_switches_voluntary=1000,
            num_ctx_switches_involuntary=50,
            nice=0,
            cmdline=['python'],
            exe='/usr/bin/python',
            cwd='/tmp',
            username='test',
            parent_pid=1234,
            children_pids=[],
            open_files_count=0,
            connections_count=0,
            create_time=time.time(),
            health=ProcessHealth(is_healthy=True),
            trends=trends
        )
        
        # Update trends multiple times
        for cpu, mem in [(30, 80), (40, 90), (60, 110), (35, 85)]:
            metrics.cpu_percent = cpu
            metrics.memory_mb = mem
            monitor._update_trends(metrics)
        
        # Check trends (should keep only last 3 values due to window size)
        assert len(trends.cpu_history) == 3
        assert len(trends.memory_history) == 3
        assert trends.cpu_history == [40, 60, 35]
        assert trends.memory_history == [90, 110, 85]
        assert trends.avg_cpu == (40 + 60 + 35) / 3
        assert trends.peak_cpu == 60
        assert trends.avg_memory == (90 + 110 + 85) / 3
        assert trends.peak_memory == 110
    
    async def test_check_alerts_high_cpu(self, monitor):
        """Test alert generation for high CPU usage."""
        # Create metrics with high CPU
        health = ProcessHealth(is_healthy=False, warning_count=1)
        trends = ProcessTrends()
        metrics = ExtendedProcessMetrics(
            pid=12345,
            cpu_percent=85.0,  # Above threshold
            memory_mb=100.0,
            uptime_seconds=3600,
            status='running',
            num_threads=5,
            num_fds=20,
            memory_percent=45.0,
            cpu_times_user=10.0,
            cpu_times_system=2.0,
            memory_rss=104857600,
            memory_vms=209715200,
            memory_shared=0,
            io_read_count=100,
            io_write_count=50,
            io_read_bytes=1024000,
            io_write_bytes=512000,
            num_ctx_switches_voluntary=1000,
            num_ctx_switches_involuntary=50,
            nice=0,
            cmdline=['python'],
            exe='/usr/bin/python',
            cwd='/tmp',
            username='test',
            parent_pid=1234,
            children_pids=[],
            open_files_count=0,
            connections_count=0,
            create_time=time.time(),
            health=health,
            trends=trends
        )
        
        initial_alert_count = len(monitor._alerts)
        await monitor._check_alerts('test_server', metrics)
        
        # Should have generated alerts
        assert len(monitor._alerts) > initial_alert_count
        
        # Find CPU alert
        cpu_alerts = [a for a in monitor._alerts if a.alert_type == 'high_cpu']
        assert len(cpu_alerts) > 0
        
        cpu_alert = cpu_alerts[-1]  # Get the latest
        assert cpu_alert.server_id == 'test_server'
        assert cpu_alert.severity == 'warning'
        assert cpu_alert.value == 85.0
        assert 'High CPU usage' in cpu_alert.message
    
    def test_get_process_metrics_schema_format(self, monitor):
        """Test getting metrics in schema format."""
        # Add extended metrics
        health = ProcessHealth(is_healthy=True)
        trends = ProcessTrends()
        extended_metrics = ExtendedProcessMetrics(
            pid=12345,
            cpu_percent=25.5,
            memory_mb=100.0,
            uptime_seconds=3600,
            status='running',
            num_threads=5,
            num_fds=20,
            memory_percent=45.0,
            cpu_times_user=10.0,
            cpu_times_system=2.0,
            memory_rss=104857600,
            memory_vms=209715200,
            memory_shared=0,
            io_read_count=100,
            io_write_count=50,
            io_read_bytes=1024000,
            io_write_bytes=512000,
            num_ctx_switches_voluntary=1000,
            num_ctx_switches_involuntary=50,
            nice=0,
            cmdline=['python'],
            exe='/usr/bin/python',
            cwd='/tmp',
            username='test',
            parent_pid=1234,
            children_pids=[],
            open_files_count=0,
            connections_count=0,
            create_time=time.time(),
            health=health,
            trends=trends
        )
        
        monitor._process_metrics['test_server'] = extended_metrics
        
        # Get schema format
        metrics = monitor.get_process_metrics('test_server')
        
        assert isinstance(metrics, ProcessMetrics)
        assert metrics.pid == 12345
        assert metrics.cpu_percent == 25.5
        assert metrics.memory_mb == 100.0
        assert metrics.uptime_seconds == 3600
        assert metrics.status == 'running'
        assert metrics.num_threads == 5
        assert metrics.num_fds == 20
    
    def test_set_alert_threshold(self, monitor):
        """Test setting custom alert thresholds."""
        monitor.set_alert_threshold('cpu_percent', 90.0)
        monitor.set_alert_threshold('memory_percent', 95.0)
        
        assert monitor._alert_thresholds['cpu_percent'] == 90.0
        assert monitor._alert_thresholds['memory_percent'] == 95.0
    
    def test_add_alert_callback(self, monitor):
        """Test adding alert callback."""
        callback = Mock()
        monitor.add_alert_callback(callback)
        
        assert callback in monitor._alert_callbacks
    
    def test_clear_alerts_all(self, monitor):
        """Test clearing all alerts."""
        # Add some test alerts
        alert1 = MonitoringAlert(
            server_id='server1',
            alert_type='test',
            severity='warning',
            message='Test alert 1',
            timestamp=datetime.now()
        )
        alert2 = MonitoringAlert(
            server_id='server2',
            alert_type='test',
            severity='error',
            message='Test alert 2',
            timestamp=datetime.now()
        )
        
        monitor._alerts = [alert1, alert2]
        
        # Clear all
        monitor.clear_alerts()
        
        assert len(monitor._alerts) == 0
    
    def test_clear_alerts_by_server(self, monitor):
        """Test clearing alerts for specific server."""
        # Add some test alerts
        alert1 = MonitoringAlert(
            server_id='server1',
            alert_type='test',
            severity='warning',
            message='Test alert 1',
            timestamp=datetime.now()
        )
        alert2 = MonitoringAlert(
            server_id='server2',
            alert_type='test',
            severity='error',
            message='Test alert 2',
            timestamp=datetime.now()
        )
        
        monitor._alerts = [alert1, alert2]
        
        # Clear for server1 only
        monitor.clear_alerts('server1')
        
        assert len(monitor._alerts) == 1
        assert monitor._alerts[0].server_id == 'server2'
    
    def test_get_alerts_all(self, monitor):
        """Test getting all alerts."""
        # Add test alerts
        alert1 = MonitoringAlert(
            server_id='server1',
            alert_type='test',
            severity='warning',
            message='Test alert 1',
            timestamp=datetime.now()
        )
        alert2 = MonitoringAlert(
            server_id='server2',
            alert_type='test',
            severity='error',
            message='Test alert 2',
            timestamp=datetime.now()
        )
        
        monitor._alerts = [alert1, alert2]
        
        alerts = monitor.get_alerts()
        
        assert len(alerts) == 2
        assert alerts[0].server_id == 'server1'
        assert alerts[1].server_id == 'server2'
    
    def test_get_alerts_by_server(self, monitor):
        """Test getting alerts for specific server."""
        # Add test alerts
        alert1 = MonitoringAlert(
            server_id='server1',
            alert_type='test',
            severity='warning',
            message='Test alert 1',
            timestamp=datetime.now()
        )
        alert2 = MonitoringAlert(
            server_id='server2',
            alert_type='test',
            severity='error',
            message='Test alert 2',
            timestamp=datetime.now()
        )
        
        monitor._alerts = [alert1, alert2]
        
        alerts = monitor.get_alerts('server1')
        
        assert len(alerts) == 1
        assert alerts[0].server_id == 'server1'
    
    @patch('app.services.process_monitor.psutil.process_iter')
    async def test_discover_mcp_processes(self, mock_process_iter, monitor):
        """Test discovering MCP-related processes."""
        # Mock processes
        mock_proc1 = Mock()
        mock_proc1.info = {
            'pid': 1001,
            'name': 'python',
            'cmdline': ['python', '-m', 'mcp.server', '--config', 'test.json'],
            'create_time': time.time() - 3600
        }
        
        mock_proc2 = Mock()
        mock_proc2.info = {
            'pid': 1002,
            'name': 'node',
            'cmdline': ['node', 'mcp-server.js'],
            'create_time': time.time() - 1800
        }
        
        mock_proc3 = Mock()
        mock_proc3.info = {
            'pid': 1003,
            'name': 'bash',
            'cmdline': ['bash', '-c', 'some other command'],
            'create_time': time.time() - 900
        }
        
        mock_process_iter.return_value = [mock_proc1, mock_proc2, mock_proc3]
        
        discovered = await monitor.discover_mcp_processes()
        
        # Should find the first two processes (MCP-related)
        assert len(discovered) >= 2
        
        # Check that the right processes were found
        pids = [proc['pid'] for proc in discovered]
        assert 1001 in pids  # python mcp process
        assert 1002 in pids  # node mcp process
        # 1003 should not be included (not MCP-related)
    
    def test_is_mcp_process_python_mcp(self, monitor):
        """Test identifying Python MCP process."""
        assert monitor._is_mcp_process(
            'python',
            ['python', '-m', 'mcp.server', '--config', 'test.json']
        ) is True
    
    def test_is_mcp_process_node_mcp(self, monitor):
        """Test identifying Node MCP process."""
        assert monitor._is_mcp_process(
            'node',
            ['node', 'mcp-server.js']
        ) is True
    
    def test_is_mcp_process_not_mcp(self, monitor):
        """Test rejecting non-MCP process."""
        assert monitor._is_mcp_process(
            'bash',
            ['bash', '-c', 'ls -la']
        ) is False
    
    @pytest.mark.integration
    async def test_real_process_monitoring(self, monitor, real_test_process):
        """Integration test with real process monitoring."""
        # Add the real process to monitoring
        monitor.add_process('real_test', real_test_process)
        
        # Wait a moment for monitoring to start
        await asyncio.sleep(0.2)
        
        # Check that process is being monitored
        assert monitor.is_process_running('real_test') is True
        
        # Get metrics
        metrics = monitor.get_process_metrics('real_test')
        assert metrics is not None
        assert metrics.pid == real_test_process
        assert metrics.cpu_percent >= 0
        assert metrics.memory_mb > 0
        
        # Get extended metrics
        extended = monitor.get_extended_metrics('real_test')
        assert extended is not None
        assert extended.cmdline is not None
        assert len(extended.cmdline) > 0
        
        # Clean up
        monitor.remove_process('real_test')
    
    @pytest.mark.integration
    async def test_monitoring_lifecycle(self, monitor):
        """Integration test for full monitoring lifecycle."""
        # Start monitoring
        await monitor.start_monitoring()
        
        # Monitor should be running
        assert monitor._health_check_task is not None
        assert not monitor._shutdown_event.is_set()
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        # Monitor should be stopped
        assert monitor._shutdown_event.is_set()


class TestProcessHealth:
    """Test cases for ProcessHealth dataclass."""
    
    def test_process_health_creation(self):
        """Test creating ProcessHealth instance."""
        health = ProcessHealth(
            is_healthy=True,
            issues=['test issue'],
            warning_count=1,
            error_count=0
        )
        
        assert health.is_healthy is True
        assert len(health.issues) == 1
        assert health.issues[0] == 'test issue'
        assert health.warning_count == 1
        assert health.error_count == 0
        assert isinstance(health.last_check, datetime)


class TestProcessTrends:
    """Test cases for ProcessTrends dataclass."""
    
    def test_process_trends_creation(self):
        """Test creating ProcessTrends instance."""
        trends = ProcessTrends(
            cpu_history=[10.0, 20.0, 30.0],
            memory_history=[100.0, 150.0, 200.0],
            avg_cpu=20.0,
            avg_memory=150.0,
            peak_cpu=30.0,
            peak_memory=200.0,
            trend_window=10
        )
        
        assert len(trends.cpu_history) == 3
        assert len(trends.memory_history) == 3
        assert trends.avg_cpu == 20.0
        assert trends.avg_memory == 150.0
        assert trends.peak_cpu == 30.0
        assert trends.peak_memory == 200.0
        assert trends.trend_window == 10


class TestMonitoringAlert:
    """Test cases for MonitoringAlert dataclass."""
    
    def test_monitoring_alert_creation(self):
        """Test creating MonitoringAlert instance."""
        timestamp = datetime.now()
        alert = MonitoringAlert(
            server_id='test_server',
            alert_type='high_cpu',
            severity='warning',
            message='CPU usage is high',
            timestamp=timestamp,
            value=85.0,
            threshold=80.0
        )
        
        assert alert.server_id == 'test_server'
        assert alert.alert_type == 'high_cpu'
        assert alert.severity == 'warning'
        assert alert.message == 'CPU usage is high'
        assert alert.timestamp == timestamp
        assert alert.value == 85.0
        assert alert.threshold == 80.0


if __name__ == '__main__':
    pytest.main([__file__])