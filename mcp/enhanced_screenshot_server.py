#!/usr/bin/env python3
"""
Enhanced Screenshot Server for BoarderframeOS
Provides multiple capture methods for macOS without permissions
"""

import asyncio
import base64
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


class ScreenshotRequest(BaseModel):
    method: str = "window"  # window, html, applescript
    filename: Optional[str] = None
    url: str = "http://localhost:8888"


class ScreenshotResponse(BaseModel):
    success: bool
    method: str
    file_path: Optional[str] = None
    base64_data: Optional[str] = None
    timestamp: str
    message: str
    error: Optional[str] = None


class EnhancedScreenshotServer:
    def __init__(self):
        self.app = FastAPI(title="Enhanced Screenshot Server")
        self.setup_cors()
        self.setup_routes()
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

    def setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        self.app.get("/health")(self.health_check)
        self.app.post("/capture")(self.capture_screenshot)
        self.app.get("/screenshots")(self.list_screenshots)
        self.app.get("/screenshots/{filename}")(self.get_screenshot)
        self.app.get("/instructions")(self.get_instructions)

    async def health_check(self):
        return {
            "status": "healthy",
            "server": "enhanced_screenshot",
            "available_methods": ["window", "html", "applescript"],
            "screenshots_directory": str(self.screenshots_dir),
            "timestamp": datetime.now().isoformat(),
        }

    async def capture_screenshot(
        self, request: ScreenshotRequest, background_tasks: BackgroundTasks
    ):
        """Capture screenshot using specified method"""
        timestamp = datetime.now()

        if request.method == "window":
            return await self.capture_window_method(request, timestamp)
        elif request.method == "html":
            return await self.capture_html_method(request, timestamp)
        elif request.method == "applescript":
            return await self.capture_applescript_method(request, timestamp)
        else:
            return ScreenshotResponse(
                success=False,
                method=request.method,
                timestamp=timestamp.isoformat(),
                message="Invalid method",
                error=f"Unknown method: {request.method}",
            )

    async def capture_window_method(
        self, request: ScreenshotRequest, timestamp: datetime
    ):
        """Interactive window capture - user must click on window"""
        filename = (
            request.filename or f"window_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        )
        file_path = self.screenshots_dir / filename

        # Create a temporary script for window capture
        script_content = f"""#!/bin/bash
echo "📸 Click on the BoarderframeOS window to capture it..."
screencapture -W -x "{file_path}"
"""

        script_path = self.screenshots_dir / "capture_window.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)

        return ScreenshotResponse(
            success=True,
            method="window",
            file_path=str(file_path),
            timestamp=timestamp.isoformat(),
            message=f"Run this command and click on the window: bash {script_path}",
            error=None,
        )

    async def capture_html_method(
        self, request: ScreenshotRequest, timestamp: datetime
    ):
        """Capture HTML content of the page"""
        try:
            import requests

            filename = (
                request.filename or f"html_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
            )
            file_path = self.screenshots_dir / filename

            # Fetch HTML
            response = requests.get(request.url, timeout=10)
            if response.status_code == 200:
                # Save HTML with base tag for proper resource loading
                html_content = response.text.replace(
                    "<head>", f'<head>\n<base href="{request.url}">'
                )

                with open(file_path, "w") as f:
                    f.write(html_content)

                # Also create a viewer HTML
                viewer_path = self.screenshots_dir / f"viewer_{filename}"
                viewer_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Viewer</title>
    <style>
        body {{ margin: 0; padding: 0; }}
        iframe {{ width: 100vw; height: 100vh; border: none; }}
    </style>
</head>
<body>
    <iframe src="{request.url}" title="BoarderframeOS"></iframe>
</body>
</html>"""

                with open(viewer_path, "w") as f:
                    f.write(viewer_html)

                return ScreenshotResponse(
                    success=True,
                    method="html",
                    file_path=str(file_path),
                    timestamp=timestamp.isoformat(),
                    message=f"HTML captured. View with: open {file_path}",
                    error=None,
                )
            else:
                raise Exception(f"HTTP {response.status_code}")

        except Exception as e:
            return ScreenshotResponse(
                success=False,
                method="html",
                timestamp=timestamp.isoformat(),
                message="HTML capture failed",
                error=str(e),
            )

    async def capture_applescript_method(
        self, request: ScreenshotRequest, timestamp: datetime
    ):
        """Use AppleScript to capture browser window"""
        filename = (
            request.filename or f"applescript_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        )
        file_path = self.screenshots_dir / filename

        # AppleScript to capture browser
        applescript = f"""
tell application "System Events"
    set browserName to ""

    -- Find active browser
    if exists (process "Google Chrome") then
        set browserName to "Google Chrome"
    else if exists (process "Safari") then
        set browserName to "Safari"
    else if exists (process "Firefox") then
        set browserName to "Firefox"
    end if

    if browserName is not "" then
        -- Activate browser
        tell application browserName
            activate
            delay 0.5
        end tell

        -- Take screenshot after delay
        do shell script "sleep 1 && screencapture -x '{file_path}'"
        return "success"
    else
        return "error: No browser found"
    end if
end tell
"""

        try:
            # Execute AppleScript
            result = subprocess.run(
                ["osascript", "-e", applescript], capture_output=True, text=True
            )

            if os.path.exists(file_path):
                return ScreenshotResponse(
                    success=True,
                    method="applescript",
                    file_path=str(file_path),
                    timestamp=timestamp.isoformat(),
                    message="Screenshot captured via AppleScript",
                    error=None,
                )
            else:
                return ScreenshotResponse(
                    success=False,
                    method="applescript",
                    timestamp=timestamp.isoformat(),
                    message="AppleScript capture failed",
                    error=result.stderr or "Unknown error",
                )

        except Exception as e:
            return ScreenshotResponse(
                success=False,
                method="applescript",
                timestamp=timestamp.isoformat(),
                message="AppleScript execution failed",
                error=str(e),
            )

    async def list_screenshots(self):
        """List all captured screenshots"""
        screenshots = []
        for file_path in sorted(self.screenshots_dir.glob("*.*")):
            screenshots.append(
                {
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "created": datetime.fromtimestamp(
                        file_path.stat().st_ctime
                    ).isoformat(),
                    "type": file_path.suffix,
                }
            )
        return {"screenshots": screenshots, "count": len(screenshots)}

    async def get_screenshot(self, filename: str):
        """Serve a screenshot file"""
        file_path = self.screenshots_dir / filename
        if file_path.exists():
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="Screenshot not found")

    async def get_instructions(self):
        """Get instructions for capturing screenshots"""
        return {
            "methods": {
                "window": {
                    "description": "Interactive window capture",
                    "instructions": [
                        "POST to /capture with method='window'",
                        "Run the generated script",
                        "Click on the BoarderframeOS window",
                    ],
                    "requires_permission": False,
                },
                "html": {
                    "description": "Capture HTML content",
                    "instructions": [
                        "POST to /capture with method='html'",
                        "HTML will be saved locally",
                        "Open the HTML file to view",
                    ],
                    "requires_permission": False,
                },
                "applescript": {
                    "description": "Automated browser capture",
                    "instructions": [
                        "POST to /capture with method='applescript'",
                        "Browser will be activated automatically",
                        "Screenshot taken after 1 second delay",
                    ],
                    "requires_permission": True,
                },
            },
            "recommended": "Use 'html' method for viewing UI without permissions",
        }


# Create app instance
screenshot_server = EnhancedScreenshotServer()
app = screenshot_server.app


if __name__ == "__main__":
    print("📸 Enhanced Screenshot Server for BoarderframeOS")
    print("=" * 50)
    print("🚀 Starting server on port 8013")
    print("📁 Screenshots directory: ./screenshots/")
    print("\nAvailable capture methods:")
    print("  - window: Interactive window capture (no permissions)")
    print("  - html: Capture HTML content (no permissions)")
    print("  - applescript: Automated capture (requires permissions)")
    print("\nAccess instructions at: http://localhost:8013/instructions")

    uvicorn.run(app, host="0.0.0.0", port=8013)
