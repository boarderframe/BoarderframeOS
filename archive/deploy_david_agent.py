#!/usr/bin/env python3
"""
Deploy David Agent using Agent Controller
Launches David as CEO of BoarderframeOS with full integration
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from boarderframeos.agents.david.david import David
from boarderframeos.core.agent_controller import agent_controller
from boarderframeos.core.agent_registry import agent_registry
from boarderframeos.core.message_bus import message_bus
from boarderframeos.core.resource_manager import resource_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/cosburn/BoarderframeOS/logs/david_deployment.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("david_deployment")


async def deploy_david():
    """Deploy David agent with full system integration"""
    try:
        logger.info("🚀 Starting David Agent Deployment")

        # Initialize core systems if needed
        await agent_registry.start()
        await resource_manager.start()
        await message_bus.start()
        await agent_controller.start()

        logger.info("✅ Core systems ready")

        # Create agent template for David
        agent_template = {
            "name": "David",
            "agent_class": "boarderframeos.agents.david.david.David",
            "role": "CEO",
            "biome": "council",
            "capabilities": [
                "strategic_leadership",
                "organizational_management",
                "resource_allocation",
                "executive_decision_making",
                "biome_coordination",
                "performance_monitoring",
            ],
            "resources": {"cpu_percent": 15.0, "memory_mb": 512, "priority": "high"},
            "config": {
                "model": "claude-3-opus-20240229",
                "temperature": 0.6,
                "max_concurrent_tasks": 5,
            },
        }

        # Deploy David using agent controller
        logger.info("📋 Registering David agent template...")
        await agent_controller.register_agent_template("david_ceo", agent_template)

        logger.info("🎯 Creating David agent instance...")
        agent_info = await agent_controller.create_agent(
            template_id="david_ceo", agent_id="david", zone="executive", priority="high"
        )

        if agent_info.get("success"):
            logger.info(f"✅ David agent created: {agent_info['agent_id']}")

            # Start the agent
            logger.info("▶️  Starting David agent...")
            start_result = await agent_controller.start_agent("david")

            if start_result.get("success"):
                logger.info("🎉 David agent successfully deployed and started!")

                # Wait a moment for startup
                await asyncio.sleep(3)

                # Get agent status
                status = await agent_controller.get_agent_status("david")
                logger.info(f"📊 David status: {status}")

                # Send welcome message to David
                await message_bus.send_message(
                    from_agent="system",
                    to_agent="david",
                    message_type="welcome",
                    content={
                        "message": "Welcome David! You are now CEO of BoarderframeOS. Solomon is your Chief of Staff.",
                        "system_state": "operational",
                        "active_agents": await agent_registry.list_agents(),
                    },
                )

                logger.info("📨 Welcome message sent to David")

                return True
            else:
                logger.error(f"❌ Failed to start David: {start_result}")
                return False
        else:
            logger.error(f"❌ Failed to create David: {agent_info}")
            return False

    except Exception as e:
        logger.error(f"💥 David deployment failed: {e}")
        return False


async def verify_david_deployment():
    """Verify David is running and responsive"""
    try:
        logger.info("🔍 Verifying David deployment...")

        # Check agent registry
        agents = await agent_registry.list_agents()
        david_found = any(agent.get("agent_id") == "david" for agent in agents)

        if david_found:
            logger.info("✅ David found in agent registry")
        else:
            logger.warning("⚠️  David not found in agent registry")
            return False

        # Check agent controller
        status = await agent_controller.get_agent_status("david")
        if status.get("status") == "running":
            logger.info("✅ David is running in agent controller")
        else:
            logger.warning(f"⚠️  David status: {status}")
            return False

        # Test message to David
        logger.info("📨 Testing communication with David...")
        response = await message_bus.send_message(
            from_agent="system",
            to_agent="david",
            message_type="status_request",
            content={"request": "initial_status"},
        )

        if response:
            logger.info("✅ David is responsive to messages")
        else:
            logger.warning("⚠️  David not responding to messages")

        logger.info("🎯 David deployment verification complete")
        return True

    except Exception as e:
        logger.error(f"💥 Verification failed: {e}")
        return False


async def main():
    """Main deployment orchestration"""
    try:
        logger.info("🌟 BoarderframeOS David Agent Deployment")
        logger.info("=" * 50)

        # Deploy David
        success = await deploy_david()

        if success:
            # Verify deployment
            verified = await verify_david_deployment()

            if verified:
                logger.info("🎉 David agent deployment SUCCESSFUL!")
                logger.info("🏢 David is now CEO of BoarderframeOS")
                logger.info("🤝 David will coordinate with Solomon as Chief of Staff")
                logger.info("📈 Organizational leadership is now active")

                # Show system status
                logger.info("\n📊 Current System Status:")
                agents = await agent_registry.list_agents()
                for agent in agents:
                    logger.info(
                        f"  • {agent.get('agent_id', 'Unknown')}: {agent.get('status', 'Unknown')} ({agent.get('role', 'No role')})"
                    )

                return 0
            else:
                logger.error("❌ David deployment verification failed")
                return 1
        else:
            logger.error("❌ David deployment failed")
            return 1

    except KeyboardInterrupt:
        logger.info("🛑 Deployment interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Deployment error: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
