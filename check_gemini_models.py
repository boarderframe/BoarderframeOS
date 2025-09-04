#!/usr/bin/env python3
"""
Script to check available Google Gemini models
"""
import os
import json
from datetime import datetime

def load_env_vars():
    """Load environment variables from .env.litellm file"""
    env_file = "/Users/cosburn/open_webui/.env.litellm"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def check_gemini_models():
    """Check available Google Gemini models"""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            return {"error": "GOOGLE_API_KEY not found"}
        
        genai.configure(api_key=api_key)
        
        # List all available models
        models = []
        for model in genai.list_models():
            # Filter for Gemini models that support generateContent
            if 'generateContent' in model.supported_generation_methods:
                models.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                    "supported_methods": model.supported_generation_methods,
                    "input_token_limit": getattr(model, 'input_token_limit', None),
                    "output_token_limit": getattr(model, 'output_token_limit', None),
                    "temperature": getattr(model, 'temperature', None),
                    "top_p": getattr(model, 'top_p', None),
                    "top_k": getattr(model, 'top_k', None)
                })
        
        return {
            "provider": "google_gemini",
            "count": len(models),
            "models": sorted(models, key=lambda x: x["name"])
        }
        
    except ImportError:
        return {"error": "google-generativeai package not installed. Install with: pip install google-generativeai"}
    except Exception as e:
        return {"error": f"Google Gemini API error: {str(e)}"}

def check_vertex_ai_models():
    """Check available models via Google Cloud Vertex AI"""
    try:
        from google.cloud import aiplatform
        
        # Try to initialize Vertex AI
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'your-project-id')
        location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        aiplatform.init(project=project_id, location=location)
        
        # Note: This would require proper GCP credentials and project setup
        # For now, just return info about common Vertex AI Gemini models
        vertex_models = [
            {
                "name": "gemini-1.5-pro",
                "display_name": "Gemini 1.5 Pro (Vertex AI)",
                "description": "Gemini 1.5 Pro via Vertex AI",
                "method": "vertex_ai"
            },
            {
                "name": "gemini-1.5-flash",
                "display_name": "Gemini 1.5 Flash (Vertex AI)", 
                "description": "Gemini 1.5 Flash via Vertex AI",
                "method": "vertex_ai"
            },
            {
                "name": "gemini-1.0-pro",
                "display_name": "Gemini 1.0 Pro (Vertex AI)",
                "description": "Gemini 1.0 Pro via Vertex AI",
                "method": "vertex_ai"
            }
        ]
        
        return {
            "provider": "google_vertex_ai",
            "note": "Requires GCP project setup and credentials",
            "count": len(vertex_models),
            "models": vertex_models
        }
        
    except ImportError:
        return {"error": "google-cloud-aiplatform package not installed"}
    except Exception as e:
        return {"note": f"Vertex AI requires GCP setup: {str(e)}"}

def main():
    """Main function to check Google models"""
    print("Checking Google Gemini models...")
    
    # Load environment variables
    load_env_vars()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "providers": {}
    }
    
    # Check Gemini API
    print("Checking Gemini API models...")
    results["providers"]["gemini_api"] = check_gemini_models()
    
    # Check Vertex AI
    print("Checking Vertex AI models...")
    results["providers"]["vertex_ai"] = check_vertex_ai_models()
    
    # Save results
    output_file = "/Users/cosburn/open_webui/gemini_models_check.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Print summary
    print("\n=== GEMINI MODELS SUMMARY ===")
    for provider, data in results["providers"].items():
        if "error" in data:
            print(f"{provider.upper()}: ERROR - {data['error']}")
        elif "note" in data and "error" not in data:
            print(f"{provider.upper()}: {data.get('count', 0)} models found")
            print(f"  Note: {data['note']}")
        else:
            print(f"{provider.upper()}: {data['count']} models found")
            
        if "models" in data:
            for model in data["models"][:5]:  # Show first 5
                name = model.get("name", "").replace("models/", "")
                display = model.get("display_name", name)
                print(f"    - {name} ({display})")
            if len(data["models"]) > 5:
                print(f"    ... and {len(data['models']) - 5} more")

if __name__ == "__main__":
    main()