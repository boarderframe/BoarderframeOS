#!/usr/bin/env python3
"""
Agent Cortex Robust Launcher - Enhanced launcher with retry logic and better error handling
Designed to work reliably when launched from subprocess in async contexts
"""

import logging
import os
import sys
import time
from pathlib import Path

# Set up logging to file
log_file = "/tmp/agent_cortex_launcher.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Ensure proper environment setup"""
    logger.info("Setting up environment for Agent Cortex")

    # Add project root to Python path
    project_root = str(Path(__file__).parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added {project_root} to Python path")

    # Set environment to prevent Flask debug mode issues
    os.environ["FLASK_DEBUG"] = "0"

    # Clear ALL problematic Werkzeug environment variables
    werkzeug_vars = [
        "WERKZEUG_RUN_MAIN",
        "WERKZEUG_SERVER_FD",
        "WERKZEUG_RESTART_TRIGGER",
    ]
    for var in werkzeug_vars:
        if var in os.environ:
            logger.info(f"Removing {var} from environment")
            os.environ.pop(var, None)

    logger.info("Environment setup complete")
    return project_root


def verify_imports():
    """Verify all required imports are available"""
    logger.info("Verifying imports...")

    try:
        # Test core imports
        import core

        logger.info("✓ core module found")

        import ui

        logger.info("✓ ui module found")

        # Test specific imports
        from core.agent_cortex import get_agent_cortex_instance

        logger.info("✓ agent_cortex module found")

        from ui.agent_cortex_management import AgentCortexManagementUI

        logger.info("✓ agent_cortex_management module found")

        return True

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False


def start_ui_with_retries(max_retries=3):
    """Start the UI with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Starting Agent Cortex UI (attempt {attempt + 1}/{max_retries})"
            )

            # Import and create the UI
            from ui.agent_cortex_management import AgentCortexManagementUI

            # Create UI instance
            ui = AgentCortexManagementUI()

            logger.info("🧠 Agent Cortex Management UI created successfully")
            logger.info("📍 Initialization will happen on first request")

            # Small delay to ensure clean startup
            time.sleep(2)

            # Run Flask app
            logger.info(f"🚀 Starting Flask app on http://0.0.0.0:{ui.port}")
            ui.app.run(host="0.0.0.0", port=ui.port, debug=False, use_reloader=False)

            # If we get here, the app exited normally
            logger.info("Agent Cortex UI exited normally")
            return True

        except Exception as e:
            logger.error(f"Failed to start UI on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info("Waiting before retry...")
                time.sleep(5)
            else:
                logger.error("All retry attempts failed")
                raise


def main():
    """Main entry point with robust error handling"""
    logger.info("=" * 60)
    logger.info("Agent Cortex Robust Launcher Starting")
    logger.info("=" * 60)

    try:
        # Setup environment
        project_root = setup_environment()
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Project root: {project_root}")

        # Verify imports before proceeding
        if not verify_imports():
            logger.error("Import verification failed")

            # Try to fix by ensuring we're in the right directory
            os.chdir(project_root)
            logger.info(f"Changed directory to {project_root}")

            # Try imports again
            if not verify_imports():
                logger.error("Import verification failed after directory change")
                sys.exit(1)

        # Start the UI with retries
        start_ui_with_retries()

    except Exception as e:
        logger.error(f"Fatal error in launcher: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
