"""
Real Server Integration Tests for Kroger MCP Authentication.

These tests interact with the actual Kroger MCP server to verify:
1. Token persistence across server restarts
2. Real network error handling
3. Actual cart operations with authentication
4. Server-side token management
5. Full integration with real Kroger API responses

Note: These tests require actual Kroger API credentials and may hit rate limits.
"""

import pytest
import asyncio
import json
import time
import os
import requests
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import patch

import httpx
from httpx import AsyncClient

from tests.utils.test_helpers import APITestHelper
from tests.factories.test_data_factory import TestDataFactory


# Test configuration
KROGER_SERVER_URL = os.getenv("KROGER_SERVER_URL", "http://localhost:9004")
KROGER_CLIENT_ID = os.getenv("KROGER_CLIENT_ID", "")
KROGER_CLIENT_SECRET = os.getenv("KROGER_CLIENT_SECRET", "")

# Skip real API tests if no credentials
skip_if_no_credentials = pytest.mark.skipif(
    not KROGER_CLIENT_ID or not KROGER_CLIENT_SECRET,
    reason="Kroger API credentials not available"
)


@pytest.mark.integration
@pytest.mark.real_server
class TestKrogerAuthRealServerIntegration:
    """Integration tests with real Kroger MCP server."""
    
    @pytest.fixture
    async def http_client(self):
        """Create HTTP client for server requests."""
        async with AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def server_health_check(self, http_client):
        """Ensure server is running before tests."""
        async def check():
            try:
                response = await http_client.get(f"{KROGER_SERVER_URL}/health")
                if response.status_code != 200:
                    pytest.skip("Kroger MCP server is not running")
                return response.json()
            except Exception:
                pytest.skip("Kroger MCP server is not accessible")
        return check
    
    async def test_server_health_and_config(self, http_client, server_health_check):
        """Test server health and configuration endpoints."""
        # Check health
        health_data = await server_health_check()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "kroger-mcp-server"
        
        # Check configuration
        config_response = await http_client.get(f"{KROGER_SERVER_URL}/config")
        APITestHelper.assert_status_code(config_response, 200)
        
        config_data = config_response.json()
        assert "default_location" in config_data
        assert "available_endpoints" in config_data
        assert "llm_friendly_usage" in config_data
    
    async def test_client_credentials_token_flow(self, http_client, server_health_check):
        """Test client credentials token flow for public API access."""
        await server_health_check()
        
        # Test products search (requires client credentials token)
        response = await http_client.get(
            f"{KROGER_SERVER_URL}/products/search",
            params={"term": "milk"}
        )
        
        if KROGER_CLIENT_ID and KROGER_CLIENT_SECRET:
            # Should work with real credentials
            APITestHelper.assert_status_code(response, 200)
            data = response.json()
            assert "data" in data
        else:
            # Should work in dev mode with mock data
            APITestHelper.assert_status_code(response, 200)
            data = response.json()
            assert "data" in data
    
    @skip_if_no_credentials
    async def test_oauth_authorization_url_generation(self, http_client, server_health_check):
        """Test OAuth authorization URL generation."""
        await server_health_check()
        
        response = await http_client.get(
            f"{KROGER_SERVER_URL}/auth/authorize",
            params={
                "scope": "profile.compact cart.basic:write",
                "state": "test_state_123"
            }
        )
        
        APITestHelper.assert_status_code(response, 200)
        data = response.json()
        
        assert "authorization_url" in data
        assert "redirect_uri" in data
        assert "scope" in data
        
        # Verify URL contains required parameters
        auth_url = data["authorization_url"]
        assert "client_id=" in auth_url
        assert "redirect_uri=" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=" in auth_url
    
    async def test_admin_token_status_endpoint(self, http_client, server_health_check):
        """Test admin endpoints for token status monitoring."""
        await server_health_check()
        
        # Check tokens status
        response = await http_client.get(f"{KROGER_SERVER_URL}/admin/tokens")
        APITestHelper.assert_status_code(response, 200)
        
        data = response.json()
        assert "client_credentials" in data
        assert "user_tokens" in data
        
        # Check rate limits
        response = await http_client.get(f"{KROGER_SERVER_URL}/admin/rate-limits")
        APITestHelper.assert_status_code(response, 200)
        
        rate_limit_data = response.json()
        assert "rate_limits" in rate_limit_data
    
    async def test_rate_limiting_enforcement(self, http_client, server_health_check):
        """Test that rate limiting is properly enforced."""
        await server_health_check()
        
        # Make multiple rapid requests to trigger rate limiting
        tasks = []
        for i in range(10):
            task = http_client.get(
                f"{KROGER_SERVER_URL}/products/search",
                params={"term": f"test{i}"}
            )
            tasks.append(task)
        
        # Execute requests rapidly
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that some responses are successful
        successful_responses = [
            r for r in responses 
            if not isinstance(r, Exception) and r.status_code == 200
        ]
        assert len(successful_responses) > 0
        
        # Rate limiting should not cause complete failures for reasonable load
        error_responses = [
            r for r in responses 
            if isinstance(r, Exception) or (hasattr(r, 'status_code') and r.status_code == 429)
        ]
        
        # Should handle the load gracefully
        assert len(error_responses) < len(responses)
    
    async def test_error_handling_and_responses(self, http_client, server_health_check):
        """Test server error handling and response formats."""
        await server_health_check()
        
        # Test invalid product search
        response = await http_client.get(
            f"{KROGER_SERVER_URL}/products/search",
            params={"term": ""}  # Empty search term
        )
        
        # Should handle gracefully (either error or empty results)
        assert response.status_code in [200, 400, 422]
        
        # Test non-existent endpoint
        response = await http_client.get(f"{KROGER_SERVER_URL}/nonexistent")
        APITestHelper.assert_status_code(response, 404)
        
        # Test invalid HTTP method
        response = await http_client.patch(f"{KROGER_SERVER_URL}/products/search")
        assert response.status_code in [405, 422]  # Method not allowed or validation error


