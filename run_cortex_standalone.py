#!/usr/bin/env python3
"""
Standalone Agent Cortex Panel
Runs completely independently
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Clear any werkzeug environment variables
for key in list(os.environ.keys()):
    if key.startswith("WERKZEUG"):
        del os.environ[key]

import asyncio
import json
from pathlib import Path

from flask import Flask, jsonify, render_template

app = Flask(__name__, template_folder="ui/templates", static_folder="ui/static")

# Global data
agent_configs = {}
llm_providers = {}
model_assignments = {}
department_structure = {}


@app.route("/")
def index():
    return render_template("agent_cortex_panel.html")


@app.route("/api/cortex/overview")
def get_overview():
    return jsonify(
        {
            "total_agents": len(agent_configs),
            "active_providers": 3,
            "departments": 24,
            "model_assignments": len(model_assignments),
            "cortex_status": "operational",
        }
    )


@app.route("/api/cortex/providers")
def get_providers():
    return jsonify(llm_providers)


@app.route("/api/cortex/agents")
def get_agents():
    agents = []

    # Add some test agents
    test_agents = [
        {
            "name": "David",
            "title": "CEO",
            "department": "Executive",
            "tier": "executive",
            "provider": "anthropic",
            "model": "claude-opus-4-20250514",
            "temperature": 0.7,
            "max_tokens": 4000,
        },
        {
            "name": "Solomon",
            "title": "Chief of Staff",
            "department": "Executive",
            "tier": "executive",
            "provider": "anthropic",
            "model": "claude-opus-4-20250514",
            "temperature": 0.3,
            "max_tokens": 4000,
        },
        {
            "name": "Adam",
            "title": "Agent Creator",
            "department": "Development",
            "tier": "specialist",
            "provider": "anthropic",
            "model": "claude-4-sonnet-20250514",
            "temperature": 0.8,
            "max_tokens": 2000,
        },
    ]

    return jsonify(test_agents)


@app.route("/api/cortex/tiers")
def get_tiers():
    return jsonify(
        {
            "executive": {
                "default_provider": "anthropic",
                "default_model": "claude-opus-4-20250514",
                "budget_provider": "anthropic",
                "budget_model": "claude-4-sonnet-20250514",
                "local_provider": "ollama",
                "local_model": "llama3.2",
                "max_cost_per_request": 0.1,
                "quality_threshold": 0.95,
            },
            "specialist": {
                "default_provider": "anthropic",
                "default_model": "claude-4-sonnet-20250514",
                "budget_provider": "openai",
                "budget_model": "gpt-4o-mini",
                "local_provider": "ollama",
                "local_model": "llama3.2",
                "max_cost_per_request": 0.05,
                "quality_threshold": 0.85,
            },
        }
    )


async def load_data():
    """Load configuration data"""
    global agent_configs, llm_providers, department_structure, model_assignments

    # Load configs
    config_path = Path("configs/agents")
    if config_path.exists():
        for config_file in config_path.glob("*.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    agent_configs[config["name"]] = config
            except:
                pass

    # Load department structure
    dept_path = Path("departments/boarderframeos-departments.json")
    if dept_path.exists():
        try:
            with open(dept_path, "r") as f:
                department_structure = json.load(f)
        except:
            pass

    # Default providers
    llm_providers = {
        "anthropic": {
            "provider_type": "anthropic",
            "models": [
                "claude-opus-4-20250514",
                "claude-4-sonnet-20250514",
                "claude-3-haiku-20240307",
            ],
            "is_active": True,
        },
        "openai": {
            "provider_type": "openai",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "is_active": True,
        },
        "ollama": {
            "provider_type": "ollama",
            "base_url": "http://localhost:11434",
            "models": ["llama3.2", "mistral", "phi"],
            "is_active": True,
        },
    }

    print("✅ Data loaded")


def main():
    print("\n🚀 Starting Standalone Agent Cortex Panel...")
    print("=" * 60)

    # Load data
    asyncio.run(load_data())

    print("\n🌐 Starting server on http://localhost:8890")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)

    # Run server
    app.run(host="127.0.0.1", port=8890, debug=False)


if __name__ == "__main__":
    main()
