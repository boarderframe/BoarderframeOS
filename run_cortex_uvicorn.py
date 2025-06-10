#!/usr/bin/env python3
"""
Run Agent Cortex Panel with Uvicorn
Alternative approach using ASGI server
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import uvicorn

app = FastAPI()

# Mount static files
if Path("ui/static").exists():
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# Simple test data
providers = {
    "anthropic": {
        "provider_type": "anthropic",
        "models": ["claude-opus-4-20250514", "claude-4-sonnet-20250514"],
        "is_active": True
    },
    "openai": {
        "provider_type": "openai",
        "models": ["gpt-4o", "gpt-4o-mini"],
        "is_active": True
    }
}

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Agent Cortex Panel</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    background: #0a0e27; 
                    color: #e0e6ed;
                    padding: 20px;
                }
                h1 { color: #64ffda; }
                .status { 
                    background: #1a1f2e; 
                    padding: 20px; 
                    border-radius: 10px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <h1>🧠 Agent Cortex Management Panel</h1>
            <div class="status">
                <h2>✅ Server is Running!</h2>
                <p>The Agent Cortex Panel is now accessible.</p>
                <p>API Endpoints:</p>
                <ul>
                    <li><a href="/api/cortex/providers" style="color: #64ffda;">/api/cortex/providers</a> - LLM Providers</li>
                    <li><a href="/api/cortex/overview" style="color: #64ffda;">/api/cortex/overview</a> - System Overview</li>
                </ul>
            </div>
        </body>
    </html>
    """

@app.get("/api/cortex/overview")
async def get_overview():
    return {
        "total_agents": 5,
        "active_providers": 2,
        "departments": 24,
        "model_assignments": 5,
        "cortex_status": "operational"
    }

@app.get("/api/cortex/providers")
async def get_providers():
    return providers

if __name__ == "__main__":
    print("\n🚀 Starting Agent Cortex Panel with Uvicorn...")
    print("🌐 Server will run at: http://localhost:8890")
    print("🛑 Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8890)