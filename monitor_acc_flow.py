#!/usr/bin/env python3
"""
Monitor ACC Message Flow
Shows real-time message flow through the system
"""

import asyncio
import json
import websockets
from datetime import datetime
import sys


async def monitor_acc():
    """Monitor ACC message flow in real-time"""
    print("🔍 ACC Message Flow Monitor")
    print("=" * 50)
    print("Monitoring messages... (Press Ctrl+C to stop)\n")
    
    try:
        async with websockets.connect("ws://localhost:8890/ws") as ws:
            print("✅ Connected to ACC WebSocket\n")
            
            # Get connection message
            conn_msg = await ws.recv()
            
            # Monitor messages
            while True:
                try:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    
                    if data.get("type") == "message":
                        msg_data = data.get("data", {})
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        from_agent = msg_data.get("from_agent", "unknown")
                        to_agent = msg_data.get("to_agent", "unknown")
                        content = msg_data.get("content", {}).get("text", "")[:100]
                        
                        # Color code based on sender
                        if from_agent == "user":
                            print(f"[{timestamp}] 👤 USER -> {to_agent}: {content}")
                        elif from_agent in ["solomon", "david"]:
                            print(f"[{timestamp}] 🤖 {from_agent.upper()} -> {to_agent}: {content}")
                        else:
                            print(f"[{timestamp}] 📨 {from_agent} -> {to_agent}: {content}")
                    
                    elif data.get("type") == "presence_update":
                        agent = data.get("agent", "unknown")
                        status = data.get("status", "unknown")
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] 🟢 {agent} is now {status}")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    break
                    
    except Exception as e:
        print(f"❌ Could not connect to ACC: {e}")
        print("\nMake sure ACC is running: ./start_acc_system.sh")


if __name__ == "__main__":
    try:
        asyncio.run(monitor_acc())
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped")