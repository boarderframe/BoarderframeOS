#!/usr/bin/env python3
"""
Debug script to check message bus state
"""
import sys
import asyncio
from pathlib import Path

# Add boarderframeos to path
sys.path.insert(0, '/Users/cosburn/BoarderframeOS/boarderframeos')

from core.message_bus import message_bus

async def check_message_bus():
    """Check what agents are registered"""
    print("Checking message bus state...")
    
    # Get registered agents
    print(f"Registered agents: {list(message_bus.agent_queues.keys())}")
    print(f"Subscribers: {list(message_bus.subscribers.keys())}")
    
    # Try to get messages for Solomon
    messages = await message_bus.get_messages("Solomon")
    print(f"Messages for Solomon: {len(messages)}")
    
    # Try lowercase
    messages_lower = await message_bus.get_messages("solomon")
    print(f"Messages for solomon: {len(messages_lower)}")

if __name__ == "__main__":
    asyncio.run(check_message_bus())