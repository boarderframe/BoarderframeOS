#!/usr/bin/env python3
"""
Agent Cortex Simple Launcher - Minimal launcher without async conflicts
Designed to work reliably when launched from subprocess in async contexts
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    """Simple launcher that avoids async conflicts"""
    # Set environment to prevent Flask debug mode issues
    # Don't set WERKZEUG_RUN_MAIN as it expects a server FD
    os.environ["FLASK_DEBUG"] = "0"

    # Clear any problematic environment variables
    os.environ.pop("WERKZEUG_RUN_MAIN", None)
    os.environ.pop("WERKZEUG_SERVER_FD", None)

    # Import and create the UI without any async initialization
    from ui.agent_cortex_management import AgentCortexManagementUI

    # Create UI instance
    ui = AgentCortexManagementUI()

    # Note: We're NOT initializing Agent Cortex here
    # It will be initialized lazily on first request
    print("🧠 Starting Agent Cortex Management UI (Simple Launcher)")
    print("📍 Initialization will happen on first request")

    # Add a small delay to ensure clean startup
    import time

    time.sleep(1)

    # Run Flask app directly without debug mode
    print(f"🚀 Agent Cortex UI starting on http://0.0.0.0:{ui.port}")
    ui.app.run(host="0.0.0.0", port=ui.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
