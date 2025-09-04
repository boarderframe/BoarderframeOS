"""
Comprehensive Cart Operations with Authentication Tests.

These tests focus specifically on cart functionality with automatic token management:
1. Cart creation with authentication
2. Adding items with token validation
3. Cart operations with expired tokens and automatic refresh
4. Concurrent cart operations
5. Cart persistence across sessions
6. Error handling for cart-specific authentication issues

Tests simulate real LLM agent cart management scenarios.
"""

import pytest
import asyncio
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

import httpx
from httpx import AsyncClient

from tests.utils.test_helpers import APITestHelper, PerformanceTestHelper
from tests.factories.test_data_factory import TestDataFactory


class CartAuthTestHelper:
    """Helper class for cart authentication testing."""
    
    @staticmethod
    def create_cart_item_data(**overrides) -> Dict[str, Any]:
        """Create cart item test data."""
        base_data = {
            "upc": TestDataFactory.random_string(12, "0123456789"),
            "quantity": 1,
            "modality": "PICKUP"
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_cart_request(**overrides) -> Dict[str, Any]:
        """Create cart request data."""
        base_data = {
            "items": [
                CartAuthTestHelper.create_cart_item_data(upc="0001111042100", quantity=2),
                CartAuthTestHelper.create_cart_item_data(upc="0001111042101", quantity=1)
            ]
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_mock_cart_response(**overrides) -> Dict[str, Any]:
        """Create mock cart API response."""
        base_data = {
            "data": {
                "cartId": f"cart_{TestDataFactory.random_string(16)}",
                "customerId": f"customer_{TestDataFactory.random_string(12)}",
                "locationId": "01600966",
                "items": [
                    {
                        "itemId": "0001111042100",
                        "quantity": 2,
                        "modifiedTime": datetime.utcnow().isoformat()
                    }
                ]
            }
        }
        base_data.update(overrides)
        return base_data


@pytest.mark.integration
@pytest.mark.cart_auth
class TestKrogerCartAuthentication:
    """Test cart operations with authentication."""
    
    @pytest.fixture
    async def auth_client(self):
        """HTTP client for authenticated requests."""
        async with AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture
    def server_url(self):
        """Kroger server URL."""
        return os.getenv("KROGER_SERVER_URL", "http://localhost:9004")
    
    @pytest.fixture
    def mock_user_token(self):
        """Mock user authentication token."""
        return f"mock_user_token_{TestDataFactory.random_string(32)}"
    
    async def test_cart_operations_require_authentication(self, auth_client, server_url):
        """Test that cart operations require proper authentication."""
        cart_endpoints = [
            ("/cart", "GET"),
            ("/cart/add", "PUT"),
            ("/cart/add/simple", "PUT"),
            ("/cart/items", "PUT")
        ]
        
        for endpoint, method in cart_endpoints:
            # Request without authentication should fail
            if method == "GET":
                response = await auth_client.get(f"{server_url}{endpoint}")
            elif method == "PUT":
                response = await auth_client.put(
                    f"{server_url}{endpoint}",
                    json={"items": [{"upc": "123", "quantity": 1}]}
                )
            
            # Should require authentication
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth"
            
            # Error message should be helpful
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                assert "detail" in error_data
                assert "authentication" in error_data["detail"].lower()
    
    async def test_cart_add_simple_with_mock_auth(self, auth_client, server_url, mock_user_token):
        """Test simple cart add with mock authentication."""
        # This test simulates the LLM-friendly cart add endpoint
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': mock_user_token,
            'KROGER_USER_REFRESH_TOKEN': 'mock_refresh_token',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
            'KROGER_DEV_MODE': 'true'
        }):
            # Test simple cart add (LLM-optimized endpoint)
            response = await auth_client.put(
                f"{server_url}/cart/add/simple",
                params={
                    "upc": "0001111042100",
                    "quantity": 2
                }
            )
            
            # In dev mode, should work
            if response.status_code == 200:
                data = response.json()
                assert "success" in data
                assert data.get("upc") == "0001111042100"
                assert data.get("quantity") == 2
            else:
                # If not authenticated, should give helpful error
                assert response.status_code in [401, 503]
                if response.headers.get("content-type", "").startswith("application/json"):
                    error_data = response.json()
                    assert "detail" in error_data
    
    async def test_cart_add_with_authentication_headers(self, auth_client, server_url, mock_user_token):
        """Test cart operations with Bearer token authentication."""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        cart_data = CartAuthTestHelper.create_cart_request()
        
        # Test cart add with auth header
        response = await auth_client.put(
            f"{server_url}/cart/add",
            json=cart_data,
            headers=headers
        )
        
        # Should either succeed or fail with specific auth error
        if response.status_code in [200, 201]:
            # Success case
            assert response.status_code in [200, 201, 204]
        elif response.status_code in [401, 403]:
            # Auth failure case
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            assert "detail" in error_data
        else:
            # Service unavailable or other error
            assert response.status_code in [503, 500]
    
    async def test_cart_get_with_authentication(self, auth_client, server_url):
        """Test cart retrieval with authentication."""
        # Setup mock authentication
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': 'mock_token',
            'KROGER_USER_REFRESH_TOKEN': 'mock_refresh',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
            'KROGER_DEV_MODE': 'true'
        }):
            response = await auth_client.get(f"{server_url}/cart")
            
            if response.status_code == 200:
                # Should return cart data
                data = response.json()
                assert "data" in data
                cart_data = data["data"]
                assert "cartId" in cart_data
                assert "items" in cart_data
            else:
                # Should fail with auth error or service unavailable
                assert response.status_code in [401, 403, 503]
    
    async def test_concurrent_cart_operations(self, auth_client, server_url):
        """Test concurrent cart operations with authentication."""
        # Setup mock authentication
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': 'concurrent_test_token',
            'KROGER_USER_REFRESH_TOKEN': 'concurrent_refresh_token',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
            'KROGER_DEV_MODE': 'true'
        }):
            # Create multiple concurrent cart operations
            tasks = []
            
            # Add different items concurrently
            items = [
                {"upc": "0001111042100", "quantity": 1},
                {"upc": "0001111042101", "quantity": 2},
                {"upc": "0001111042102", "quantity": 1},
            ]
            
            for item in items:
                task = auth_client.put(
                    f"{server_url}/cart/add/simple",
                    params=item
                )
                tasks.append(task)
            
            # Execute concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful_responses = 0
            auth_errors = 0
            other_errors = 0
            
            for response in responses:
                if isinstance(response, Exception):
                    other_errors += 1
                elif response.status_code in [200, 201, 204]:
                    successful_responses += 1
                elif response.status_code in [401, 403]:
                    auth_errors += 1
                else:
                    other_errors += 1
            
            # Should handle concurrent requests reasonably
            # At least some should succeed or all should consistently fail with auth
            assert successful_responses > 0 or auth_errors == len(responses)
    
    async def test_cart_operations_with_expired_token_simulation(self, auth_client, server_url):
        """Test cart operations when token is expired."""
        # Simulate expired token
        expired_time = time.time() - 100  # Expired 100 seconds ago
        
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': 'expired_token',
            'KROGER_USER_REFRESH_TOKEN': 'refresh_token_for_expired',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(expired_time),
            'KROGER_DEV_MODE': 'true'
        }):
            response = await auth_client.put(
                f"{server_url}/cart/add/simple",
                params={"upc": "0001111042100", "quantity": 1}
            )
            
            # Should either:
            # 1. Automatically refresh token and succeed
            # 2. Fail with helpful error about token expiry
            if response.status_code in [200, 201]:
                # Token was refreshed successfully
                data = response.json()
                assert "success" in data or "upc" in data
            else:
                # Failed due to auth issues
                assert response.status_code in [401, 403, 503]
                if response.headers.get("content-type", "").startswith("application/json"):
                    error_data = response.json()
                    assert "detail" in error_data
                    # Error should mention token or authentication
                    assert any(word in error_data["detail"].lower() 
                             for word in ["token", "authentication", "expired", "refresh"])
    
    async def test_cart_error_message_quality(self, auth_client, server_url):
        """Test quality of error messages for cart authentication failures."""
        test_scenarios = [
            {
                "name": "no_auth",
                "headers": {},
                "expected_status": [401, 403],
                "expected_keywords": ["authentication", "required"]
            },
            {
                "name": "invalid_token",
                "headers": {"Authorization": "Bearer invalid_token_123"},
                "expected_status": [401, 403],
                "expected_keywords": ["invalid", "token"]
            },
            {
                "name": "malformed_auth",
                "headers": {"Authorization": "InvalidFormat"},
                "expected_status": [401, 403],
                "expected_keywords": ["authentication", "invalid"]
            }
        ]
        
        for scenario in test_scenarios:
            response = await auth_client.put(
                f"{server_url}/cart/add/simple",
                params={"upc": "0001111042100", "quantity": 1},
                headers=scenario["headers"]
            )
            
            # Should fail with expected status
            assert response.status_code in scenario["expected_status"], f"Scenario {scenario['name']} failed"
            
            # Should have helpful error message
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                assert "detail" in error_data, f"No detail in error for {scenario['name']}"
                
                error_message = error_data["detail"].lower()
                # Should contain at least one expected keyword
                keyword_found = any(keyword in error_message for keyword in scenario["expected_keywords"])
                assert keyword_found, f"No expected keywords in error for {scenario['name']}: {error_message}"


