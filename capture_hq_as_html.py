#!/usr/bin/env python3
"""
Capture Corporate HQ as HTML for viewing
"""
import sys
from datetime import datetime

import requests


def capture_corporate_hq():
    """Capture the Corporate HQ HTML content"""
    try:
        # Get the HTML from Corporate HQ
        response = requests.get("http://localhost:8888")
        if response.status_code == 200:
            # Save the HTML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"corporate_hq_capture_{timestamp}.html"

            with open(filename, "w") as f:
                f.write(response.text)

            print(f"✅ Captured Corporate HQ to: {filename}")
            print(f"   Size: {len(response.text):,} bytes")
            print(f"   Status: {response.status_code}")
            print(f"\nTo view: open {filename}")

            # Also save a simplified version for easier viewing
            simplified = f"corporate_hq_simplified_{timestamp}.html"
            with open(simplified, "w") as f:
                # Add base tag to handle relative URLs
                html = response.text.replace(
                    "<head>", '<head>\n<base href="http://localhost:8888/">'
                )
                f.write(html)

            print(f"\nAlso saved simplified version: {simplified}")
            return filename

    except Exception as e:
        print(f"❌ Error capturing Corporate HQ: {e}")
        return None


if __name__ == "__main__":
    capture_corporate_hq()
