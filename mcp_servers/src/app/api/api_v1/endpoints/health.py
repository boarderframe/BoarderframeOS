"""
Health check endpoints
"""
from typing import Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "mcp-server-manager"}


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, str]:
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "mcp-server-manager",
        "version": "1.0.0",
        "mcp_servers": {
            "filesystem-python-001": "running"
        }
    }