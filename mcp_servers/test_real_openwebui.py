#!/usr/bin/env python3
"""
Test script to make the exact requests that Open WebUI makes that trigger SSE wrapping
"""

import requests
import json
import time

def test_sse_trigger():
    """Test the exact request pattern that triggers SSE"""
    print("🧪 Testing the exact SSE trigger pattern...")
    
    # This is the critical pattern from our logs:
    # Accept: text/event-stream, application/json
    # User-Agent: open-webui/1.0
    # Cache-Control: no-cache
    
    headers = {
        'Accept': 'text/event-stream, application/json',
        'User-Agent': 'open-webui/1.0',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    }
    
    try:
        print("📡 Making request with SSE trigger headers...")
        response = requests.get(
            'http://localhost:9004/search_products?query=milk&location_id=01400403',
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response body (first 500 chars):")
        print(response.text[:500])
        
        # Check if this triggers SSE wrapping
        if 'data:' in response.text and response.text.startswith('data:'):
            print("🚨 SSE WRAPPING DETECTED!")
            
            # Extract the actual JSON from SSE format
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    data_content = line[6:]  # Remove 'data: ' prefix
                    try:
                        json_data = json.loads(data_content)
                        print("✅ Successfully extracted JSON from SSE wrapper:")
                        print(json.dumps(json_data, indent=2)[:300] + "...")
                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse JSON from SSE: {data_content[:100]}")
        else:
            print("✅ No SSE wrapping detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_non_sse_request():
    """Test with pure JSON accept header"""
    print("\n🧪 Testing pure JSON request (should NOT trigger SSE)...")
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'open-webui/1.0',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'http://localhost:9004/search_products?query=milk&location_id=01400403',
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response: {response.text[:200]}...")
        
        if response.text.startswith('data:'):
            print("🚨 Unexpected SSE wrapping with JSON-only Accept header!")
        else:
            print("✅ No SSE wrapping as expected")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_openapi_endpoint():
    """Test the OpenAPI endpoint with SSE headers"""
    print("\n🧪 Testing OpenAPI endpoint (this was seen in our logs)...")
    
    headers = {
        'Accept': 'text/event-stream, application/json',
        'User-Agent': 'open-webui/1.0',
        'Cache-Control': 'no-cache'
    }
    
    try:
        response = requests.get(
            'http://localhost:9004/openapi.json',
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.text.startswith('data:'):
            print("🚨 OpenAPI.json is being SSE-wrapped!")
            print("First few lines:")
            lines = response.text.split('\n')[:5]
            for i, line in enumerate(lines):
                print(f"  {i+1}: {line}")
        else:
            print("✅ OpenAPI.json returned as normal JSON")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_search_with_streaming():
    """Test search endpoint expecting streaming response"""
    print("\n🧪 Testing search endpoint that might stream results...")
    
    headers = {
        'Accept': 'text/event-stream',
        'User-Agent': 'open-webui/1.0',
        'Cache-Control': 'no-cache'
    }
    
    try:
        response = requests.get(
            'http://localhost:9004/search_products?query=milk&location_id=01400403',
            headers=headers,
            stream=True,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        # Read first chunk
        first_chunk = ""
        for chunk in response.iter_content(chunk_size=100, decode_unicode=True):
            if chunk:
                first_chunk = chunk
                break
        
        print(f"First chunk: {first_chunk}")
        
        if first_chunk.startswith('data:'):
            print("🚨 Streaming SSE response detected!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Real Open WebUI Request Analysis")
    print("="*60)
    
    test_sse_trigger()
    test_non_sse_request() 
    test_openapi_endpoint()
    test_search_with_streaming()
    
    print("\n" + "="*60)
    print("🔍 Check the HTTP monitor logs for detailed request analysis")