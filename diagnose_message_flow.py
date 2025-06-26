#!/usr/bin/env python3
"""
Diagnose Message Flow
Comprehensive diagnostic tool for ACC and agent message routing
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.message_bus import message_bus, AgentMessage, MessageType


async def check_message_bus_status():
    """Check message bus status"""
    print("\n📊 MESSAGE BUS STATUS")
    print("=" * 50)
    
    if not message_bus.running:
        print("❌ Message bus is NOT running")
        return False
    
    print("✅ Message bus is running")
    
    stats = message_bus.get_message_stats()
    print(f"\n📈 Statistics:")
    print(f"   Total agents registered: {stats['total_agents']}")
    print(f"   Total topics: {stats['total_topics']}")
    print(f"   Message history size: {stats['message_history_size']}")
    
    print(f"\n👥 Registered Agents:")
    for agent, queue_size in stats['queue_sizes'].items():
        print(f"   - {agent}: {queue_size} messages in queue")
    
    # Check if ACC is registered
    acc_registered = "acc_system" in stats['queue_sizes']
    if acc_registered:
        print(f"\n✅ ACC is registered with message bus")
    else:
        print(f"\n❌ ACC is NOT registered with message bus")
    
    return True


async def check_acc_connectivity():
    """Check ACC WebSocket and API connectivity"""
    print("\n🌐 ACC CONNECTIVITY")
    print("=" * 50)
    
    import httpx
    
    # Check HTTP API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8890/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ ACC HTTP API is healthy")
                print(f"   - WebSocket connections: {data.get('websocket_connections', 0)}")
                print(f"   - Database: {data.get('database', 'unknown')}")
            else:
                print(f"❌ ACC HTTP API returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to ACC HTTP API: {e}")
        return False
    
    # Check WebSocket
    try:
        import websockets
        
        async with websockets.connect("ws://localhost:8890/ws") as ws:
            # Wait for connection message
            initial = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(initial)
            if data.get("type") == "connection":
                print(f"✅ ACC WebSocket is accessible")
                print(f"   - Connection ID: {data.get('connection_id')}")
            else:
                print(f"⚠️ Unexpected WebSocket response: {data}")
    except Exception as e:
        print(f"❌ Cannot connect to ACC WebSocket: {e}")
    
    return True


async def test_message_routing():
    """Test actual message routing"""
    print("\n🧪 MESSAGE ROUTING TEST")
    print("=" * 50)
    
    # Register a test receiver
    test_queue = asyncio.Queue()
    test_agent = "diagnostic_receiver"
    
    await message_bus.register_agent(test_agent)
    print(f"✅ Registered test agent: {test_agent}")
    
    # Test 1: Direct message
    print("\n📤 Test 1: Direct Message")
    test_msg = AgentMessage(
        from_agent="diagnostic_tool",
        to_agent=test_agent,
        message_type=MessageType.TASK_REQUEST,
        content={"test": "direct_message"},
        correlation_id="diag-1"
    )
    
    success = await message_bus.send_message(test_msg)
    print(f"   Send result: {success}")
    
    # Check if received
    messages = await message_bus.get_messages(test_agent, timeout=1.0)
    if messages:
        print(f"   ✅ Message received by {test_agent}")
    else:
        print(f"   ❌ Message NOT received by {test_agent}")
    
    # Test 2: ACC routing
    print("\n📤 Test 2: ACC Message Routing")
    
    # First check if acc_system is registered
    if "acc_system" not in message_bus.agent_queues:
        await message_bus.register_agent("acc_system")
        print("   Registered acc_system")
    
    acc_msg = AgentMessage(
        from_agent="diagnostic_tool",
        to_agent="acc_system",
        message_type=MessageType.TASK_RESPONSE,
        content={"response": "Test response for ACC"},
        correlation_id="diag-2"
    )
    
    success = await message_bus.send_message(acc_msg)
    print(f"   Send to ACC result: {success}")
    
    # Check if ACC received it
    acc_messages = await message_bus.get_messages("acc_system", timeout=1.0)
    if acc_messages:
        print(f"   ✅ ACC received {len(acc_messages)} message(s)")
    else:
        print(f"   ❌ ACC did NOT receive messages")
    
    # Cleanup
    await message_bus.unregister_agent(test_agent)
    
    return True


async def check_agent_responses():
    """Check if agents are responding to messages"""
    print("\n🤖 AGENT RESPONSE CHECK")
    print("=" * 50)
    
    # Get list of registered agents
    stats = message_bus.get_message_stats()
    agents = list(stats['queue_sizes'].keys())
    
    print(f"Found {len(agents)} registered agents")
    
    # Try to find a responsive agent
    responsive_agents = []
    
    for agent in agents:
        if agent in ["acc_system", "diagnostic_receiver", "diagnostic_tool"]:
            continue  # Skip system agents
        
        print(f"\n🔍 Testing {agent}...")
        
        # Send a test message
        test_msg = AgentMessage(
            from_agent="diagnostic_tool",
            to_agent=agent,
            message_type=MessageType.TASK_REQUEST,
            content={"type": "user_chat", "message": "Diagnostic test - please respond"},
            correlation_id=f"diag-agent-{agent}",
            requires_response=True
        )
        
        await message_bus.send_message(test_msg)
        print(f"   📤 Sent test message")
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check agent's queue
        agent_queue_size = message_bus.agent_queues.get(agent, asyncio.Queue()).qsize()
        print(f"   📥 Agent queue size: {agent_queue_size}")
        
        # Check if we got a response in ACC queue
        if "acc_system" in message_bus.agent_queues:
            acc_messages = await message_bus.get_messages("acc_system", timeout=0.5)
            for msg in acc_messages:
                if msg.from_agent == agent:
                    print(f"   ✅ {agent} sent a response!")
                    responsive_agents.append(agent)
                    break
            else:
                print(f"   ❌ No response from {agent}")
        
    print(f"\n📊 Summary: {len(responsive_agents)} of {len(agents)} agents are responsive")
    if responsive_agents:
        print(f"   Responsive agents: {', '.join(responsive_agents)}")
    
    return len(responsive_agents) > 0


async def diagnose_message_flow():
    """Run complete diagnostic"""
    print("🔍 BOARDERFRAMEOS MESSAGE FLOW DIAGNOSTIC")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    results = {
        "message_bus": False,
        "acc_connectivity": False,
        "message_routing": False,
        "agent_responses": False
    }
    
    # Check each component
    try:
        results["message_bus"] = await check_message_bus_status()
    except Exception as e:
        print(f"❌ Error checking message bus: {e}")
    
    try:
        results["acc_connectivity"] = await check_acc_connectivity()
    except Exception as e:
        print(f"❌ Error checking ACC: {e}")
    
    try:
        if results["message_bus"]:
            results["message_routing"] = await test_message_routing()
    except Exception as e:
        print(f"❌ Error testing routing: {e}")
    
    try:
        if results["message_bus"]:
            results["agent_responses"] = await check_agent_responses()
    except Exception as e:
        print(f"❌ Error checking agents: {e}")
    
    # Summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    all_good = all(results.values())
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")
    
    if all_good:
        print("\n✅ All systems operational!")
    else:
        print("\n⚠️ Issues detected. Recommendations:")
        
        if not results["message_bus"]:
            print("   1. Start the message bus first")
        
        if not results["acc_connectivity"]:
            print("   2. Make sure ACC is running on port 8890")
        
        if not results["message_routing"]:
            print("   3. Check message bus configuration")
        
        if not results["agent_responses"]:
            print("   4. Ensure agents are running and have ACC response handling enabled")
    
    return all_good


async def main():
    """Main entry point"""
    try:
        # Start message bus if needed
        if not message_bus.running:
            print("Starting message bus for diagnostics...")
            await message_bus.start()
        
        # Run diagnostic
        success = await diagnose_message_flow()
        
        if not success:
            print("\n💡 To fix issues, try running:")
            print("   python fix_acc_bidirectional_flow.py")
            print("   python patch_acc_response_flow.py")
        
    except KeyboardInterrupt:
        print("\n👋 Diagnostic interrupted")
    except Exception as e:
        print(f"\n❌ Diagnostic error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())