#!/bin/bash
# Start BoarderframeOS Screenshot Server

echo "🚀 Starting BoarderframeOS Screenshot Server..."
echo "─────────────────────────────────────────────"

# Check if server is already running
if lsof -i :8011 > /dev/null 2>&1; then
    echo "⚠️  Screenshot server is already running on port 8011"
    echo "   To stop it: lsof -ti :8011 | xargs kill"
    exit 1
fi

# Navigate to BoarderframeOS directory
cd "$(dirname "$0")"

# Check for required dependencies
echo "📦 Checking dependencies..."
python3 -c "import PIL" 2>/dev/null || echo "   ⚠️  PIL not installed - image processing features will be limited"
python3 -c "import pyautogui" 2>/dev/null || echo "   ℹ️  pyautogui not installed - using macOS screencapture"

# Start the screenshot server
echo "🏃 Starting server on port 8011..."
python3 mcp/screenshot_server.py

echo "✅ Screenshot server stopped"
