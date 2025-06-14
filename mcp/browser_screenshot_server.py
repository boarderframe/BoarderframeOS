#!/usr/bin/env python3
"""
Browser-based Screenshot Server for BoarderframeOS
Uses Selenium to capture screenshots without macOS permissions
"""

import asyncio
import base64
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    print("Warning: Selenium not installed. Install with: pip install selenium")

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not installed. Install with: pip install Pillow")


class BrowserScreenshotRequest(BaseModel):
    url: str = "http://localhost:8888"
    width: int = 1920
    height: int = 1080
    wait_time: int = 3
    full_page: bool = False
    selector: Optional[str] = None


class BrowserScreenshotResponse(BaseModel):
    success: bool
    screenshot_id: str
    base64_data: Optional[str] = None
    file_path: Optional[str] = None
    timestamp: str
    error: Optional[str] = None
    dimensions: Dict[str, int] = {"width": 0, "height": 0}


class BrowserScreenshotServer:
    def __init__(self):
        self.app = FastAPI(title="Browser Screenshot Server")
        self.setup_cors()
        self.setup_routes()
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.driver = None

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
        self.app.post("/capture/element")(self.capture_element)
        self.app.get("/status")(self.get_status)
        self.app.post("/shutdown")(self.shutdown_driver)

    async def health_check(self):
        return {
            "status": "healthy",
            "server": "browser_screenshot",
            "selenium": HAS_SELENIUM,
            "pil": HAS_PIL,
            "driver_active": self.driver is not None,
            "timestamp": datetime.now().isoformat(),
        }

    def get_driver(self):
        """Get or create Chrome driver"""
        if not HAS_SELENIUM:
            raise HTTPException(status_code=500, detail="Selenium not installed")

        if self.driver is None:
            options = ChromeOptions()
            options.add_argument("--headless")  # Run in background
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            try:
                self.driver = webdriver.Chrome(options=options)
            except Exception as e:
                # Try with Safari as fallback on macOS
                try:
                    self.driver = webdriver.Safari()
                except:
                    raise HTTPException(
                        status_code=500, detail=f"Could not start browser: {e}"
                    )

        return self.driver

    async def capture_screenshot(self, request: BrowserScreenshotRequest):
        """Capture screenshot of a webpage"""
        try:
            driver = self.get_driver()

            # Set window size
            driver.set_window_size(request.width, request.height)

            # Navigate to URL
            driver.get(request.url)

            # Wait for page load
            await asyncio.sleep(request.wait_time)

            # Take screenshot
            if request.full_page:
                # Get full page dimensions
                total_height = driver.execute_script(
                    "return document.body.scrollHeight"
                )
                driver.set_window_size(request.width, total_height)
                await asyncio.sleep(0.5)

            screenshot_bytes = driver.get_screenshot_as_png()

            # Generate filename
            timestamp = datetime.now()
            screenshot_id = timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"browser_screenshot_{screenshot_id}.png"
            file_path = self.screenshots_dir / filename

            # Save screenshot
            with open(file_path, "wb") as f:
                f.write(screenshot_bytes)

            # Get dimensions
            if HAS_PIL:
                img = Image.open(io.BytesIO(screenshot_bytes))
                dimensions = {"width": img.width, "height": img.height}
            else:
                dimensions = {"width": request.width, "height": request.height}

            # Convert to base64
            base64_data = base64.b64encode(screenshot_bytes).decode("utf-8")

            return BrowserScreenshotResponse(
                success=True,
                screenshot_id=screenshot_id,
                base64_data=base64_data,
                file_path=str(file_path),
                timestamp=timestamp.isoformat(),
                dimensions=dimensions,
            )

        except Exception as e:
            return BrowserScreenshotResponse(
                success=False,
                screenshot_id="",
                timestamp=datetime.now().isoformat(),
                error=str(e),
            )

    async def capture_element(self, request: BrowserScreenshotRequest):
        """Capture screenshot of specific element"""
        try:
            if not request.selector:
                raise ValueError("Element selector required")

            driver = self.get_driver()
            driver.get(request.url)

            # Wait for element
            wait = WebDriverWait(driver, 10)
            element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, request.selector))
            )

            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            await asyncio.sleep(0.5)

            # Take screenshot of element
            screenshot_bytes = element.screenshot_as_png

            # Save and process same as full screenshot
            timestamp = datetime.now()
            screenshot_id = timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"element_screenshot_{screenshot_id}.png"
            file_path = self.screenshots_dir / filename

            with open(file_path, "wb") as f:
                f.write(screenshot_bytes)

            base64_data = base64.b64encode(screenshot_bytes).decode("utf-8")

            return BrowserScreenshotResponse(
                success=True,
                screenshot_id=screenshot_id,
                base64_data=base64_data,
                file_path=str(file_path),
                timestamp=timestamp.isoformat(),
            )

        except Exception as e:
            return BrowserScreenshotResponse(
                success=False,
                screenshot_id="",
                timestamp=datetime.now().isoformat(),
                error=str(e),
            )

    async def get_status(self):
        """Get current driver status"""
        return {
            "driver_active": self.driver is not None,
            "current_url": self.driver.current_url if self.driver else None,
            "window_size": self.driver.get_window_size() if self.driver else None,
            "screenshots_count": len(list(self.screenshots_dir.glob("*.png"))),
        }

    async def shutdown_driver(self):
        """Shutdown browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        return {"status": "shutdown"}


# Create app instance
browser_server = BrowserScreenshotServer()
app = browser_server.app


if __name__ == "__main__":
    print("🌐 Starting Browser Screenshot Server on port 8012")
    print("📸 Screenshots will be saved to ./screenshots/")
    print("🔧 Using Selenium WebDriver for capture")

    if not HAS_SELENIUM:
        print("\n⚠️  WARNING: Selenium not installed!")
        print("   Install with: pip install selenium")
        print("   Also install ChromeDriver: brew install chromedriver\n")

    uvicorn.run(app, host="0.0.0.0", port=8012)
