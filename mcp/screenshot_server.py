#!/usr/bin/env python3
"""
BoarderframeOS MCP Screenshot Server
Advanced screenshot capture for macOS with enterprise features
"""

import asyncio
import base64
import io
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logging.warning("PIL not available - image processing features disabled")

try:
    import pyautogui
    HAS_PYAUTOGUI = True
    # Disable pyautogui failsafe for server use
    pyautogui.FAILSAFE = False
except ImportError:
    HAS_PYAUTOGUI = False
    logging.warning("pyautogui not available - fallback to macOS screencapture")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_screenshot")

# Configuration
SCREENSHOTS_DIR = Path.home() / "BoarderframeOS" / "screenshots"
MAX_SCREENSHOT_AGE = timedelta(hours=24)  # Auto-cleanup old screenshots
MAX_SCREENSHOT_SIZE = 5 * 1024 * 1024  # 5MB limit
DEFAULT_QUALITY = 85  # JPEG quality

# Ensure screenshots directory exists
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

class ScreenshotRequest(BaseModel):
    """Screenshot capture request model"""
    region: Optional[Dict[str, int]] = Field(default=None, description="Region to capture {x, y, width, height}")
    display: int = Field(default=1, description="Display number to capture (1-based)")
    format: str = Field(default="jpeg", description="Output format: jpeg, png")
    quality: int = Field(default=DEFAULT_QUALITY, description="JPEG quality (1-100)")
    scale: float = Field(default=1.0, description="Scale factor (0.1-2.0)")
    annotation: Optional[Dict[str, Any]] = Field(default=None, description="Annotation to add")
    save_to_disk: bool = Field(default=True, description="Save screenshot to disk")
    return_base64: bool = Field(default=True, description="Return base64 encoded image")

class AnnotationRequest(BaseModel):
    """Annotation configuration"""
    text: Optional[str] = None
    rectangles: Optional[List[Dict[str, int]]] = None  # [{"x": 0, "y": 0, "width": 100, "height": 50}]
    circles: Optional[List[Dict[str, int]]] = None     # [{"x": 50, "y": 50, "radius": 25}]
    arrows: Optional[List[Dict[str, int]]] = None      # [{"x1": 0, "y1": 0, "x2": 100, "y2": 100}]
    color: str = "red"
    font_size: int = 16

class ScreenshotResponse(BaseModel):
    """Screenshot response model"""
    success: bool
    screenshot_id: str
    file_path: Optional[str] = None
    base64_data: Optional[str] = None
    format: str
    dimensions: Dict[str, int]
    file_size: int
    timestamp: str
    error: Optional[str] = None

