"""
API v1 router configuration
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import mcp_servers, health, configurations
from app.api import openwebui_tools

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(mcp_servers.router, prefix="/servers", tags=["mcp-servers"])
api_router.include_router(configurations.router, tags=["configurations"])

# Add Open WebUI compatible tools at /tools endpoint
api_router.include_router(openwebui_tools.router, prefix="/tools", tags=["openwebui-tools"])