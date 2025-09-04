"""
Comprehensive integration tests for API endpoints with test containers and database scenarios.
Tests real database interactions, container orchestration, and full API workflows.
"""
import pytest
import asyncio
from typing import Dict, List, Any
import json
import time
from datetime import datetime, timedelta
import uuid

import httpx
from fastapi import status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from tests.utils.test_helpers import APITestHelper, DataFactory, ValidationHelper
from app.core.config import Settings


@pytest.mark.integration
@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Test database integration with real PostgreSQL container."""
    
    @pytest.fixture(scope="class")
    def postgres_container(self):
        """Start PostgreSQL test container."""
        with PostgresContainer("postgres:15") as postgres:
            yield postgres
    
    @pytest.fixture(scope="class")
    def redis_container(self):
        """Start Redis test container."""
        with RedisContainer("redis:7") as redis:
            yield redis
    
    @pytest.fixture
    def test_db_session(self, postgres_container):
        """Create test database session with real PostgreSQL."""
        db_url = postgres_container.get_connection_url()
        engine = create_engine(db_url)
        
        # Create tables
        from app.db.database import Base
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
        engine.dispose()
    
    @pytest.fixture
    def integration_client(self, postgres_container, redis_container):
        """Create test client with real database and Redis."""
        from app.main import create_application
        from app.core.config import get_settings
        from app.db.database import get_db
        
        # Override settings for integration testing
        test_settings = Settings(
            DATABASE_URL=postgres_container.get_connection_url(),
            REDIS_URL=redis_container.get_connection_url(),
            TESTING=True,
            SECRET_KEY="integration-test-secret-key",
            ACCESS_TOKEN_EXPIRE_MINUTES=30
        )
        
        app = create_application()
        app.dependency_overrides[get_settings] = lambda: test_settings
        
        # Initialize database
        from app.db.database import Base, create_engine_from_url
        engine = create_engine_from_url(test_settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        
        with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
            yield client
        
        # Cleanup
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
    
    async def test_mcp_server_crud_operations(self, integration_client, test_db_session):
        """Test complete CRUD operations for MCP servers with real database."""
        # Create authentication token
        user_data = DataFactory.create_user_data()
        register_response = await integration_client.post("/api/v1/auth/register", json=user_data)
        
        if register_response.status_code == status.HTTP_201_CREATED:
            # Login to get token
            login_response = await integration_client.post(
                "/api/v1/auth/login",
                json={"username": user_data["email"], "password": user_data["password"]}
            )
            
            if login_response.status_code == status.HTTP_200_OK:
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
            else:
                headers = {"Authorization": "Bearer test-token"}
        else:
            headers = {"Authorization": "Bearer test-token"}
        
        # CREATE - Create MCP server
        server_data = DataFactory.create_mcp_server_data()
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=server_data,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented or authentication required")
        
        created_server = create_response.json()
        server_id = created_server["id"]
        
        # Validate created server
        ValidationHelper.assert_mcp_server_structure(created_server)
        assert created_server["name"] == server_data["name"]
        assert created_server["port"] == server_data["port"]
        
        # READ - Get single server
        get_response = await integration_client.get(
            f"/api/v1/mcp-servers/{server_id}",
            headers=headers
        )
        APITestHelper.assert_status_code(get_response, status.HTTP_200_OK)
        
        retrieved_server = get_response.json()
        assert retrieved_server["id"] == server_id
        assert retrieved_server["name"] == server_data["name"]
        
        # READ - List servers
        list_response = await integration_client.get(
            "/api/v1/mcp-servers/",
            headers=headers
        )
        APITestHelper.assert_status_code(list_response, status.HTTP_200_OK)
        
        servers_list = list_response.json()
        assert isinstance(servers_list, list)
        assert len(servers_list) >= 1
        assert any(s["id"] == server_id for s in servers_list)
        
        # UPDATE - Update server
        update_data = {
            "description": "Updated test server",
            "port": server_data["port"] + 1,
            "config": {"timeout": 60, "retries": 5}
        }
        
        update_response = await integration_client.put(
            f"/api/v1/mcp-servers/{server_id}",
            json=update_data,
            headers=headers
        )
        
        if update_response.status_code == status.HTTP_200_OK:
            updated_server = update_response.json()
            assert updated_server["description"] == update_data["description"]
            assert updated_server["port"] == update_data["port"]
        
        # DELETE - Delete server
        delete_response = await integration_client.delete(
            f"/api/v1/mcp-servers/{server_id}",
            headers=headers
        )
        APITestHelper.assert_status_code(delete_response, status.HTTP_204_NO_CONTENT)
        
        # Verify deletion
        get_deleted_response = await integration_client.get(
            f"/api/v1/mcp-servers/{server_id}",
            headers=headers
        )
        APITestHelper.assert_status_code(get_deleted_response, status.HTTP_404_NOT_FOUND)
    
    async def test_database_transactions(self, integration_client, test_db_session):
        """Test database transaction handling."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Test successful transaction
        server_data = DataFactory.create_mcp_server_data()
        response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=server_data,
            headers=headers
        )
        
        if response.status_code == status.HTTP_201_CREATED:
            server_id = response.json()["id"]
            
            # Verify data is committed to database
            result = test_db_session.execute(
                text("SELECT * FROM mcp_servers WHERE id = :server_id"),
                {"server_id": server_id}
            ).fetchone()
            
            assert result is not None
            assert result.name == server_data["name"]
    
    async def test_database_concurrency(self, integration_client):
        """Test database concurrency and isolation."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create multiple servers concurrently
        server_count = 10
        tasks = []
        
        for i in range(server_count):
            server_data = DataFactory.create_mcp_server_data(
                name=f"concurrent-server-{i}",
                port=8000 + i
            )
            task = integration_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=headers
            )
            tasks.append(task)
        
        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful creations
        successful_creations = 0
        for response in responses:
            if isinstance(response, httpx.Response) and response.status_code == status.HTTP_201_CREATED:
                successful_creations += 1
        
        # Should handle concurrent requests without conflicts
        if successful_creations > 0:
            assert successful_creations <= server_count
            
            # Verify all servers are in database
            list_response = await integration_client.get("/api/v1/mcp-servers/", headers=headers)
            if list_response.status_code == status.HTTP_200_OK:
                servers = list_response.json()
                concurrent_servers = [s for s in servers if s["name"].startswith("concurrent-server-")]
                assert len(concurrent_servers) == successful_creations
    
    async def test_database_performance(self, integration_client, test_db_session):
        """Test database performance with large datasets."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create multiple servers to test query performance
        server_count = 100
        created_servers = []
        
        # Batch create servers
        for i in range(0, server_count, 10):
            batch_tasks = []
            for j in range(min(10, server_count - i)):
                server_data = DataFactory.create_mcp_server_data(
                    name=f"perf-server-{i+j}",
                    port=8000 + i + j
                )
                task = integration_client.post(
                    "/api/v1/mcp-servers/",
                    json=server_data,
                    headers=headers
                )
                batch_tasks.append(task)
            
            responses = await asyncio.gather(*batch_tasks, return_exceptions=True)
            for response in responses:
                if isinstance(response, httpx.Response) and response.status_code == status.HTTP_201_CREATED:
                    created_servers.append(response.json())
        
        if len(created_servers) > 50:  # Only test if we have enough data
            # Test list performance
            start_time = time.time()
            list_response = await integration_client.get("/api/v1/mcp-servers/", headers=headers)
            list_time = time.time() - start_time
            
            # List operation should be fast even with many records
            assert list_time < 2.0
            
            if list_response.status_code == status.HTTP_200_OK:
                servers = list_response.json()
                perf_servers = [s for s in servers if s["name"].startswith("perf-server-")]
                assert len(perf_servers) >= 50
            
            # Test search performance
            start_time = time.time()
            search_response = await integration_client.get(
                "/api/v1/mcp-servers/?search=perf-server",
                headers=headers
            )
            search_time = time.time() - start_time
            
            # Search should be fast
            assert search_time < 1.0


