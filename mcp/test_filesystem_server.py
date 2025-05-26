#!/usr/bin/env python3
"""
Test script for the Unified MCP Filesystem Server
This script verifies that the server can start and basic functionality works.
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add the current directory to Python path so we can import the server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filesystem_server import UnifiedFilesystemServer

async def test_basic_functionality():
    """Test basic server functionality"""
    print("🧪 Testing Unified MCP Filesystem Server...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        # Initialize server
        server = UnifiedFilesystemServer(base_path=temp_dir)
        print("✅ Server initialized successfully")
        
        # Test basic file operations
        test_content = "Hello, MCP Filesystem Server!"
        test_path = "test_file.txt"
        
        # Test write
        print("📝 Testing file write...")
        write_result = await server.write_file_async(test_path, test_content)
        if "error" in write_result:
            print(f"❌ Write failed: {write_result['error']}")
            return False
        print("✅ File write successful")
        
        # Test read
        print("📖 Testing file read...")
        read_result = await server.read_file_async(test_path)
        if "error" in read_result:
            print(f"❌ Read failed: {read_result['error']}")
            return False
        
        if read_result["content"] != test_content:
            print(f"❌ Content mismatch: expected '{test_content}', got '{read_result['content']}'")
            return False
        print("✅ File read successful")
        
        # Test list directory
        print("📋 Testing directory listing...")
        list_result = await server.list_directory_async("")
        if "error" in list_result:
            print(f"❌ List failed: {list_result['error']}")
            return False
        
        found_file = any(item["name"] == "test_file.txt" for item in list_result["entries"])
        if not found_file:
            print("❌ Test file not found in directory listing")
            return False
        print("✅ Directory listing successful")
        
        # Test search
        print("🔍 Testing file search...")
        search_result = await server.search_files_async("test", content_search=True)
        if "error" in search_result:
            print(f"❌ Search failed: {search_result['error']}")
            return False
        print("✅ File search successful")
        
        # Test metadata
        print("📊 Testing file metadata...")
        metadata_result = await server.get_file_metadata_async(test_path)
        if "error" in metadata_result:
            print(f"❌ Metadata failed: {metadata_result['error']}")
            return False
        print("✅ File metadata successful")
        
        # Test delete
        print("🗑️ Testing file delete...")
        delete_result = await server.delete_file_async(test_path)
        if "error" in delete_result:
            print(f"❌ Delete failed: {delete_result['error']}")
            return False
        print("✅ File delete successful")
        
        print("🎉 All basic functionality tests passed!")
        return True

async def test_ai_features():
    """Test AI features if available"""
    print("\n🤖 Testing AI features...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        server = UnifiedFilesystemServer(base_path=temp_dir)
        
        # Initialize the vector database for AI features
        if hasattr(server, '_initialize_vector_db'):
            await server._initialize_vector_db()
        
        # Test content analysis
        test_content = """
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
"""
        
        test_path = "test_code.py"
        await server.write_file_async(test_path, test_content)
        
        print("🔍 Testing content analysis...")
        analysis_result = await server.analyze_content_async(test_path)
        if "error" in analysis_result:
            print(f"⚠️ Content analysis failed (AI features may not be available): {analysis_result['error']}")
        else:
            print("✅ Content analysis successful")
            
        # Test embeddings if available
        if server.embedding_model:
            print("🧠 Testing embeddings generation...")
            embedding_result = await server.generate_embeddings_async(test_path)
            if "error" in embedding_result:
                print(f"⚠️ Embeddings failed: {embedding_result['error']}")
            else:
                print("✅ Embeddings generation successful")
        else:
            print("⚠️ Embedding model not available")

async def main():
    """Main test function"""
    print("🚀 Starting MCP Filesystem Server Tests\n")
    
    try:
        # Test basic functionality
        basic_success = await test_basic_functionality()
        
        if basic_success:
            # Test AI features
            await test_ai_features()
            
            print("\n✨ Testing completed successfully!")
            print("\n🔧 To start the server manually, run:")
            print("   python filesystem_server.py")
            print("\n📡 The server will be available at:")
            print("   HTTP: http://localhost:8001")
            print("   WebSocket: ws://localhost:8001/ws/events")
            print("   JSON-RPC: http://localhost:8001/rpc")
            
        else:
            print("\n❌ Basic functionality tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
