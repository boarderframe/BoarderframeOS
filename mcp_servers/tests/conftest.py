"""
Pytest configuration and shared fixtures for Kroger MCP Authentication tests.
"""
import asyncio
import os
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import Mock

import httpx


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    original_env = os.environ.copy()
    
    test_env = {
        "KROGER_CLIENT_ID": "test_client_id",
        "KROGER_CLIENT_SECRET": "test_client_secret", 
        "KROGER_REDIRECT_URI": "http://localhost:9004/auth/callback",
        "KROGER_BASE_URL": "https://api.kroger.com/v1",
        "KROGER_DEV_MODE": "true",
        "TEST_MODE": "true"
    }
    
    os.environ.update(test_env)
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
async def async_http_client():
    """Create an async HTTP client for testing."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        yield temp.name
    os.unlink(temp.name)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_kroger_server_url():
    """Mock Kroger server URL for testing."""
    return os.getenv("KROGER_SERVER_URL", "http://localhost:9004")


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "cart_auth: mark test as cart authentication test"
    )
    config.addinivalue_line(
        "markers", "llm_integration: mark test as LLM integration test"
    )
    config.addinivalue_line(
        "markers", "real_server: mark test requiring real server"
    )
    config.addinivalue_line(
        "markers", "real_network: mark test requiring real network"
    )
    config.addinivalue_line(
        "markers", "real_persistence: mark test requiring real persistence"
    )
    config.addinivalue_line(
        "markers", "llm_scenarios: mark test as LLM scenario test"
    )


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time
    import psutil
    
    start_time = time.time()
    start_memory = psutil.virtual_memory().used
    
    yield
    
    end_time = time.time()
    end_memory = psutil.virtual_memory().used
    
    execution_time = end_time - start_time
    memory_delta = end_memory - start_memory
    
    # Store metrics for potential analysis
    return {
        "execution_time": execution_time,
        "memory_delta": memory_delta
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for each test."""
    # Ensure we're in test mode
    os.environ.setdefault("TEST_MODE", "true")
    os.environ.setdefault("KROGER_DEV_MODE", "true")
    yield
    # Cleanup happens automatically with autouse