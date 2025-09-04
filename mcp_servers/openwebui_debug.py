#!/usr/bin/env python3
"""
Open WebUI HTTP Traffic Debug Monitor
Specifically designed to catch the "data: {" SSE transformation
"""

import asyncio
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import sys
from urllib.parse import urlparse, parse_qs

class OpenWebUIDebugMonitor:
    def __init__(self):
        self.captured_requests = []
        self.proxy_port = 8888
        self.target_server = "http://localhost:9004"
        self.sse_detected = False
        
    def analyze_response(self, response_text, headers):
        """Analyze response for SSE patterns and transformation points"""
        analysis = {
            "is_valid_json": False,
            "starts_with_data": False,
            "contains_sse_format": False,
            "transformation_detected": False,
            "content_type": headers.get('Content-Type', ''),
            "response_length": len(response_text),
            "first_100_chars": response_text[:100] if response_text else ''
        }
        
        # Check if valid JSON
        try:
            json.loads(response_text)
            analysis["is_valid_json"] = True
        except:
            pass
            
        # Check for SSE patterns
        if response_text.startswith('data: '):
            analysis["starts_with_data"] = True
            analysis["transformation_detected"] = True
            print(f"🚨 TRANSFORMATION DETECTED: Response starts with 'data: '")
            
        if 'text/event-stream' in headers.get('Content-Type', ''):
            analysis["contains_sse_format"] = True
            print(f"🚨 SSE CONTENT-TYPE DETECTED: {headers.get('Content-Type')}")
            
        # Check for common SSE patterns
        sse_patterns = ['data: {', 'event: ', 'id: ', 'retry: ']
        for pattern in sse_patterns:
            if pattern in response_text:
                analysis["contains_sse_format"] = True
                print(f"🚨 SSE PATTERN DETECTED: '{pattern}' found in response")
                
        return analysis

class DebugProxyHandler(BaseHTTPRequestHandler):
    def __init__(self, monitor, *args, **kwargs):
        self.monitor = monitor
        super().__init__(*args, **kwargs)
        
    def log_message(self, format, *args):
        """Override to prevent default logging"""
        pass
        
    def do_GET(self):
        self._handle_request('GET')
        
    def do_POST(self):
        self._handle_request('POST')
        
    def do_PUT(self):
        self._handle_request('PUT')
        
    def do_DELETE(self):
        self._handle_request('DELETE')
        
    def _handle_request(self, method):
        """Handle request and monitor for transformations"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Capture request details
            headers = dict(self.headers)
            content_length = int(headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
            
            target_url = f"{self.monitor.target_server}{self.path}"
            
            print(f"\n{'='*80}")
            print(f"[{timestamp}] PROXYING: {method} {self.path}")
            print(f"User-Agent: {headers.get('User-Agent', 'Unknown')}")
            print(f"Accept: {headers.get('Accept', 'Unknown')}")
            
            # Forward to actual server
            response = requests.request(
                method=method,
                url=target_url,
                headers=headers,
                data=body,
                allow_redirects=False,
                timeout=30
            )
            
            # Analyze the response
            analysis = self.monitor.analyze_response(response.text, response.headers)
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"Response Length: {len(response.text)}")
            
            # Log transformation detection
            if analysis["transformation_detected"]:
                print(f"🚨🚨🚨 TRANSFORMATION POINT FOUND! 🚨🚨🚨")
                print(f"Original server returned JSON, but proxy is seeing SSE format!")
                
            # Store request data
            request_data = {
                "timestamp": timestamp,
                "method": method,
                "path": self.path,
                "user_agent": headers.get('User-Agent', ''),
                "accept_header": headers.get('Accept', ''),
                "response_status": response.status_code,
                "response_headers": dict(response.headers),
                "analysis": analysis,
                "first_100_response": response.text[:100]
            }
            
            self.monitor.captured_requests.append(request_data)
            
            # Forward response to client
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            
            # Here's where we might catch transformation!
            response_to_send = response.content
            
            # Check if this is where transformation happens
            if isinstance(response_to_send, bytes):
                response_str = response_to_send.decode('utf-8', errors='ignore')
                if response_str.startswith('data: ') and not response.text.startswith('data: '):
                    print(f"🚨🚨🚨 TRANSFORMATION IN PROXY! 🚨🚨🚨")
                    print(f"Original: {response.text[:100]}")
                    print(f"Transformed: {response_str[:100]}")
            
            self.wfile.write(response_to_send)
            
        except Exception as e:
            print(f"❌ Proxy error: {e}")
            self.send_error(500, f"Proxy error: {e}")

def create_debug_handler(monitor):
    """Create handler with monitor instance"""
    def handler(*args, **kwargs):
        return DebugProxyHandler(monitor, *args, **kwargs)
    return handler

def main():
    monitor = OpenWebUIDebugMonitor()
    
    print("🔍 Open WebUI Debug Monitor - SSE Transformation Detector")
    print(f"Target MCP Server: {monitor.target_server}")
    print(f"Debug Proxy Port: {monitor.proxy_port}")
    print("="*80)
    
    # Create and start proxy server
    handler = create_debug_handler(monitor)
    httpd = HTTPServer(('localhost', monitor.proxy_port), handler)
    
    print(f"\n🚀 Debug proxy started on http://localhost:{monitor.proxy_port}")
    print("\n📋 CONFIGURATION INSTRUCTIONS:")
    print("1. In Open WebUI, go to Settings > Connections")
    print(f"2. Set OpenAI API Base URL to: http://localhost:{monitor.proxy_port}")
    print("3. Make a request through Open WebUI")
    print("4. Watch this console for transformation detection")
    print("\n⌨️  Press Ctrl+C to stop and see captured traffic...")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping debug monitor...")
        
    # Analysis and reporting
    print(f"\n📊 CAPTURED {len(monitor.captured_requests)} REQUESTS")
    print("="*80)
    
    transformation_found = False
    for req in monitor.captured_requests:
        if req["analysis"]["transformation_detected"]:
            transformation_found = True
            print(f"🚨 TRANSFORMATION DETECTED:")
            print(f"   Method: {req['method']}")
            print(f"   Path: {req['path']}")
            print(f"   User-Agent: {req['user_agent']}")
            print(f"   Accept: {req['accept_header']}")
            print(f"   Response: {req['first_100_response']}")
            
    if not transformation_found:
        print("✅ No transformations detected in proxy layer")
        print("➡️  The SSE format is likely being introduced by Open WebUI client-side")
        
    # Save detailed log
    with open('/Users/cosburn/MCP Servers/openwebui_debug_log.json', 'w') as f:
        json.dump(monitor.captured_requests, f, indent=2)
        
    print(f"\n💾 Debug log saved to: openwebui_debug_log.json")
    
if __name__ == "__main__":
    main()