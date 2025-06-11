"""
Tests for the BaseAgent framework.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.base_agent import BaseAgent, AgentStatus


class TestBaseAgent:
    """Test cases for BaseAgent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_agent_config):
        """Test agent initialization with config."""
        agent = BaseAgent(**test_agent_config)
        
        assert agent.name == "TestAgent"
        assert agent.department == "Testing"
        assert agent.role == "Test Runner"
        assert agent.status == AgentStatus.INITIALIZING
        assert len(agent.memory) == 0
    
    @pytest.mark.asyncio
    async def test_agent_lifecycle(self, test_agent_config):
        """Test agent lifecycle transitions."""
        agent = BaseAgent(**test_agent_config)
        
        # Initialize
        await agent.initialize()
        assert agent.status == AgentStatus.IDLE
        
        # Start
        await agent.start()
        assert agent.status == AgentStatus.RUNNING
        
        # Stop
        await agent.stop()
        assert agent.status == AgentStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_agent_memory_management(self, test_agent_config):
        """Test agent memory operations."""
        agent = BaseAgent(**test_agent_config)
        await agent.initialize()
        
        # Add memory
        memory_item = {
            "type": "interaction",
            "content": "Test interaction",
            "timestamp": "2025-06-10T10:00:00"
        }
        await agent.add_memory(memory_item)
        
        assert len(agent.memory) == 1
        assert agent.memory[0]["content"] == "Test interaction"
        
        # Search memory
        results = await agent.search_memory("interaction")
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, test_agent_config):
        """Test agent health monitoring."""
        agent = BaseAgent(**test_agent_config)
        await agent.initialize()
        await agent.start()
        
        health = await agent.health_check()
        
        assert health["status"] == "healthy"
        assert health["name"] == "TestAgent"
        assert "uptime" in health
        assert "memory_usage" in health
    
    @pytest.mark.asyncio
    async def test_agent_message_handling(self, test_agent_config):
        """Test agent message processing."""
        agent = BaseAgent(**test_agent_config)
        agent.handle_message = AsyncMock(return_value={"response": "processed"})
        
        await agent.initialize()
        await agent.start()
        
        message = {
            "type": "task",
            "content": "Test task",
            "from": "test_sender"
        }
        
        result = await agent.handle_message(message)
        
        agent.handle_message.assert_called_once_with(message)
        assert result["response"] == "processed"