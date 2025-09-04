#!/usr/bin/env python3
"""
Comprehensive Server Diagnostics Test
Tests server response format to identify JSON parsing issues
"""

import requests
import json
import time
import sys
from urllib.parse import urlencode

def test_server_diagnostics():
    """Run comprehensive server diagnostics"""
    
    base_url = "http://localhost:9004"
    
    print("=" * 80)
    print("COMPREHENSIVE SERVER DIAGNOSTICS")
    print("=" * 80)
    
    # Test 1: Basic connectivity and headers
    print("\n1. TESTING BASIC CONNECTIVITY AND HEADERS")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health endpoint status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Content-Type: {response.headers.get('content-type', 'NOT SET')}")
        print(f"Content-Length: {response.headers.get('content-length', 'NOT SET')}")
        print(f"Transfer-Encoding: {response.headers.get('transfer-encoding', 'NOT SET')}")
        print(f"Raw response: {repr(response.text[:200])}")
        
        try:
            json_data = response.json()
            print(f"JSON parsing: SUCCESS - {type(json_data)}")
        except Exception as e:
            print(f"JSON parsing: FAILED - {e}")
            
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test 2: Product search endpoint
    print("\n2. TESTING PRODUCT SEARCH ENDPOINT")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/products/search", params={"term": "milk"})
        print(f"Product search status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Content-Type: {response.headers.get('content-type', 'NOT SET')}")
        print(f"Content-Length: {response.headers.get('content-length', 'NOT SET')}")
        print(f"Transfer-Encoding: {response.headers.get('transfer-encoding', 'NOT SET')}")
        print(f"Response size: {len(response.text)} characters")
        print(f"First 200 chars: {repr(response.text[:200])}")
        
        try:
            json_data = response.json()
            print(f"JSON parsing: SUCCESS - {type(json_data)}")
            if isinstance(json_data, dict):
                print(f"Response keys: {list(json_data.keys())}")
        except Exception as e:
            print(f"JSON parsing: FAILED - {e}")
            print(f"Response type appears to be: {type(response.text)}")
            
    except Exception as e:
        print(f"Product search failed: {e}")
    
    # Test 3: Check for streaming responses
    print("\n3. TESTING FOR STREAMING RESPONSES")
    print("-" * 50)
    
    try:
        response = requests.get(f"{base_url}/products/search", params={"term": "bread"}, stream=True)
        print(f"Streaming request status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        # Check if response is streamed
        chunks = []
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            if chunk:
                chunks.append(chunk)
                if len(chunks) > 5:  # Limit to first 5 chunks
                    break
        
        print(f"Number of chunks received: {len(chunks)}")
        if chunks:
            print(f"First chunk: {repr(chunks[0][:200])}")
            full_content = ''.join(chunks)
            try:
                json_data = json.loads(full_content)
                print(f"Streaming JSON parsing: SUCCESS")
            except Exception as e:
                print(f"Streaming JSON parsing: FAILED - {e}")
        
    except Exception as e:
        print(f"Streaming test failed: {e}")
    
    # Test 4: Raw socket test
    print("\n4. TESTING RAW HTTP REQUEST")
    print("-" * 50)
    
    try:
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 9004))
        
        request = (
            "GET /health HTTP/1.1\r\n"
            "Host: localhost:9004\r\n"
            "Connection: close\r\n"
            "\r\n"
        )
        
        sock.send(request.encode())
        response = sock.recv(4096).decode()
        sock.close()
        
        print(f"Raw HTTP response:")
        print(repr(response))
        
        # Parse HTTP response
        if '\r\n\r\n' in response:
            headers_part, body_part = response.split('\r\n\r\n', 1)
            print(f"Headers: {repr(headers_part)}")
            print(f"Body: {repr(body_part)}")
            
            try:
                json_data = json.loads(body_part)
                print(f"Raw JSON parsing: SUCCESS")
            except Exception as e:
                print(f"Raw JSON parsing: FAILED - {e}")
        
    except Exception as e:
        print(f"Raw socket test failed: {e}")
    
    # Test 5: Different endpoints
    print("\n5. TESTING MULTIPLE ENDPOINTS")
    print("-" * 50)
    
    endpoints_to_test = [
        "/config",
        "/locations/search", 
        "/products/search/compact?term=apple&limit=3",
        "/admin/tokens/status"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"{endpoint} - Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'NOT SET')}")
            print(f"  Size: {len(response.text)} chars")
            
            try:
                json_data = response.json()
                print(f"  JSON parsing: SUCCESS")
            except Exception as e:
                print(f"  JSON parsing: FAILED - {e}")
        except Exception as e:
            print(f"{endpoint} - Request failed: {e}")
    
    # Test 6: Check for middleware/proxy interference
    print("\n6. TESTING FOR MIDDLEWARE/PROXY INTERFERENCE")
    print("-" * 50)
    
    try:
        # Test with different user agents
        user_agents = [
            "curl/8.7.1",
            "Python-requests/2.31.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "MCP-Client/1.0"
        ]
        
        for ua in user_agents:
            response = requests.get(f"{base_url}/health", headers={"User-Agent": ua})
            print(f"User-Agent '{ua}' - Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type')}")
            print(f"  Server: {response.headers.get('server', 'NOT SET')}")
            
    except Exception as e:
        print(f"User-Agent test failed: {e}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_server_diagnostics()
    sys.exit(0 if success else 1)