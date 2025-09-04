#!/usr/bin/env python3
"""
Test script to simulate different types of requests that Open WebUI might make
to help understand the SSE wrapping issue
"""

import requests
import json
import time
from datetime import datetime

class OpenWebUITestClient:
    def __init__(self, base_url="http://localhost:9004"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_regular_json_request(self):
        """Test regular JSON API request"""
        print("\n🔍 Testing regular JSON request...")
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'test-client/1.0'
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/openapi.json",
                headers=headers,
                timeout=10
            )
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
            if response.headers.get('Content-Type', '').startswith('application/json'):
                print(f"✅ JSON Response: {len(response.text)} chars")
            else:
                print(f"❌ Non-JSON Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def test_sse_request(self):
        """Test request with SSE accept header"""
        print("\n🔍 Testing SSE request...")
        
        headers = {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'User-Agent': 'test-client/1.0'
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/openapi.json",
                headers=headers,
                timeout=10,
                stream=True
            )
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
            print(f"✅ Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def test_openwebui_simulation(self):
        """Simulate Open WebUI request patterns"""
        print("\n🔍 Testing Open WebUI simulation...")
        
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Content-Type': 'application/json',
            'User-Agent': 'open-webui/1.0',
            'Connection': 'keep-alive'
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/openapi.json",
                headers=headers,
                timeout=10
            )
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
            print(f"✅ Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def test_tool_call_request(self):
        """Test a tool call request"""
        print("\n🔍 Testing tool call request...")
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'open-webui/1.0'
        }
        
        # Try to call a tool
        payload = {
            "name": "search_products",
            "arguments": {
                "query": "milk",
                "location_id": "01400403"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/tools/search_products/call",
                headers=headers,
                json=payload,
                timeout=10
            )
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
            print(f"✅ Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def test_mcp_endpoints(self):
        """Test MCP-specific endpoints"""
        print("\n🔍 Testing MCP endpoints...")
        
        endpoints = [
            "/",
            "/tools",
            "/health",
            "/docs"
        ]
        
        for endpoint in endpoints:
            print(f"\n📡 Testing {endpoint}...")
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'open-webui/1.0'
            }
            
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                print(f"  ✅ Status: {response.status_code}")
                print(f"  ✅ Content-Type: {response.headers.get('Content-Type')}")
                
                # Check if response is SSE-wrapped
                if 'data:' in response.text and '\\n\\n' in response.text:
                    print(f"  🚨 SSE-WRAPPED RESPONSE DETECTED!")
                elif response.headers.get('Content-Type', '').startswith('application/json'):
                    print(f"  ✅ Clean JSON response")
                else:
                    print(f"  ⚠️  Other response type")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    def test_streaming_request(self):
        """Test streaming request"""
        print("\n🔍 Testing streaming request...")
        
        headers = {
            'Accept': 'text/event-stream, application/json',
            'User-Agent': 'open-webui/1.0',
            'Cache-Control': 'no-cache'
        }
        
        try:
            response = self.session.get(
                f"{self.base_url}/openapi.json",
                headers=headers,
                stream=True,
                timeout=10
            )
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
            
            # Read first chunk
            chunk = next(response.iter_content(chunk_size=200), b'')
            print(f"✅ First chunk: {chunk.decode('utf-8', errors='ignore')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Open WebUI Request Analysis")
    print("="*60)
    
    client = OpenWebUITestClient()
    
    # Run different test scenarios
    client.test_regular_json_request()
    client.test_sse_request()
    client.test_openwebui_simulation()
    client.test_tool_call_request()
    client.test_mcp_endpoints()
    client.test_streaming_request()
    
    print("\n" + "="*60)
    print("🏁 Test complete! Check the HTTP monitor logs for details.")

if __name__ == "__main__":
    main()