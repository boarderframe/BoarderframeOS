#!/usr/bin/env python3
"""
Launch Enhanced Corporate HQ with all enhanced agents
Quick launcher for the enhanced UI
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    print(f"✓ Loaded environment from: {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed, trying to load .env manually")
    # Manual .env loading as fallback
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value


def main():
    """Launch enhanced Corporate HQ"""
    print("=" * 60)
    print("🚀 Launching Enhanced Corporate HQ")
    print("=" * 60)

    # Debug: Show environment status
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"\n✓ Claude API key found (starts with: {api_key[:15]}...)")
    else:
        print("\n❌ ANTHROPIC_API_KEY not found in environment")
        print("\nTroubleshooting steps:")
        print("1. Make sure .env file exists in BoarderframeOS directory")
        print("2. Check that .env contains: ANTHROPIC_API_KEY=your-key-here")
        print("3. Try running: source .env (on Mac/Linux)")
        print("4. Or manually export: export ANTHROPIC_API_KEY='your-key-here'")
        return

    print("✓ Enhanced agents ready")
    print("\nStarting server...")

    # Import and run the enhanced HQ
    try:
        from enhanced_corporate_hq import main as run_hq

        run_hq()
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install fastapi uvicorn httpx")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutdown complete.")
