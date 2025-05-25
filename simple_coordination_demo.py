#!/usr/bin/env python3
"""
Enhanced Agent Coordination Demo - No API Keys Required
Demonstrates the coordination features without starting actual agent processes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boarderframeos'))

import asyncio
import logging
from datetime import datetime, timedelta

from core.agent_controller import AgentController, TaskPriority, AgentTask
from core.agent_registry import AgentCapability
from core.enhanced_message_bus import EnhancedAgentMessage, RoutingStrategy, DeliveryStatus
from core.message_bus import MessageType, MessagePriority

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coordination_demo")

class SimpleCoordinationDemo:
    """Demonstrates enhanced agent coordination capabilities without real agents"""
    
    def __init__(self):
        self.controller = AgentController()
        
    async def setup_demo_environment(self):
        """Setup the demo environment with mock agent registrations"""
        try:
            logger.info("Setting up demo environment...")
            
            # Start the agent controller
            await self.controller.start()
            logger.info("✅ Agent controller started")
            
            # Register agent capabilities without starting the actual agents
            await self.register_mock_capabilities()
            logger.info("✅ Mock capabilities registered")
            
        except Exception as e:
            logger.error(f"Setup error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def register_mock_capabilities(self):
        """Register capabilities for mock agents"""
        # Solomon capabilities
        solomon_capabilities = [
            AgentCapability.PLANNING,
            AgentCapability.COORDINATION,
            AgentCapability.ANALYSIS
        ]
        await self.controller.register_agent_capabilities("solomon", solomon_capabilities)
        
        # David capabilities  
        david_capabilities = [
            AgentCapability.RESEARCH,
            AgentCapability.ANALYSIS,
            AgentCapability.PLANNING
        ]
        await self.controller.register_agent_capabilities("david", david_capabilities)
        
        # Analyst capabilities
        analyst_capabilities = [
            AgentCapability.ANALYSIS,
            AgentCapability.MONITORING,
            AgentCapability.RESEARCH
        ]
        await self.controller.register_agent_capabilities("analyst_agent", analyst_capabilities)
        
        logger.info("Registered capabilities for all mock agents")
    
    async def demo_agent_discovery_by_capability(self):
        """Demonstrate agent discovery by capability"""
        logger.info("\n=== DEMO: Agent Discovery by Capability ===")
        
        # Find agents with specific capabilities
        analysis_agents = await self.controller.find_agents_by_capability(AgentCapability.ANALYSIS)
        research_agents = await self.controller.find_agents_by_capability(AgentCapability.RESEARCH)
        planning_agents = await self.controller.find_agents_by_capability(AgentCapability.PLANNING)
        
        logger.info(f"🔍 Agents with ANALYSIS capability: {analysis_agents}")
        logger.info(f"🔍 Agents with RESEARCH capability: {research_agents}")
        logger.info(f"🔍 Agents with PLANNING capability: {planning_agents}")
    
    async def demo_message_bus_features(self):
        """Demonstrate enhanced message bus features"""
        logger.info("\n=== DEMO: Enhanced Message Bus Features ===")
        
        # Get the enhanced message bus
        message_bus = self.controller.enhanced_message_bus
        
        # Register mock agents with the message bus
        await message_bus.register_agent("solomon", queue_size=10)
        await message_bus.register_agent("david", queue_size=10) 
        await message_bus.register_agent("analyst_agent", queue_size=10)
        
        # Test capability-based routing
        message = EnhancedAgentMessage(
            from_agent="solomon",
            to_agent="",  # Will be resolved by capability
            message_type=MessageType.TASK_REQUEST,
            content={
                "task": "analyze_market_data",
                "data": "Q4_sales.csv",
                "priority": "high"
            },
            routing_strategy=RoutingStrategy.CAPABILITY_BASED,
            required_capabilities=["analysis"]
        )
        
        success = await message_bus.send_enhanced_message(message)
        logger.info(f"✅ Capability-based message routing: {success}")
        
        # Test workflow creation
        workflow_id = await message_bus.create_workflow(
            workflow_id="demo_workflow",
            steps=[
                {"agent": "david", "action": "research", "data": "market_trends"},
                {"agent": "analyst_agent", "action": "analyze", "data": "research_results"},
                {"agent": "solomon", "action": "plan", "data": "analysis_results"}
            ]
        )
        logger.info(f"✅ Workflow created: {workflow_id}")
        
        # Get performance metrics
        metrics = await message_bus.get_performance_metrics()
        logger.info(f"✅ Performance metrics:")
        logger.info(f"   Messages sent: {metrics['delivery_metrics']['total_messages_sent']}")
        logger.info(f"   Active agents: {metrics['delivery_metrics']['active_agents']}")
        logger.info(f"   Queue sizes: {metrics['queue_metrics']}")
    
    async def demo_coordination_patterns(self):
        """Demonstrate coordination patterns"""
        logger.info("\n=== DEMO: Coordination Patterns ===")
        
        # Sequential workflow
        sequential_workflow = await self.controller.create_workflow(
            workflow_id="sequential_demo",
            pattern="sequential",
            participants=["david", "analyst_agent", "solomon"],
            coordinator="solomon",
            tasks=[
                {"step": 1, "agent": "david", "action": "research"},
                {"step": 2, "agent": "analyst_agent", "action": "analyze"},
                {"step": 3, "agent": "solomon", "action": "synthesize"}
            ]
        )
        logger.info(f"✅ Sequential workflow created: {sequential_workflow}")
        
        # Parallel workflow
        parallel_workflow = await self.controller.create_workflow(
            workflow_id="parallel_demo",
            pattern="parallel", 
            participants=["david", "analyst_agent", "solomon"],
            coordinator="solomon",
            tasks=[
                {"agent": "david", "action": "research_market"},
                {"agent": "analyst_agent", "action": "analyze_competitors"},
                {"agent": "solomon", "action": "review_strategy"}
            ]
        )
        logger.info(f"✅ Parallel workflow created: {parallel_workflow}")
        
        # Get workflow status
        status = await self.controller.coordination_manager.get_workflow_status(sequential_workflow)
        if status:
            logger.info(f"📊 Sequential workflow status: {status['state']}")
    
    async def demo_consensus_mechanism(self):
        """Demonstrate consensus decision making"""
        logger.info("\n=== DEMO: Consensus Decision Making ===")
        
        # Create consensus proposal
        result = await self.controller.create_consensus_proposal(
            proposal_id="budget_allocation",
            proposal_data={
                "question": "Should we allocate 40% of budget to AI research?",
                "options": ["yes", "no", "modify"],
                "context": "Q1 budget planning meeting"
            },
            participants=["solomon", "david", "analyst_agent"],
            voting_timeout=300
        )
        
        logger.info(f"✅ Consensus proposal created: {result}")
        logger.info("🗳️ Proposal sent to participants for voting")
    
    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring"""
        logger.info("\\n=== DEMO: Performance Monitoring ===\")
        
        # Get coordination metrics
        coordination_metrics = await self.controller.get_coordination_metrics()
        
        logger.info("📊 Current System Metrics:")
        logger.info(f"   Active Workflows: {coordination_metrics.get('active_workflows', 0)}")
        logger.info(f"   Registered Agents: {len(coordination_metrics.get('agent_capabilities', {}))}")
        logger.info(f"   Message Bus Status: Active")
        
        # Get message bus performance
        if hasattr(self.controller, 'enhanced_message_bus'):
            bus_metrics = await self.controller.enhanced_message_bus.get_performance_metrics()
            logger.info(f"   Total Messages: {bus_metrics['delivery_metrics']['total_messages_sent']}")
            logger.info(f"   Average Queue Size: {bus_metrics['delivery_metrics']['average_queue_size']:.2f}")

async def run_demo():
    """Run the coordination demo"""
    demo = SimpleCoordinationDemo()
    
    try:
        await demo.setup_demo_environment()
        
        await demo.demo_agent_discovery_by_capability()
        await demo.demo_message_bus_features()  
        await demo.demo_coordination_patterns()
        await demo.demo_consensus_mechanism()
        await demo.demo_performance_monitoring()
        
        logger.info("\\n🎉 All coordination demos completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await demo.controller.stop()

if __name__ == "__main__":
    asyncio.run(run_demo())
