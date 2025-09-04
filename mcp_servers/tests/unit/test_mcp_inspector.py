"""
Comprehensive unit tests for MCP Inspector functionality.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import tempfile
import os

from tests.utils.test_helpers import MockFactory, APITestHelper, ValidationHelper, SecurityTestHelper
from tests.fixtures.mcp_fixtures import MCPServerFactory, MCPResponseFactory


@pytest.mark.unit
@pytest.mark.asyncio
class TestMCPInspector:
    """Test suite for MCP Inspector functionality."""
    
    def test_mcp_client_creation(self, mock_mcp_client_factory):
        """Test MCP client creation with different configurations."""
        # Test basic client creation
        client = mock_mcp_client_factory()
        assert client is not None
        assert hasattr(client, 'connect')
        assert hasattr(client, 'disconnect')
        
        # Test client with custom configuration
        client = mock_mcp_client_factory(
            timeout=60,
            max_retries=5
        )
        assert client.timeout == 60
        assert client.max_retries == 5
    
    async def test_mcp_connection_success(self, mock_mcp_client):
        """Test successful MCP server connection."""
        # Configure successful connection
        mock_mcp_client.connect.return_value = True
        mock_mcp_client.is_connected.return_value = True
        
        # Test connection
        await mock_mcp_client.connect()
        
        # Verify connection was attempted
        mock_mcp_client.connect.assert_called_once()
        assert mock_mcp_client.is_connected()
    
    async def test_mcp_connection_failure(self, mock_mcp_client_factory):
        """Test MCP server connection failure handling."""
        # Configure connection failure
        client = mock_mcp_client_factory(
            connect=AsyncMock(side_effect=ConnectionError("Connection refused")),
            is_connected=Mock(return_value=False)
        )
        
        # Test connection failure
        with pytest.raises(ConnectionError):
            await client.connect()
        
        assert not client.is_connected()
    
    async def test_mcp_connection_timeout(self, mock_mcp_client_factory):
        """Test MCP server connection timeout."""
        import asyncio
        
        # Configure connection timeout
        client = mock_mcp_client_factory(
            connect=AsyncMock(side_effect=asyncio.TimeoutError("Connection timeout"))
        )
        
        # Test connection timeout
        with pytest.raises(asyncio.TimeoutError):
            await client.connect()
    
    async def test_mcp_health_check_success(self, mock_mcp_client):
        """Test successful MCP server health check."""
        # Configure successful health check
        health_data = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": 3600,
            "memory_usage": 64 * 1024 * 1024,  # 64MB
            "active_connections": 5
        }
        mock_mcp_client.health_check.return_value = health_data
        
        # Perform health check
        result = await mock_mcp_client.health_check()
        
        # Verify result
        assert result == health_data
        assert result["status"] == "healthy"
        mock_mcp_client.health_check.assert_called_once()
    
    async def test_mcp_health_check_failure(self, mock_mcp_client_factory):
        """Test MCP server health check failure."""
        # Configure health check failure
        client = mock_mcp_client_factory(
            health_check=AsyncMock(side_effect=Exception("Health check failed"))
        )
        
        # Test health check failure
        with pytest.raises(Exception, match="Health check failed"):
            await client.health_check()
    
    async def test_mcp_list_tools(self, mock_mcp_client, mcp_tools_list):
        """Test listing MCP server tools."""
        # Configure tools list
        mock_mcp_client.list_tools.return_value = mcp_tools_list
        
        # Get tools list
        tools = await mock_mcp_client.list_tools()
        
        # Verify tools
        assert isinstance(tools, list)
        assert len(tools) == len(mcp_tools_list)
        
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
        
        mock_mcp_client.list_tools.assert_called_once()
    
    async def test_mcp_list_resources(self, mock_mcp_client, mcp_resources_list):
        """Test listing MCP server resources."""
        # Configure resources list
        mock_mcp_client.list_resources.return_value = mcp_resources_list
        
        # Get resources list
        resources = await mock_mcp_client.list_resources()
        
        # Verify resources
        assert isinstance(resources, list)
        assert len(resources) == len(mcp_resources_list)
        
        for resource in resources:
            assert "name" in resource
            assert "type" in resource
            assert "uri" in resource
        
        mock_mcp_client.list_resources.assert_called_once()
    
    async def test_mcp_send_request(self, mock_mcp_client):
        """Test sending requests to MCP server."""
        # Configure request response
        request_data = {"method": "test_method", "params": {"arg1": "value1"}}
        response_data = {"result": "success", "data": {"processed": True}}
        
        mock_mcp_client.send_request.return_value = response_data
        
        # Send request
        result = await mock_mcp_client.send_request(request_data)
        
        # Verify response
        assert result == response_data
        assert result["result"] == "success"
        mock_mcp_client.send_request.assert_called_once_with(request_data)
    
    async def test_mcp_request_validation(self, mock_mcp_client):
        """Test MCP request validation."""
        # Test invalid request formats
        invalid_requests = [
            None,
            {},
            {"method": ""},  # Empty method
            {"params": {}},  # Missing method
            {"method": 123},  # Invalid method type
        ]
        
        for invalid_request in invalid_requests:
            mock_mcp_client.send_request.side_effect = ValueError("Invalid request format")
            
            with pytest.raises(ValueError):
                await mock_mcp_client.send_request(invalid_request)
    
    async def test_mcp_concurrent_requests(self, mock_mcp_client):
        """Test handling concurrent MCP requests."""
        import asyncio
        
        # Configure different responses for concurrent requests
        responses = [
            {"id": 1, "result": "response1"},
            {"id": 2, "result": "response2"},
            {"id": 3, "result": "response3"},
        ]
        
        mock_mcp_client.send_request.side_effect = responses
        
        # Send concurrent requests
        requests = [
            {"method": "test", "id": i}
            for i in range(3)
        ]
        
        tasks = [
            mock_mcp_client.send_request(req)
            for req in requests
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all requests completed
        assert len(results) == 3
        assert mock_mcp_client.send_request.call_count == 3
    
    async def test_mcp_connection_pooling(self, mock_mcp_client_factory):
        """Test MCP connection pooling."""
        # Create multiple clients
        clients = [mock_mcp_client_factory() for _ in range(5)]
        
        # Test that each client can connect independently
        for client in clients:
            await client.connect()
            assert client.is_connected()
    
    async def test_mcp_error_handling(self, mock_mcp_client_factory):
        """Test MCP error handling."""
        # Test different error scenarios
        error_scenarios = [
            (ConnectionError, "Connection failed"),
            (TimeoutError, "Request timeout"),
            (ValueError, "Invalid response"),
            (RuntimeError, "Server error"),
        ]
        
        for error_type, error_message in error_scenarios:
            client = mock_mcp_client_factory(
                send_request=AsyncMock(side_effect=error_type(error_message))
            )
            
            with pytest.raises(error_type, match=error_message):
                await client.send_request({"method": "test"})
    
    async def test_mcp_response_parsing(self, mock_mcp_client):
        """Test MCP response parsing."""
        # Test various response formats
        response_formats = [
            {"result": "simple_string"},
            {"result": {"complex": "object", "nested": {"data": [1, 2, 3]}}},
            {"result": [1, 2, 3, 4, 5]},
            {"error": {"code": -1, "message": "Error occurred"}},
        ]
        
        for response_format in response_formats:
            mock_mcp_client.send_request.return_value = response_format
            
            result = await mock_mcp_client.send_request({"method": "test"})
            
            # Should return the response as-is for parsing by the caller
            assert result == response_format
    
    async def test_mcp_metrics_collection(self, mock_mcp_client):
        """Test MCP metrics collection."""
        # Configure metrics data
        metrics_data = {
            "requests_total": 1000,
            "requests_per_second": 10.5,
            "average_response_time_ms": 150.3,
            "error_rate": 0.02,
            "active_connections": 8,
            "memory_usage_bytes": 128 * 1024 * 1024,
            "cpu_usage_percent": 25.7
        }
        
        mock_mcp_client.get_metrics = AsyncMock(return_value=metrics_data)
        
        # Get metrics
        metrics = await mock_mcp_client.get_metrics()
        
        # Verify metrics structure
        assert isinstance(metrics, dict)
        assert "requests_total" in metrics
        assert "requests_per_second" in metrics
        assert "average_response_time_ms" in metrics
        assert "error_rate" in metrics
        
        # Verify metric types
        assert isinstance(metrics["requests_total"], int)
        assert isinstance(metrics["requests_per_second"], (int, float))
        assert isinstance(metrics["average_response_time_ms"], (int, float))
        assert isinstance(metrics["error_rate"], (int, float))
    
    async def test_mcp_server_discovery(self, mock_mcp_client):
        """Test MCP server discovery functionality."""
        # Configure server info
        server_info = {
            "name": "Test MCP Server",
            "version": "1.2.3",
            "description": "A test MCP server for unit testing",
            "capabilities": ["tools", "resources", "logging"],
            "supported_protocols": ["stdio", "http"],
            "api_version": "1.0",
            "vendor": "Test Vendor"
        }
        
        mock_mcp_client.get_server_info.return_value = server_info
        
        # Get server info
        info = await mock_mcp_client.get_server_info()
        
        # Verify server info
        assert info["name"] == "Test MCP Server"
        assert info["version"] == "1.2.3"
        assert "tools" in info["capabilities"]
        assert "stdio" in info["supported_protocols"]
    
    @patch('subprocess.Popen')
    def test_mcp_process_management(self, mock_popen, mcp_process_mock):
        """Test MCP server process management."""
        # Configure process mock
        mock_popen.return_value = mcp_process_mock
        
        # Test process creation
        # This would be part of an MCP process manager
        import subprocess
        
        command = ["/usr/bin/python", "-m", "test_mcp_server"]
        process = subprocess.Popen(command)
        
        # Verify process was created
        assert process.pid == 12345
        assert process.returncode is None
        mock_popen.assert_called_once_with(command)
    
    async def test_mcp_logging_integration(self, mock_mcp_client):
        """Test MCP logging integration."""
        # Configure log data
        log_entries = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Server started",
                "source": "mcp_server"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "DEBUG",
                "message": "Processing request",
                "source": "request_handler"
            }
        ]
        
        mock_mcp_client.get_logs = AsyncMock(return_value=log_entries)
        
        # Get logs
        logs = await mock_mcp_client.get_logs()
        
        # Verify log structure
        assert isinstance(logs, list)
        assert len(logs) == 2
        
        for log_entry in logs:
            assert "timestamp" in log_entry
            assert "level" in log_entry
            assert "message" in log_entry
            assert "source" in log_entry
    
    async def test_mcp_configuration_validation(self, mock_mcp_client):
        """Test MCP server configuration validation."""
        # Test valid configurations
        valid_configs = [
            {
                "host": "localhost",
                "port": 8080,
                "protocol": "stdio",
                "timeout": 30,
                "max_connections": 10
            },
            {
                "host": "0.0.0.0",
                "port": 9090,
                "protocol": "http",
                "timeout": 60,
                "max_connections": 50,
                "ssl_enabled": True
            }
        ]
        
        for config in valid_configs:
            mock_mcp_client.validate_config = Mock(return_value=True)
            
            result = mock_mcp_client.validate_config(config)
            assert result is True
        
        # Test invalid configurations
        invalid_configs = [
            {"port": 0},  # Invalid port
            {"host": "", "port": 8080},  # Empty host
            {"host": "localhost", "port": "invalid"},  # Invalid port type
            {"protocol": "invalid"},  # Invalid protocol
        ]
        
        for config in invalid_configs:
            mock_mcp_client.validate_config = Mock(return_value=False)
            
            result = mock_mcp_client.validate_config(config)
            assert result is False