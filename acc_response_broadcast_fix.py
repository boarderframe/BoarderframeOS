#!/usr/bin/env python3
"""
ACC Response Broadcast Fix
Patches the ACC to ensure agent responses are broadcast to WebSocket clients
"""

import sys
import os
from pathlib import Path

print("🔧 ACC Response Broadcast Fix")
print("=" * 50)

# Check if ACC file exists
acc_file = Path("agent_communication_center_enhanced.py")
if not acc_file.exists():
    print("❌ ACC file not found!")
    sys.exit(1)

# Read the current code
with open(acc_file, 'r') as f:
    lines = f.readlines()

# Find the handle_send_message method
print("\n1️⃣ Analyzing handle_send_message method...")
handle_method_start = None
for i, line in enumerate(lines):
    if "async def handle_send_message" in line:
        handle_method_start = i
        print(f"✅ Found handle_send_message at line {i+1}")
        break

if handle_method_start is None:
    print("❌ Could not find handle_send_message method!")
    sys.exit(1)

# Check if response broadcasting is already present
has_response_broadcast = False
for i in range(handle_method_start, min(handle_method_start + 100, len(lines))):
    if "is_response" in lines[i] and "Broadcasting agent response" in lines[i]:
        has_response_broadcast = True
        print("✅ Response broadcasting code already exists")
        break

# Create a patched version that ensures responses are broadcast
print("\n2️⃣ Creating enhanced ACC with guaranteed response broadcasting...")

enhanced_acc = '''#!/usr/bin/env python3
"""
Enhanced ACC with Fixed Response Broadcasting
This version ensures agent responses are always broadcast to WebSocket clients
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Import the original ACC
sys.path.insert(0, str(Path(__file__).parent))
from agent_communication_center_enhanced import EnhancedACC, ChatMessage

class ACCWithFixedBroadcast(EnhancedACC):
    """Enhanced ACC that properly broadcasts agent responses"""
    
    async def handle_send_message(self, message: ChatMessage, connection_id: Optional[str] = None) -> Dict[str, Any]:
        """Process and route a message with fixed response broadcasting"""
        
        # Call parent implementation
        result = await super().handle_send_message(message, connection_id)
        
        # Additional check: If this is an agent response, ensure it's broadcast
        if message.from_agent and message.from_agent != "user":
            print(f"🔔 BROADCAST FIX: Ensuring response from {message.from_agent} is broadcast")
            
            # Get the message data that was stored
            message_data = {
                "id": result.get("message_id"),
                "from_agent": message.from_agent,
                "to_agent": message.to_agent or "user",
                "content": {"text": message.content},
                "format": message.format.value,
                "timestamp": datetime.now().isoformat()
            }
            
            # Force broadcast to all WebSocket connections
            broadcast_count = 0
            disconnected = []
            
            for conn_id, ws in list(self.websocket_connections.items()):
                try:
                    await ws.send_json({
                        "type": "message",
                        "data": message_data
                    })
                    broadcast_count += 1
                    print(f"   ✅ Broadcast to connection {conn_id}")
                except Exception as e:
                    print(f"   ❌ Failed to broadcast to {conn_id}: {e}")
                    disconnected.append(conn_id)
            
            # Clean up disconnected
            for conn_id in disconnected:
                self.websocket_connections.pop(conn_id, None)
            
            print(f"   📡 Broadcast complete: {broadcast_count} clients")
        
        return result

# Import remaining dependencies
from typing import Optional, Dict, Any
from datetime import datetime

async def main():
    """Run the enhanced ACC with fixed broadcasting"""
    print("🚀 Starting Enhanced ACC with Fixed Response Broadcasting")
    print("=" * 50)
    
    # Create and run the enhanced ACC
    acc = ACCWithFixedBroadcast()
    await acc.run()

if __name__ == "__main__":
    asyncio.run(main())
'''

with open("acc_with_broadcast_fix.py", "w") as f:
    f.write(enhanced_acc)

os.chmod("acc_with_broadcast_fix.py", 0o755)
print("✅ Created acc_with_broadcast_fix.py")

# Create a simple test to verify broadcasting
print("\n3️⃣ Creating broadcast test...")

test_script = '''#!/usr/bin/env python3
"""
Test ACC Response Broadcasting
"""

import asyncio
import json
import websockets
import httpx
from datetime import datetime


async def test_broadcasting():
    """Test that agent responses are broadcast"""
    print("🧪 Testing ACC Response Broadcasting")
    print("=" * 40)
    
    received_broadcasts = []
    
    # Connect WebSocket to listen for broadcasts
    try:
        async with websockets.connect("ws://localhost:8890/ws") as ws:
            print("✅ Connected to WebSocket")
            
            # Get connection message
            conn_msg = await ws.recv()
            print(f"✅ Connection established")
            
            # Listen for broadcasts in background
            async def listen():
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                        data = json.loads(msg)
                        if data.get("type") == "message":
                            received_broadcasts.append(data)
                            print(f"📥 Received broadcast: {data.get('data', {}).get('from_agent', 'unknown')}")
                    except asyncio.TimeoutError:
                        continue
                    except:
                        break
            
            # Start listener
            listen_task = asyncio.create_task(listen())
            
            # Send a test agent response
            async with httpx.AsyncClient() as client:
                print("\\n📤 Sending test agent response...")
                response = await client.post(
                    "http://localhost:8890/api/messages",
                    json={
                        "from_agent": "test_agent",
                        "to_agent": "user",
                        "content": f"Test broadcast at {datetime.now()}",
                        "format": "text",
                        "is_response": True
                    }
                )
                
                if response.status_code == 200:
                    print("✅ Response sent successfully")
                else:
                    print(f"❌ Failed to send: {response.status_code}")
            
            # Wait for broadcast
            await asyncio.sleep(2)
            
            # Check results
            print(f"\\n📊 Results: Received {len(received_broadcasts)} broadcasts")
            
            if received_broadcasts:
                print("✅ SUCCESS: Broadcasting is working!")
                for bc in received_broadcasts:
                    data = bc.get("data", {})
                    print(f"   - From: {data.get('from_agent')} Content: {data.get('content', {}).get('text', '')[:50]}...")
            else:
                print("❌ FAILURE: No broadcasts received")
            
            # Cancel listener
            listen_task.cancel()
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_broadcasting())
'''

with open("test_acc_broadcasting.py", "w") as f:
    f.write(test_script)

os.chmod("test_acc_broadcasting.py", 0o755)
print("✅ Created test_acc_broadcasting.py")

print("\n📋 Fix Summary:")
print("-" * 40)
print("The issue is that agent responses need to be broadcast to WebSocket clients.")
print("\n✅ Solutions Created:")
print("1. acc_with_broadcast_fix.py - Enhanced ACC that guarantees broadcasting")
print("2. test_acc_broadcasting.py - Test script to verify broadcasting works")
print("\n🚀 To apply the fix:")
print("1. Stop current ACC: pkill -f agent_communication_center")
print("2. Start fixed ACC: python acc_with_broadcast_fix.py")
print("3. Test broadcasting: python test_acc_broadcasting.py")
print("\nOr use the original ACC - it should already have the broadcasting logic!")
print("The key is ensuring agents are using the ACC versions (solomon_acc.py)")