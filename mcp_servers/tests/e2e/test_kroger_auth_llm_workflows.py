"""
End-to-End LLM Integration Tests for Kroger MCP Authentication.

These tests simulate complete workflows that an LLM agent would experience:
1. Initial authentication setup
2. Product search with automatic token management
3. Cart operations with authentication handling
4. Error recovery scenarios
5. Session persistence across interactions
6. Multi-step shopping workflows

Tests are designed to match real LLM usage patterns and validate the complete user experience.
"""

import pytest
import asyncio
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
from httpx import AsyncClient

from tests.utils.test_helpers import APITestHelper, PerformanceTestHelper
from tests.factories.test_data_factory import TestDataFactory


# Test configuration
KROGER_SERVER_URL = os.getenv("KROGER_SERVER_URL", "http://localhost:9004")
TEST_TIMEOUT = 30.0


class LLMTestScenario(Enum):
    """LLM test scenario types."""
    GROCERY_SHOPPING = "grocery_shopping"
    PRODUCT_RESEARCH = "product_research"
    STORE_LOCATOR = "store_locator"
    CART_MANAGEMENT = "cart_management"
    USER_PROFILE = "user_profile"


@dataclass
class LLMStep:
    """Represents a single step in an LLM workflow."""
    action: str
    endpoint: str
    params: Dict[str, Any]
    expected_status: int = 200
    requires_auth: bool = False
    description: str = ""


@dataclass
class LLMWorkflow:
    """Represents a complete LLM workflow."""
    name: str
    scenario: LLMTestScenario
    steps: List[LLMStep]
    expected_duration: float = 10.0
    description: str = ""


