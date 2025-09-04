"""
MCP server-related test fixtures.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

from app.schemas.mcp_server import (
    MCPServer, 
    MCPServerCreate, 
    MCPServerUpdate, 
    MCPServerStatus,
    MCPServerHealth
)
from app.models.mcp_server import MCPServer as MCPServerModel


@pytest.fixture
def mcp_server_create_data() -> Dict[str, Any]:
    """Base MCP server creation data."""
    return {
        "name": "test-mcp-server",
        "description": "A test MCP server for unit testing",
        "host": "localhost",
        "port": 8080,
        "protocol": "stdio",
        "command": "/usr/bin/python",
        "args": ["-m", "test_mcp_server"],
        "env": {
            "TEST_MODE": "true",
            "LOG_LEVEL": "debug"
        },
        "config": {
            "timeout": 30,
            "retries": 3,
            "auto_restart": True
        }
    }


@pytest.fixture
def mcp_server_update_data() -> Dict[str, Any]:
    """MCP server update data."""
    return {
        "description": "Updated test MCP server",
        "port": 8081,
        "config": {
            "timeout": 60,
            "retries": 5,
            "auto_restart": False
        }
    }


@pytest.fixture
def mcp_server_response_data() -> Dict[str, Any]:
    """MCP server response data with all fields."""
    return {
        "id": 1,
        "name": "test-mcp-server",
        "description": "A test MCP server for unit testing",
        "host": "localhost",
        "port": 8080,
        "protocol": "stdio",
        "command": "/usr/bin/python",
        "args": ["-m", "test_mcp_server"],
        "env": {
            "TEST_MODE": "true",
            "LOG_LEVEL": "debug"
        },
        "config": {
            "timeout": 30,
            "retries": 3,
            "auto_restart": True
        },
        "status": MCPServerStatus.ACTIVE.value,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "last_health_check": datetime.utcnow().isoformat(),
        "error_message": None
    }


@pytest.fixture
def mcp_server_factory():
    """Factory for creating MCP server test data."""
    def _create_server(**kwargs) -> Dict[str, Any]:
        default_data = {
            "name": "test-server",
            "description": "Test MCP server",
            "host": "localhost",
            "port": 8080,
            "protocol": "stdio",
            "command": "/usr/bin/python",
            "args": ["-m", "server"],
            "env": {"TEST": "true"},
            "config": {"timeout": 30}
        }
        default_data.update(kwargs)
        return default_data
    return _create_server


@pytest.fixture
def multiple_mcp_servers() -> List[Dict[str, Any]]:
    """Multiple MCP servers for list testing."""
    base_time = datetime.utcnow()
    servers = []
    
    for i in range(3):
        server = {
            "id": i + 1,
            "name": f"test-server-{i + 1}",
            "description": f"Test server number {i + 1}",
            "host": "localhost",
            "port": 8080 + i,
            "protocol": "stdio",
            "command": "/usr/bin/python",
            "args": ["-m", f"server_{i + 1}"],
            "env": {"SERVER_ID": str(i + 1)},
            "config": {"timeout": 30 + i * 10},
            "status": list(MCPServerStatus)[i % len(MCPServerStatus)].value,
            "created_at": (base_time - timedelta(hours=i)).isoformat(),
            "updated_at": (base_time - timedelta(minutes=i * 30)).isoformat(),
            "last_health_check": (base_time - timedelta(minutes=i * 10)).isoformat(),
            "error_message": None if i != 2 else "Connection timeout"
        }
        servers.append(server)
    
    return servers


@pytest.fixture
def mcp_server_model() -> MCPServerModel:
    """SQLAlchemy MCP server model instance."""
    return MCPServerModel(
        id=1,
        name="test-server",
        description="Test MCP server",
        host="localhost",
        port=8080,
        protocol="stdio",
        command="/usr/bin/python",
        args=["-m", "test_server"],
        env={"TEST": "true"},
        config={"timeout": 30},
        status=MCPServerStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_health_check=datetime.utcnow(),
        error_message=None
    )


@pytest.fixture
def mcp_server_health_data() -> Dict[str, Any]:
    """MCP server health check data."""
    return {
        "server_id": 1,
        "status": MCPServerStatus.ACTIVE.value,
        "response_time_ms": 150.5,
        "error_message": None,
        "last_check": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mcp_server_error_data() -> Dict[str, Any]:
    """MCP server error data."""
    return {
        "server_id": 1,
        "status": MCPServerStatus.ERROR.value,
        "response_time_ms": None,
        "error_message": "Connection refused",
        "last_check": datetime.utcnow().isoformat()
    }


@pytest.fixture
def invalid_mcp_server_data() -> List[Dict[str, Any]]:
    """Invalid MCP server data for validation testing."""
    return [
        # Missing required fields
        {"description": "Missing name"},
        {"name": "test", "description": "Missing port"},
        
        # Invalid port numbers
        {"name": "test", "port": 0},
        {"name": "test", "port": 70000},
        {"name": "test", "port": -1},
        
        # Invalid data types
        {"name": 123, "port": 8080},
        {"name": "test", "port": "not-a-number"},
        {"name": "test", "port": 8080, "args": "not-a-list"},
        
        # Invalid protocol
        {"name": "test", "port": 8080, "protocol": "invalid-protocol"},
        
        # Empty strings
        {"name": "", "port": 8080},
        {"name": "test", "host": "", "port": 8080},
    ]


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    mock_client = Mock()
    
    # Mock async methods
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.send_request = AsyncMock()
    mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
    mock_client.list_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "A test tool"}
    ])
    mock_client.list_resources = AsyncMock(return_value=[
        {"name": "test_resource", "type": "text"}
    ])
    mock_client.get_server_info = AsyncMock(return_value={
        "name": "Test Server",
        "version": "1.0.0"
    })
    
    # Mock connection state
    mock_client.is_connected = Mock(return_value=True)
    mock_client.connection_error = None
    
    return mock_client


@pytest.fixture
def mock_mcp_client_factory():
    """Factory for creating mock MCP clients."""
    def _create_client(**kwargs):
        mock_client = Mock()
        
        # Default behavior
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_client.is_connected = Mock(return_value=True)
        
        # Apply overrides
        for key, value in kwargs.items():
            setattr(mock_client, key, value)
        
        return mock_client
    
    return _create_client


@pytest.fixture
def mcp_process_mock():
    """Mock subprocess for MCP server process."""
    mock_process = Mock()
    mock_process.pid = 12345
    mock_process.returncode = None
    mock_process.poll.return_value = None
    mock_process.terminate.return_value = None
    mock_process.kill.return_value = None
    mock_process.wait.return_value = 0
    mock_process.communicate.return_value = (b"stdout", b"stderr")
    return mock_process


@pytest.fixture
def mcp_server_logs() -> List[Dict[str, Any]]:
    """Sample MCP server logs for testing."""
    base_time = datetime.utcnow()
    logs = []
    
    for i in range(5):
        log_entry = {
            "timestamp": (base_time - timedelta(minutes=i)).isoformat(),
            "level": ["INFO", "DEBUG", "WARN", "ERROR"][i % 4],
            "message": f"Log message {i + 1}",
            "source": "mcp_server",
            "context": {"request_id": f"req_{i + 1}"}
        }
        logs.append(log_entry)
    
    return logs


@pytest.fixture
def mcp_server_metrics() -> Dict[str, Any]:
    """Sample MCP server metrics for testing."""
    return {
        "requests_total": 1234,
        "requests_per_second": 5.7,
        "response_time_avg_ms": 125.3,
        "response_time_p95_ms": 250.1,
        "response_time_p99_ms": 400.8,
        "errors_total": 12,
        "error_rate": 0.01,
        "uptime_seconds": 86400,
        "memory_usage_bytes": 104857600,
        "cpu_usage_percent": 15.2,
        "active_connections": 3
    }


@pytest.fixture
def mcp_tools_list() -> List[Dict[str, Any]]:
    """Sample MCP tools list for testing."""
    return [
        {
            "name": "file_reader",
            "description": "Read files from the filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                }
            }
        },
        {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"}
                }
            }
        }
    ]


@pytest.fixture
def mcp_resources_list() -> List[Dict[str, Any]]:
    """Sample MCP resources list for testing."""
    return [
        {
            "name": "config.json",
            "type": "text/json",
            "description": "Server configuration file",
            "uri": "file:///etc/mcp/config.json"
        },
        {
            "name": "data.csv",
            "type": "text/csv", 
            "description": "Sample data file",
            "uri": "file:///data/sample.csv"
        }
    ]