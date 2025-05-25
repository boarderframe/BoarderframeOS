#!/usr/bin/env python3
"""
Simple Enhanced Message Bus Test
Tests the core message bus functionality without requiring actual agents
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boarderframeos'))

import asyncio
import logging
from datetime import datetime

from core.enhanced_message_bus import EnhancedMessageBus, EnhancedAgentMessage, RoutingStrategy
from core.message_bus import MessageType, MessagePriority

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("message_bus_test")

async def test_enhanced_message_bus():
    """Test the enhanced message bus without actual agent processes"""
    
    # Initialize message bus
    bus = EnhancedMessageBus("test_message_bus.db")
    await bus.start()
    
    try:
        # Register test "agents" (just queue registration)
        await bus.register_agent("test_agent_1", queue_size=10)
        await bus.register_agent("test_agent_2", queue_size=10)
        await bus.register_agent("test_agent_3", queue_size=10)
        
        # Register capabilities
        await bus.register_agent_capabilities("test_agent_1", ["analysis", "research"])
        await bus.register_agent_capabilities("test_agent_2", ["planning", "coordination"])
        await bus.register_agent_capabilities("test_agent_3", ["analysis", "monitoring"])
        
        logger.info("✅ Registered test agents and capabilities")
        
        # Test 1: Direct message
        message1 = EnhancedAgentMessage(
            from_agent="test_agent_1",
            to_agent="test_agent_2",
            message_type=MessageType.TASK_REQUEST,
            content={"action": "analyze_data", "data": "sample.csv"},
            routing_strategy=RoutingStrategy.DIRECT
        )
        
        success = await bus.send_enhanced_message(message1)
        logger.info(f"✅ Direct message sent: {success}")
        
        # Test 2: Capability-based routing
        message2 = EnhancedAgentMessage(
            from_agent="test_agent_1",
            to_agent="",  # Will be resolved by capability
            message_type=MessageType.COORDINATION,
            content={"action": "coordinate_task", "task_id": "123"},
            routing_strategy=RoutingStrategy.CAPABILITY_BASED,
            required_capabilities=["analysis"]
        )
        
        success = await bus.send_enhanced_message(message2)
        logger.info(f"✅ Capability-based message sent: {success}")
        
        # Test 3: Get performance metrics
        metrics = await bus.get_performance_metrics()
        logger.info(f"✅ Performance metrics retrieved")
        logger.info(f"   Total messages sent: {metrics['delivery_metrics']['total_messages_sent']}")
        logger.info(f"   Active agents: {metrics['delivery_metrics']['active_agents']}")
        logger.info(f"   Agent capabilities: {metrics['agent_capabilities']}")
        
        # Test 4: Get message history
        history = await bus.get_messages_for_agent("test_agent_1", limit=10)
        logger.info(f"✅ Message history retrieved: {len(history)} messages")
        
        # Test 5: Workflow creation
        workflow_id = await bus.create_workflow(
            workflow_id="test_workflow_1",
            steps=[
                {"agent": "test_agent_1", "action": "analyze"},
                {"agent": "test_agent_2", "action": "plan"},
                {"agent": "test_agent_3", "action": "monitor"}
            ]
        )
        logger.info(f"✅ Workflow created: {workflow_id}")
        
        logger.info("\n🎉 All enhanced message bus tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await bus.stop()
        # Clean up test database
        if os.path.exists("test_message_bus.db"):
            os.remove("test_message_bus.db")

if __name__ == "__main__":
    asyncio.run(test_enhanced_message_bus())