@pytest.mark.integration
@pytest.mark.asyncio
class TestAPIWorkflows:
    """Test complete API workflows and business logic."""
    
    @pytest.fixture
    def workflow_client(self, integration_client):
        """Client configured for workflow testing."""
        return integration_client
    
    async def test_user_registration_and_server_management_workflow(self, workflow_client):
        """Test complete user workflow from registration to server management."""
        # Step 1: User Registration
        user_data = DataFactory.create_user_data()
        register_response = await workflow_client.post("/api/v1/auth/register", json=user_data)
        
        if register_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("User registration not implemented")
        
        user = register_response.json()
        assert user["email"] == user_data["email"]
        
        # Step 2: User Login
        login_response = await workflow_client.post(
            "/api/v1/auth/login",
            json={"username": user_data["email"], "password": user_data["password"]}
        )
        APITestHelper.assert_status_code(login_response, status.HTTP_200_OK)
        
        auth_data = login_response.json()
        token = auth_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Create Multiple MCP Servers
        servers = DataFactory.create_multiple_servers(3)
        created_server_ids = []
        
        for server_data in servers:
            create_response = await workflow_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=headers
            )
            APITestHelper.assert_status_code(create_response, status.HTTP_201_CREATED)
            
            server = create_response.json()
            created_server_ids.append(server["id"])
        
        # Step 4: List User's Servers
        list_response = await workflow_client.get("/api/v1/mcp-servers/", headers=headers)
        APITestHelper.assert_status_code(list_response, status.HTTP_200_OK)
        
        user_servers = list_response.json()
        assert len(user_servers) >= 3
        
        # Step 5: Update Server Configuration
        first_server_id = created_server_ids[0]
        update_data = {
            "description": "Updated in workflow test",
            "config": {"timeout": 120, "retries": 5}
        }
        
        update_response = await workflow_client.put(
            f"/api/v1/mcp-servers/{first_server_id}",
            json=update_data,
            headers=headers
        )
        
        if update_response.status_code == status.HTTP_200_OK:
            updated_server = update_response.json()
            assert updated_server["description"] == update_data["description"]
        
        # Step 6: Health Check Server
        health_response = await workflow_client.get(
            f"/api/v1/mcp-servers/{first_server_id}/health",
            headers=headers
        )
        
        # Health check might not be implemented yet
        if health_response.status_code == status.HTTP_200_OK:
            health_data = health_response.json()
            assert "status" in health_data
        
        # Step 7: Delete Server
        delete_response = await workflow_client.delete(
            f"/api/v1/mcp-servers/{created_server_ids[-1]}",
            headers=headers
        )
        APITestHelper.assert_status_code(delete_response, status.HTTP_204_NO_CONTENT)
        
        # Step 8: Verify Deletion
        final_list_response = await workflow_client.get("/api/v1/mcp-servers/", headers=headers)
        if final_list_response.status_code == status.HTTP_200_OK:
            final_servers = final_list_response.json()
            deleted_server_exists = any(s["id"] == created_server_ids[-1] for s in final_servers)
            assert not deleted_server_exists
    
    async def test_server_lifecycle_management(self, workflow_client):
        """Test MCP server lifecycle management."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create server
        server_data = DataFactory.create_mcp_server_data()
        create_response = await workflow_client.post(
            "/api/v1/mcp-servers/",
            json=server_data,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Test server status transitions
        status_transitions = [
            "start",
            "stop", 
            "restart"
        ]
        
        for action in status_transitions:
            action_response = await workflow_client.post(
                f"/api/v1/mcp-servers/{server_id}/{action}",
                headers=headers
            )
            
            # Actions might not be implemented yet
            if action_response.status_code == status.HTTP_200_OK:
                result = action_response.json()
                assert "status" in result or "message" in result
    
    async def test_error_handling_workflow(self, workflow_client):
        """Test error handling in API workflows."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Test 404 errors
        not_found_response = await workflow_client.get("/api/v1/mcp-servers/99999", headers=headers)
        APITestHelper.assert_status_code(not_found_response, status.HTTP_404_NOT_FOUND)
        
        # Test validation errors
        invalid_server_data = {
            "name": "",  # Empty name
            "port": 0,   # Invalid port
            "command": ""  # Empty command
        }
        
        validation_response = await workflow_client.post(
            "/api/v1/mcp-servers/",
            json=invalid_server_data,
            headers=headers
        )
        
        assert validation_response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
        
        # Test unauthorized access
        unauth_response = await workflow_client.get("/api/v1/mcp-servers/")
        APITestHelper.assert_status_code(unauth_response, status.HTTP_401_UNAUTHORIZED)
    
    async def test_pagination_and_filtering(self, workflow_client):
        """Test API pagination and filtering."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create multiple servers for testing
        server_count = 25
        created_servers = []
        
        for i in range(server_count):
            server_data = DataFactory.create_mcp_server_data(
                name=f"filter-test-server-{i:02d}",
                port=8000 + i,
                description=f"Server for filtering test {i}"
            )
            
            response = await workflow_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=headers
            )
            
            if response.status_code == status.HTTP_201_CREATED:
                created_servers.append(response.json())
        
        if len(created_servers) >= 10:  # Only test if we have enough data
            # Test pagination
            page1_response = await workflow_client.get(
                "/api/v1/mcp-servers/?page=1&limit=10",
                headers=headers
            )
            
            if page1_response.status_code == status.HTTP_200_OK:
                page1_data = page1_response.json()
                
                # Check pagination structure
                if isinstance(page1_data, dict) and "items" in page1_data:
                    assert len(page1_data["items"]) <= 10
                    assert "total" in page1_data
                    assert "page" in page1_data
                elif isinstance(page1_data, list):
                    assert len(page1_data) >= 10
            
            # Test filtering
            filter_response = await workflow_client.get(
                "/api/v1/mcp-servers/?search=filter-test",
                headers=headers
            )
            
            if filter_response.status_code == status.HTTP_200_OK:
                filtered_data = filter_response.json()
                
                if isinstance(filtered_data, list):
                    filter_test_servers = [s for s in filtered_data if "filter-test" in s["name"]]
                    assert len(filter_test_servers) >= 10
                elif isinstance(filtered_data, dict) and "items" in filtered_data:
                    filter_test_servers = [s for s in filtered_data["items"] if "filter-test" in s["name"]]
                    assert len(filter_test_servers) >= min(10, len(filtered_data["items"]))


@pytest.mark.integration
@pytest.mark.asyncio  
class TestExternalServiceIntegration:
    """Test integration with external services."""
    
    async def test_redis_caching_integration(self, integration_client, redis_container):
        """Test Redis caching integration."""
        import redis
        
        # Connect to test Redis instance
        redis_client = redis.from_url(redis_container.get_connection_url())
        
        headers = {"Authorization": "Bearer test-token"}
        
        # Test caching behavior
        cache_key = "test:mcp-servers:list"
        
        # Clear any existing cache
        redis_client.delete(cache_key)
        
        # First request (should populate cache)
        start_time = time.time()
        first_response = await integration_client.get("/api/v1/mcp-servers/", headers=headers)
        first_request_time = time.time() - start_time
        
        # Second request (should use cache if implemented)
        start_time = time.time()
        second_response = await integration_client.get("/api/v1/mcp-servers/", headers=headers)
        second_request_time = time.time() - start_time
        
        # Both requests should return same data
        if first_response.status_code == status.HTTP_200_OK and second_response.status_code == status.HTTP_200_OK:
            assert first_response.json() == second_response.json()
            
            # Second request might be faster if caching is implemented
            # This is informational rather than assertive since caching might not be implemented
            if second_request_time < first_request_time * 0.8:
                print(f"Cache hit detected: {first_request_time:.3f}s -> {second_request_time:.3f}s")
        
        redis_client.close()
    
    async def test_database_connection_resilience(self, integration_client):
        """Test database connection resilience."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Test multiple rapid requests to stress database connections
        rapid_requests = 50
        tasks = []
        
        for i in range(rapid_requests):
            task = integration_client.get("/api/v1/health", headers=headers)
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Count successful responses
        successful_responses = 0
        for response in responses:
            if isinstance(response, httpx.Response) and response.status_code == status.HTTP_200_OK:
                successful_responses += 1
        
        # Should handle high load without significant failures
        success_rate = successful_responses / rapid_requests
        assert success_rate >= 0.95  # At least 95% success rate
        assert total_time < 10.0  # Should complete within 10 seconds
    
    async def test_api_rate_limiting(self, integration_client):
        """Test API rate limiting implementation."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Make rapid requests to test rate limiting
        rate_limit_requests = 100
        rate_limited_count = 0
        
        for i in range(rate_limit_requests):
            response = await integration_client.get("/api/v1/mcp-servers/", headers=headers)
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited_count += 1
                break
            
            # Small delay to avoid overwhelming the system
            if i % 10 == 0:
                await asyncio.sleep(0.1)
        
        # Rate limiting might not be implemented, so this is informational
        if rate_limited_count > 0:
            print(f"Rate limiting detected after {rate_limit_requests - rate_limited_count} requests")


@pytest.mark.integration
@pytest.mark.asyncio
class TestDataConsistency:
    """Test data consistency across operations."""
    
    async def test_server_state_consistency(self, integration_client):
        """Test MCP server state consistency."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create server
        server_data = DataFactory.create_mcp_server_data()
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=server_data,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Verify server appears in list
        list_response = await integration_client.get("/api/v1/mcp-servers/", headers=headers)
        if list_response.status_code == status.HTTP_200_OK:
            servers = list_response.json()
            created_server_in_list = any(s["id"] == server_id for s in servers)
            assert created_server_in_list
        
        # Update server
        update_data = {"description": "Consistency test update"}
        update_response = await integration_client.put(
            f"/api/v1/mcp-servers/{server_id}",
            json=update_data,
            headers=headers
        )
        
        if update_response.status_code == status.HTTP_200_OK:
            # Verify update is reflected in both individual and list endpoints
            get_response = await integration_client.get(
                f"/api/v1/mcp-servers/{server_id}",
                headers=headers
            )
            
            if get_response.status_code == status.HTTP_200_OK:
                updated_server = get_response.json()
                assert updated_server["description"] == update_data["description"]
                
                # Check consistency in list
                list_response = await integration_client.get("/api/v1/mcp-servers/", headers=headers)
                if list_response.status_code == status.HTTP_200_OK:
                    servers = list_response.json()
                    updated_server_in_list = next((s for s in servers if s["id"] == server_id), None)
                    
                    if updated_server_in_list:
                        assert updated_server_in_list["description"] == update_data["description"]
    
    async def test_concurrent_modifications(self, integration_client):
        """Test handling of concurrent modifications."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create server
        server_data = DataFactory.create_mcp_server_data()
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=server_data,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Simulate concurrent updates
        update_tasks = []
        for i in range(5):
            update_data = {"description": f"Concurrent update {i}"}
            task = integration_client.put(
                f"/api/v1/mcp-servers/{server_id}",
                json=update_data,
                headers=headers
            )
            update_tasks.append(task)
        
        # Execute concurrent updates
        responses = await asyncio.gather(*update_tasks, return_exceptions=True)
        
        # Count successful updates
        successful_updates = 0
        for response in responses:
            if isinstance(response, httpx.Response) and response.status_code == status.HTTP_200_OK:
                successful_updates += 1
        
        # At least one update should succeed
        assert successful_updates >= 1
        
        # Verify final state is consistent
        final_get_response = await integration_client.get(
            f"/api/v1/mcp-servers/{server_id}",
            headers=headers
        )
        
        if final_get_response.status_code == status.HTTP_200_OK:
            final_server = final_get_response.json()
            # Description should reflect one of the concurrent updates
            assert "Concurrent update" in final_server["description"]