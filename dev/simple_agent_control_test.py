#!/usr/bin/env python3
"""
Simple Agent Control System Test - BoarderframeOS
Validates that the existing agent control infrastructure works correctly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from boarderframeos.core.agent_controller import agent_controller
from boarderframeos.core.agent_registry import (
    AgentCapability,
    AgentDiscoveryInfo,
    AgentState,
    agent_registry,
)
from boarderframeos.core.message_bus import message_bus
from boarderframeos.core.resource_manager import ResourceLimit, resource_manager


async def test_agent_control_system():
    """Test the complete agent control system"""

    print("🚀 Testing BoarderframeOS Agent Control System")
    print("=" * 60)

    try:
        # 1. Test Agent Registry
        print("\n1️⃣  Testing Agent Registry & Discovery Service")

        # Register test agents
        solomon_info = AgentDiscoveryInfo(
            agent_id="solomon-001",
            name="Solomon",
            role="AI Coordinator",
            capabilities=[AgentCapability.COORDINATION, AgentCapability.PLANNING],
            state=AgentState.IDLE,
            zone="primary",
            model="claude-3.5-sonnet"
        )

        david_info = AgentDiscoveryInfo(
            agent_id="david-001",
            name="David",
            role="Development Assistant",
            capabilities=[AgentCapability.DEVELOPMENT, AgentCapability.ANALYSIS],
            state=AgentState.IDLE,
            zone="development",
            model="claude-3.5-sonnet"
        )

        # Register agents
        await agent_registry.register_agent(solomon_info)
        await agent_registry.register_agent(david_info)

        print(f"   ✅ Registered Solomon: {solomon_info.agent_id}")
        print(f"   ✅ Registered David: {david_info.agent_id}")

        # Test discovery
        coordination_agents = agent_registry.find_agents_by_capability(AgentCapability.COORDINATION)
        development_agents = agent_registry.find_agents_by_capability(AgentCapability.DEVELOPMENT)

        print(f"   🔍 Found {len(coordination_agents)} coordination agents")
        print(f"   🔍 Found {len(development_agents)} development agents")

        # Get all agents
        all_agents = agent_registry.list_agents()
        print(f"   📊 Total registered agents: {len(all_agents)}")

        # 2. Test Resource Management
        print("\n2️⃣  Testing Resource Management System")

        # Start resource manager
        await resource_manager.start()

        # Set resource limits
        solomon_limits = ResourceLimit(cpu_percent=80.0, memory_mb=4096.0, gpu_percent=50.0)
        resource_manager.set_agent_limits("solomon-001", solomon_limits)
        print(f"   ⚙️  Set resource limits for Solomon")

        # Get system usage
        system_usage = resource_manager.get_system_usage()
        print(f"   💻 System CPU usage: {system_usage.cpu_percent:.1f}%")
        print(f"   🧠 System memory usage: {system_usage.memory_mb:.1f} MB")
        print(f"   🎮 System GPU usage: {system_usage.gpu_percent:.1f}%")

        # Check agent limits
        solomon_limits_check = resource_manager.get_agent_limits("solomon-001")
        print(f"   📋 Solomon CPU limit: {solomon_limits_check.cpu_percent}%")

        # 3. Test Agent Controller
        print("\n3️⃣  Testing Agent Controller")

        # Start agent controller
        await agent_controller.start()

        # Check task queue
        task_count = len(agent_controller.task_queue)
        print(f"   📝 Current tasks in queue: {task_count}")

        # Check running processes
        running_count = len(agent_controller.running_processes)
        print(f"   🔄 Running agent processes: {running_count}")

        # Test task assignment
        from boarderframeos.core.agent_controller import TaskPriority

        task_id = await agent_controller.assign_task(
            agent_id="solomon-001",
            task_type="analysis",
            data={"content": "Test analysis task for Solomon"},
            priority=TaskPriority.NORMAL
        )
        print(f"   📋 Assigned task to Solomon: {task_id}")

        # 4. Test Message Bus
        print("\n4️⃣  Testing Message Bus Communication")

        # Start message bus
        await message_bus.start()

        # Test subscription
        await message_bus.subscribe_to_topic("test_controller", "system_events")
        print(f"   📡 Subscribed to system events")

        # Test message sending (will be queued since no actual agents are running)
        from boarderframeos.core.message_bus import (
            AgentMessage,
            MessagePriority,
            MessageType,
        )

        test_message = AgentMessage(
            from_agent="test_controller",
            to_agent="solomon-001",
            message_type=MessageType.TASK_REQUEST,
            content={"task": "test", "data": "hello"},
            priority=MessagePriority.NORMAL
        )

        await message_bus.send_message(test_message)
        print(f"   📨 Sent test message to Solomon")

        # 5. System Status Summary
        print("\n5️⃣  System Status Summary")

        # Registry status
        all_agents = agent_registry.list_agents()
        print(f"   👥 Registered agents: {len(all_agents)}")

        # Resource status
        system_resources = resource_manager.system_resources
        if system_resources:
            print(f"   💻 System cores: {system_resources.cpu_cores}")
            print(f"   🧠 Total memory: {system_resources.memory_total_mb:.0f} MB")
            print(f"   🎮 GPU count: {system_resources.gpu_count}")

        # Controller status
        config_count = len(agent_controller.agent_configs)
        print(f"   ⚙️  Agent configurations: {config_count}")

        # Message bus status
        topic_count = len(message_bus.topics) if hasattr(message_bus, 'topics') else 0
        print(f"   📡 Message bus topics: {topic_count}")

        print("\n✅ Agent Control System Test Completed Successfully!")
        print("   The BoarderframeOS agent control infrastructure is operational.")
        print("   Ready for agent deployment and management.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_agent_control_system())
    sys.exit(0 if success else 1)
