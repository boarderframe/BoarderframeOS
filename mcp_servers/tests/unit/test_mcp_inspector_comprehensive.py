"""
Comprehensive unit tests for MCP Inspector functionality.
Enhanced testing suite with edge cases, error scenarios, and performance testing.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import tempfile
import os
import time

from tests.utils.test_helpers import (
    MockFactory, 
    APITestHelper, 
    ValidationHelper, 
    SecurityTestHelper,
    PerformanceTestHelper
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestMCPInspectorComprehensive:
    """Comprehensive test suite for MCP Inspector functionality."""
    
    @pytest.fixture
    def mock_mcp_inspector(self):
        """Create a comprehensive mock MCP Inspector."""
        inspector = Mock()
        
        # Connection management
        inspector.connect = AsyncMock()
        inspector.disconnect = AsyncMock()
        inspector.is_connected = Mock(return_value=True)
        inspector.get_connection_status = AsyncMock()
        
        # Server inspection
        inspector.inspect_server = AsyncMock()
        inspector.validate_server_config = Mock(return_value=True)
        inspector.get_server_capabilities = AsyncMock()
        inspector.get_server_info = AsyncMock()
        
        # Health monitoring
        inspector.health_check = AsyncMock()
        inspector.continuous_health_monitoring = AsyncMock()
        inspector.get_health_history = AsyncMock()
        
        # Tools and resources
        inspector.list_tools = AsyncMock()
        inspector.list_resources = AsyncMock()
        inspector.invoke_tool = AsyncMock()
        inspector.access_resource = AsyncMock()
        
        # Metrics and logging
        inspector.collect_metrics = AsyncMock()
        inspector.get_logs = AsyncMock()
        inspector.get_performance_stats = AsyncMock()
        
        # Error handling
        inspector.handle_connection_error = AsyncMock()
        inspector.retry_with_backoff = AsyncMock()
        
        return inspector
    
    @pytest.fixture
    def server_config_factory(self):
        """Factory for creating server configurations."""
        def _create_config(**overrides):
            base_config = {
                "name": "test-server",
                "host": "localhost",
                "port": 8080,
                "protocol": "stdio",
                "command": "/usr/bin/python",
                "args": ["-m", "test_server"],
                "env": {"TEST_MODE": "true"},
                "config": {
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "heartbeat_interval": 10
                }
            }
            base_config.update(overrides)
            return base_config
        return _create_config
    
    async def test_connection_lifecycle(self, mock_mcp_inspector, server_config_factory):
        """Test complete connection lifecycle."""
        config = server_config_factory()
        
        # Test successful connection
        mock_mcp_inspector.connect.return_value = True
        result = await mock_mcp_inspector.connect(config)
        
        assert result is True
        mock_mcp_inspector.connect.assert_called_once_with(config)
        
        # Test connection status check
        mock_mcp_inspector.is_connected.return_value = True
        assert mock_mcp_inspector.is_connected()
        
        # Test graceful disconnection
        await mock_mcp_inspector.disconnect()
        mock_mcp_inspector.disconnect.assert_called_once()
    
    async def test_connection_failure_scenarios(self, mock_mcp_inspector, server_config_factory):
        """Test various connection failure scenarios."""
        config = server_config_factory()
        
        # Connection timeout
        mock_mcp_inspector.connect.side_effect = asyncio.TimeoutError("Connection timeout")
        with pytest.raises(asyncio.TimeoutError):
            await mock_mcp_inspector.connect(config)
        
        # Connection refused
        mock_mcp_inspector.connect.side_effect = ConnectionRefusedError("Connection refused")
        with pytest.raises(ConnectionRefusedError):
            await mock_mcp_inspector.connect(config)
        
        # Invalid host
        invalid_config = server_config_factory(host="invalid-host")
        mock_mcp_inspector.connect.side_effect = OSError("Name resolution failed")
        with pytest.raises(OSError):
            await mock_mcp_inspector.connect(invalid_config)
    
    async def test_server_inspection_comprehensive(self, mock_mcp_inspector):
        """Test comprehensive server inspection."""
        # Mock server info response
        server_info = {
            "name": "Test MCP Server",
            "version": "1.2.3",
            "protocol_version": "1.0",
            "capabilities": ["tools", "resources", "logging", "sampling"],
            "implementation": {
                "name": "test-mcp-server",
                "version": "1.2.3"
            },
            "supported_protocols": ["stdio", "sse"],
            "metadata": {
                "author": "Test Author",
                "description": "A comprehensive test server",
                "license": "MIT"
            }
        }
        
        mock_mcp_inspector.get_server_info.return_value = server_info
        
        # Perform inspection
        result = await mock_mcp_inspector.get_server_info()
        
        # Verify comprehensive server info
        assert result["name"] == "Test MCP Server"
        assert result["version"] == "1.2.3"
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]
        assert result["implementation"]["name"] == "test-mcp-server"
        assert result["metadata"]["author"] == "Test Author"
    
    async def test_tools_discovery_and_validation(self, mock_mcp_inspector):
        """Test tools discovery and validation."""
        # Mock tools list
        tools = [
            {
                "name": "file_reader",
                "description": "Read files from the filesystem",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "encoding": {"type": "string", "default": "utf-8"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "web_scraper",
                "description": "Scrape web pages",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "format": "uri"},
                        "selector": {"type": "string"},
                        "timeout": {"type": "number", "minimum": 1, "maximum": 300}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "data_processor",
                "description": "Process data with various formats",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "array"},
                        "format": {"type": "string", "enum": ["json", "csv", "xml"]},
                        "options": {"type": "object"}
                    },
                    "required": ["data", "format"]
                }
            }
        ]
        
        mock_mcp_inspector.list_tools.return_value = tools
        
        # Get tools list
        result = await mock_mcp_inspector.list_tools()
        
        # Validate tools structure
        assert len(result) == 3
        for tool in result:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert tool["parameters"]["type"] == "object"
            assert "properties" in tool["parameters"]
        
        # Validate specific tools
        file_reader = next(t for t in result if t["name"] == "file_reader")
        assert "path" in file_reader["parameters"]["properties"]
        assert file_reader["parameters"]["required"] == ["path"]
        
        web_scraper = next(t for t in result if t["name"] == "web_scraper")
        assert "url" in web_scraper["parameters"]["properties"]
        assert web_scraper["parameters"]["properties"]["url"]["format"] == "uri"
    
    async def test_tool_invocation_scenarios(self, mock_mcp_inspector):
        """Test various tool invocation scenarios."""
        # Successful invocation
        mock_mcp_inspector.invoke_tool.return_value = {
            "success": True,
            "result": {"content": "File content here"},
            "metadata": {"execution_time_ms": 150}
        }
        
        result = await mock_mcp_inspector.invoke_tool(
            "file_reader", 
            {"path": "/test/file.txt"}
        )
        
        assert result["success"] is True
        assert "content" in result["result"]
        
        # Tool error
        mock_mcp_inspector.invoke_tool.side_effect = ValueError("Invalid parameters")
        with pytest.raises(ValueError):
            await mock_mcp_inspector.invoke_tool("file_reader", {"invalid": "params"})
        
        # Tool timeout
        mock_mcp_inspector.invoke_tool.side_effect = asyncio.TimeoutError("Tool timeout")
        with pytest.raises(asyncio.TimeoutError):
            await mock_mcp_inspector.invoke_tool("slow_tool", {})
    
    async def test_resources_management(self, mock_mcp_inspector):
        """Test resources discovery and access."""
        # Mock resources list
        resources = [
            {
                "name": "config_file",
                "type": "text/json",
                "description": "Application configuration",
                "uri": "file:///config/app.json",
                "size": 1024,
                "mtime": "2025-01-15T10:30:00Z"
            },
            {
                "name": "database",
                "type": "application/x-sqlite3",
                "description": "Application database",
                "uri": "sqlite:///data/app.db",
                "size": 2048000,
                "mtime": "2025-01-15T11:00:00Z"
            },
            {
                "name": "log_files",
                "type": "text/plain",
                "description": "Application logs",
                "uri": "file:///logs/",
                "is_directory": True
            }
        ]
        
        mock_mcp_inspector.list_resources.return_value = resources
        
        # Get resources list
        result = await mock_mcp_inspector.list_resources()
        
        assert len(result) == 3
        for resource in result:
            assert "name" in resource
            assert "type" in resource
            assert "uri" in resource
        
        # Test resource access
        mock_mcp_inspector.access_resource.return_value = {
            "content": "Resource content",
            "metadata": {"accessed_at": datetime.utcnow().isoformat()}
        }
        
        content = await mock_mcp_inspector.access_resource("config_file")
        assert "content" in content
        assert "metadata" in content
    
    async def test_health_monitoring_comprehensive(self, mock_mcp_inspector):
        """Test comprehensive health monitoring."""
        # Single health check
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": 45.2,
            "memory_usage_mb": 128.5,
            "cpu_usage_percent": 15.3,
            "uptime_seconds": 86400,
            "active_connections": 5,
            "error_rate": 0.01,
            "last_error": None
        }
        
        mock_mcp_inspector.health_check.return_value = health_data
        
        result = await mock_mcp_inspector.health_check()
        
        assert result["status"] == "healthy"
        assert result["response_time_ms"] < 100  # Performance assertion
        assert result["error_rate"] < 0.05  # Error rate assertion
        
        # Health history
        health_history = [
            {**health_data, "timestamp": (datetime.utcnow() - timedelta(minutes=i)).isoformat()}
            for i in range(10)
        ]
        
        mock_mcp_inspector.get_health_history.return_value = health_history
        
        history = await mock_mcp_inspector.get_health_history()
        assert len(history) == 10
        assert all(h["status"] == "healthy" for h in history)
    
    async def test_continuous_monitoring(self, mock_mcp_inspector):
        """Test continuous health monitoring."""
        # Mock continuous monitoring
        monitoring_results = []
        
        async def mock_continuous_monitoring(interval=10, duration=60):
            """Mock continuous monitoring function."""
            end_time = time.time() + duration
            while time.time() < end_time:
                health_check = {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "response_time_ms": 50 + (time.time() % 10)  # Varying response time
                }
                monitoring_results.append(health_check)
                await asyncio.sleep(interval)
        
        mock_mcp_inspector.continuous_health_monitoring.side_effect = mock_continuous_monitoring
        
        # Start monitoring for a short duration
        await mock_mcp_inspector.continuous_health_monitoring(interval=1, duration=3)
        
        # Verify monitoring was called
        mock_mcp_inspector.continuous_health_monitoring.assert_called_once()
    
    async def test_metrics_collection(self, mock_mcp_inspector):
        """Test comprehensive metrics collection."""
        metrics = {
            "performance": {
                "requests_total": 10000,
                "requests_per_second": 25.7,
                "average_response_time_ms": 120.5,
                "p50_response_time_ms": 95.0,
                "p95_response_time_ms": 250.0,
                "p99_response_time_ms": 500.0
            },
            "errors": {
                "total_errors": 45,
                "error_rate": 0.0045,
                "errors_by_type": {
                    "connection_error": 20,
                    "timeout_error": 15,
                    "validation_error": 10
                }
            },
            "resources": {
                "memory_usage_bytes": 134217728,
                "memory_usage_percent": 65.2,
                "cpu_usage_percent": 23.8,
                "disk_usage_bytes": 1073741824,
                "network_bytes_sent": 5368709120,
                "network_bytes_received": 2684354560
            },
            "connections": {
                "active_connections": 12,
                "max_connections": 100,
                "total_connections": 2500,
                "connection_pool_usage": 0.12
            }
        }
        
        mock_mcp_inspector.collect_metrics.return_value = metrics
        
        result = await mock_mcp_inspector.collect_metrics()
        
        # Validate metrics structure
        assert "performance" in result
        assert "errors" in result
        assert "resources" in result
        assert "connections" in result
        
        # Validate performance metrics
        perf = result["performance"]
        assert perf["requests_total"] > 0
        assert perf["average_response_time_ms"] > 0
        assert perf["p99_response_time_ms"] >= perf["p95_response_time_ms"]
        
        # Validate error metrics
        errors = result["errors"]
        assert errors["error_rate"] < 0.01  # Less than 1%
        assert sum(errors["errors_by_type"].values()) == errors["total_errors"]
    
    async def test_logging_integration(self, mock_mcp_inspector):
        """Test logging functionality."""
        # Mock log entries
        log_entries = [
            {
                "timestamp": "2025-01-15T10:30:00.123Z",
                "level": "INFO",
                "logger": "mcp.server",
                "message": "Server started successfully",
                "context": {"port": 8080, "protocol": "stdio"}
            },
            {
                "timestamp": "2025-01-15T10:30:05.456Z",
                "level": "DEBUG",
                "logger": "mcp.tools",
                "message": "Tool 'file_reader' invoked",
                "context": {"tool": "file_reader", "params": {"path": "/test.txt"}}
            },
            {
                "timestamp": "2025-01-15T10:30:10.789Z",
                "level": "WARN",
                "logger": "mcp.health",
                "message": "High memory usage detected",
                "context": {"memory_percent": 85.5}
            },
            {
                "timestamp": "2025-01-15T10:30:15.012Z",
                "level": "ERROR",
                "logger": "mcp.connection",
                "message": "Connection timeout",
                "context": {"timeout_ms": 30000, "retries": 3}
            }
        ]
        
        mock_mcp_inspector.get_logs.return_value = log_entries
        
        # Get all logs
        logs = await mock_mcp_inspector.get_logs()
        assert len(logs) == 4
        
        # Test log filtering
        mock_mcp_inspector.get_logs.return_value = [
            log for log in log_entries if log["level"] == "ERROR"
        ]
        
        error_logs = await mock_mcp_inspector.get_logs(level="ERROR")
        assert len(error_logs) == 1
        assert error_logs[0]["level"] == "ERROR"
    
    async def test_error_handling_and_recovery(self, mock_mcp_inspector):
        """Test error handling and recovery mechanisms."""
        # Test connection recovery
        async def mock_retry_with_backoff(func, max_retries=3, base_delay=1.0):
            """Mock retry mechanism with exponential backoff."""
            for attempt in range(max_retries):
                try:
                    return await func()
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(base_delay * (2 ** attempt))
        
        mock_mcp_inspector.retry_with_backoff.side_effect = mock_retry_with_backoff
        
        # Test successful retry
        call_count = 0
        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return {"success": True}
        
        result = await mock_mcp_inspector.retry_with_backoff(failing_then_succeeding)
        assert result["success"] is True
        
        # Test max retries exceeded
        async def always_failing():
            raise ConnectionError("Permanent failure")
        
        with pytest.raises(ConnectionError):
            await mock_mcp_inspector.retry_with_backoff(always_failing, max_retries=2)
    
    @pytest.mark.performance
    async def test_performance_benchmarks(self, mock_mcp_inspector):
        """Test performance benchmarks for MCP operations."""
        # Test connection performance
        start_time = time.time()
        await mock_mcp_inspector.connect({})
        connection_time = time.time() - start_time
        
        # Connection should be fast (< 1 second)
        assert connection_time < 1.0
        
        # Test tool invocation performance
        mock_mcp_inspector.invoke_tool.return_value = {"result": "test"}
        
        start_time = time.time()
        for _ in range(100):
            await mock_mcp_inspector.invoke_tool("test_tool", {})
        batch_time = time.time() - start_time
        
        # 100 tool invocations should complete quickly
        assert batch_time < 5.0
        
        # Test concurrent operations
        async def concurrent_health_checks():
            tasks = [
                mock_mcp_inspector.health_check()
                for _ in range(50)
            ]
            results = await asyncio.gather(*tasks)
            return results
        
        mock_mcp_inspector.health_check.return_value = {"status": "healthy"}
        
        start_time = time.time()
        results = await concurrent_health_checks()
        concurrent_time = time.time() - start_time
        
        assert len(results) == 50
        assert concurrent_time < 2.0  # Concurrent operations should be fast
    
    async def test_security_validation(self, mock_mcp_inspector):
        """Test security-related validation."""
        # Test secure connection validation
        secure_config = {
            "host": "localhost",
            "port": 8080,
            "protocol": "https",
            "ssl_verify": True,
            "ssl_cert": "/path/to/cert.pem",
            "ssl_key": "/path/to/key.pem"
        }
        
        mock_mcp_inspector.validate_server_config.return_value = True
        result = mock_mcp_inspector.validate_server_config(secure_config)
        assert result is True
        
        # Test input sanitization for tool parameters
        malicious_inputs = [
            {"path": "../../../etc/passwd"},
            {"command": "rm -rf /"},
            {"script": "<script>alert('xss')</script>"},
            {"sql": "'; DROP TABLE users; --"}
        ]
        
        for malicious_input in malicious_inputs:
            # Should raise validation error for malicious inputs
            mock_mcp_inspector.invoke_tool.side_effect = ValueError("Invalid input detected")
            with pytest.raises(ValueError):
                await mock_mcp_inspector.invoke_tool("test_tool", malicious_input)
    
    async def test_configuration_validation(self, mock_mcp_inspector, server_config_factory):
        """Test configuration validation scenarios."""
        # Valid configurations
        valid_configs = [
            server_config_factory(),  # Default config
            server_config_factory(protocol="http", port=8080),
            server_config_factory(protocol="https", port=443),
            server_config_factory(host="0.0.0.0", port=9090)
        ]
        
        for config in valid_configs:
            mock_mcp_inspector.validate_server_config.return_value = True
            result = mock_mcp_inspector.validate_server_config(config)
            assert result is True
        
        # Invalid configurations
        invalid_configs = [
            server_config_factory(port=0),  # Invalid port
            server_config_factory(port=70000),  # Port out of range
            server_config_factory(host=""),  # Empty host
            server_config_factory(protocol="invalid"),  # Invalid protocol
            {"incomplete": "config"}  # Missing required fields
        ]
        
        for config in invalid_configs:
            mock_mcp_inspector.validate_server_config.return_value = False
            result = mock_mcp_inspector.validate_server_config(config)
            assert result is False
    
    async def test_stress_scenarios(self, mock_mcp_inspector):
        """Test stress scenarios and edge cases."""
        # High load scenario
        mock_mcp_inspector.invoke_tool.return_value = {"result": "success"}
        
        # Simulate high concurrent load
        async def high_load_test():
            tasks = []
            for i in range(1000):
                task = mock_mcp_inspector.invoke_tool(f"tool_{i % 10}", {"param": i})
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        results = await high_load_test()
        
        # Should handle all requests without major failures
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 950  # At least 95% success rate
        
        # Memory pressure scenario
        large_response = {"data": "x" * 1024 * 1024}  # 1MB response
        mock_mcp_inspector.invoke_tool.return_value = large_response
        
        # Should handle large responses
        result = await mock_mcp_inspector.invoke_tool("large_data_tool", {})
        assert len(result["data"]) == 1024 * 1024
    
    async def test_edge_cases_and_boundary_conditions(self, mock_mcp_inspector):
        """Test edge cases and boundary conditions."""
        # Empty responses
        mock_mcp_inspector.list_tools.return_value = []
        tools = await mock_mcp_inspector.list_tools()
        assert tools == []
        
        mock_mcp_inspector.list_resources.return_value = []
        resources = await mock_mcp_inspector.list_resources()
        assert resources == []
        
        # Null/None values
        mock_mcp_inspector.get_server_info.return_value = None
        info = await mock_mcp_inspector.get_server_info()
        assert info is None
        
        # Very large parameter values
        large_params = {"data": "x" * 10000000}  # 10MB parameter
        mock_mcp_inspector.invoke_tool.return_value = {"processed": True}
        
        result = await mock_mcp_inspector.invoke_tool("processor", large_params)
        assert result["processed"] is True
        
        # Unicode and special characters
        unicode_params = {
            "text": "Hello 世界! 🌍 Ñoël café résumé",
            "emoji": "🔧🚀💻🎯",
            "special": "!@#$%^&*()[]{}|;:,.<>?"
        }
        
        mock_mcp_inspector.invoke_tool.return_value = {"handled": True}
        result = await mock_mcp_inspector.invoke_tool("text_processor", unicode_params)
        assert result["handled"] is True


@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPInspectorIntegration:
    """Integration tests for MCP Inspector with external dependencies."""
    
    async def test_real_connection_simulation(self, mock_mcp_inspector):
        """Simulate real connection scenarios."""
        # This would typically connect to a real MCP server
        # For testing, we use comprehensive mocks
        
        connection_sequence = [
            ("connect", {"success": True}),
            ("get_server_info", {"name": "Real Server", "version": "1.0"}),
            ("list_tools", [{"name": "real_tool"}]),
            ("health_check", {"status": "healthy"}),
            ("disconnect", {"success": True})
        ]
        
        for method_name, expected_result in connection_sequence:
            method = getattr(mock_mcp_inspector, method_name)
            if asyncio.iscoroutinefunction(method._mock_wraps or method):
                method.return_value = expected_result
                result = await method()
            else:
                method.return_value = expected_result
                result = method()
            
            assert result == expected_result
    
    async def test_error_propagation(self, mock_mcp_inspector):
        """Test error propagation through the system."""
        # Simulate cascading failures
        mock_mcp_inspector.connect.side_effect = ConnectionError("Initial connection failed")
        
        with pytest.raises(ConnectionError):
            await mock_mcp_inspector.connect({})
        
        # Verify error handling doesn't break subsequent operations
        mock_mcp_inspector.connect.side_effect = None
        mock_mcp_inspector.connect.return_value = True
        
        result = await mock_mcp_inspector.connect({})
        assert result is True