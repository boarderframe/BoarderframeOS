#!/usr/bin/env python3
"""
Test script to verify MCP server endpoints return clean JSON responses
without SSE/streaming data: prefixes
"""

import json
import sys
import httpx
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:9004"
FIXED_URL = "http://localhost:9005"

def check_json_response(url: str, endpoint: str, params: Dict[str, Any] = None) -> Tuple[bool, str, Any]:
    """
    Check if an endpoint returns clean JSON without SSE/streaming artifacts
    Returns: (is_clean, message, response_data)
    """
    full_url = f"{url}{endpoint}"
    
    try:
        with httpx.Client() as client:
            response = client.get(full_url, params=params, timeout=5.0)
            
            # Check status code
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}", None
            
            # Check content type
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return False, f"Wrong content-type: {content_type}", None
            
            # Check for SSE prefix in raw text
            raw_text = response.text
            if raw_text.startswith("data: "):
                return False, "Response has SSE 'data: ' prefix", None
            
            # Try to parse JSON
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON: {e}", None
            
            # Check for SSE artifacts in parsed data
            json_str = json.dumps(data)
            if "data: " in json_str and "llm_response" not in json_str:
                # Allow "data: " in llm_response field as it might be part of the content
                return False, "Found 'data: ' in JSON content", data
            
            return True, "Clean JSON response", data
            
    except httpx.TimeoutException:
        return False, "Request timeout", None
    except Exception as e:
        return False, f"Error: {e}", None

def test_endpoints(server_name: str, base_url: str) -> Dict[str, Any]:
    """Test all endpoints on a server"""
    
    print(f"\n{'='*60}")
    print(f"Testing {server_name} at {base_url}")
    print(f"{'='*60}")
    
    # Define test cases
    test_cases = [
        {
            "name": "Health Check",
            "endpoint": "/health",
            "params": None
        },
        {
            "name": "Test JSON",
            "endpoint": "/test/json",
            "params": None
        },
        {
            "name": "LLM-Ready Search (milk)",
            "endpoint": "/products/search/llm-ready",
            "params": {"term": "milk", "limit": 2}
        },
        {
            "name": "LLM-Ready Search (bread)",
            "endpoint": "/products/search/llm-ready",
            "params": {"term": "bread", "limit": 1}
        },
        {
            "name": "LLM-Ready Search (empty)",
            "endpoint": "/products/search/llm-ready",
            "params": {"term": "xyz123notfound", "limit": 1}
        }
    ]
    
    results = []
    all_clean = True
    
    for test in test_cases:
        is_clean, message, data = check_json_response(
            base_url,
            test["endpoint"],
            test["params"]
        )
        
        # Format params for display
        params_str = ""
        if test["params"]:
            params_str = "?" + "&".join([f"{k}={v}" for k, v in test["params"].items()])
        
        status = "✅ PASS" if is_clean else "❌ FAIL"
        print(f"\n{status} {test['name']}")
        print(f"  Endpoint: {test['endpoint']}{params_str}")
        print(f"  Result: {message}")
        
        if is_clean and data:
            # Show sample of response structure
            keys = list(data.keys())[:5]
            print(f"  Response keys: {keys}")
            
            # Check for specific fields
            if "llm_response" in data:
                print(f"  Has llm_response: Yes ({len(data['llm_response'])} chars)")
            if "artifact_available" in data:
                print(f"  Artifact available: {data['artifact_available']}")
        
        results.append({
            "test": test["name"],
            "endpoint": test["endpoint"],
            "params": test["params"],
            "passed": is_clean,
            "message": message
        })
        
        if not is_clean:
            all_clean = False
    
    return {
        "server": server_name,
        "url": base_url,
        "timestamp": datetime.now().isoformat(),
        "all_tests_passed": all_clean,
        "results": results
    }

def main():
    """Main test runner"""
    
    print("\n" + "="*60)
    print("MCP Server JSON Response Testing")
    print("Testing for clean JSON without SSE/streaming artifacts")
    print("="*60)
    
    # Test main server
    main_results = test_endpoints("Main Kroger MCP Server", BASE_URL)
    
    # Test fixed server if running
    fixed_results = None
    try:
        with httpx.Client() as client:
            response = client.get(f"{FIXED_URL}/health", timeout=1.0)
            if response.status_code == 200:
                fixed_results = test_endpoints("Fixed Test Server", FIXED_URL)
    except:
        print(f"\nFixed test server not running at {FIXED_URL}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    print(f"\nMain Server ({BASE_URL}):")
    print(f"  All tests passed: {main_results['all_tests_passed']}")
    passed = sum(1 for r in main_results['results'] if r['passed'])
    total = len(main_results['results'])
    print(f"  Tests: {passed}/{total} passed")
    
    if fixed_results:
        print(f"\nFixed Server ({FIXED_URL}):")
        print(f"  All tests passed: {fixed_results['all_tests_passed']}")
        passed = sum(1 for r in fixed_results['results'] if r['passed'])
        total = len(fixed_results['results'])
        print(f"  Tests: {passed}/{total} passed")
    
    # Save results
    results_file = "json_response_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "main_server": main_results,
            "fixed_server": fixed_results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    # Exit code
    exit_code = 0 if main_results['all_tests_passed'] else 1
    if fixed_results and not fixed_results['all_tests_passed']:
        exit_code = 1
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())