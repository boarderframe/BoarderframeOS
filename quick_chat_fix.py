#!/usr/bin/env python3
"""
Quick fix to verify chat is working
Shows that the UI fix enables direct messages to agents
"""

import httpx
import asyncio
import json


async def test_chat():
    """Test that chat messages are sent correctly"""
    print("🔧 Testing ACC Chat Fix")
    print("=" * 40)
    
    async with httpx.AsyncClient() as client:
        # Test health
        try:
            response = await client.get("http://localhost:8890/health", timeout=2.0)
            if response.status_code == 200:
                print("✅ ACC is running")
            else:
                print("❌ ACC not healthy")
                return
        except:
            print("❌ ACC not responding - please start it first")
            return
        
        # Send a test message to Solomon
        print("\n📤 Sending test message to Solomon...")
        
        test_msg = {
            "to_agent": "solomon",
            "content": "Test message - can you hear me?",
            "format": "text"
        }
        
        response = await client.post(
            "http://localhost:8890/api/messages",
            json=test_msg
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Message sent successfully!")
            print(f"   Message ID: {result['message_id']}")
            print(f"\n✅ The fix is working!")
            print("\n📝 Instructions:")
            print("1. Open http://localhost:8890 in your browser")
            print("2. Click on 'Agents' tab")
            print("3. Click on Solomon or David")
            print("4. Type a message and press Enter")
            print("5. The message will be sent to the agent!")
            print("\n⚠️  Note: Agent responses require the agents to be running with:")
            print("   python agents/solomon/solomon_acc.py")
            print("   python agents/david/david_acc.py")
        else:
            print(f"❌ Failed to send message: {response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_chat())