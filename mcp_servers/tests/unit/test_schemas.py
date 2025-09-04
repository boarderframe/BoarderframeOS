"""
Unit tests for Pydantic schemas.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.mcp_server import (
    MCPServerBase,
    MCPServerCreate,
    MCPServerUpdate,
    MCPServer,
    MCPServerStatus,
    MCPServerHealth
)
from tests.utils import DataFactory, ValidationHelper


@pytest.mark.unit
class TestMCPServerSchemas:
    """Test suite for MCP server schemas."""
    
    def test_mcp_server_base_valid_data(self, sample_mcp_server_data: dict):
        """Test MCPServerBase with valid data."""
        server = MCPServerBase(**sample_mcp_server_data)
        
        assert server.name == sample_mcp_server_data["name"]
        assert server.description == sample_mcp_server_data["description"]
        assert server.host == sample_mcp_server_data["host"]
        assert server.port == sample_mcp_server_data["port"]
        assert server.protocol == sample_mcp_server_data["protocol"]
        assert server.command == sample_mcp_server_data["command"]
        assert server.args == sample_mcp_server_data["args"]
        assert server.env == sample_mcp_server_data["env"]
        assert server.config == sample_mcp_server_data["config"]
    
    def test_mcp_server_base_minimal_data(self):
        """Test MCPServerBase with minimal required data."""
        minimal_data = {
            "name": "test-server",
            "port": 8080
        }
        
        server = MCPServerBase(**minimal_data)
        
        assert server.name == "test-server"
        assert server.port == 8080
        assert server.host == "localhost"  # Default value
        assert server.protocol == "stdio"  # Default value
        assert server.description is None
        assert server.command is None
        assert server.args is None
        assert server.env is None
        assert server.config is None
    
    def test_mcp_server_base_port_validation(self):
        """Test port validation in MCPServerBase."""
        base_data = {"name": "test", "host": "localhost"}
        
        # Valid ports
        valid_ports = [1, 80, 8080, 65535]
        for port in valid_ports:
            server = MCPServerBase(**base_data, port=port)
            assert server.port == port
        
        # Invalid ports
        invalid_ports = [0, -1, 65536, 70000]
        for port in invalid_ports:
            with pytest.raises(ValidationError) as exc_info:
                MCPServerBase(**base_data, port=port)
            assert "Port must be between 1 and 65535" in str(exc_info.value)
    
    def test_mcp_server_create_schema(self, sample_mcp_server_data: dict):
        """Test MCPServerCreate schema."""
        server = MCPServerCreate(**sample_mcp_server_data)
        
        # Should inherit all functionality from MCPServerBase
        assert server.name == sample_mcp_server_data["name"]
        assert server.port == sample_mcp_server_data["port"]
    
    def test_mcp_server_update_schema(self, mcp_server_update_data: dict):
        """Test MCPServerUpdate schema."""
        server = MCPServerUpdate(**mcp_server_update_data)
        
        assert server.description == mcp_server_update_data["description"]
        assert server.port == mcp_server_update_data["port"]
        assert server.config == mcp_server_update_data["config"]
        
        # Fields not provided should be None
        assert server.name is None
        assert server.host is None
    
    def test_mcp_server_update_empty(self):
        """Test MCPServerUpdate with no data."""
        server = MCPServerUpdate()
        
        # All fields should be None for optional update
        assert server.name is None
        assert server.description is None
        assert server.host is None
        assert server.port is None
        assert server.protocol is None
        assert server.command is None
        assert server.args is None
        assert server.env is None
        assert server.config is None
    
    def test_mcp_server_update_port_validation(self):
        """Test port validation in MCPServerUpdate."""
        # Valid port
        server = MCPServerUpdate(port=8080)
        assert server.port == 8080
        
        # Invalid port
        with pytest.raises(ValidationError) as exc_info:
            MCPServerUpdate(port=0)
        assert "Port must be between 1 and 65535" in str(exc_info.value)
        
        # None port (should be allowed)
        server = MCPServerUpdate(port=None)
        assert server.port is None
    
    def test_mcp_server_response_schema(self, mcp_server_response_data: dict):
        """Test MCPServer response schema."""
        server = MCPServer(**mcp_server_response_data)
        
        assert server.id == mcp_server_response_data["id"]
        assert server.name == mcp_server_response_data["name"]
        assert server.status == mcp_server_response_data["status"]
        assert server.created_at is not None
        assert server.updated_at is not None
    
    def test_mcp_server_status_enum(self):
        """Test MCPServerStatus enum values."""
        assert MCPServerStatus.ACTIVE == "active"
        assert MCPServerStatus.INACTIVE == "inactive"
        assert MCPServerStatus.ERROR == "error"
        assert MCPServerStatus.STARTING == "starting"
        assert MCPServerStatus.STOPPING == "stopping"
        
        # Test all values are unique
        values = [status.value for status in MCPServerStatus]
        assert len(values) == len(set(values))
    
    def test_mcp_server_health_schema(self, mcp_server_health_data: dict):
        """Test MCPServerHealth schema."""
        health = MCPServerHealth(**mcp_server_health_data)
        
        assert health.server_id == mcp_server_health_data["server_id"]
        assert health.status == mcp_server_health_data["status"]
        assert health.response_time_ms == mcp_server_health_data["response_time_ms"]
        assert health.error_message == mcp_server_health_data["error_message"]
        assert health.last_check is not None
    
    def test_mcp_server_health_with_error(self, mcp_server_error_data: dict):
        """Test MCPServerHealth schema with error data."""
        health = MCPServerHealth(**mcp_server_error_data)
        
        assert health.status == MCPServerStatus.ERROR
        assert health.response_time_ms is None
        assert health.error_message == "Connection refused"
    
    def test_schema_validation_with_invalid_types(self):
        """Test schema validation with invalid data types."""
        invalid_data_sets = [
            {"name": 123, "port": 8080},  # Invalid name type
            {"name": "test", "port": "not-a-number"},  # Invalid port type
            {"name": "test", "port": 8080, "args": "not-a-list"},  # Invalid args type
            {"name": "test", "port": 8080, "env": "not-a-dict"},  # Invalid env type
        ]
        
        for invalid_data in invalid_data_sets:
            with pytest.raises(ValidationError):
                MCPServerBase(**invalid_data)
    
    def test_schema_validation_with_missing_required_fields(self):
        """Test schema validation with missing required fields."""
        # Missing name
        with pytest.raises(ValidationError) as exc_info:
            MCPServerBase(port=8080)
        assert "name" in str(exc_info.value)
        
        # Missing port
        with pytest.raises(ValidationError) as exc_info:
            MCPServerBase(name="test")
        assert "port" in str(exc_info.value)
    
    def test_schema_validation_with_empty_strings(self):
        """Test schema validation with empty strings."""
        # Empty name should be invalid
        with pytest.raises(ValidationError):
            MCPServerBase(name="", port=8080)
        
        # Empty host should be invalid if provided
        with pytest.raises(ValidationError):
            MCPServerBase(name="test", host="", port=8080)
    
    def test_schema_serialization(self, sample_mcp_server_data: dict):
        """Test schema serialization to dict."""
        server = MCPServerBase(**sample_mcp_server_data)
        
        # Test dict() method
        server_dict = server.dict()
        assert isinstance(server_dict, dict)
        assert server_dict["name"] == sample_mcp_server_data["name"]
        assert server_dict["port"] == sample_mcp_server_data["port"]
        
        # Test json() method
        server_json = server.json()
        assert isinstance(server_json, str)
        
        import json
        parsed_json = json.loads(server_json)
        assert parsed_json["name"] == sample_mcp_server_data["name"]
    
    def test_schema_deserialization_from_json(self, sample_mcp_server_data: dict):
        """Test schema deserialization from JSON."""
        import json
        
        # Serialize to JSON
        server = MCPServerBase(**sample_mcp_server_data)
        json_str = server.json()
        
        # Deserialize from JSON
        json_data = json.loads(json_str)
        new_server = MCPServerBase(**json_data)
        
        assert new_server.name == server.name
        assert new_server.port == server.port
        assert new_server.config == server.config
    
    @pytest.mark.parametrize("field_name,invalid_value", [
        ("protocol", "invalid-protocol"),
        ("port", 0),
        ("port", 70000),
        ("name", ""),
        ("host", ""),
    ])
    def test_individual_field_validation(self, field_name: str, invalid_value):
        """Test individual field validation."""
        base_data = {"name": "test", "port": 8080}
        base_data[field_name] = invalid_value
        
        with pytest.raises(ValidationError) as exc_info:
            MCPServerBase(**base_data)
        
        # The error should mention the problematic field
        assert field_name in str(exc_info.value) or "validation error" in str(exc_info.value).lower()
    
    def test_schema_with_complex_nested_data(self):
        """Test schema with complex nested configuration."""
        complex_data = {
            "name": "complex-server",
            "port": 8080,
            "env": {
                "NESTED_VAR": "value",
                "COMPLEX_VAR": json.dumps({"nested": {"data": [1, 2, 3]}})
            },
            "config": {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "settings": {
                        "pool_size": 10,
                        "timeout": 30
                    }
                },
                "features": ["feature1", "feature2"],
                "limits": {
                    "max_connections": 100,
                    "rate_limit": 1000
                }
            }
        }
        
        server = MCPServerBase(**complex_data)
        
        assert server.name == "complex-server"
        assert server.env["NESTED_VAR"] == "value"
        assert server.config["database"]["host"] == "localhost"
        assert server.config["features"] == ["feature1", "feature2"]
        
        # Test serialization/deserialization of complex data
        server_dict = server.dict()
        new_server = MCPServerBase(**server_dict)
        assert new_server.config == server.config


import json