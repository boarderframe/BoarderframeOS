#!/usr/bin/env python3
"""
macOS Screenshot Helper for BoarderframeOS
Works around permission issues by using window capture
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def capture_window_screenshot(output_path=None, window_title="BoarderframeOS"):
    """
    Capture screenshot of a specific window using macOS screencapture
    This method doesn't require screen recording permissions
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"boarderframe_window_{timestamp}.png"

    try:
        # Method 1: Interactive window capture (user clicks on window)
        print(f"📸 Preparing to capture window screenshot...")
        print(f"   When prompted, click on the {window_title} window in your browser")
        print(f"   Output will be saved to: {output_path}")

        # Use -W flag for window capture (interactive)
        cmd = ["screencapture", "-W", "-x", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"\n✅ Screenshot captured successfully!")
            print(f"   File: {output_path}")
            print(f"   Size: {file_size:,} bytes")
            return output_path
        else:
            print(f"\n❌ Screenshot capture failed")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return None

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def capture_window_by_id(window_id, output_path=None):
    """
    Capture screenshot of a specific window by ID
    First, we need to find the window ID
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"boarderframe_window_{timestamp}.png"

    try:
        # Use -l flag with window ID
        cmd = ["screencapture", "-l", str(window_id), "-x", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            return None

    except Exception as e:
        print(f"Error capturing window by ID: {e}")
        return None


def list_windows():
    """
    List all windows (requires additional tools on macOS)
    This is a placeholder - would need osascript or other tools
    """
    print("\n📋 Window Capture Instructions:")
    print("1. Open BoarderframeOS in your browser (http://localhost:8888)")
    print("2. Make sure the window is visible")
    print("3. Run: python macos_screenshot_helper.py")
    print("4. Click on the BoarderframeOS window when the cursor changes")
    print(
        "\nNote: This uses interactive window capture which doesn't require permissions"
    )


def capture_with_delay(delay=3, output_path=None):
    """
    Capture screenshot after a delay (still requires permissions)
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"boarderframe_delayed_{timestamp}.png"

    print(f"\n⏱️  Capturing screenshot in {delay} seconds...")
    print("   Switch to the BoarderframeOS window now!")

    for i in range(delay, 0, -1):
        print(f"   {i}...")
        time.sleep(1)

    # Try to capture
    cmd = ["screencapture", "-x", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0 and os.path.exists(output_path):
        print(f"\n✅ Screenshot saved to: {output_path}")
        return output_path
    else:
        print(f"\n❌ Screenshot failed: {result.stderr}")
        return None


def main():
    print("🖼️  BoarderframeOS Screenshot Helper")
    print("=" * 50)

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_windows()
        elif sys.argv[1] == "delay":
            delay = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            capture_with_delay(delay)
        else:
            output_path = sys.argv[1]
            capture_window_screenshot(output_path)
    else:
        # Default: interactive window capture
        capture_window_screenshot()


if __name__ == "__main__":
    main()
