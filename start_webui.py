#!/usr/bin/env python3
import sys
import os

# Add the backend directory to Python path
backend_dir = "/Users/cosburn/open_webui/open-webui/backend"
sys.path.insert(0, backend_dir)

# Set environment variables
os.environ["ENV"] = "dev"
os.environ["HOST"] = "0.0.0.0"
os.environ["PORT"] = "8080"
os.environ["DATA_DIR"] = f"{backend_dir}/data"

try:
    import uvicorn
    print("Starting Open WebUI...")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Run the app
    uvicorn.run(
        "open_webui.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        access_log=True
    )
except Exception as e:
    print(f"Error starting Open WebUI: {e}")
    import traceback
    traceback.print_exc()