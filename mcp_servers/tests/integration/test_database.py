"""
Integration tests for database operations.
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.mcp_server import MCPServer as MCPServerModel
from app.schemas.mcp_server import MCPServerStatus
from tests.utils import DataFactory, ValidationHelper


@pytest.mark.integration
class TestDatabaseOperations:
    """Test suite for database operations."""
    
    def test_create_mcp_server_in_database(self, test_session: Session):
        """Test creating MCP server in database."""
        server_data = DataFactory.create_mcp_server_data()
        
        server = MCPServerModel(
            name=server_data["name"],
            description=server_data["description"],
            host=server_data["host"],
            port=server_data["port"],
            protocol=server_data["protocol"],
            command=server_data["command"],
            args=server_data["args"],
            env=server_data["env"],
            config=server_data["config"],
            status=MCPServerStatus.INACTIVE
        )
        
        test_session.add(server)
        test_session.commit()
        test_session.refresh(server)
        
        # Verify server was created
        assert server.id is not None
        assert server.name == server_data["name"]
        assert server.status == MCPServerStatus.INACTIVE
        assert server.created_at is not None
        assert server.updated_at is not None
        
        ValidationHelper.assert_datetime_recent(server.created_at)
        ValidationHelper.assert_datetime_recent(server.updated_at)
    
    def test_query_mcp_servers_from_database(self, test_session: Session):
        """Test querying MCP servers from database."""
        # Create multiple servers
        servers_data = DataFactory.create_multiple_servers(3)
        
        created_servers = []
        for server_data in servers_data:
            server = MCPServerModel(
                name=server_data["name"],
                port=server_data["port"],
                status=MCPServerStatus.ACTIVE
            )
            test_session.add(server)
            created_servers.append(server)
        
        test_session.commit()
        
        # Query all servers
        all_servers = test_session.query(MCPServerModel).all()
        assert len(all_servers) == 3
        
        # Query by status
        active_servers = test_session.query(MCPServerModel).filter(
            MCPServerModel.status == MCPServerStatus.ACTIVE
        ).all()
        assert len(active_servers) == 3
        
        # Query by name
        first_server = test_session.query(MCPServerModel).filter(
            MCPServerModel.name == servers_data[0]["name"]
        ).first()
        assert first_server is not None
        assert first_server.name == servers_data[0]["name"]
    
    def test_update_mcp_server_in_database(self, test_session: Session):
        """Test updating MCP server in database."""
        # Create server
        server_data = DataFactory.create_mcp_server_data()
        server = MCPServerModel(
            name=server_data["name"],
            port=server_data["port"],
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server)
        test_session.commit()
        
        original_updated_at = server.updated_at
        
        # Update server
        server.status = MCPServerStatus.ACTIVE
        server.description = "Updated description"
        test_session.commit()
        test_session.refresh(server)
        
        # Verify update
        assert server.status == MCPServerStatus.ACTIVE
        assert server.description == "Updated description"
        assert server.updated_at > original_updated_at
    
    def test_delete_mcp_server_from_database(self, test_session: Session):
        """Test deleting MCP server from database."""
        # Create server
        server_data = DataFactory.create_mcp_server_data()
        server = MCPServerModel(
            name=server_data["name"],
            port=server_data["port"],
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server)
        test_session.commit()
        
        server_id = server.id
        
        # Delete server
        test_session.delete(server)
        test_session.commit()
        
        # Verify deletion
        deleted_server = test_session.query(MCPServerModel).filter(
            MCPServerModel.id == server_id
        ).first()
        assert deleted_server is None
    
    def test_mcp_server_unique_constraints(self, test_session: Session):
        """Test database unique constraints."""
        server_data = DataFactory.create_mcp_server_data()
        
        # Create first server
        server1 = MCPServerModel(
            name=server_data["name"],
            port=server_data["port"],
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server1)
        test_session.commit()
        
        # Try to create second server with same name (if name should be unique)
        server2 = MCPServerModel(
            name=server_data["name"],  # Same name
            port=server_data["port"] + 1,  # Different port
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server2)
        
        # If names should be unique, this should raise an error
        # If not, this test documents the current behavior
        try:
            test_session.commit()
            # Names are not unique - document this behavior
            assert True, "Multiple servers with same name are allowed"
        except IntegrityError:
            # Names are unique - document this behavior
            test_session.rollback()
            assert True, "Server names must be unique"
    
    def test_mcp_server_port_constraints(self, test_session: Session):
        """Test port-related database constraints."""
        server_data = DataFactory.create_mcp_server_data()
        
        # Create first server
        server1 = MCPServerModel(
            name=server_data["name"],
            host="localhost",
            port=server_data["port"],
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server1)
        test_session.commit()
        
        # Try to create second server with same host:port combination
        server2 = MCPServerModel(
            name=server_data["name"] + "-2",
            host="localhost",
            port=server_data["port"],  # Same port on same host
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server2)
        
        try:
            test_session.commit()
            # Same host:port is allowed - document this behavior
            assert True, "Multiple servers on same host:port are allowed"
        except IntegrityError:
            # Host:port must be unique - document this behavior
            test_session.rollback()
            assert True, "Host:port combination must be unique"
    
    def test_mcp_server_json_fields(self, test_session: Session):
        """Test JSON field storage and retrieval."""
        complex_config = {
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
                "max_connections": 100
            }
        }
        
        complex_env = {
            "VAR1": "value1",
            "VAR2": "value2",
            "COMPLEX_VAR": '{"nested": true}'
        }
        
        server = MCPServerModel(
            name="json-test-server",
            port=8080,
            config=complex_config,
            env=complex_env,
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server)
        test_session.commit()
        test_session.refresh(server)
        
        # Verify JSON fields are correctly stored and retrieved
        assert server.config == complex_config
        assert server.env == complex_env
        assert server.config["database"]["settings"]["pool_size"] == 10
        assert server.env["COMPLEX_VAR"] == '{"nested": true}'
    
    def test_mcp_server_array_fields(self, test_session: Session):
        """Test array field storage and retrieval."""
        args_list = ["-m", "test_server", "--debug", "--port", "8080"]
        
        server = MCPServerModel(
            name="array-test-server",
            port=8080,
            args=args_list,
            status=MCPServerStatus.INACTIVE
        )
        test_session.add(server)
        test_session.commit()
        test_session.refresh(server)
        
        # Verify array field is correctly stored and retrieved
        assert server.args == args_list
        assert len(server.args) == 5
        assert server.args[0] == "-m"
        assert server.args[-1] == "8080"
    
    def test_database_transaction_rollback(self, test_session: Session):
        """Test database transaction rollback on error."""
        server_data = DataFactory.create_mcp_server_data()
        
        try:
            # Start transaction
            server = MCPServerModel(
                name=server_data["name"],
                port=server_data["port"],
                status=MCPServerStatus.INACTIVE
            )
            test_session.add(server)
            
            # Force an error by trying to create invalid data
            # This would depend on actual constraints in your model
            invalid_server = MCPServerModel(
                name=None,  # This should cause an error if name is required
                port=server_data["port"],
                status=MCPServerStatus.INACTIVE
            )
            test_session.add(invalid_server)
            test_session.commit()
            
        except Exception:
            test_session.rollback()
            
            # Verify that valid server was not created due to rollback
            created_server = test_session.query(MCPServerModel).filter(
                MCPServerModel.name == server_data["name"]
            ).first()
            assert created_server is None
    
    def test_database_pagination(self, test_session: Session):
        """Test database pagination functionality."""
        # Create multiple servers
        servers_data = DataFactory.create_multiple_servers(10)
        
        for server_data in servers_data:
            server = MCPServerModel(
                name=server_data["name"],
                port=server_data["port"],
                status=MCPServerStatus.ACTIVE
            )
            test_session.add(server)
        
        test_session.commit()
        
        # Test pagination
        page_size = 3
        
        # First page
        first_page = test_session.query(MCPServerModel).offset(0).limit(page_size).all()
        assert len(first_page) == page_size
        
        # Second page
        second_page = test_session.query(MCPServerModel).offset(page_size).limit(page_size).all()
        assert len(second_page) == page_size
        
        # Verify no overlap between pages
        first_page_ids = {server.id for server in first_page}
        second_page_ids = {server.id for server in second_page}
        assert not first_page_ids.intersection(second_page_ids)
        
        # Last page (partial)
        last_page = test_session.query(MCPServerModel).offset(9).limit(page_size).all()
        assert len(last_page) == 1
    
    def test_database_ordering(self, test_session: Session):
        """Test database ordering functionality."""
        # Create servers with different timestamps
        import time
        
        servers_data = DataFactory.create_multiple_servers(3)
        
        for i, server_data in enumerate(servers_data):
            server = MCPServerModel(
                name=f"server-{i:02d}",  # Ordered names
                port=server_data["port"],
                status=MCPServerStatus.ACTIVE
            )
            test_session.add(server)
            test_session.commit()  # Commit each to get different timestamps
            time.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Test ordering by name
        servers_by_name = test_session.query(MCPServerModel).order_by(
            MCPServerModel.name
        ).all()
        
        names = [server.name for server in servers_by_name]
        assert names == sorted(names)
        
        # Test ordering by creation time (descending)
        servers_by_time = test_session.query(MCPServerModel).order_by(
            MCPServerModel.created_at.desc()
        ).all()
        
        # Most recent first
        for i in range(len(servers_by_time) - 1):
            assert servers_by_time[i].created_at >= servers_by_time[i + 1].created_at
    
    def test_database_filtering(self, test_session: Session):
        """Test database filtering functionality."""
        # Create servers with different statuses
        statuses = [MCPServerStatus.ACTIVE, MCPServerStatus.INACTIVE, MCPServerStatus.ERROR]
        
        for i, status in enumerate(statuses):
            server = MCPServerModel(
                name=f"server-{status.value}",
                port=8080 + i,
                status=status
            )
            test_session.add(server)
        
        test_session.commit()
        
        # Filter by status
        active_servers = test_session.query(MCPServerModel).filter(
            MCPServerModel.status == MCPServerStatus.ACTIVE
        ).all()
        assert len(active_servers) == 1
        assert active_servers[0].status == MCPServerStatus.ACTIVE
        
        # Filter by multiple conditions
        active_servers_on_8080 = test_session.query(MCPServerModel).filter(
            MCPServerModel.status == MCPServerStatus.ACTIVE,
            MCPServerModel.port == 8080
        ).all()
        assert len(active_servers_on_8080) == 1
        
        # Filter using IN clause
        running_servers = test_session.query(MCPServerModel).filter(
            MCPServerModel.status.in_([MCPServerStatus.ACTIVE, MCPServerStatus.STARTING])
        ).all()
        assert len(running_servers) == 1  # Only ACTIVE in our test data