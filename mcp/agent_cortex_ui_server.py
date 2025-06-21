#!/usr/bin/env python3
"""
Agent Cortex UI Server - MCP-style server wrapper for Agent Cortex Management UI
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    # Import the UI
    from ui.agent_cortex_management import AgentCortexManagementUI

    # Create and run the UI
    print("🧠 Starting Agent Cortex Management UI Server")
    ui = AgentCortexManagementUI()
    print(f"📍 Agent Cortex UI running on http://0.0.0.0:{ui.port}")

    # Run the Flask app
    ui.app.run(host="0.0.0.0", port=ui.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
