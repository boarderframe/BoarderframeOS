#!/usr/bin/env python3
"""
Install missing dependencies for BoarderframeOS
"""
import subprocess
import sys

print("📦 Installing BoarderframeOS dependencies...")

dependencies = [
    "aiosqlite",    # For database server
    "fastapi",      # For API servers
    "uvicorn",      # For running FastAPI
    "httpx",        # For HTTP client
    "pydantic",     # For data validation
    "websockets",   # For WebSocket support
    "aiofiles",     # For async file operations
]

for dep in dependencies:
    print(f"Installing {dep}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])

print("\n✅ Dependencies installed successfully!")
print("\nNow you can run:")
print("  python /Users/cosburn/BoarderframeOS/boarderframeos/startup.py")