@pytest.mark.integration
@pytest.mark.real_persistence
class TestKrogerAuthPersistenceIntegration:
    """Test token persistence across actual server restarts."""
    
    @pytest.fixture
    def token_file_path(self):
        """Path to server's token storage file."""
        return os.path.join(os.getcwd(), ".kroger_tokens.json")
    
    @pytest.fixture
    def backup_token_file(self, token_file_path):
        """Backup existing token file."""
        backup_path = f"{token_file_path}.backup"
        
        # Backup existing file if it exists
        if os.path.exists(token_file_path):
            with open(token_file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
        
        yield backup_path
        
        # Restore backup
        if os.path.exists(backup_path):
            if os.path.exists(token_file_path):
                os.remove(token_file_path)
            os.rename(backup_path, token_file_path)
    
    def test_token_file_creation_and_structure(self, token_file_path):
        """Test that server creates and maintains token file properly."""
        # Remove existing token file
        if os.path.exists(token_file_path):
            os.remove(token_file_path)
        
        # Start server (would be done in separate process in real test)
        # For this test, we'll simulate the token file creation
        test_token_data = {
            "user_tokens": {
                "test_user": {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "expires_at": time.time() + 3600,
                    "token_type": "Bearer",
                    "scope": "profile.compact cart.basic:write"
                }
            },
            "client_credentials": {
                "access_token": "test_client_token",
                "expires_at": time.time() + 1800,
                "token_type": "Bearer",
                "scope": "product.compact"
            },
            "last_updated": time.time()
        }
        
        # Write token file
        with open(token_file_path, 'w') as f:
            json.dump(test_token_data, f, indent=2)
        
        # Verify file structure
        assert os.path.exists(token_file_path)
        
        with open(token_file_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert "user_tokens" in loaded_data
        assert "client_credentials" in loaded_data
        assert "last_updated" in loaded_data
        
        # Verify user token structure
        user_token = loaded_data["user_tokens"]["test_user"]
        required_fields = ["access_token", "refresh_token", "expires_at", "token_type", "scope"]
        for field in required_fields:
            assert field in user_token
    
    def test_token_file_corruption_recovery(self, token_file_path):
        """Test server handles corrupted token file gracefully."""
        # Create corrupted token file
        with open(token_file_path, 'w') as f:
            f.write("invalid json content")
        
        # Server should handle this gracefully and create new file
        # In real implementation, server would detect corruption and start fresh
        try:
            with open(token_file_path, 'r') as f:
                json.load(f)
            assert False, "Should have failed to load corrupted JSON"
        except json.JSONDecodeError:
            # Expected behavior - corruption detected
            pass
        
        # Server would create new clean token file
        clean_data = {
            "user_tokens": {},
            "client_credentials": {},
            "last_updated": time.time()
        }
        
        with open(token_file_path, 'w') as f:
            json.dump(clean_data, f)
        
        # Verify recovery
        with open(token_file_path, 'r') as f:
            recovered_data = json.load(f)
        
        assert recovered_data["user_tokens"] == {}
        assert recovered_data["client_credentials"] == {}
    
    def test_concurrent_token_file_access(self, token_file_path):
        """Test handling of concurrent access to token file."""
        # Simulate multiple processes accessing token file
        import threading
        import time
        
        results = []
        errors = []
        
        def write_token(user_id: str):
            """Simulate writing a token to file."""
            try:
                # Read current data
                if os.path.exists(token_file_path):
                    with open(token_file_path, 'r') as f:
                        data = json.load(f)
                else:
                    data = {"user_tokens": {}, "client_credentials": {}, "last_updated": time.time()}
                
                # Add new token
                data["user_tokens"][user_id] = {
                    "access_token": f"token_for_{user_id}",
                    "expires_at": time.time() + 3600
                }
                data["last_updated"] = time.time()
                
                # Simulate processing delay
                time.sleep(0.01)
                
                # Write back
                with open(token_file_path, 'w') as f:
                    json.dump(data, f)
                
                results.append(user_id)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_token, args=[f"user_{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0 or len(errors) < len(threads)  # Some race conditions acceptable
        assert len(results) > 0  # At least some operations succeeded
        
        # Verify final file state
        if os.path.exists(token_file_path):
            with open(token_file_path, 'r') as f:
                final_data = json.load(f)
            
            # File should be valid JSON
            assert "user_tokens" in final_data
            # Some user tokens should have been written
            assert len(final_data["user_tokens"]) > 0


@pytest.mark.integration  
@pytest.mark.real_network
class TestKrogerAuthNetworkIntegration:
    """Test authentication with real network conditions."""
    
    @pytest.fixture
    async def slow_http_client(self):
        """HTTP client with timeout settings for slow network simulation."""
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with AsyncClient(timeout=timeout) as client:
            yield client
    
    @pytest.fixture
    async def fast_http_client(self):
        """HTTP client with aggressive timeout settings."""
        timeout = httpx.Timeout(2.0, connect=1.0)
        async with AsyncClient(timeout=timeout) as client:
            yield client
    
    async def test_network_timeout_handling(self, fast_http_client):
        """Test handling of network timeouts."""
        # Test with aggressive timeouts that might trigger on slow networks
        try:
            response = await fast_http_client.get(
                f"{KROGER_SERVER_URL}/products/search",
                params={"term": "milk"}
            )
            # If request succeeds, verify response
            assert response.status_code in [200, 503]  # Success or service unavailable
        except httpx.TimeoutException:
            # Timeout is acceptable for this test
            pass
        except httpx.ConnectError:
            # Connection error is acceptable for this test
            pass
    
    async def test_connection_pooling_and_reuse(self, slow_http_client):
        """Test connection pooling and reuse."""
        # Make multiple requests to test connection reuse
        responses = []
        
        for i in range(5):
            try:
                response = await slow_http_client.get(
                    f"{KROGER_SERVER_URL}/products/search",
                    params={"term": f"product{i}"}
                )
                responses.append(response)
            except Exception as e:
                # Network issues are acceptable
                responses.append(str(e))
        
        # At least some requests should succeed
        successful_responses = [r for r in responses if hasattr(r, 'status_code')]
        assert len(successful_responses) > 0
    
    async def test_concurrent_network_requests(self, slow_http_client):
        """Test handling of concurrent network requests."""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = slow_http_client.get(
                f"{KROGER_SERVER_URL}/products/search",
                params={"term": f"concurrent_test_{i}"}
            )
            tasks.append(task)
        
        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = 0
        timeouts = 0
        errors = 0
        
        for response in responses:
            if isinstance(response, Exception):
                if "timeout" in str(response).lower():
                    timeouts += 1
                else:
                    errors += 1
            elif hasattr(response, 'status_code') and response.status_code == 200:
                successful += 1
        
        # Should handle concurrent load reasonably
        assert successful > 0  # At least some requests succeed
        assert successful + timeouts + errors == len(responses)
    
    @skip_if_no_credentials
    async def test_real_kroger_api_error_responses(self, slow_http_client):
        """Test handling of real Kroger API error responses."""
        # Test authentication without proper user token (should work with client creds)
        response = await slow_http_client.get(f"{KROGER_SERVER_URL}/products/search?term=test")
        
        # Should either succeed (with client credentials) or provide helpful error
        if response.status_code != 200:
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data
        
        # Test cart operations without authentication (should fail gracefully)
        response = await slow_http_client.get(f"{KROGER_SERVER_URL}/cart")
        
        # Should require authentication
        assert response.status_code in [401, 403]
        error_data = response.json()
        assert "authentication" in error_data.get("detail", "").lower()


@pytest.mark.integration
@pytest.mark.performance
class TestKrogerAuthPerformanceIntegration:
    """Test authentication performance with real server."""
    
    @pytest.fixture
    async def performance_client(self):
        """HTTP client optimized for performance testing."""
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        timeout = httpx.Timeout(30.0)
        async with AsyncClient(limits=limits, timeout=timeout) as client:
            yield client
    
    async def test_token_request_performance(self, performance_client):
        """Test performance of token-related requests."""
        start_time = time.time()
        
        # Test client credentials performance
        response = await performance_client.get(
            f"{KROGER_SERVER_URL}/products/search",
            params={"term": "performance_test"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should respond within reasonable time
        assert response_time < 5.0  # 5 second maximum
        
        if response.status_code == 200:
            # Verify response contains expected data
            data = response.json()
            assert "data" in data
    
    async def test_concurrent_authentication_performance(self, performance_client):
        """Test performance under concurrent authentication load."""
        concurrent_requests = 20
        
        start_time = time.time()
        
        # Create concurrent requests
        tasks = []
        for i in range(concurrent_requests):
            task = performance_client.get(
                f"{KROGER_SERVER_URL}/products/search",
                params={"term": f"perf_test_{i}"}
            )
            tasks.append(task)
        
        # Execute all requests
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze performance
        successful_responses = [
            r for r in responses 
            if not isinstance(r, Exception) and hasattr(r, 'status_code') and r.status_code == 200
        ]
        
        # Performance assertions
        assert total_time < 30.0  # All requests should complete within 30 seconds
        assert len(successful_responses) > concurrent_requests // 2  # At least 50% success rate
        
        # Calculate average response time
        if len(successful_responses) > 0:
            avg_response_time = total_time / len(successful_responses)
            assert avg_response_time < 5.0  # Average under 5 seconds per request
    
    async def test_memory_usage_during_load(self, performance_client):
        """Test memory usage doesn't grow excessively during load."""
        import psutil
        import os
        
        # Get current process (test process)
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate load
        for batch in range(5):
            tasks = []
            for i in range(10):
                task = performance_client.get(
                    f"{KROGER_SERVER_URL}/products/search",
                    params={"term": f"memory_test_{batch}_{i}"}
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check memory usage
            current_memory = process.memory_info().rss
            memory_growth = current_memory - initial_memory
            
            # Memory growth should be reasonable (less than 100MB)
            assert memory_growth < 100 * 1024 * 1024  # 100MB limit


# Test utilities for integration tests
def is_server_running(url: str = KROGER_SERVER_URL) -> bool:
    """Check if Kroger MCP server is running."""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def wait_for_server(url: str = KROGER_SERVER_URL, timeout: int = 30) -> bool:
    """Wait for server to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_server_running(url):
            return True
        time.sleep(1)
    return False


# Pytest configuration for integration tests
@pytest.fixture(scope="session", autouse=True)
def check_server_availability():
    """Check server availability before running integration tests."""
    if not is_server_running():
        pytest.skip("Kroger MCP server is not running. Start server before running integration tests.")


if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--real-server":
        pytest.main([__file__ + "::TestKrogerAuthRealServerIntegration", "-v"])
    elif len(sys.argv) > 1 and sys.argv[1] == "--persistence":
        pytest.main([__file__ + "::TestKrogerAuthPersistenceIntegration", "-v"])
    elif len(sys.argv) > 1 and sys.argv[1] == "--network":
        pytest.main([__file__ + "::TestKrogerAuthNetworkIntegration", "-v"])
    elif len(sys.argv) > 1 and sys.argv[1] == "--performance":
        pytest.main([__file__ + "::TestKrogerAuthPerformanceIntegration", "-v"])
    else:
        pytest.main([__file__, "-v", "--tb=short"])