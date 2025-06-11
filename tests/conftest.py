"""
Pytest configuration and fixtures for BoarderframeOS tests.
"""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Set testing environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://boarderframe:test@localhost:5434/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        pool_pre_ping=True,
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.fixture
def mock_llm_response():
    """Mock LLM API responses for testing."""
    def _mock_response(content: str):
        return {
            "choices": [{
                "message": {
                    "content": content,
                    "role": "assistant"
                }
            }],
            "usage": {
                "total_tokens": 100,
                "prompt_tokens": 50,
                "completion_tokens": 50
            }
        }
    return _mock_response


@pytest.fixture
def test_agent_config():
    """Sample agent configuration for testing."""
    return {
        "name": "TestAgent",
        "department": "Testing",
        "role": "Test Runner",
        "tier": 3,
        "model_binding": "worker_swarm",
        "capabilities": ["testing", "validation"],
        "memory_size": 1000
    }
