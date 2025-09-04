#!/usr/bin/env python3
"""
Advanced traffic analyzer to pinpoint JSON->SSE conversion
Uses multiple monitoring techniques to capture the exact transformation point
"""

import asyncio
import json
import mitmproxy.http
from mitmproxy import options, master
from mitmproxy.tools.dump import DumpMaster
import threading
import time
from datetime import datetime
import logging
import subprocess
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSEDetector:
    def __init__(self):
        self.conversions = []
        self.all_requests = []
        
    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        """Intercept and analyze requests"""
        req_data = {
            'timestamp': datetime.now().isoformat(),
            'method': flow.request.method,
            'url': flow.request.pretty_url,
            'headers': dict(flow.request.headers),
            'content': flow.request.get_text() if flow.request.content else '',
            'is_json_request': 'application/json' in flow.request.headers.get('content-type', ''),
            'expects_sse': 'text/event-stream' in flow.request.headers.get('accept', ''),
            'stream_param': 'stream' in flow.request.get_text() if flow.request.content else False
        }
        
        # Store request for later correlation with response
        flow.request_data = req_data
        self.all_requests.append(req_data)
        
        # Log interesting requests
        if req_data['expects_sse'] or req_data['stream_param']:
            logger.warning(f"🔍 SSE REQUEST DETECTED: {req_data['url']}")
            logger.info(f"   Accept: {req_data['headers'].get('accept', 'N/A')}")
            if req_data['content']:
                logger.info(f"   Body: {req_data['content'][:100]}...")

    def response(self, flow: mitmproxy.http.HTTPFlow) -> None:
        """Intercept and analyze responses"""
        req_data = getattr(flow, 'request_data', {})
        
        resp_data = {
            'timestamp': datetime.now().isoformat(),
            'status_code': flow.response.status_code,
            'headers': dict(flow.response.headers),
            'content': flow.response.get_text() if flow.response.content else '',
            'content_type': flow.response.headers.get('content-type', ''),
            'is_sse_response': 'text/event-stream' in flow.response.headers.get('content-type', ''),
            'has_data_prefix': False,
            'is_chunked': 'chunked' in flow.response.headers.get('transfer-encoding', ''),
            'connection_type': flow.response.headers.get('connection', '')
        }
        
        # Check for SSE data format
        content = resp_data['content']
        if content:
            resp_data['has_data_prefix'] = content.startswith('data: ')
            resp_data['has_event_prefix'] = 'event:' in content
            resp_data['has_sse_structure'] = bool(
                content.startswith('data: ') or 
                'event:' in content or 
                content.count('\n\n') > 0
            )
        
        # Detect JSON->SSE conversions
        conversion_detected = False
        
        # Case 1: JSON request with SSE response
        if (req_data.get('is_json_request') and resp_data['is_sse_response']):
            conversion_detected = True
            logger.error("🚨 JSON→SSE CONVERSION DETECTED (Content-Type)")
            
        # Case 2: JSON request with SSE data format but wrong content-type
        if (req_data.get('is_json_request') and resp_data['has_data_prefix']):
            conversion_detected = True
            logger.error("🚨 JSON→SSE CONVERSION DETECTED (Data Format)")
            
        # Case 3: Request expects SSE but gets wrong content-type
        if (req_data.get('expects_sse') and not resp_data['is_sse_response']):
            logger.warning("⚠️ SSE EXPECTED BUT NOT RECEIVED")
            
        if conversion_detected:
            conversion_entry = {
                'request': req_data,
                'response': resp_data,
                'conversion_type': 'json_to_sse',
                'detection_timestamp': datetime.now().isoformat()
            }
            self.conversions.append(conversion_entry)
            
            # Detailed logging
            logger.error(f"URL: {req_data.get('url', 'N/A')}")
            logger.error(f"Request Content-Type: {req_data.get('headers', {}).get('content-type', 'N/A')}")
            logger.error(f"Response Content-Type: {resp_data['content_type']}")
            logger.error(f"Request Accept: {req_data.get('headers', {}).get('accept', 'N/A')}")
            if content:
                logger.error(f"Response Preview: {content[:200]}...")
        
        # Log all SSE responses
        if resp_data['is_sse_response'] or resp_data['has_data_prefix']:
            logger.info(f"📡 SSE RESPONSE: {req_data.get('url', 'N/A')}")
            logger.info(f"   Content-Type: {resp_data['content_type']}")
            if content:
                logger.info(f"   Content: {content[:100]}...")

    def save_analysis(self, filename="/tmp/mitmproxy_analysis.json"):
        """Save detailed analysis"""
        analysis = {
            'total_requests': len(self.all_requests),
            'conversions_detected': len(self.conversions),
            'conversions': self.conversions,
            'all_requests': self.all_requests,
            'summary': {
                'json_requests': len([r for r in self.all_requests if r.get('is_json_request')]),
                'sse_expectations': len([r for r in self.all_requests if r.get('expects_sse')]),
                'stream_requests': len([r for r in self.all_requests if r.get('stream_param')])
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        logger.info(f"Analysis saved to {filename}")

def run_mitmproxy():
    """Run mitmproxy in background"""
    detector = SSEDetector()
    
    opts = options.Options(listen_port=8082)
    
    class SSEMaster(DumpMaster):
        def __init__(self, opts):
            super().__init__(opts)
            self.detector = detector
            
        def request(self, flow):
            self.detector.request(flow)
            
        def response(self, flow):
            self.detector.response(flow)
    
    m = SSEMaster(opts)
    
    def signal_handler(sig, frame):
        logger.info("Saving analysis and shutting down...")
        detector.save_analysis()
        m.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting mitmproxy on port 8082")
    logger.info("Configure your browser/curl to use proxy: http://localhost:8082")
    
    try:
        asyncio.run(m.run())
    except KeyboardInterrupt:
        detector.save_analysis()

def run_curl_through_proxy():
    """Run curl tests through the proxy"""
    time.sleep(2)  # Wait for proxy to start
    
    proxy_tests = [
        # Test through mitmproxy
        "curl -x http://localhost:8082 -k http://localhost:8080/api/health",
        "curl -x http://localhost:8082 -k -H 'Accept: text/event-stream' http://localhost:8080/api/health",
        "curl -x http://localhost:8082 -k -X POST -H 'Content-Type: application/json' -H 'Accept: text/event-stream' -d '{\"stream\":true}' http://localhost:8080/api/chat/completions",
    ]
    
    for test in proxy_tests:
        logger.info(f"Running: {test}")
        try:
            result = subprocess.run(test, shell=True, capture_output=True, text=True, timeout=10)
            logger.info(f"Status: {result.returncode}")
            if result.stdout:
                logger.info(f"Output: {result.stdout[:200]}...")
        except Exception as e:
            logger.error(f"Test failed: {e}")
        time.sleep(1)

if __name__ == '__main__':
    # Start proxy monitoring in background
    proxy_thread = threading.Thread(target=run_mitmproxy, daemon=True)
    proxy_thread.start()
    
    # Run some test traffic through the proxy
    test_thread = threading.Thread(target=run_curl_through_proxy, daemon=True)
    test_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down traffic analyzer...")