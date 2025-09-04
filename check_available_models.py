#!/usr/bin/env python3
"""
Script to check available models from OpenAI and Anthropic APIs
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
    
def check_openai_models():
    """Check available OpenAI models"""
    try:
        import openai
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return {"error": "OPENAI_API_KEY not found"}
        
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()
        
        model_list = []
        for model in models.data:
            model_list.append({
                "id": model.id,
                "created": model.created,
                "owned_by": model.owned_by
            })
        
        return {
            "provider": "openai",
            "count": len(model_list),
            "models": sorted(model_list, key=lambda x: x["id"])
        }
        
    except Exception as e:
        return {"error": f"OpenAI API error: {str(e)}"}

def check_anthropic_models():
    """Check available Anthropic models"""
    try:
        import anthropic
        
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not found"}
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test common Claude model names to see which ones are available
        test_models = [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229", 
            "claude-3-opus-20240229",
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022",
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-opus-4-20250805"
        ]
        
        available_models = []
        for model in test_models:
            try:
                # Try a minimal completion to test if model exists
                response = client.messages.create(
                    model=model,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                available_models.append({
                    "id": model,
                    "status": "available",
                    "tested": True
                })
            except anthropic.NotFoundError:
                print(f"Model not found: {model}")
            except Exception as e:
                available_models.append({
                    "id": model,
                    "status": "error",
                    "error": str(e),
                    "tested": True
                })
        
        return {
            "provider": "anthropic", 
            "count": len(available_models),
            "models": available_models,
            "note": "Tested common Claude model names"
        }
        
    except Exception as e:
        return {"error": f"Anthropic API error: {str(e)}"}

def main():
    """Main function to check all providers"""
    print("Checking available models...")
    
    # Load environment variables
    load_env_vars()
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "providers": {}
    }
    
    # Check OpenAI
    print("Checking OpenAI models...")
    results["providers"]["openai"] = check_openai_models()
    
    # Check Anthropic
    print("Checking Anthropic models...")
    results["providers"]["anthropic"] = check_anthropic_models()
    
    # Save results
    output_file = "/Users/cosburn/open_webui/available_models_check.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    for provider, data in results["providers"].items():
        if "error" in data:
            print(f"{provider.upper()}: ERROR - {data['error']}")
        else:
            print(f"{provider.upper()}: {data['count']} models found")
            if provider == "anthropic":
                available = [m for m in data["models"] if m["status"] == "available"]
                print(f"  Available Claude models: {len(available)}")
                for model in available:
                    print(f"    - {model['id']}")

if __name__ == "__main__":
    main()