#!/usr/bin/env python3
"""
Simple Message Bus Test
Tests basic message bus functionality without complex coordination
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from boarderframeos.core.message_bus import MessageBus, MessageType, MessagePriority, AgentMessage
from boarderframeos.core.enhanced_message_bus import enhanced_message_bus, EnhancedAgentMessage, RoutingStrategy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simple_message_test")

class TestAgent:
    """Simple test agent for message bus testing"""
    
    def __init__(self, name: str):
        self.name = name
        self.received_messages = []
    
    async def handle_message(self, message):
        """Handle incoming message"""
        logger.info(f"Agent {self.name} received: {message.content}")
        self.received_messages.append(message)
        return {"status": "received", "agent": self.name}

async def test_basic_message_bus():
    """Test basic message bus functionality"""
    logger.info("🧪 Testing Basic Message Bus")
    
    try:
        # Create test agents
        agent_a = TestAgent("AgentA")
        agent_b = TestAgent("AgentB")
        
        # Create message bus
        bus = MessageBus()
        
        # Register agents
        await bus.register_agent("agent_a")
        await bus.register_agent("agent_b")
        
        # Subscribe to handle messages (for basic testing)
        await bus.subscribe_to_topic("agent_a", "default", agent_a.handle_message)
        await bus.subscribe_to_topic("agent_b", "default", agent_b.handle_message)
        
        # Send basic message
        message = AgentMessage(
            from_agent="agent_a",
            to_agent="agent_b",
            message_type=MessageType.COORDINATION,
            content={"action": "hello", "data": "test message"},
            priority=MessagePriority.NORMAL
        )
        
        response = await bus.send_message(message)
        logger.info(f"✅ Basic message sent, response: {response}")
        
        # Test topic subscription
        await bus.subscribe_to_topic("agent_a", "test_topic")
        await bus.publish_to_topic("test_topic", {
            "message": "topic broadcast",
            "sender": "system"
        })
        
        logger.info("✅ Basic message bus test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic message bus test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_message_bus():
    """Test enhanced message bus functionality"""
    logger.info("🧪 Testing Enhanced Message Bus")
    
    try:
        # Start enhanced message bus
        await enhanced_message_bus.start()
        
        # Register test agents
        await enhanced_message_bus.register_agent("test_agent_1", ["coordination", "analysis"])
        await enhanced_message_bus.register_agent("test_agent_2", ["research", "communication"])
        
        # Create enhanced message
        message = EnhancedAgentMessage(
            from_agent="test_agent_1",
            to_agent="test_agent_2",
            message_type=MessageType.TASK_REQUEST,
            content={"task": "analyze_data", "priority": "high"},
            routing_strategy=RoutingStrategy.DIRECT,
            priority=MessagePriority.HIGH
        )
        
        # Send enhanced message
        success = await enhanced_message_bus.send_enhanced_message(message)
        logger.info(f"✅ Enhanced message sent: {success}")
        
        # Test capability-based discovery
        agents = await enhanced_message_bus.discover_agents_by_capability("coordination")
        logger.info(f"✅ Agents with coordination capability: {agents}")
        
        # Stop enhanced message bus
        await enhanced_message_bus.stop()
        
        logger.info("✅ Enhanced message bus test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced message bus test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_message_routing():
    """Test different message routing strategies"""
    logger.info("🧪 Testing Message Routing Strategies")
    
    try:
        await enhanced_message_bus.start()
        
        # Register multiple agents
        agents = ["router_agent_1", "router_agent_2", "router_agent_3"]
        for agent in agents:
            await enhanced_message_bus.register_agent(agent, ["routing_test"])
        
        # Test different routing strategies
        routing_strategies = [
            RoutingStrategy.DIRECT,
            RoutingStrategy.ROUND_ROBIN,
            RoutingStrategy.LOAD_BALANCED
        ]
        
        for strategy in routing_strategies:
            message = EnhancedAgentMessage(
                from_agent="system",
                to_agent="router_agent_1",  # Will be routed based on strategy
                message_type=MessageType.TASK_REQUEST,
                content={"test": f"routing_test_{strategy.value}"},
                routing_strategy=strategy
            )
            
            success = await enhanced_message_bus.send_enhanced_message(message)
            logger.info(f"✅ Routing strategy {strategy.value}: {success}")
        
        await enhanced_message_bus.stop()
        
        logger.info("✅ Message routing test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Message routing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_message_persistence():
    """Test message persistence features"""
    logger.info("🧪 Testing Message Persistence")
    
    try:
        await enhanced_message_bus.start()
        
        # Send persistent message
        message = EnhancedAgentMessage(
            from_agent="persistent_sender",
            to_agent="persistent_receiver",
            message_type=MessageType.COORDINATION,
            content={"persistent": True, "data": "test_persistence"},
            persistent=True,
            ttl_seconds=3600
        )
        
        success = await enhanced_message_bus.send_enhanced_message(message)
        logger.info(f"✅ Persistent message sent: {success}")
        
        # Test message retrieval
        history = enhanced_message_bus.get_message_history()
        logger.info(f"✅ Message history contains {len(history)} messages")
        
        await enhanced_message_bus.stop()
        
        logger.info("✅ Message persistence test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Message persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all message bus tests"""
    logger.info("🌟 Simple Message Bus Testing")
    logger.info("=" * 50)
    
    tests = [
        ("Basic Message Bus", test_basic_message_bus),
        ("Enhanced Message Bus", test_enhanced_message_bus),
        ("Message Routing", test_message_routing),
        ("Message Persistence", test_message_persistence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All message bus tests PASSED!")
        return 0
    else:
        logger.error("❌ Some message bus tests FAILED!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
