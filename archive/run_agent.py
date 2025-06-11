#!/usr/bin/env python3
"""
Universal agent runner for BoarderframeOS
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add boarderframeos to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
    print(
        f"Loaded environment variables. API key present: {'ANTHROPIC_API_KEY' in os.environ}"
    )
except ImportError:
    print("python-dotenv not installed, trying to load .env manually")
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
        print(
            f"Manually loaded .env. API key present: {'ANTHROPIC_API_KEY' in os.environ}"
        )
except Exception as e:
    print(f"Error loading environment: {e}")


async def run_agent(agent_name: str):
    """Run a specific agent"""
    try:
        if agent_name == "solomon":
            from agents.solomon.solomon import Solomon

            agent = Solomon()
        elif agent_name == "david":
            from agents.david.david import David

            agent = David()
        elif agent_name == "adam":
            from agents.primordials.adam import Adam

            agent = Adam()
        elif agent_name == "eve":
            from agents.primordials.eve import Eve

            agent = Eve()
        elif agent_name == "bezalel":
            from agents.primordials.bezalel import Bezalel

            agent = Bezalel()
        else:
            print(f"Unknown agent: {agent_name}")
            return

        print(f"Starting {agent_name} agent...")

        # Run the agent
        try:
            await agent.run()
        except KeyboardInterrupt:
            print(f"\nShutting down {agent_name}...")
            await agent.terminate()

    except Exception as e:
        print(f"Failed to run {agent_name}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a BoarderframeOS agent")
    parser.add_argument(
        "agent",
        choices=["solomon", "david", "adam", "eve", "bezalel"],
        help="Agent to run",
    )
    args = parser.parse_args()

    asyncio.run(run_agent(args.agent))
