#!/usr/bin/env python3
"""
Test script for the MCP client library
"""
import asyncio
import sys
import os
import json
import httpx
from pathlib import Path

# Add the boarderframeos directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "boarderframeos"))

try:
    from core.mcp_client import MCPClient, MCPConfig
except ImportError:
    print("MCP client not found, using direct HTTP calls for testing")

async def test_mcp_client():
    """Test the MCP client library functionality"""
    print("🚀 Testing MCP Client Library...")
    
    # Initialize client with proper config
    config = MCPConfig(
        base_url="http://localhost:8001",
        api_key="default-key-boarderframe-dev-1234567890"
    )
    client = MCPClient(config)
    
    try:
        # Test 1: Health check
        print("\n📊 Testing health check...")
        health = await client.health_check()
        print(f"✅ Health: {health['status']}")
        print(f"📈 Vector search available: {health['features']['vector_search']['available']}")
        
        # Test 2: Create a test file
        print("\n📁 Testing file operations...")
        test_content = "This is a test file created by the MCP client library"
        result = await client.create_file("test_files/client_test.txt", test_content)
        print(f"✅ File created: {result['success']}")
        
        # Test 3: Read the file back
        file_content = await client.read_file("test_files/client_test.txt")
        print(f"✅ File read back: {file_content[:50]}...")
        
        # Test 4: List files
        files = await client.list_files("test_files")
        print(f"✅ Files listed: {len(files)} files found")
        for file in files[:3]:  # Show first 3
            print(f"   📄 {file['name']} ({file['size']} bytes)")
        
        # Test 5: Save agent data
        print("\n🤖 Testing agent operations...")
        agent_config = {
            "name": "test-client-agent",
            "type": "test",
            "capabilities": ["file_operations", "memory_search"],
            "config": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }
        
        agent_result = await client.save_agent("test-client-agent", agent_config)
        print(f"✅ Agent saved: {agent_result['success']}")
        
        # Test 6: List agents
        agents = await client.list_agents()
        print(f"✅ Agents listed: {len(agents)} agents found")
        for agent in agents:
            print(f"   🤖 {agent['name']} ({agent.get('type', 'unknown')})")
        
        # Test 7: Save memory
        print("\n🧠 Testing memory operations...")
        memory_data = {
            "content": "The MCP client library test was successful. All basic operations are working correctly.",
            "metadata": {
                "type": "test_result",
                "timestamp": "2024-01-20T10:30:00Z",
                "tags": ["mcp", "client", "test", "success"],
                "importance": 0.8
            }
        }
        
        memory_result = await client.save_memory("test-client-agent", "mcp_client_test", memory_data)
        print(f"✅ Memory saved: {memory_result['success']}")
        
        # Test 8: Search memories
        print("\n🔍 Testing memory search...")
        search_results = await client.search_memories("test-client-agent", "successful test operations")
        print(f"✅ Memory search: {len(search_results)} results found")
        for result in search_results[:2]:  # Show first 2
            print(f"   🧠 {result['id']}: {result['content'][:60]}...")
            print(f"      Similarity: {result['similarity']:.3f}")
        
        # Test 9: Batch operations
        print("\n📦 Testing batch operations...")
        batch_files = [
            ("batch_test_1.txt", "First batch file content"),
            ("batch_test_2.txt", "Second batch file content"),
            ("batch_test_3.txt", "Third batch file content")
        ]
        
        batch_result = await client.batch_create_files("test_files", batch_files)
        print(f"✅ Batch files created: {batch_result['success']}")
        print(f"   📊 Results: {batch_result['results']}")
        
        # Test 10: Quick operations
        print("\n⚡ Testing quick operations...")
        quick_file = await client.quick_save_file("quick_test.txt", "Quick save test content")
        print(f"✅ Quick file save: {quick_file}")
        
        quick_memory = await client.quick_save_memory("test-client-agent", "quick_memory", 
                                                     "This is a quick memory save test")
        print(f"✅ Quick memory save: {quick_memory}")
        
        print("\n🎉 All MCP client tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await client.close()

if __name__ == "__main__":
    success = asyncio.run(test_mcp_client())
    if success:
        print("\n✅ MCP Client Library is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ MCP Client Library tests failed!")
        sys.exit(1)
