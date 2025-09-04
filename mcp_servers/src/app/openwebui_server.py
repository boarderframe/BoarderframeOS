"""
Simplified OpenAPI Server for Open WebUI Integration
Flat structure with direct tool endpoints
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.openwebui_tools import router as tools_router


def create_openwebui_app() -> FastAPI:
    """Create a simplified FastAPI app specifically for Open WebUI integration."""
    
    app = FastAPI(
        title="MCP Filesystem Tools",
        version="1.0.0",
        description="Filesystem tools for Open WebUI - MCP Server integration",
        # Ensure OpenAPI spec is easily accessible
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration for Open WebUI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Open WebUI needs broad access
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Include the tools router at root level for Open WebUI
    app.include_router(tools_router, prefix="", tags=["tools"])

    # Root endpoint for Open WebUI discovery
    @app.get("/")
    async def root():
        """Root endpoint providing server information."""
        return {
            "name": "MCP Filesystem Tools",
            "description": "Filesystem operations for Open WebUI",
            "version": "1.0.0",
            "tools": [
                "list_directory",
                "read_file", 
                "write_file",
                "search_files",
                "create_directory",
                "get_file_info"
            ],
            "openapi_url": "/openapi.json"
        }

    return app


app = create_openwebui_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.openwebui_server:app",
        host="0.0.0.0",
        port=8080,  # Different port to avoid conflicts
        reload=True,
        log_level="info",
    )