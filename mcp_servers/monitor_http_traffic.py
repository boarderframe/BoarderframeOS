#!/usr/bin/env python3
"""
HTTP Traffic Monitor for MCP Server - Open WebUI Integration Debug
Captures exact HTTP requests/responses to identify SSE format introduction
"""

import asyncio
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

class HTTPTrafficMonitor:
    def __init__(self):
        self.captured_requests = []
        self.proxy_port = 8888
        self.target_server = "http://localhost:9004"
        
    def log_request(self, method, url, headers, body, response_headers, response_body):
        """Log detailed request/response information"""
        timestamp = datetime.now().isoformat()
        
        request_info = {
            "timestamp": timestamp,
            "method": method,
            "url": url,
            "request_headers": dict(headers),
            "request_body": body,
            "response_headers": dict(response_headers),
            "response_body": response_body,
            "content_type": response_headers.get('Content-Type', ''),
            "is_sse": 'text/event-stream' in response_headers.get('Content-Type', ''),
            "user_agent": headers.get('User-Agent', '')
        }
        
        self.captured_requests.append(request_info)
        
        print(f"\n{'='*80}")
        print(f"[{timestamp}] {method} {url}")
        print(f"User-Agent: {headers.get('User-Agent', 'Unknown')}")
        print(f"Content-Type: {response_headers.get('Content-Type', 'Unknown')}")
        
        if 'text/event-stream' in response_headers.get('Content-Type', ''):
            print("🚨 SSE DETECTED! This is where the format is being introduced!")
            
        print(f"Request Headers:")
        for k, v in headers.items():
            print(f"  {k}: {v}")
            
        if body:
            print(f"Request Body: {body}")
            
        print(f"Response Headers:")
        for k, v in response_headers.items():
            print(f"  {k}: {v}")
            
        print(f"Response Body (first 500 chars):")
        print(f"  {response_body[:500]}...")
        
        if response_body.startswith('data: '):
            print("🔍 FOUND THE ISSUE: Response starts with 'data: ' - this is SSE format!")
            
        print(f"{'='*80}")
        
        return request_info

class ProxyHandler(BaseHTTPRequestHandler):
    def __init__(self, monitor, *args, **kwargs):
        self.monitor = monitor
        super().__init__(*args, **kwargs)
        
    def do_GET(self):
        self._proxy_request('GET')
        
    def do_POST(self):
        self._proxy_request('POST')
        
    def do_PUT(self):
        self._proxy_request('PUT')
        
    def do_DELETE(self):
        self._proxy_request('DELETE')
        
    def _proxy_request(self, method):
        """Proxy the request to the actual MCP server and capture traffic"""
        try:
            # Get request headers
            headers = dict(self.headers)
            
            # Get request body
            content_length = int(headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
            
            # Build target URL
            target_url = f"{self.monitor.target_server}{self.path}"
            
            # Make request to actual server
            response = requests.request(
                method=method,
                url=target_url,
                headers=headers,
                data=body,
                allow_redirects=False
            )
            
            # Log the traffic
            self.monitor.log_request(
                method=method,
                url=target_url,
                headers=headers,
                body=body,
                response_headers=response.headers,
                response_body=response.text
            )
            
            # Send response back to client
            self.send_response(response.status_code)
            
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            
            self.wfile.write(response.content)
            
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_error(500, f"Proxy error: {e}")

def create_proxy_handler(monitor):
    """Create a proxy handler with the monitor instance"""
    def handler(*args, **kwargs):
        return ProxyHandler(monitor, *args, **kwargs)
    return handler

def test_different_clients(monitor):
    """Test the MCP server with different HTTP clients"""
    print("\n" + "="*80)
    print("TESTING DIFFERENT HTTP CLIENTS")
    print("="*80)
    
    base_url = "http://localhost:9004"
    
    # Test 1: Direct curl (already done)
    print("\n1. Testing with curl...")
    subprocess.run([
        "curl", "-v", "-H", "Accept: application/json", 
        "-H", "User-Agent: DirectCurl/1.0", f"{base_url}/health"
    ])
    
    # Test 2: Python requests
    print("\n2. Testing with Python requests...")
    try:
        response = requests.get(f"{base_url}/health", headers={
            "Accept": "application/json",
            "User-Agent": "PythonRequests/1.0"
        })
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {response.text}")
    except Exception as e:
        print(f"Python requests error: {e}")
    
    # Test 3: OpenWebUI-like request
    print("\n3. Testing with OpenWebUI-like headers...")
    try:
        response = requests.get(f"{base_url}/health", headers={
            "Accept": "text/event-stream",
            "User-Agent": "Mozilla/5.0 (compatible; OpenWebUI)",
            "Cache-Control": "no-cache"
        })
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Body: {response.text}")
        
        if response.headers.get('Content-Type') == 'text/event-stream':
            print("🚨 FOUND IT! OpenWebUI-like Accept header triggers SSE response!")
            
    except Exception as e:
        print(f"OpenWebUI-like request error: {e}")

def main():
    monitor = HTTPTrafficMonitor()
    
    print("Starting HTTP Traffic Monitor for MCP Server Debug")
    print(f"Target server: {monitor.target_server}")
    print(f"Proxy listening on port: {monitor.proxy_port}")
    
    # Test different clients first
    test_different_clients(monitor)
    
    # Start proxy server
    handler = create_proxy_handler(monitor)
    httpd = HTTPServer(('localhost', monitor.proxy_port), handler)
    
    print(f"\nProxy server started. Configure Open WebUI to use:")
    print(f"http://localhost:{monitor.proxy_port}")
    print("\nPress Ctrl+C to stop monitoring and see captured traffic...")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        
    # Save captured traffic
    with open('/Users/cosburn/MCP Servers/captured_traffic.json', 'w') as f:
        json.dump(monitor.captured_requests, f, indent=2)
        
    print(f"\nCaptured {len(monitor.captured_requests)} requests")
    print("Traffic saved to captured_traffic.json")
    
    # Analyze for SSE patterns
    sse_requests = [r for r in monitor.captured_requests if r['is_sse']]
    if sse_requests:
        print(f"\n🚨 Found {len(sse_requests)} SSE requests!")
        for req in sse_requests:
            print(f"  - {req['method']} {req['url']} from {req['user_agent']}")
    else:
        print("\nNo SSE requests detected in captured traffic")

if __name__ == "__main__":
    main()