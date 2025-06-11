#!/usr/bin/env python3
"""
Working Agent Cortex Panel using threading
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template

# Create Flask app
app = Flask(__name__, template_folder="ui/templates", static_folder="ui/static")

# Load data
agent_configs = {}
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


@app.route("/")
def index():
    return render_template("agent_cortex_panel.html")


@app.route("/api/cortex/overview")
def get_overview():
    return jsonify(
        {
            "total_agents": 5,
            "active_providers": 3,
            "departments": 24,
            "model_assignments": 5,
            "cortex_status": "operational",
        }
    )


@app.route("/api/cortex/providers")
def get_providers():
    return jsonify(llm_providers)


@app.route("/api/cortex/agents")
def get_agents():
    agents = [
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
        {
            "name": "Eve",
            "title": "Agent Evolver",
            "department": "Development",
            "tier": "specialist",
            "provider": "anthropic",
            "model": "claude-4-sonnet-20250514",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        {
            "name": "Bezalel",
            "title": "Master Programmer",
            "department": "Development",
            "tier": "specialist",
            "provider": "anthropic",
            "model": "claude-4-sonnet-20250514",
            "temperature": 0.5,
            "max_tokens": 3000,
        },
    ]
    return jsonify(agents)


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
            }
        }
    )


def run_server():
    """Run Flask in a separate thread"""
    from werkzeug.serving import make_server

    server = make_server("localhost", 8890, app, threaded=True)
    server.serve_forever()


if __name__ == "__main__":
    print("\n🚀 Starting Agent Cortex Panel (Working Version)...")
    print("=" * 60)

    # Start server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait a moment for server to start
    time.sleep(1)

    print("🌐 Server running at: http://localhost:8890")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)

    # Test the server
    import requests

    try:
        response = requests.get("http://localhost:8890/api/cortex/overview")
        if response.status_code == 200:
            print("\n✅ Server is responding correctly!")
            print(f"   API test: {response.json()}")
        else:
            print("\n❌ Server returned error:", response.status_code)
    except Exception as e:
        print(f"\n❌ Could not connect to server: {e}")

    print("\n📌 If you can't access http://localhost:8890, try:")
    print("   1. Check firewall settings")
    print("   2. Try http://127.0.0.1:8890")
    print("   3. Check System Settings > Privacy & Security")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
