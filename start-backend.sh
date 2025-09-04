#!/bin/bash
# Open WebUI Backend Startup Script
cd /Users/cosburn/open_webui/open-webui/backend
source venv/bin/activate
export CORS_ALLOW_ORIGIN="http://localhost:5173"
uvicorn open_webui.main:app --host 0.0.0.0 --port 8080 --reload