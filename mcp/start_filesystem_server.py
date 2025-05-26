#!/usr/bin/env python3
"""
Enhanced startup script for the Unified MCP Filesystem Server
with improved status reporting and health monitoring
"""

import os
import sys
import asyncio
import argparse
import httpx
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from filesystem_server import UnifiedFilesystemServer

def parse_args():
    parser = argparse.ArgumentParser(description="Start the Unified MCP Filesystem Server")
    parser.add_argument(
        "--port", "-p", 
        type=int, 
        default=8001, 
        help="Port to run the server on (default: 8001)"
    )
    parser.add_argument(
        "--base-path", "-b",
        type=str,
        default=None,
        help="Base directory for file operations (default: current directory)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI features (embeddings, content analysis)"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform health check on running server and exit"
    )
    return parser.parse_args()

async def perform_health_check(port):
    """Perform comprehensive health check on the filesystem server"""
    print(f"🔍 Performing health check on filesystem server at port {port}...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Basic health check
            health_response = await client.get(f"http://localhost:{port}/health", timeout=5.0)
            health_data = health_response.json()
            
            print(f"✅ Server Status: {health_data.get('status', 'unknown')}")
            print(f"⏱️  Uptime: {health_data.get('uptime', 0):.2f} seconds")
            print(f"📁 Base Path: {health_data.get('base_path', 'unknown')}")
            print(f"🤖 AI Available: {health_data.get('ai_available', False)}")
            print(f"🔄 Active Operations: {health_data.get('active_operations', 0)}")
            print(f"👥 Connected Clients: {health_data.get('connected_clients', 0)}")
            
            # Feature availability
            features = health_data.get('features', {})
            print("\n🔧 Available Features:")
            for feature, available in features.items():
                status = "✅" if available else "❌"
                print(f"   {status} {feature}")
            
            # Test basic functionality
            print("\n🧪 Testing basic functionality...")
            rpc_payload = {
                "jsonrpc": "2.0",
                "method": "list_directory",
                "params": {"path": ""},
                "id": 1
            }
            rpc_response = await client.post(
                f"http://localhost:{port}/rpc", 
                json=rpc_payload,
                timeout=5.0
            )
            
            if rpc_response.status_code == 200:
                print("✅ Directory listing works")
            else:
                print(f"❌ Directory listing failed: {rpc_response.status_code}")
                
            return health_response.status_code == 200
            
    except httpx.ConnectError:
        print(f"❌ Cannot connect to server on port {port}")
        print("   Server may not be running or port may be incorrect")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def main():
    args = parse_args()
    
    # Handle health check mode
    if args.health_check:
        success = await perform_health_check(args.port)
        sys.exit(0 if success else 1)
    
    # Set logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set environment variables for feature toggles
    if args.no_ai:
        os.environ["DISABLE_AI"] = "true"
    
    # Determine base path
    base_path = args.base_path or os.getcwd()
    base_path = Path(base_path).resolve()
    
    print(f"🚀 Starting Unified MCP Filesystem Server")
    print(f"📁 Base directory: {base_path}")
    print(f"🌐 Port: {args.port}")
    print(f"🤖 AI features: {'disabled' if args.no_ai else 'enabled'}")
    print()
    
    # Create and start server
    server = UnifiedFilesystemServer(base_path=str(base_path))
    
    print("🔧 Server endpoints:")
    print(f"   Health check:     http://localhost:{args.port}/health")
    print(f"   Statistics:       http://localhost:{args.port}/stats")
    print(f"   File operations:  http://localhost:{args.port}/rpc (JSON-RPC)")
    print(f"   WebSocket events: ws://localhost:{args.port}/ws/events")
    print(f"   File watching:    http://localhost:{args.port}/fs/watch (SSE)")
    print(f"   API Documentation: http://localhost:{args.port}/docs")
    print()
    
    try:
        print("🔄 Initializing server...")
        await server.start(port=args.port)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        try:
            await server.stop()
            print("✅ Server stopped gracefully")
        except Exception as e:
            print(f"⚠️  Error during shutdown: {e}")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
