#!/usr/bin/env python3
"""
HTTP Monitor to trace the exact source of SSE "data: " prefix issue
"""
import asyncio
import aiohttp
from aiohttp import web
import logging
import json
import time
from typing import Any, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HTTPMonitor:
    def __init__(self, port: int = 9998):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        # Monitor endpoint that proxies to our MCP servers
        self.app.router.add_route('*', '/monitor/{service_port}/{path:.*}', self.monitor_request)
        self.app.router.add_get('/test-direct', self.test_direct)
        self.app.router.add_get('/health', self.health)
        
    async def monitor_request(self, request: web.Request) -> web.Response:
        """Monitor and log all requests/responses to trace SSE conversion"""
        service_port = request.match_info['service_port']
        path = request.match_info['path']
        
        target_url = f"http://localhost:{service_port}/{path}"
        if request.query_string:
            target_url += f"?{request.query_string}"
            
        logger.info(f"=== MONITORING REQUEST ===")
        logger.info(f"Method: {request.method}")
        logger.info(f"Target URL: {target_url}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Query: {dict(request.query)}")
        
        try:
            # Forward the request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers={k: v for k, v in request.headers.items() 
                            if k.lower() not in ['host', 'content-length']},
                    data=await request.read() if request.can_read_body else None
                ) as response:
                    # Log response details
                    response_text = await response.text()
                    
                    logger.info(f"=== RESPONSE FROM TARGET ===")
                    logger.info(f"Status: {response.status}")
                    logger.info(f"Headers: {dict(response.headers)}")
                    logger.info(f"Content-Type: {response.headers.get('content-type', 'None')}")
                    logger.info(f"Response Length: {len(response_text)}")
                    logger.info(f"First 200 chars: {response_text[:200]}")
                    
                    # Check for SSE indicators
                    if "data: " in response_text:
                        logger.error(f"❌ FOUND 'data: ' PREFIX IN RESPONSE!")
                        logger.error(f"Full response: {response_text}")
                    else:
                        logger.info(f"✅ NO 'data: ' prefix found")
                        
                    # Return response preserving headers
                    response_headers = {k: v for k, v in response.headers.items() 
                                      if k.lower() not in ['content-length', 'transfer-encoding', 'content-type']}
                    
                    return web.Response(
                        body=response_text,
                        status=response.status,
                        headers=response_headers,
                        content_type=response.headers.get('content-type')
                    )
                    
        except Exception as e:
            logger.error(f"Error forwarding request: {e}")
            return web.Response(
                text=f"Monitor error: {str(e)}",
                status=500
            )
            
    async def test_direct(self, request: web.Request) -> web.Response:
        """Test direct responses to compare"""
        logger.info("=== DIRECT TEST RESPONSE ===")
        
        test_response = {
            "message": "Direct response from monitor",
            "timestamp": time.time(),
            "data": ["item1", "item2", "item3"]
        }
        
        response_text = json.dumps(test_response, indent=2)
        logger.info(f"Direct response: {response_text}")
        
        return web.Response(
            text=response_text,
            content_type="application/json"
        )
        
    async def health(self, request: web.Request) -> web.Response:
        """Health check"""
        return web.Response(
            text=json.dumps({"status": "monitoring", "port": self.port}),
            content_type="application/json"
        )
        
    async def run(self):
        """Start the monitor server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"HTTP Monitor running on port {self.port}")
        logger.info(f"Usage: curl http://localhost:{self.port}/monitor/9001/products/search?term=milk")
        logger.info(f"Direct test: curl http://localhost:{self.port}/test-direct")
        
        try:
            await asyncio.Future()  # run forever
        except KeyboardInterrupt:
            logger.info("Shutting down monitor...")
        finally:
            await runner.cleanup()

if __name__ == "__main__":
    monitor = HTTPMonitor()
    asyncio.run(monitor.run())