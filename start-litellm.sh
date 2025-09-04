#!/bin/bash
# LiteLLM Server Startup Script
cd /Users/cosburn/open_webui

# Load environment variables from .env.litellm
if [ -f ".env.litellm" ]; then
    echo "Loading environment variables from .env.litellm"
    set -a  # automatically export all variables
    source .env.litellm
    set +a  # turn off automatic export
fi

# Activate virtual environment and start LiteLLM
source litellm_venv/bin/activate
litellm --config litellm_config.yaml --port 4001 --host 0.0.0.0