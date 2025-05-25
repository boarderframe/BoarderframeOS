#!/usr/bin/env python3
"""
Debug MessageType Enum Issue
Simple test to identify the enum creation problem
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_enum")

def test_basic_imports():
    """Test basic imports"""
    try:
        logger.info("Testing basic message bus import...")
        from boarderframeos.core.message_bus import MessageType, MessagePriority
        logger.info(f"✅ MessageType: {list(MessageType)}")
        logger.info(f"✅ MessagePriority: {list(MessagePriority)}")
        
        logger.info("Testing enhanced message bus import...")
        from boarderframeos.core.enhanced_message_bus import DeliveryStatus, RoutingStrategy
        logger.info(f"✅ DeliveryStatus: {list(DeliveryStatus)}")
        logger.info(f"✅ RoutingStrategy: {list(RoutingStrategy)}")
        
        logger.info("Testing agent coordination manager import...")
        from boarderframeos.core.agent_coordination_manager import CoordinationPattern, TaskState
        logger.info(f"✅ CoordinationPattern: {list(CoordinationPattern)}")
        logger.info(f"✅ TaskState: {list(TaskState)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_message_creation():
    """Test message creation"""
    try:
        logger.info("Testing AgentMessage creation...")
        from boarderframeos.core.message_bus import AgentMessage, MessageType, MessagePriority
        
        # Test basic message creation
        message = AgentMessage(
            from_agent="test_sender",
            to_agent="test_receiver", 
            message_type=MessageType.COORDINATION,
            content={"test": "data"},
            priority=MessagePriority.NORMAL
        )
        
        logger.info(f"✅ Created message: {message.message_type}")
        
        logger.info("Testing EnhancedAgentMessage creation...")
        from boarderframeos.core.enhanced_message_bus import EnhancedAgentMessage, RoutingStrategy
        
        enhanced_message = EnhancedAgentMessage(
            from_agent="test_sender",
            to_agent="test_receiver",
            message_type=MessageType.COORDINATION,
            content={"test": "enhanced_data"},
            routing_strategy=RoutingStrategy.DIRECT
        )
        
        logger.info(f"✅ Created enhanced message: {enhanced_message.message_type}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Message creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_controller():
    """Test agent controller initialization"""
    try:
        logger.info("Testing agent controller import...")
        from boarderframeos.core.agent_controller import agent_controller
        
        logger.info("Testing agent controller start...")
        await agent_controller.start()
        
        logger.info("✅ Agent controller started successfully")
        
        logger.info("Testing agent controller stop...")
        await agent_controller.stop()
        
        logger.info("✅ Agent controller stopped successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent controller error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main debug function"""
    logger.info("🔍 Debugging MessageType Enum Issue")
    logger.info("=" * 50)
    
    # Test basic imports
    if not test_basic_imports():
        logger.error("❌ Basic imports failed")
        return 1
    
    # Test message creation
    if not test_message_creation():
        logger.error("❌ Message creation failed")
        return 1
    
    # Test agent controller
    if not await test_agent_controller():
        logger.error("❌ Agent controller test failed")
        return 1
    
    logger.info("✅ All tests passed!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
