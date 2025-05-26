#!/usr/bin/env python3
"""
BoarderframeOS MCP Integration Script
Integrates the filesystem server with the broader BoarderframeOS ecosystem
"""

import os
import sys
import yaml
import asyncio
import subprocess
from pathlib import Path

def load_boarderframe_config():
    """Load BoarderframeOS configuration"""
    config_path = Path(__file__).parent.parent / "boarderframe.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def update_mcp_server_config(config: dict):
    """Update MCP server configuration in boarderframe.yaml"""
    config_path = Path(__file__).parent.parent / "boarderframe.yaml"
    
    # Ensure mcp_servers section exists
    if "mcp_servers" not in config:
        config["mcp_servers"] = {}
    
    # Update filesystem server configuration
    config["mcp_servers"]["filesystem"] = {
        "enabled": True,
        "port": 8001,
        "path": "mcp/filesystem_server.py",
        "startup_script": "mcp/start_filesystem_server.py",
        "health_endpoint": "http://localhost:8001/health",
        "features": {
            "ai_content_analysis": True,
            "vector_embeddings": True,
            "real_time_monitoring": True,
            "version_control": True,
            "integrity_checking": True
        },
        "dependencies": [
            "aiofiles",
            "sentence-transformers",
            "xxhash",
            "aiosqlite",
            "watchdog",
            "tiktoken",
            "pygments"
        ]
    }
    
    # Write back to config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print("✅ Updated BoarderframeOS configuration with MCP filesystem server")

async def test_integration():
    """Test integration with BoarderframeOS"""
    print("🧪 Testing BoarderframeOS MCP integration...")
    
    # Test if server can start
    try:
        proc = subprocess.Popen([
            sys.executable, "start_filesystem_server.py", "--health-check"
        ], cwd=Path(__file__).parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        stdout, stderr = proc.communicate(timeout=10)
        
        if proc.returncode == 0:
            print("✅ Filesystem server health check passed")
        else:
            print("⚠️  Filesystem server health check failed")
            if stderr:
                print(f"Error: {stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️  Health check timed out")
        proc.kill()
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

def main():
    print("🔧 BoarderframeOS MCP Filesystem Server Integration")
    print("=" * 50)
    
    # Load current config
    config = load_boarderframe_config()
    print(f"📄 Loaded config from: {Path(__file__).parent.parent / 'boarderframe.yaml'}")
    
    # Update MCP server configuration
    update_mcp_server_config(config)
    
    # Test integration
    asyncio.run(test_integration())
    
    print("\n🚀 Integration complete!")
    print("\nNext steps:")
    print("1. Start the filesystem server: python mcp/start_filesystem_server.py")
    print("2. Monitor server health: python mcp/monitor_filesystem_server.py")
    print("3. Run tests: python mcp/test_filesystem_server.py")
    print("4. Check dashboard: http://localhost:8888")

if __name__ == "__main__":
    main()
