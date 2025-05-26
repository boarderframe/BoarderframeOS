#!/usr/bin/env python3
"""
Agent startup wrapper that handles proper Python path setup
"""
import sys
import os
import importlib.util
import asyncio
from pathlib import Path

async def start_agent(agent_path: str):
    """Start an agent with proper import paths"""
    # Add boarderframeos to Python path
    boarderframeos_path = Path(__file__).parent.absolute()
    if str(boarderframeos_path) not in sys.path:
        sys.path.insert(0, str(boarderframeos_path))
    
    # Load the agent module
    agent_file = Path(agent_path).absolute()
    spec = importlib.util.spec_from_file_location("agent_module", agent_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find and run the main function
    if hasattr(module, 'main'):
        await module.main()
    else:
        print(f"No main function found in {agent_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python start_agent.py <agent_path>")
        sys.exit(1)
    
    asyncio.run(start_agent(sys.argv[1]))