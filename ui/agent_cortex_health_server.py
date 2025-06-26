#!/usr/bin/env python3
"""
Simple health check server for Agent Cortex
Provides a lightweight health endpoint without full initialization
"""

import logging
import sys
from pathlib import Path

from flask import Flask, jsonify

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Simple Flask app for health checks
app = Flask(__name__)

# Configure minimal logging
logging.basicConfig(level=logging.WARNING)


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "Agent Cortex",
            "port": 8889,
            "note": "Full UI initialization happens on first request",
        }
    )


@app.route("/")
def index():
    """Root endpoint"""
    return """
    <html>
    <head>
        <title>Agent Cortex</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #1a1a1a;
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                padding: 2rem;
                background: #2a2a2a;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }
            h1 { color: #6366f1; }
            .status {
                color: #10b981;
                font-size: 1.2rem;
                margin: 1rem 0;
            }
            .note {
                color: #888;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 Agent Cortex</h1>
            <div class="status">✅ Service Running</div>
            <p>Intelligent model selection and orchestration system</p>
            <div class="note">Full UI loads on demand to optimize startup time</div>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    print("🧠 Starting Agent Cortex Health Server on port 8889")
    app.run(host="0.0.0.0", port=8889, debug=False)
