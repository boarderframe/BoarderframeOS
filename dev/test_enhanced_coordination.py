#!/usr/bin/env python3
"""
Simple Enhanced Message Bus Test
Tests the enhanced coordination features
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boarderframeos'))

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("message_bus_test")

async def test_enhanced_message_bus():
    """Test the enhanced message bus features"""
    logger.info("=== Testing Enhanced Message Bus ===")
    
    try:
        # Import with proper path
        from core.enhanced_message_bus import EnhancedMessageBus, EnhancedAgentMessage, RoutingStrategy, DeliveryStatus
        from core.message_bus import MessageType, MessagePriority
        
        # Initialize enhanced message bus
        logger.info("Initializing Enhanced Message Bus...")
        bus = EnhancedMessageBus()
        await bus.start()
        
        # Test 1: Basic message creation
        logger.info("Test 1: Creating enhanced message...")
        message = EnhancedAgentMessage(
            from_agent="test_sender",
            to_agent="test_receiver", 
            message_type=MessageType.TASK_REQUEST,
            content={"task": "analyze_data", "priority": "high"},
            routing_strategy=RoutingStrategy.CAPABILITY_BASED,
            required_capabilities=["data_analysis"]
        )
        logger.info(f"Created message: {message.message_id}")
        
        # Test 2: Register agent capabilities
        logger.info("Test 2: Registering agent capabilities...")
        await bus.register_agent_capabilities("test_agent", ["data_analysis", "reporting"])
        
        # Test 3: Capability-based discovery
        logger.info("Test 3: Testing capability discovery...")
        agents = await bus.discover_agents_by_capability("data_analysis")
        logger.info(f"Agents with data_analysis capability: {agents}")
        
        # Test 4: Performance metrics
        logger.info("Test 4: Getting performance metrics...")
        metrics = await bus.get_performance_metrics()
        logger.info(f"Performance metrics: {metrics}")
        
        # Test 5: Circuit breaker functionality
        logger.info("Test 5: Testing circuit breaker...")
        breaker = bus.circuit_breakers.get("test_agent")
        if breaker:
            logger.info(f"Circuit breaker state: {breaker.state}")
        
        await bus.stop()
        logger.info("Enhanced Message Bus test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

async def test_coordination_manager():
    """Test the coordination manager features"""
    logger.info("=== Testing Coordination Manager ===")
    
    try:
        from core.agent_coordination_manager import AgentCoordinationManager, CoordinationPattern
        
        logger.info("Initializing Coordination Manager...")
        manager = AgentCoordinationManager()
        await manager.start()
        
        # Test workflow creation
        logger.info("Test: Creating workflow...")
        workflow_id = await manager.create_workflow(
            workflow_id="test_workflow_001",
            pattern=CoordinationPattern.SEQUENTIAL,
            participants=["agent1", "agent2", "agent3"],
            coordinator="test_coordinator",
            tasks=[
                {"step": 1, "agent": "agent1", "action": "analyze"},
                {"step": 2, "agent": "agent2", "action": "process"},
                {"step": 3, "agent": "agent3", "action": "report"}
            ]
        )
        logger.info(f"Created workflow: {workflow_id}")
        
        # Test consensus request
        logger.info("Test: Requesting consensus...")
        consensus_result = await manager.consensus_manager.request_consensus(
            proposal_id="test_decision_001",
            participants=["agent1", "agent2", "agent3"],
            proposal={"decision": "Should we proceed with project X?", "options": ["yes", "no"]},
            voting_method="majority"
        )
        logger.info(f"Consensus result: {consensus_result}")
        
        # Test auction
        logger.info("Test: Starting auction...")
        auction_result = await manager.auction_manager.start_auction(
            auction_id="test_auction_001",
            task={"description": "Analyze market data", "complexity": "medium"},
            participants=["agent1", "agent2"],
            duration_seconds=30
        )
        logger.info(f"Auction result: {auction_result}")
        
        await manager.stop()
        logger.info("Coordination Manager test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

async def test_agent_controller_coordination():
    """Test the agent controller coordination features"""
    logger.info("=== Testing Agent Controller Coordination ===")
    
    try:
        from core.agent_controller import AgentController
        
        logger.info("Initializing Agent Controller...")
        controller = AgentController()
        await controller.start()
        
        # Test capability registration
        logger.info("Test: Registering agent capabilities...")
        from core.agent_registry import AgentCapability
        capabilities = [
            AgentCapability(name="data_analysis", description="Analyze data"),
            AgentCapability(name="reporting", description="Generate reports")
        ]
        await controller.register_agent_capabilities("test_agent", capabilities)
        
        # Test capability discovery
        logger.info("Test: Discovering agents by capability...")
        agents = await controller.discover_agents_by_capability("data_analysis")
        logger.info(f"Found agents: {agents}")
        
        # Test workflow creation
        logger.info("Test: Creating agent workflow...")
        workflow_id = await controller.create_agent_workflow(
            workflow_type="sequential",
            participants=["agent1", "agent2"],
            tasks=[
                {"step": 1, "action": "analyze"},
                {"step": 2, "action": "report"}
            ]
        )
        logger.info(f"Created workflow: {workflow_id}")
        
        # Test coordination metrics
        logger.info("Test: Getting coordination metrics...")
        metrics = await controller.get_agent_coordination_metrics()
        logger.info(f"Coordination metrics: {metrics}")
        
        await controller.stop()
        logger.info("Agent Controller coordination test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

async def main():
    """Run all coordination tests"""
    logger.info("Starting Enhanced Agent Coordination Tests...")
    
    # Test enhanced message bus
    bus_success = await test_enhanced_message_bus()
    
    # Test coordination manager  
    coord_success = await test_coordination_manager()
    
    # Test agent controller
    controller_success = await test_agent_controller_coordination()
    
    # Summary
    logger.info("=== TEST SUMMARY ===")
    logger.info(f"Enhanced Message Bus: {'✓ PASS' if bus_success else '✗ FAIL'}")
    logger.info(f"Coordination Manager: {'✓ PASS' if coord_success else '✗ FAIL'}")
    logger.info(f"Agent Controller: {'✓ PASS' if controller_success else '✗ FAIL'}")
    
    if all([bus_success, coord_success, controller_success]):
        logger.info("🎉 All coordination tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
