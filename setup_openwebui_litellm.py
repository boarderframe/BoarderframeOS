#!/usr/bin/env python3
"""
Script to configure Open WebUI to connect to LiteLLM proxy
"""
import requests
import json

# Configuration
OPEN_WEBUI_URL = "http://localhost:8080"
LITELLM_URL = "http://localhost:4000"
LITELLM_API_KEY = "litellm-master-key-2024"

def configure_openai_api():
    """Configure Open WebUI to use LiteLLM as OpenAI API"""
    
    # Configuration data
    config_data = {
        "OPENAI_API_BASE_URLS": [LITELLM_URL],
        "OPENAI_API_KEYS": [LITELLM_API_KEY],
        "ENABLE_OPENAI_API": True
    }
    
    print("Configuring Open WebUI to connect to LiteLLM...")
    print(f"LiteLLM URL: {LITELLM_URL}")
    print(f"Open WebUI URL: {OPEN_WEBUI_URL}")
    
    # Try to configure via API (this might require authentication)
    try:
        for key, value in config_data.items():
            response = requests.post(
                f"{OPEN_WEBUI_URL}/api/config/{key.lower()}",
                json={"value": value},
                timeout=10
            )
            if response.status_code == 200:
                print(f"✅ Successfully configured {key}")
            else:
                print(f"❌ Failed to configure {key}: {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error configuring via API: {e}")
    
    print("\nManual configuration required:")
    print("1. Go to http://localhost:5173")
    print("2. Sign up or log in as admin")
    print("3. Go to Settings > Admin Panel > General")
    print("4. Configure OpenAI API:")
    print(f"   - API Base URL: {LITELLM_URL}")
    print(f"   - API Key: {LITELLM_API_KEY}")
    print("5. Save settings")
    print("6. Refresh models in the interface")

if __name__ == "__main__":
    configure_openai_api()