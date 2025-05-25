#!/usr/bin/env python3
"""
Enhanced Agent Coordination Demo
Demonstrates the new coordination features in the Agent Controller
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'boarderframeos'))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from core.agent_controller import AgentController, TaskPriority, AgentTask
from core.agent_registry import AgentCapability
from core.enhanced_message_bus import EnhancedAgentMessage, RoutingStrategy, DeliveryStatus
from core.message_bus import MessageType, MessagePriority

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coordination_demo")

class CoordinationDemo:
    """Demonstrates enhanced agent coordination capabilities"""
    
    def __init__(self):
        self.controller = AgentController()
        self.demo_agents = ["solomon", "david", "analyst_agent"]
        
    async def setup_demo_environment(self):
        """Setup the demo environment with agents and capabilities"""
        try:
            logger.info("Setting up demo environment...")
            
            # Start the agent controller
            await self.controller.start()
            logger.info("✅ Agent controller started")
            
            # Register agent capabilities
            await self.register_demo_capabilities()
            logger.info("✅ Demo capabilities registered")
            
            # Create and start demo agents if they don't exist
            await self.ensure_demo_agents()
            logger.info("✅ Demo agents ensured")
            
        except Exception as e:
            logger.error(f"Setup error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def register_demo_capabilities(self):
        """Register capabilities for demo agents"""
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
        
        logger.info("Registered capabilities for all demo agents")
    
    async def ensure_demo_agents(self):
        """Ensure demo agents are available"""
        # Check if API key is available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment. Agent processes won't start but coordination features will work.")
            return
            
        for agent_name in self.demo_agents:
            try:
                # Try to create agent if it doesn't exist
                if agent_name not in self.controller.agent_configs:
                    await self.controller.create_agent(
                        name=agent_name,
                        agent_type="general",
                        role=f"{agent_name.title()} Agent",
                        goals=[f"Assist with {agent_name} related tasks"],
                        zone="demo_zone"
                    )
                    logger.info(f"Created demo agent: {agent_name}")
                
                # Start the agent if not running
                if agent_name not in self.controller.running_processes:
                    logger.info(f"Attempting to start agent: {agent_name}")
                    success = await self.controller.start_agent(agent_name)
                    if success:
                        logger.info(f"✅ Started demo agent: {agent_name}")
                        # Give the agent a moment to initialize
                        await asyncio.sleep(2)
                    else:
                        logger.warning(f"⚠️ Failed to start agent: {agent_name} (may need API key or have other issues)")
                        
            except Exception as e:
                logger.warning(f"Could not setup agent {agent_name}: {e}")
                import traceback
                traceback.print_exc()
    
    async def demo_capability_based_routing(self):
        """Demonstrate capability-based task routing"""
        logger.info("\n=== DEMO: Capability-Based Task Routing ===")
        
        # Task requiring data analysis capability
        task_id = await self.controller.auto_assign_task(
            task_type="data_analysis",
            data={
                "dataset": "sales_data_2024.csv",
                "analysis_type": "trend_analysis",
                "requirements": ["statistical_analysis", "visualization"]
            },
            required_capabilities=[
                AgentCapability.ANALYSIS
            ],
            routing_strategy="capability_based"
        )
        
        if task_id:
            logger.info(f"✅ Task assigned with capability-based routing: {task_id}")
            
            # Check which agent got the task
            if task_id in self.controller.task_queue:
                task = self.controller.task_queue[task_id]
                logger.info(f"📍 Task assigned to agent: {task.agent_id}")
            else:
                logger.info("📍 Task was processed immediately")
        else:
            logger.warning("⚠️ No agents available for capability-based routing (agents may not be running)")
            logger.info("💡 This is normal if agent processes aren't started - coordination features still work")
    
    async def demo_load_balanced_routing(self):
        """Demonstrate load-balanced task routing"""
        logger.info("\n=== DEMO: Load-Balanced Task Routing ===")
        
        # Create multiple similar tasks to show load balancing
        task_ids = []
        for i in range(3):
            task_id = await self.controller.auto_assign_task(
                task_type="research",
                data={
                    "topic": f"Market Research Topic {i+1}",
                    "depth": "comprehensive",
                    "deadline": (datetime.now() + timedelta(hours=2)).isoformat()
                },
                required_capabilities=[
                    AgentCapability.RESEARCH
                ],
                routing_strategy="load_balanced"
            )
            
            if task_id:
                task_ids.append(task_id)
                task = self.controller.task_queue[task_id]
                logger.info(f"✅ Task {i+1} assigned to: {task.agent_id}")
        
        logger.info(f"📊 Created {len(task_ids)} tasks with load-balanced routing")
    
    async def demo_sequential_workflow(self):
        """Demonstrate sequential workflow coordination"""
        logger.info("\n=== DEMO: Sequential Workflow Coordination ===")
        
        # Check if we have running agents
        running_agents = list(self.controller.running_processes.keys())
        if not running_agents:
            logger.info("ℹ️ No agents running - using registered agent configurations for demo")
            participants = ["david", "analyst_agent", "solomon"]
        else:
            participants = running_agents[:3]  # Use first 3 running agents
            
        logger.info(f"📋 Workflow participants: {participants}")
        
        # Create a sequential workflow: Research -> Analysis -> Decision
        workflow_tasks = [
            {
                "agent": participants[0] if len(participants) > 0 else "david",
                "task": {
                    "type": "research",
                    "data": {"topic": "AI Market Trends", "scope": "comprehensive"}
                }
            },
            {
                "agent": participants[1] if len(participants) > 1 else "analyst_agent", 
                "task": {
                    "type": "data_analysis",
                    "data": {"input": "research_output", "analysis_type": "trend_analysis"}
                }
            },
            {
                "agent": participants[2] if len(participants) > 2 else "solomon",
                "task": {
                    "type": "strategic_decision",
                    "data": {"analysis_input": "trend_analysis", "decision_scope": "investment"}
                }
            }
        ]
        
        try:
            workflow_id = await self.controller.create_agent_workflow(
                workflow_type="sequential",
                participants=participants,
                tasks=workflow_tasks
            )
            
            if workflow_id:
                logger.info(f"✅ Created sequential workflow: {workflow_id}")
                logger.info("🔄 Workflow will execute: Research → Analysis → Decision")
            else:
                logger.warning("⚠️ Failed to create sequential workflow")
        except Exception as e:
            logger.warning(f"⚠️ Workflow creation error: {e}")
            logger.info("💡 This may happen if coordination manager is not fully initialized")
    
    async def demo_parallel_workflow(self):
        """Demonstrate parallel workflow coordination"""
        logger.info("\n=== DEMO: Parallel Workflow Coordination ===")
        
        # Create a parallel workflow: Multiple agents working simultaneously
        parallel_tasks = [
            {
                "agent": "david",
                "task": {
                    "type": "research",
                    "data": {"topic": "Competitor Analysis", "focus": "features"}
                }
            },
            {
                "agent": "analyst_agent",
                "task": {
                    "type": "data_analysis", 
                    "data": {"dataset": "market_data", "type": "competitive_analysis"}
                }
            },
            {
                "agent": "solomon",
                "task": {
                    "type": "strategic_thinking",
                    "data": {"context": "competitive_landscape", "horizon": "quarterly"}
                }
            }
        ]
        
        workflow_id = await self.controller.create_agent_workflow(
            workflow_type="parallel",
            participants=["david", "analyst_agent", "solomon"],
            tasks=parallel_tasks
        )
        
        if workflow_id:
            logger.info(f"✅ Created parallel workflow: {workflow_id}")
            logger.info("⚡ All agents will work simultaneously")
        else:
            logger.error("❌ Failed to create parallel workflow")
    
    async def demo_consensus_decision(self):
        """Demonstrate consensus-based decision making"""
        logger.info("\n=== DEMO: Consensus Decision Making ===")
        
        # Create a proposal for agents to vote on
        proposal = {
            "title": "Should we invest in new AI infrastructure?",
            "options": ["yes", "no", "defer"],
            "context": {
                "budget": "$500K",
                "timeline": "Q2 2024",
                "expected_roi": "150%"
            },
            "decision_criteria": ["cost_benefit", "strategic_alignment", "risk_assessment"]
        }
        
        consensus_result = await self.controller.request_agent_consensus(
            decision_id="ai_infrastructure_investment",
            participants=["solomon", "david", "analyst_agent"],
            proposal=proposal,
            voting_method="majority"
        )
        
        logger.info(f"🗳️ Consensus result: {consensus_result}")
    
    async def demo_task_auction(self):
        """Demonstrate task auction mechanism"""
        logger.info("\n=== DEMO: Task Auction Mechanism ===")
        
        # Create a task for auction
        auction_task = {
            "title": "Comprehensive Market Analysis Report",
            "description": "Create detailed analysis of emerging AI markets",
            "requirements": ["research", "data_analysis", "reporting"],
            "deadline": (datetime.now() + timedelta(days=3)).isoformat(),
            "complexity": "high",
            "estimated_effort": "40 hours"
        }
        
        auction_result = await self.controller.initiate_agent_auction(
            auction_id="market_analysis_auction",
            task=auction_task,
            participants=["solomon", "david", "analyst_agent"],
            duration=30  # 30 seconds for demo
        )
        
        logger.info(f"🏆 Auction result: {auction_result}")
    
    async def demo_agent_discovery(self):
        """Demonstrate agent discovery by capability"""
        logger.info("\n=== DEMO: Agent Discovery by Capability ===")
        
        # Discover agents with specific capabilities
        capabilities_to_search = ["data_analysis", "strategic_thinking", "research"]
        
        for capability in capabilities_to_search:
            agents = await self.controller.discover_agents_by_capability(capability)
            logger.info(f"🔍 Agents with '{capability}' capability: {agents}")
    
    async def demo_coordination_metrics(self):
        """Show coordination metrics"""
        logger.info("\n=== DEMO: Coordination Metrics ===")
        
        metrics = await self.controller.get_agent_coordination_metrics()
        
        logger.info("📊 Current Coordination Metrics:")
        logger.info(f"   Active Workflows: {metrics['active_workflows']}")
        logger.info(f"   Agent Capabilities: {metrics['agent_capabilities']}")
        logger.info(f"   Message Bus Metrics: {metrics.get('message_bus_metrics', 'N/A')}")
        logger.info(f"   Coordination Patterns: {metrics.get('coordination_patterns', 'N/A')}")
    
    async def run_all_demos(self):
        """Run all coordination demos"""
        try:
            await self.setup_demo_environment()
            
            # Run individual demos
            await self.demo_capability_based_routing()
            await asyncio.sleep(2)
            
            await self.demo_load_balanced_routing()
            await asyncio.sleep(2)
            
            await self.demo_agent_discovery()
            await asyncio.sleep(2)
            
            await self.demo_sequential_workflow()
            await asyncio.sleep(3)
            
            await self.demo_parallel_workflow()
            await asyncio.sleep(3)
            
            await self.demo_consensus_decision()
            await asyncio.sleep(2)
            
            await self.demo_task_auction()
            await asyncio.sleep(2)
            
            await self.demo_coordination_metrics()
            
            logger.info("\n🎉 All coordination demos completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
        finally:
            # Cleanup
            await self.controller.stop()

async def main():
    """Main demo function"""
    demo = CoordinationDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main())