class ScreenshotManager:
    """Advanced screenshot management with caching and cleanup"""

    def __init__(self):
        self.screenshot_cache = {}
        self.cleanup_task = None

    async def initialize(self):
        """Initialize screenshot manager"""
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_old_screenshots())
        logger.info("Screenshot manager initialized")

    async def capture_screenshot(self, request: ScreenshotRequest) -> ScreenshotResponse:
        """Capture screenshot with advanced options"""
        try:
            screenshot_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            # Capture using best available method
            if HAS_PYAUTOGUI:
                image_data = await self._capture_with_pyautogui(request)
            else:
                image_data = await self._capture_with_macos(request)

            if not image_data:
                raise Exception("Failed to capture screenshot")

            # Process image
            if HAS_PIL:
                image = Image.open(io.BytesIO(image_data))

                # Apply scaling
                if request.scale != 1.0:
                    new_size = (
                        int(image.width * request.scale),
                        int(image.height * request.scale)
                    )
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

                # Add annotations
                if request.annotation and HAS_PIL:
                    image = await self._add_annotations(image, request.annotation)

                # Convert to requested format
                output_buffer = io.BytesIO()
                if request.format.lower() == "jpeg":
                    image = image.convert("RGB")  # JPEG doesn't support transparency
                    image.save(output_buffer, format="JPEG", quality=request.quality, optimize=True)
                else:
                    image.save(output_buffer, format="PNG", optimize=True)

                image_data = output_buffer.getvalue()
                dimensions = {"width": image.width, "height": image.height}
            else:
                # Fallback dimensions
                dimensions = {"width": 0, "height": 0}

            # Check size limit
            if len(image_data) > MAX_SCREENSHOT_SIZE:
                raise Exception(f"Screenshot too large: {len(image_data)} bytes (max {MAX_SCREENSHOT_SIZE})")

            # Save to disk if requested
            file_path = None
            if request.save_to_disk:
                filename = f"screenshot_{screenshot_id}_{timestamp.replace(':', '-')}.{request.format}"
                file_path = SCREENSHOTS_DIR / filename

                with open(file_path, "wb") as f:
                    f.write(image_data)

                logger.info(f"Screenshot saved: {file_path}")

            # Prepare response
            response = ScreenshotResponse(
                success=True,
                screenshot_id=screenshot_id,
                file_path=str(file_path) if file_path else None,
                base64_data=base64.b64encode(image_data).decode() if request.return_base64 else None,
                format=request.format,
                dimensions=dimensions,
                file_size=len(image_data),
                timestamp=timestamp
            )

            # Cache screenshot metadata
            self.screenshot_cache[screenshot_id] = {
                "file_path": file_path,
                "timestamp": datetime.fromisoformat(timestamp),
                "format": request.format,
                "dimensions": dimensions,
                "file_size": len(image_data)
            }

            return response

        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return ScreenshotResponse(
                success=False,
                screenshot_id="",
                format=request.format,
                dimensions={"width": 0, "height": 0},
                file_size=0,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )

    async def _capture_with_pyautogui(self, request: ScreenshotRequest) -> bytes:
        """Capture screenshot using pyautogui"""
        try:
            if request.region:
                # Capture specific region
                screenshot = pyautogui.screenshot(
                    region=(
                        request.region["x"],
                        request.region["y"],
                        request.region["width"],
                        request.region["height"]
                    )
                )
            else:
                # Capture full screen
                screenshot = pyautogui.screenshot()

            # Convert to bytes
            buffer = io.BytesIO()
            screenshot.save(buffer, format="PNG")
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"pyautogui capture failed: {e}")
            return None

    async def _capture_with_macos(self, request: ScreenshotRequest) -> bytes:
        """Capture screenshot using macOS screencapture command"""
        try:
            # Build screencapture command
            cmd = ["screencapture", "-t", "png", "-x"]  # -x removes shutter sound

            # Add display option
            if request.display > 1:
                cmd.extend(["-D", str(request.display)])

            # Add region option
            if request.region:
                region_str = f"{request.region['x']},{request.region['y']},{request.region['width']},{request.region['height']}"
                cmd.extend(["-R", region_str])

            # Use stdout for image data
            cmd.append("-")

            # Execute command
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.error(f"screencapture failed: {stderr.decode()}")
                return None

            return stdout

        except Exception as e:
            logger.error(f"macOS capture failed: {e}")
            return None

    async def _add_annotations(self, image: Image.Image, annotation: Dict[str, Any]) -> Image.Image:
        """Add annotations to image"""
        if not HAS_PIL:
            return image

        try:
            # Create drawing context
            draw = ImageDraw.Draw(image)

            # Parse annotation
            ann = AnnotationRequest(**annotation)
            color = ann.color

            # Load font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", ann.font_size)
            except:
                font = ImageFont.load_default()

            # Draw rectangles
            if ann.rectangles:
                for rect in ann.rectangles:
                    draw.rectangle(
                        [rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]],
                        outline=color,
                        width=2
                    )

            # Draw circles
            if ann.circles:
                for circle in ann.circles:
                    x, y, r = circle["x"], circle["y"], circle["radius"]
                    draw.ellipse([x-r, y-r, x+r, y+r], outline=color, width=2)

            # Draw arrows
            if ann.arrows:
                for arrow in ann.arrows:
                    x1, y1, x2, y2 = arrow["x1"], arrow["y1"], arrow["x2"], arrow["y2"]
                    draw.line([x1, y1, x2, y2], fill=color, width=3)

                    # Draw arrowhead
                    import math
                    angle = math.atan2(y2 - y1, x2 - x1)
                    arrow_length = 10
                    arrow_angle = math.pi / 6

                    # Arrowhead points
                    x3 = x2 - arrow_length * math.cos(angle - arrow_angle)
                    y3 = y2 - arrow_length * math.sin(angle - arrow_angle)
                    x4 = x2 - arrow_length * math.cos(angle + arrow_angle)
                    y4 = y2 - arrow_length * math.sin(angle + arrow_angle)

                    draw.line([x2, y2, x3, y3], fill=color, width=2)
                    draw.line([x2, y2, x4, y4], fill=color, width=2)

            # Draw text
            if ann.text:
                draw.text((10, 10), ann.text, fill=color, font=font)

            return image

        except Exception as e:
            logger.error(f"Annotation failed: {e}")
            return image

    async def list_screenshots(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent screenshots"""
        screenshots = []

        try:
            # Get from cache first
            for screenshot_id, info in self.screenshot_cache.items():
                screenshots.append({
                    "id": screenshot_id,
                    "file_path": str(info["file_path"]) if info["file_path"] else None,
                    "timestamp": info["timestamp"].isoformat(),
                    "format": info["format"],
                    "dimensions": info["dimensions"],
                    "file_size": info["file_size"]
                })

            # Also scan directory for persisted screenshots
            if SCREENSHOTS_DIR.exists():
                for file_path in sorted(SCREENSHOTS_DIR.glob("screenshot_*"), reverse=True):
                    if len(screenshots) >= limit:
                        break

                    # Skip if already in cache
                    if any(s.get("file_path") == str(file_path) for s in screenshots):
                        continue

                    stat = file_path.stat()
                    screenshots.append({
                        "id": file_path.stem,
                        "file_path": str(file_path),
                        "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "format": file_path.suffix[1:],
                        "dimensions": {"width": 0, "height": 0},  # Would need to open file to get
                        "file_size": stat.st_size
                    })

            # Sort by timestamp and limit
            screenshots.sort(key=lambda x: x["timestamp"], reverse=True)
            return screenshots[:limit]

        except Exception as e:
            logger.error(f"Failed to list screenshots: {e}")
            return []

    async def get_screenshot(self, screenshot_id: str) -> Optional[Dict[str, Any]]:
        """Get screenshot by ID"""
        try:
            # Check cache first
            if screenshot_id in self.screenshot_cache:
                info = self.screenshot_cache[screenshot_id]

                # Read file if it exists
                if info["file_path"] and info["file_path"].exists():
                    with open(info["file_path"], "rb") as f:
                        image_data = f.read()

                    return {
                        "id": screenshot_id,
                        "base64_data": base64.b64encode(image_data).decode(),
                        "format": info["format"],
                        "dimensions": info["dimensions"],
                        "file_size": info["file_size"],
                        "timestamp": info["timestamp"].isoformat()
                    }

            # Search in directory
            for file_path in SCREENSHOTS_DIR.glob(f"screenshot_{screenshot_id}*"):
                with open(file_path, "rb") as f:
                    image_data = f.read()

                return {
                    "id": screenshot_id,
                    "base64_data": base64.b64encode(image_data).decode(),
                    "format": file_path.suffix[1:],
                    "dimensions": {"width": 0, "height": 0},
                    "file_size": len(image_data),
                    "timestamp": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get screenshot {screenshot_id}: {e}")
            return None

    async def delete_screenshot(self, screenshot_id: str) -> bool:
        """Delete screenshot by ID"""
        try:
            deleted = False

            # Remove from cache
            if screenshot_id in self.screenshot_cache:
                info = self.screenshot_cache[screenshot_id]
                if info["file_path"] and info["file_path"].exists():
                    info["file_path"].unlink()
                    deleted = True
                del self.screenshot_cache[screenshot_id]

            # Search and delete from directory
            for file_path in SCREENSHOTS_DIR.glob(f"screenshot_{screenshot_id}*"):
                file_path.unlink()
                deleted = True

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete screenshot {screenshot_id}: {e}")
            return False

    async def _cleanup_old_screenshots(self):
        """Background task to cleanup old screenshots"""
        while True:
            try:
                cutoff_time = datetime.now() - MAX_SCREENSHOT_AGE
                deleted_count = 0

                # Cleanup cache
                to_delete = []
                for screenshot_id, info in self.screenshot_cache.items():
                    if info["timestamp"] < cutoff_time:
                        to_delete.append(screenshot_id)

                for screenshot_id in to_delete:
                    if await self.delete_screenshot(screenshot_id):
                        deleted_count += 1

                # Cleanup directory
                if SCREENSHOTS_DIR.exists():
                    for file_path in SCREENSHOTS_DIR.glob("screenshot_*"):
                        if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_time:
                            try:
                                file_path.unlink()
                                deleted_count += 1
                            except Exception as e:
                                logger.error(f"Failed to delete {file_path}: {e}")

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old screenshots")

                # Sleep for 1 hour
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(300)  # Sleep 5 minutes on error

class MCPScreenshotServer:
    """MCP Screenshot Server for BoarderframeOS"""

    def __init__(self):
        self.app = FastAPI(
            title="BoarderframeOS Screenshot MCP Server",
            version="1.0.0",
            description="Advanced screenshot capture with annotations and management"
        )
        self.setup_app()
        self.screenshot_manager = ScreenshotManager()

    def setup_app(self):
        """Setup FastAPI application"""
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add routes
        self.app.get("/health")(self.health_check)
        self.app.post("/capture")(self.capture_screenshot)
        self.app.get("/screenshots")(self.list_screenshots)
        self.app.get("/screenshots/{screenshot_id}")(self.get_screenshot)
        self.app.delete("/screenshots/{screenshot_id}")(self.delete_screenshot)
        self.app.get("/displays")(self.get_displays)
        self.app.post("/cleanup")(self.cleanup_screenshots)

    async def start(self, port: int = 8011):
        """Start the screenshot server"""
        logger.info(f"Starting MCP Screenshot Server on port {port}")

        # Initialize screenshot manager
        await self.screenshot_manager.initialize()

        # Check dependencies
        deps = {
            "PIL": HAS_PIL,
            "pyautogui": HAS_PYAUTOGUI,
            "macOS screencapture": sys.platform == "darwin"
        }

        logger.info(f"Dependencies: {deps}")

        # Start server
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()

    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server": "mcp_screenshot",
            "dependencies": {
                "PIL": HAS_PIL,
                "pyautogui": HAS_PYAUTOGUI,
                "platform": sys.platform
            },
            "screenshot_cache_size": len(self.screenshot_manager.screenshot_cache),
            "screenshots_directory": str(SCREENSHOTS_DIR)
        }

    async def capture_screenshot(self, request: ScreenshotRequest):
        """Capture screenshot endpoint"""
        return await self.screenshot_manager.capture_screenshot(request)

    async def list_screenshots(self, limit: int = 50):
        """List screenshots endpoint"""
        screenshots = await self.screenshot_manager.list_screenshots(limit)
        return {
            "screenshots": screenshots,
            "count": len(screenshots),
            "limit": limit
        }

    async def get_screenshot(self, screenshot_id: str):
        """Get specific screenshot endpoint"""
        screenshot = await self.screenshot_manager.get_screenshot(screenshot_id)
        if screenshot:
            return screenshot
        else:
            raise HTTPException(status_code=404, detail="Screenshot not found")

    async def delete_screenshot(self, screenshot_id: str):
        """Delete screenshot endpoint"""
        deleted = await self.screenshot_manager.delete_screenshot(screenshot_id)
        if deleted:
            return {"success": True, "message": f"Screenshot {screenshot_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Screenshot not found")

    async def get_displays(self):
        """Get display information"""
        try:
            if HAS_PYAUTOGUI:
                size = pyautogui.size()
                return {
                    "displays": [
                        {
                            "id": 1,
                            "width": size.width,
                            "height": size.height,
                            "primary": True
                        }
                    ]
                }
            else:
                # Fallback for macOS
                result = await asyncio.create_subprocess_exec(
                    "system_profiler", "SPDisplaysDataType", "-json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await result.communicate()

                if result.returncode == 0:
                    data = json.loads(stdout.decode())
                    displays = []

                    for i, display in enumerate(data.get("SPDisplaysDataType", [])):
                        displays.append({
                            "id": i + 1,
                            "width": 1920,  # Default fallback
                            "height": 1080,
                            "primary": i == 0
                        })

                    return {"displays": displays}

            return {"displays": [{"id": 1, "width": 1920, "height": 1080, "primary": True}]}

        except Exception as e:
            logger.error(f"Failed to get displays: {e}")
            return {"displays": [{"id": 1, "width": 1920, "height": 1080, "primary": True}]}

    async def cleanup_screenshots(self, background_tasks: BackgroundTasks):
        """Manual cleanup of old screenshots"""
        try:
            cutoff_time = datetime.now() - MAX_SCREENSHOT_AGE
            deleted_count = 0

            # Cleanup in background
            background_tasks.add_task(self._perform_cleanup, cutoff_time)

            return {
                "success": True,
                "message": "Cleanup initiated",
                "cutoff_time": cutoff_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Cleanup initiation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _perform_cleanup(self, cutoff_time: datetime):
        """Perform actual cleanup"""
        deleted_count = 0

        # Cleanup cache
        to_delete = []
        for screenshot_id, info in self.screenshot_manager.screenshot_cache.items():
            if info["timestamp"] < cutoff_time:
                to_delete.append(screenshot_id)

        for screenshot_id in to_delete:
            if await self.screenshot_manager.delete_screenshot(screenshot_id):
                deleted_count += 1

        logger.info(f"Manual cleanup completed: {deleted_count} screenshots deleted")

async def main():
    """Run the server directly"""
    port = 8011

    # Get port from command line if specified
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid port: {sys.argv[1]}. Using default: {port}")

    # Create and start server
    server = MCPScreenshotServer()
    await server.start(port)

if __name__ == "__main__":
    try:
        # Run the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Screenshot Server")
