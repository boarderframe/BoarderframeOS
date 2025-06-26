#!/usr/bin/env python3
"""
BoarderframeOS Logging Setup
Import this module to configure logging for any component
"""

import logging
import logging.config
import json
import os

def setup_logging(component_name="boarderframeos"):
    """Setup logging for a component"""
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "configs/monitoring/logging_config.json"
    )
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        logging.config.dictConfig(config)
        logger = logging.getLogger(f"boarderframeos.{component_name}")
    else:
        # Fallback to basic config
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(f"boarderframeos.{component_name}")
        
    return logger

# Convenience functions
def get_agent_logger(agent_name):
    """Get logger for an agent"""
    return setup_logging(f"agents.{agent_name}")

def get_api_logger(endpoint_name):
    """Get logger for an API endpoint"""
    return setup_logging(f"api.{endpoint_name}")

def get_error_logger():
    """Get error logger"""
    return setup_logging("errors")
