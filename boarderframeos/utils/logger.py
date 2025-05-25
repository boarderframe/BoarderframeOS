"""
Simple logging setup for BoarderframeOS
"""
import logging
import sys
from pathlib import Path

def setup_logging(level=logging.INFO):
    """Setup basic logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "boarderframeos.log")
        ]
    )
    
    return logging.getLogger("boarderframeos")