#!/usr/bin/env python3
"""
Simple UI startup script for BoarderframeOS
"""

import asyncio
import uvicorn
import logging
from pathlib import Path
import sys

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    """Start the UI server"""
    print("🚀 Starting BoarderframeOS UI Server...")
    print("📍 Dashboard will be available at: http://localhost:8080")
    print("💬 Solomon chat at: http://localhost:8080/solomon")
    print("👥 Agent monitor at: http://localhost:8080/agents")
    print()
    
    try:
        # Start the web server
        uvicorn.run(
            "ui.web_server:app",
            host="0.0.0.0",
            port=8080,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 UI Server stopped")
    except Exception as e:
        print(f"❌ Failed to start UI server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())