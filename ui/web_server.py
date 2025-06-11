"""
Web Server for BoarderframeOS UI
Serves the web interface and API endpoints
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..core.agent_orchestrator import orchestrator
from .websocket_server import UIEvent, ws_server

logger = logging.getLogger("web_server")

app = FastAPI(title="BoarderframeOS Dashboard", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files and templates
ui_dir = Path(__file__).parent
static_dir = ui_dir / "static"
templates_dir = ui_dir / "templates"

static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


# Request models
class SolomonMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class AgentCommand(BaseModel):
    command: str
    agent_id: str
    params: Optional[Dict] = {}


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "title": "BoarderframeOS Dashboard"}
    )


@app.get("/solomon", response_class=HTMLResponse)
async def solomon_interface(request: Request):
    """Solomon communication interface"""
    return templates.TemplateResponse(
        "solomon.html", {"request": request, "title": "Solomon - Chief of Staff"}
    )


@app.get("/agents", response_class=HTMLResponse)
async def agents_monitor(request: Request):
    """Agent monitoring page"""
    return templates.TemplateResponse(
        "agents.html", {"request": request, "title": "Agent Monitor"}
    )


@app.get("/orchestration", response_class=HTMLResponse)
async def orchestration_view(request: Request):
    """Orchestration visualization page"""
    return templates.TemplateResponse(
        "orchestration.html", {"request": request, "title": "Orchestration Control"}
    )


@app.get("/llm", response_class=HTMLResponse)
async def llm_monitor(request: Request):
    """LLM activity monitor page"""
    return templates.TemplateResponse(
        "llm.html", {"request": request, "title": "LLM Activity Monitor"}
    )


# API Routes
@app.get("/api/status")
async def get_system_status():
    """Get current system status"""
    try:
        status = await orchestrator.get_system_status()
        return {"success": True, "data": status}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/agents")
async def get_agents():
    """Get all agent information"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8004/query",
                json={
                    "sql": "SELECT id, name, biome, status, config FROM agents ORDER BY created_at DESC"
                },
            )

            if response.status_code == 200 and response.json().get("success"):
                agents = response.json().get("data", [])
                return {"success": True, "agents": agents}
            else:
                return {"success": False, "error": "Database query failed"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/agents/{agent_id}")
async def get_agent_details(agent_id: str):
    """Get detailed agent information"""
    try:
        async with httpx.AsyncClient() as client:
            # Get agent basic info
            agent_response = await client.post(
                "http://localhost:8004/query",
                json={"sql": "SELECT * FROM agents WHERE id = ?", "params": [agent_id]},
            )

            if not agent_response.json().get("success"):
                raise HTTPException(status_code=404, detail="Agent not found")

            agent_data = agent_response.json()["data"][0]

            # Get agent metrics
            metrics_response = await client.post(
                "http://localhost:8004/query",
                json={
                    "sql": """
                    SELECT metric_name, metric_value, recorded_at
                    FROM metrics
                    WHERE agent_id = ?
                    ORDER BY recorded_at DESC LIMIT 100
                """,
                    "params": [agent_id],
                },
            )

            metrics = []
            if metrics_response.json().get("success"):
                metrics = metrics_response.json().get("data", [])

            # Get recent interactions
            interactions_response = await client.post(
                "http://localhost:8004/query",
                json={
                    "sql": """
                    SELECT interaction_type, data, created_at
                    FROM agent_interactions
                    WHERE source_agent = ? OR target_agent = ?
                    ORDER BY created_at DESC LIMIT 50
                """,
                    "params": [agent_id, agent_id],
                },
            )

            interactions = []
            if interactions_response.json().get("success"):
                interactions = interactions_response.json().get("data", [])

            return {
                "success": True,
                "agent": agent_data,
                "metrics": metrics,
                "interactions": interactions,
            }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/solomon/message")
async def send_solomon_message(message: SolomonMessage):
    """Send message to Solomon"""
    try:
        # Forward to WebSocket server for handling
        event = UIEvent(
            event_type="solomon_user_message",
            data={"message": message.message, "session_id": message.session_id},
        )
        await ws_server.broadcast_event(event)

        return {"success": True, "message": "Message sent to Solomon"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/agents/command")
async def send_agent_command(command: AgentCommand):
    """Send command to agent orchestrator"""
    try:
        if command.command == "start":
            success = await orchestrator.start_agent(command.agent_id, **command.params)
        elif command.command == "stop":
            success = await orchestrator.stop_agent(command.agent_id)
        elif command.command == "restart":
            await orchestrator.stop_agent(command.agent_id)
            await asyncio.sleep(2)
            success = await orchestrator.start_agent(command.agent_id, **command.params)
        else:
            return {"success": False, "error": f"Unknown command: {command.command}"}

        return {"success": success, "message": f"Command {command.command} executed"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/servers")
async def get_mcp_servers():
    """Get MCP server status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/servers")

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": "Registry unavailable"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/llm/activity")
async def get_llm_activity():
    """Get LLM server activity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8005/stats")

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": "LLM server unavailable"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/biomes")
async def get_biome_status():
    """Get biome health and population"""
    try:
        biomes = ["forge", "arena", "library", "market", "council", "garden"]
        biome_data = {}

        async with httpx.AsyncClient() as client:
            for biome in biomes:
                response = await client.post(
                    "http://localhost:8004/query",
                    json={
                        "sql": """
                        SELECT COUNT(*) as count, AVG(fitness_score) as avg_fitness
                        FROM agents
                        WHERE biome = ? AND status = 'active'
                    """,
                        "params": [biome],
                    },
                )

                if response.json().get("success"):
                    data = response.json()["data"][0]
                    biome_data[biome] = {
                        "population": data["count"],
                        "avg_fitness": data["avg_fitness"] or 0.0,
                        "health": min(
                            1.0, (data["count"] / 10) * (data["avg_fitness"] or 0.5)
                        ),
                    }

        return {"success": True, "biomes": biome_data}

    except Exception as e:
        return {"success": False, "error": str(e)}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()

    try:
        # Add to WebSocket server clients
        ws_server.clients.add(websocket)

        # Send initial state
        await ws_server._send_initial_state(websocket)

        # Handle messages
        while True:
            data = await websocket.receive_text()
            await ws_server._handle_client_message(websocket, data)

    except WebSocketDisconnect:
        ws_server.clients.discard(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_server.clients.discard(websocket)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting BoarderframeOS Web Server")

    # Start WebSocket server
    await ws_server.start()

    logger.info("Web Server initialized successfully")


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="BoarderframeOS Web Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(f"Starting BoarderframeOS Web Server on {args.host}:{args.port}")
    uvicorn.run("web_server:app", host=args.host, port=args.port, reload=args.reload)
