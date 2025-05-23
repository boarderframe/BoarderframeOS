#!/bin/bash
# Script to start Solomon agent with chat server interface

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs/agents

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    # Check if .env file exists
    if [ -f ".env" ]; then
        echo "🔑 Loading API key from .env file..."
        source .env
    else
        echo "⚠️  Warning: ANTHROPIC_API_KEY not found in environment or .env file."
        echo "Creating .env file template. Please edit it with your API key."
        echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
        echo "✏️  Created .env file. Please add your Anthropic API key and run this script again."
        exit 1
    fi
fi

# Start the Solomon systems
echo "🧠 Starting Solomon agent and chat server..."
/Users/cosburn/miniconda3/bin/python start_solomon_combined.py