class LLMTestAgent:
    """Simulates an LLM agent interacting with Kroger MCP server."""
    
    def __init__(self, server_url: str = KROGER_SERVER_URL):
        self.server_url = server_url
        self.session_data: Dict[str, Any] = {}
        self.execution_log: List[Dict[str, Any]] = []
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = AsyncClient(timeout=TEST_TIMEOUT)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
    
    def log_step(self, step: str, status: str, data: Dict[str, Any] = None):
        """Log execution step."""
        self.execution_log.append({
            "timestamp": time.time(),
            "step": step,
            "status": status,
            "data": data or {}
        })
    
    async def authenticate_user(self, user_id: str = None) -> bool:
        """Simulate user authentication for cart operations."""
        if not user_id:
            user_id = f"llm_test_user_{TestDataFactory.random_string(8)}"
        
        self.user_id = user_id
        
        try:
            # Check if we can get auth URL (simulates LLM getting auth flow)
            response = await self.client.get(
                f"{self.server_url}/auth/authorize",
                params={
                    "scope": "profile.compact cart.basic:write",
                    "state": f"llm_test_{TestDataFactory.random_string(8)}"
                }
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.session_data["auth_url"] = auth_data.get("authorization_url")
                self.log_step("get_auth_url", "success", auth_data)
                
                # In real scenario, user would complete OAuth flow
                # For testing, we simulate having tokens
                self.auth_token = "simulated_auth_token"
                return True
            else:
                self.log_step("get_auth_url", "failed", {"status": response.status_code})
                return False
                
        except Exception as e:
            self.log_step("authenticate_user", "error", {"error": str(e)})
            return False
    
    async def execute_step(self, step: LLMStep) -> Dict[str, Any]:
        """Execute a single workflow step."""
        step_start = time.time()
        
        try:
            # Prepare request
            headers = {}
            if step.requires_auth and self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Execute request
            if step.action.upper() == "GET":
                response = await self.client.get(
                    f"{self.server_url}{step.endpoint}",
                    params=step.params,
                    headers=headers
                )
            elif step.action.upper() == "POST":
                response = await self.client.post(
                    f"{self.server_url}{step.endpoint}",
                    json=step.params,
                    headers=headers
                )
            elif step.action.upper() == "PUT":
                response = await self.client.put(
                    f"{self.server_url}{step.endpoint}",
                    json=step.params,
                    headers=headers
                )
            else:
                raise ValueError(f"Unsupported action: {step.action}")
            
            step_duration = time.time() - step_start
            
            # Process response
            result = {
                "step": step.description or step.endpoint,
                "status_code": response.status_code,
                "duration": step_duration,
                "success": response.status_code == step.expected_status,
                "response_size": len(response.content) if response.content else 0
            }
            
            # Parse response data if JSON
            try:
                if response.headers.get("content-type", "").startswith("application/json"):
                    result["data"] = response.json()
            except:
                result["data"] = None
            
            # Store relevant data for subsequent steps
            if result["success"] and result.get("data"):
                self._store_session_data(step, result["data"])
            
            self.log_step(f"execute_{step.action.lower()}", 
                         "success" if result["success"] else "failed", 
                         result)
            
            return result
            
        except Exception as e:
            step_duration = time.time() - step_start
            error_result = {
                "step": step.description or step.endpoint,
                "status_code": 0,
                "duration": step_duration,
                "success": False,
                "error": str(e)
            }
            
            self.log_step(f"execute_{step.action.lower()}", "error", error_result)
            return error_result
    
    def _store_session_data(self, step: LLMStep, data: Dict[str, Any]):
        """Store relevant data from responses for session continuity."""
        # Store cart IDs
        if "cart" in step.endpoint.lower() and "cartId" in data:
            self.session_data["cart_id"] = data["cartId"]
        
        # Store product IDs from search results
        if "products" in step.endpoint.lower() and "data" in data:
            products = data["data"]
            if products and isinstance(products, list):
                self.session_data["last_products"] = [
                    p.get("productId") for p in products[:5]  # Store first 5 product IDs
                ]
        
        # Store location IDs
        if "locations" in step.endpoint.lower() and "data" in data:
            locations = data["data"]
            if locations and isinstance(locations, list):
                self.session_data["last_locations"] = [
                    l.get("locationId") for l in locations[:3]  # Store first 3 location IDs
                ]
    
    async def execute_workflow(self, workflow: LLMWorkflow) -> Dict[str, Any]:
        """Execute a complete LLM workflow."""
        workflow_start = time.time()
        results = []
        
        self.log_step("start_workflow", "info", {"workflow": workflow.name})
        
        for i, step in enumerate(workflow.steps):
            # Check if step requires authentication
            if step.requires_auth and not self.auth_token:
                auth_success = await self.authenticate_user()
                if not auth_success:
                    self.log_step("workflow_auth_failed", "error", {"step": i})
                    break
            
            # Execute step
            step_result = await self.execute_step(step)
            results.append(step_result)
            
            # If step failed and it's critical, stop workflow
            if not step_result["success"] and step.expected_status < 400:
                self.log_step("workflow_step_failed", "warning", {
                    "step": i,
                    "step_name": step.description or step.endpoint
                })
                # Continue execution for non-critical failures
        
        workflow_duration = time.time() - workflow_start
        
        # Analyze workflow results
        successful_steps = sum(1 for r in results if r["success"])
        failed_steps = len(results) - successful_steps
        
        workflow_result = {
            "workflow": workflow.name,
            "scenario": workflow.scenario.value,
            "total_duration": workflow_duration,
            "steps_executed": len(results),
            "steps_successful": successful_steps,
            "steps_failed": failed_steps,
            "success_rate": successful_steps / len(results) if results else 0,
            "results": results,
            "session_data": self.session_data.copy(),
            "within_expected_time": workflow_duration <= workflow.expected_duration
        }
        
        self.log_step("complete_workflow", "success", workflow_result)
        return workflow_result


# Predefined LLM workflows
def create_grocery_shopping_workflow() -> LLMWorkflow:
    """Create a typical grocery shopping workflow."""
    return LLMWorkflow(
        name="grocery_shopping",
        scenario=LLMTestScenario.GROCERY_SHOPPING,
        description="Complete grocery shopping workflow with cart operations",
        expected_duration=15.0,
        steps=[
            LLMStep(
                action="GET",
                endpoint="/config",
                params={},
                description="Get server configuration"
            ),
            LLMStep(
                action="GET",
                endpoint="/products/search",
                params={"term": "milk"},
                description="Search for milk products"
            ),
            LLMStep(
                action="GET",
                endpoint="/products/search",
                params={"term": "bread"},
                description="Search for bread products"
            ),
            LLMStep(
                action="GET",
                endpoint="/products/search/compact",
                params={"term": "eggs", "limit": 5},
                description="Search for eggs with compact response"
            ),
            LLMStep(
                action="GET",
                endpoint="/locations/search",
                params={},
                description="Find nearby stores"
            ),
            # Cart operations would require authentication in real scenario
            # For testing, we'll simulate these as well
        ]
    )


def create_product_research_workflow() -> LLMWorkflow:
    """Create a product research workflow."""
    return LLMWorkflow(
        name="product_research",
        scenario=LLMTestScenario.PRODUCT_RESEARCH,
        description="Research products across multiple categories",
        expected_duration=12.0,
        steps=[
            LLMStep(
                action="GET",
                endpoint="/products/search",
                params={"term": "organic"},
                description="Search for organic products"
            ),
            LLMStep(
                action="GET",
                endpoint="/products/search",
                params={"term": "gluten free"},
                description="Search for gluten-free products"
            ),
            LLMStep(
                action="GET",
                endpoint="/products/search/compact",
                params={"term": "vitamins", "limit": 10},
                description="Search for vitamins with compact response"
            ),
            LLMStep(
                action="GET",
                endpoint="/locations/search",
                params={},
                description="Find stores for availability check"
            )
        ]
    )


def create_store_locator_workflow() -> LLMWorkflow:
    """Create a store locator workflow."""
    return LLMWorkflow(
        name="store_locator",
        scenario=LLMTestScenario.STORE_LOCATOR,
        description="Find and analyze store locations",
        expected_duration=8.0,
        steps=[
            LLMStep(
                action="GET",
                endpoint="/config",
                params={},
                description="Get default location configuration"
            ),
            LLMStep(
                action="GET",
                endpoint="/locations/search",
                params={},
                description="Search for nearby stores"
            ),
            # Would normally have specific location details, but that requires location IDs
            # from the search results
        ]
    )


def create_error_recovery_workflow() -> LLMWorkflow:
    """Create a workflow that tests error recovery."""
    return LLMWorkflow(
        name="error_recovery",
        scenario=LLMTestScenario.PRODUCT_RESEARCH,
        description="Test error handling and recovery",
        expected_duration=10.0,
        steps=[
            LLMStep(
                action="GET",
                endpoint="/products/search",
                params={"term": ""},  # Empty search term
                expected_status=422,  # Expect validation error
                description="Test empty search term handling"
            ),
            LLMStep(
                action="GET",
                endpoint="/nonexistent",
                params={},
                expected_status=404,
                description="Test 404 error handling"
            ),
            LLMStep(
                action="GET",
                endpoint="/products/search",
                params={"term": "recovery_test"},
                description="Successful request after errors"
            )
        ]
    )


@pytest.mark.e2e
@pytest.mark.llm_integration
class TestKrogerAuthLLMWorkflows:
    """End-to-end LLM workflow tests."""
    
    @pytest.fixture
    async def llm_agent(self):
        """Create LLM test agent."""
        async with LLMTestAgent() as agent:
            yield agent
    
    @pytest.fixture
    def workflows(self):
        """Get all test workflows."""
        return [
            create_grocery_shopping_workflow(),
            create_product_research_workflow(),
            create_store_locator_workflow(),
            create_error_recovery_workflow()
        ]
    
    async def test_grocery_shopping_workflow(self, llm_agent):
        """Test complete grocery shopping workflow."""
        workflow = create_grocery_shopping_workflow()
        result = await llm_agent.execute_workflow(workflow)
        
        # Verify workflow execution
        assert result["steps_executed"] > 0
        assert result["success_rate"] >= 0.8  # At least 80% success rate
        assert result["within_expected_time"]
        
        # Verify specific outcomes
        assert "session_data" in result
        
        # Should have found products in searches
        search_results = [r for r in result["results"] if "search" in r["step"]]
        assert len(search_results) >= 3
        
        # At least some searches should return data
        successful_searches = [r for r in search_results if r["success"] and r.get("data")]
        assert len(successful_searches) > 0
    
    async def test_product_research_workflow(self, llm_agent):
        """Test product research workflow."""
        workflow = create_product_research_workflow()
        result = await llm_agent.execute_workflow(workflow)
        
        assert result["success_rate"] >= 0.75
        assert result["within_expected_time"]
        
        # Should have performed multiple product searches
        search_steps = [r for r in result["results"] if "search" in r.get("step", "").lower()]
        assert len(search_steps) >= 3
        
        # Verify response times are reasonable for research workflow
        avg_response_time = sum(r["duration"] for r in result["results"]) / len(result["results"])
        assert avg_response_time < 3.0  # Average under 3 seconds per step
    
    async def test_store_locator_workflow(self, llm_agent):
        """Test store locator workflow."""
        workflow = create_store_locator_workflow()
        result = await llm_agent.execute_workflow(workflow)
        
        assert result["success_rate"] >= 0.8
        assert result["within_expected_time"]
        
        # Should have retrieved configuration and locations
        config_step = next((r for r in result["results"] if "config" in r.get("step", "")), None)
        assert config_step and config_step["success"]
        
        location_step = next((r for r in result["results"] if "locations" in r.get("step", "")), None)
        assert location_step and location_step["success"]
    
    async def test_error_recovery_workflow(self, llm_agent):
        """Test error handling and recovery."""
        workflow = create_error_recovery_workflow()
        result = await llm_agent.execute_workflow(workflow)
        
        # Should handle errors gracefully
        assert result["steps_executed"] == len(workflow.steps)
        
        # Check that expected errors were handled correctly
        error_results = result["results"]
        
        # First step should fail with validation error
        assert error_results[0]["status_code"] in [400, 422]
        
        # Second step should fail with 404
        assert error_results[1]["status_code"] == 404
        
        # Third step should succeed (recovery)
        assert error_results[2]["success"]
    
    async def test_concurrent_llm_workflows(self, workflows):
        """Test multiple LLM workflows running concurrently."""
        async def run_workflow(workflow):
            async with LLMTestAgent() as agent:
                return await agent.execute_workflow(workflow)
        
        # Run multiple workflows concurrently
        tasks = [run_workflow(workflow) for workflow in workflows[:3]]  # Use first 3 workflows
        results = await asyncio.gather(*tasks)
        
        # All workflows should complete successfully
        assert len(results) == 3
        
        for result in results:
            assert result["success_rate"] >= 0.7  # At least 70% success under load
            assert result["total_duration"] < 20.0  # Complete within 20 seconds
    
    async def test_llm_session_persistence(self, llm_agent):
        """Test that LLM session data persists across multiple interactions."""
        # First interaction
        workflow1 = create_product_research_workflow()
        result1 = await llm_agent.execute_workflow(workflow1)
        
        initial_session_data = llm_agent.session_data.copy()
        
        # Second interaction should build on first
        workflow2 = create_store_locator_workflow()
        result2 = await llm_agent.execute_workflow(workflow2)
        
        # Session data should persist and potentially grow
        final_session_data = llm_agent.session_data
        
        # Should have retained some data from first workflow
        for key in initial_session_data:
            assert key in final_session_data
        
        # Both workflows should succeed
        assert result1["success_rate"] >= 0.7
        assert result2["success_rate"] >= 0.7
    
    async def test_llm_performance_under_load(self, llm_agent):
        """Test LLM workflow performance characteristics."""
        # Run the same workflow multiple times to test consistency
        workflow = create_grocery_shopping_workflow()
        
        results = []
        for i in range(5):
            result = await llm_agent.execute_workflow(workflow)
            results.append(result)
        
        # Analyze performance consistency
        durations = [r["total_duration"] for r in results]
        success_rates = [r["success_rate"] for r in results]
        
        # Performance should be consistent
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        # Variance should be reasonable
        assert max_duration - min_duration < avg_duration  # Variance less than average
        assert avg_duration < 20.0  # Average completion under 20 seconds
        
        # Success rates should be consistently high
        avg_success_rate = sum(success_rates) / len(success_rates)
        min_success_rate = min(success_rates)
        
        assert avg_success_rate >= 0.8
        assert min_success_rate >= 0.7  # Even worst case should be decent
    
    async def test_llm_error_message_quality(self, llm_agent):
        """Test that error messages are helpful for LLM agents."""
        # Test various error scenarios
        error_steps = [
            LLMStep("GET", "/cart", {}, 401, True, "Test authentication required"),
            LLMStep("GET", "/products/search", {"term": ""}, 422, False, "Test validation error"),
            LLMStep("GET", "/nonexistent", {}, 404, False, "Test not found error"),
        ]
        
        for step in error_steps:
            result = await llm_agent.execute_step(step)
            
            # Error should be handled gracefully
            assert not result["success"]
            assert result["status_code"] == step.expected_status
            
            # Should have response data with error information
            if result.get("data"):
                error_data = result["data"]
                # Error messages should be present and helpful
                assert "detail" in error_data or "error" in error_data
                
                error_message = error_data.get("detail", error_data.get("error", ""))
                assert len(error_message) > 10  # Should be descriptive
                assert any(word in error_message.lower() for word in 
                          ["authentication", "required", "invalid", "not found", "validation"])


@pytest.mark.e2e
@pytest.mark.llm_integration
@pytest.mark.performance
class TestKrogerAuthLLMPerformance:
    """Performance tests for LLM workflows."""
    
    async def test_rapid_sequential_requests(self):
        """Test rapid sequential requests as LLM might make."""
        async with LLMTestAgent() as agent:
            search_terms = ["milk", "bread", "eggs", "cheese", "yogurt", "butter", "chicken", "beef"]
            
            start_time = time.time()
            results = []
            
            for term in search_terms:
                step = LLMStep("GET", "/products/search", {"term": term}, description=f"Search for {term}")
                result = await agent.execute_step(step)
                results.append(result)
            
            total_time = time.time() - start_time
            
            # Should complete all searches quickly
            assert total_time < 15.0  # All 8 searches in under 15 seconds
            
            # Most searches should succeed
            successful = sum(1 for r in results if r["success"])
            assert successful >= len(search_terms) * 0.8  # 80% success rate
            
            # Average response time should be reasonable
            avg_response_time = sum(r["duration"] for r in results) / len(results)
            assert avg_response_time < 3.0  # Under 3 seconds average
    
    async def test_llm_memory_usage_patterns(self):
        """Test memory usage patterns during LLM workflows."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run multiple workflows
        workflows = [
            create_grocery_shopping_workflow(),
            create_product_research_workflow(),
            create_store_locator_workflow()
        ]
        
        async with LLMTestAgent() as agent:
            for workflow in workflows:
                await agent.execute_workflow(workflow)
                
                # Check memory usage after each workflow
                current_memory = process.memory_info().rss
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable (less than 50MB)
                assert memory_growth < 50 * 1024 * 1024
    
    async def test_llm_response_size_efficiency(self):
        """Test that responses are efficiently sized for LLM consumption."""
        async with LLMTestAgent() as agent:
            # Test compact vs regular responses
            regular_step = LLMStep("GET", "/products/search", {"term": "milk"})
            compact_step = LLMStep("GET", "/products/search/compact", {"term": "milk", "limit": 5})
            
            regular_result = await agent.execute_step(regular_step)
            compact_result = await agent.execute_step(compact_step)
            
            if regular_result["success"] and compact_result["success"]:
                # Compact response should be smaller
                assert compact_result["response_size"] <= regular_result["response_size"]
                
                # Both should contain useful data
                assert regular_result.get("data") is not None
                assert compact_result.get("data") is not None


# Helper functions for test setup
async def setup_test_environment():
    """Setup test environment for LLM integration tests."""
    # Check server health
    try:
        async with AsyncClient() as client:
            response = await client.get(f"{KROGER_SERVER_URL}/health")
            if response.status_code != 200:
                pytest.skip("Kroger MCP server is not healthy")
    except Exception:
        pytest.skip("Cannot connect to Kroger MCP server")


@pytest.fixture(scope="session", autouse=True)
async def test_environment():
    """Setup test environment."""
    await setup_test_environment()


if __name__ == "__main__":
    # Run LLM workflow tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "llm_integration"])