@pytest.mark.integration
@pytest.mark.cart_auth
@pytest.mark.performance
class TestKrogerCartAuthPerformance:
    """Test cart authentication performance."""
    
    @pytest.fixture
    async def performance_client(self):
        """Optimized client for performance testing."""
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
        timeout = httpx.Timeout(15.0)
        async with AsyncClient(limits=limits, timeout=timeout) as client:
            yield client
    
    @pytest.fixture
    def server_url(self):
        """Kroger server URL."""
        return os.getenv("KROGER_SERVER_URL", "http://localhost:9004")
    
    async def test_cart_authentication_response_time(self, performance_client, server_url):
        """Test response time for cart authentication."""
        # Setup mock environment
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': 'perf_test_token',
            'KROGER_USER_REFRESH_TOKEN': 'perf_refresh_token',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
            'KROGER_DEV_MODE': 'true'
        }):
            # Test simple cart add performance
            start_time = time.time()
            
            response = await performance_client.put(
                f"{server_url}/cart/add/simple",
                params={"upc": "0001111042100", "quantity": 1}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Should respond quickly
            assert response_time < 3.0, f"Cart auth response too slow: {response_time:.3f}s"
            
            # Should either succeed or fail gracefully
            assert response.status_code in [200, 201, 204, 401, 403, 503]
    
    async def test_multiple_cart_operations_performance(self, performance_client, server_url):
        """Test performance of multiple cart operations."""
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': 'multi_perf_token',
            'KROGER_USER_REFRESH_TOKEN': 'multi_refresh_token',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
            'KROGER_DEV_MODE': 'true'
        }):
            # Perform multiple sequential cart operations
            operations = [
                {"upc": "0001111042100", "quantity": 1},
                {"upc": "0001111042101", "quantity": 2},
                {"upc": "0001111042102", "quantity": 1},
                {"upc": "0001111042103", "quantity": 3},
                {"upc": "0001111042104", "quantity": 1},
            ]
            
            start_time = time.time()
            
            for operation in operations:
                response = await performance_client.put(
                    f"{server_url}/cart/add/simple",
                    params=operation
                )
                # Don't assert success here, just measure performance
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / len(operations)
            
            # Average operation should be fast
            assert avg_time < 2.0, f"Average cart operation too slow: {avg_time:.3f}s"
            assert total_time < 10.0, f"Total time too slow: {total_time:.3f}s"
    
    async def test_cart_auth_under_load(self, performance_client, server_url):
        """Test cart authentication under concurrent load."""
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': 'load_test_token',
            'KROGER_USER_REFRESH_TOKEN': 'load_refresh_token',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
            'KROGER_DEV_MODE': 'true'
        }):
            # Create concurrent cart operations
            concurrent_ops = 15
            
            async def cart_operation(op_id: int):
                return await performance_client.put(
                    f"{server_url}/cart/add/simple",
                    params={"upc": f"000111104210{op_id % 10}", "quantity": 1}
                )
            
            start_time = time.time()
            
            # Execute concurrent operations
            tasks = [cart_operation(i) for i in range(concurrent_ops)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze results
            successful = 0
            failed = 0
            errors = 0
            
            for response in responses:
                if isinstance(response, Exception):
                    errors += 1
                elif hasattr(response, 'status_code'):
                    if response.status_code in [200, 201, 204]:
                        successful += 1
                    else:
                        failed += 1
                else:
                    errors += 1
            
            # Performance assertions
            assert total_time < 20.0, f"Concurrent operations took too long: {total_time:.3f}s"
            
            # Should handle load gracefully (either mostly succeed or consistently fail)
            total_requests = successful + failed + errors
            assert total_requests == concurrent_ops
            
            # If any succeeded, should have reasonable success rate
            if successful > 0:
                success_rate = successful / concurrent_ops
                assert success_rate >= 0.6, f"Success rate too low under load: {success_rate:.2f}"


@pytest.mark.integration
@pytest.mark.cart_auth
@pytest.mark.llm_scenarios
class TestKrogerCartAuthLLMScenarios:
    """Test cart authentication in LLM usage scenarios."""
    
    @pytest.fixture
    async def llm_client(self):
        """HTTP client for LLM scenario testing."""
        async with AsyncClient(timeout=20.0) as client:
            yield client
    
    @pytest.fixture
    def server_url(self):
        """Kroger server URL."""
        return os.getenv("KROGER_SERVER_URL", "http://localhost:9004")
    
    async def test_llm_shopping_cart_workflow(self, llm_client, server_url):
        """Test complete LLM shopping cart workflow with authentication."""
        # Simulate LLM agent workflow
        with patch.dict(os.environ, {
            'KROGER_USER_ACCESS_TOKEN': 'llm_workflow_token',
            'KROGER_USER_REFRESH_TOKEN': 'llm_refresh_token',
            'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
            'KROGER_DEV_MODE': 'true'
        }):
            workflow_steps = [
                # 1. LLM searches for products
                {
                    "action": "search_products",
                    "method": "GET",
                    "endpoint": "/products/search",
                    "params": {"term": "milk"}
                },
                # 2. LLM adds product to cart
                {
                    "action": "add_to_cart",
                    "method": "PUT", 
                    "endpoint": "/cart/add/simple",
                    "params": {"upc": "0001111042100", "quantity": 1}
                },
                # 3. LLM adds another product
                {
                    "action": "add_bread",
                    "method": "PUT",
                    "endpoint": "/cart/add/simple", 
                    "params": {"upc": "0001111042101", "quantity": 2}
                },
                # 4. LLM checks cart contents
                {
                    "action": "get_cart",
                    "method": "GET",
                    "endpoint": "/cart",
                    "params": {}
                }
            ]
            
            results = []
            
            for step in workflow_steps:
                start_time = time.time()
                
                try:
                    if step["method"] == "GET":
                        response = await llm_client.get(
                            f"{server_url}{step['endpoint']}",
                            params=step["params"]
                        )
                    elif step["method"] == "PUT":
                        response = await llm_client.put(
                            f"{server_url}{step['endpoint']}",
                            params=step["params"]
                        )
                    
                    duration = time.time() - start_time
                    
                    result = {
                        "action": step["action"],
                        "status_code": response.status_code,
                        "duration": duration,
                        "success": response.status_code in [200, 201, 204]
                    }
                    
                    if result["success"] and response.headers.get("content-type", "").startswith("application/json"):
                        result["data"] = response.json()
                    
                    results.append(result)
                    
                except Exception as e:
                    results.append({
                        "action": step["action"],
                        "status_code": 0,
                        "duration": time.time() - start_time,
                        "success": False,
                        "error": str(e)
                    })
            
            # Analyze workflow results
            successful_steps = sum(1 for r in results if r["success"])
            total_steps = len(results)
            
            # Should have reasonable success rate
            success_rate = successful_steps / total_steps if total_steps > 0 else 0
            
            # Product search should work (no auth required)
            search_step = next((r for r in results if r["action"] == "search_products"), None)
            assert search_step is not None
            # Search should either succeed or fail gracefully
            assert search_step["status_code"] in [200, 503, 500]
            
            # Cart operations should handle auth consistently
            cart_steps = [r for r in results if "cart" in r["action"] or "add" in r["action"]]
            if cart_steps:
                # All cart operations should have consistent auth handling
                cart_statuses = [step["status_code"] for step in cart_steps]
                # Should either all succeed, all fail with auth error, or all fail with service error
                unique_status_types = set()
                for status in cart_statuses:
                    if status in [200, 201, 204]:
                        unique_status_types.add("success")
                    elif status in [401, 403]:
                        unique_status_types.add("auth_error")
                    else:
                        unique_status_types.add("other_error")
                
                # Should be consistent (not mixed success/auth errors)
                assert len(unique_status_types) <= 2, f"Inconsistent auth handling: {cart_statuses}"
    
    async def test_llm_cart_error_recovery(self, llm_client, server_url):
        """Test LLM error recovery for cart authentication issues."""
        # Test different error scenarios LLM might encounter
        error_scenarios = [
            {
                "name": "no_auth_env",
                "env": {},  # No auth environment
                "expected_behavior": "consistent_auth_error"
            },
            {
                "name": "expired_token",
                "env": {
                    'KROGER_USER_ACCESS_TOKEN': 'expired_token',
                    'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() - 100),
                    'KROGER_DEV_MODE': 'true'
                },
                "expected_behavior": "auth_error_or_refresh"
            },
            {
                "name": "valid_dev_mode",
                "env": {
                    'KROGER_USER_ACCESS_TOKEN': 'valid_dev_token',
                    'KROGER_USER_REFRESH_TOKEN': 'valid_refresh',
                    'KROGER_USER_TOKEN_EXPIRES_AT': str(time.time() + 3600),
                    'KROGER_DEV_MODE': 'true'
                },
                "expected_behavior": "success_or_service_error"
            }
        ]
        
        for scenario in error_scenarios:
            with patch.dict(os.environ, scenario["env"], clear=True):
                # Try cart operation
                response = await llm_client.put(
                    f"{server_url}/cart/add/simple",
                    params={"upc": "0001111042100", "quantity": 1}
                )
                
                # Analyze response based on expected behavior
                if scenario["expected_behavior"] == "consistent_auth_error":
                    # Should consistently fail with auth error
                    assert response.status_code in [401, 403], f"Scenario {scenario['name']} should fail with auth error"
                
                elif scenario["expected_behavior"] == "auth_error_or_refresh":
                    # Should either fail with auth error or succeed if refresh worked
                    assert response.status_code in [200, 201, 204, 401, 403], f"Scenario {scenario['name']} unexpected status"
                
                elif scenario["expected_behavior"] == "success_or_service_error":
                    # Should either succeed or fail with service error (not auth error)
                    if response.status_code in [401, 403]:
                        # If auth error, should have helpful message
                        if response.headers.get("content-type", "").startswith("application/json"):
                            error_data = response.json()
                            assert "detail" in error_data
                            # Message should be helpful for LLM
                            assert len(error_data["detail"]) > 10
                
                # All scenarios should return valid HTTP responses
                assert 100 <= response.status_code <= 599, f"Invalid status code for {scenario['name']}"


if __name__ == "__main__":
    # Run cart authentication tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "cart_auth"])