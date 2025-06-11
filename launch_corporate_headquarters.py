#!/usr/bin/env python3
"""
Simple launcher for BoarderframeOS Corporate Headquarters
"""
import subprocess
import sys
from pathlib import Path


def launch_corporate_headquarters():
    """Launch the BoarderframeOS Corporate Headquarters"""
    headquarters_path = Path(__file__).parent / "corporate_headquarters.py"

    print("🚀 Launching BoarderframeOS Corporate Headquarters...")
    print(f"📂 Corporate Headquarters file: {headquarters_path}")
    print("🌐 Will open at: http://localhost:8888")
    print("🔄 Corporate Headquarters will auto-refresh every 30 seconds")
    print("💬 Chat with Solomon, David, and Adam agents")
    print("\n⚠️  If you encounter errors, check the terminal output below:")
    print("="*60)

    try:
        # Launch Corporate Headquarters
        subprocess.run([sys.executable, str(headquarters_path)])
    except KeyboardInterrupt:
        print("\n👋 BoarderframeOS Corporate Headquarters shutdown requested by user")
    except Exception as e:
        print(f"\n❌ Error launching BoarderframeOS Corporate Headquarters: {e}")

if __name__ == "__main__":
    launch_corporate_headquarters()
