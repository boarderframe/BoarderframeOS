"""
MCP Server Manager - FastAPI Application Entry Point
"""
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.api_v1.api import api_router


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MCP Server Manager",
        version="1.0.0",
        description="MCP Server Manager - Manage and monitor MCP servers",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
    )

    # Set CORS for frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:8080",
            "http://localhost:8081",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:3003",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8081"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    # Add OPTIONS handler for OpenAPI endpoint
    @app.options("/api/v1/openapi.json")
    async def options_openapi():
        return {"detail": "OK"}

    return app


app = create_application()


@app.on_event("startup")
async def startup_event() -> None:
    """Application startup event handler."""
    import logging
    from app.services.mcp_service import mcp_service
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP Server Manager application")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shutdown event handler."""
    import logging
    from app.services.mcp_service import mcp_service
    
    logger = logging.getLogger(__name__)
    logger.info("Shutting down MCP Server Manager application")
    
    # Gracefully shutdown the process manager
    await mcp_service.shutdown()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
    """Global HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-server-manager"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )