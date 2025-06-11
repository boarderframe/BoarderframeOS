#!/usr/bin/env python3
"""
Start PostgreSQL Database MCP Server
Launches the enhanced PostgreSQL-based database server
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("postgres_server_launcher")

def main():
    """Launch PostgreSQL database MCP server"""

    # Check if environment is set up
    if not os.getenv("DATABASE_URL"):
        logger.warning("DATABASE_URL not set, using default")
        os.environ["DATABASE_URL"] = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"

    if not os.getenv("REDIS_URL"):
        logger.warning("REDIS_URL not set, using default")
        os.environ["REDIS_URL"] = "redis://localhost:6379"

    # Launch server
    server_script = Path(__file__).parent / "database_server_postgres.py"

    logger.info("Starting PostgreSQL Database MCP Server...")
    logger.info(f"Database: {os.getenv('DATABASE_URL')}")
    logger.info(f"Redis: {os.getenv('REDIS_URL')}")
    logger.info("Server will be available at http://localhost:8000")

    try:
        # Run with different port to avoid conflict with SQLite server
        subprocess.run([
            sys.executable, str(server_script),
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"Server failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
