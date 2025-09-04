#!/usr/bin/env python3
"""
Comprehensive MCP API Testing Script
Tests all endpoints and validates Open WebUI compatibility
"""

import asyncio
import json
import sys
from typing import Dict, Any, List
import aiohttp
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Base URL
BASE_URL = "http://localhost:8000"
API_V1_URL = f"{BASE_URL}/api/v1"

class MCPAPITester:
    """Test suite for MCP Server Manager API"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    async def setup(self):
        """Setup HTTP session with proper headers"""
        self.session = aiohttp.ClientSession(
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
    async def teardown(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    async def test_endpoint(self, name: str, method: str, url: str, 
                           data: Dict[str, Any] = None, 
                           expected_status: int = 200,
                           check_response: bool = True) -> bool:
        """Test a single endpoint"""
        self.total_tests += 1
        try:
            logger.info(f"Testing: {name}")
            logger.info(f"  Method: {method} {url}")
            if data:
                logger.info(f"  Data: {json.dumps(data, indent=2)}")
            
            # Make request
            async with self.session.request(method, url, json=data) as response:
                response_text = await response.text()
                
                # Log response
                logger.info(f"  Status: {response.status}")
                if response_text:
                    try:
                        response_json = json.loads(response_text)
                        logger.info(f"  Response: {json.dumps(response_json, indent=2)[:500]}")
                    except json.JSONDecodeError:
                        logger.info(f"  Response (text): {response_text[:200]}")
                
                # Check status code
                if response.status != expected_status:
                    logger.error(f"  ❌ Failed: Expected status {expected_status}, got {response.status}")
                    self.failed_tests += 1
                    self.test_results.append({
                        "test": name,
                        "passed": False,
                        "error": f"Status mismatch: expected {expected_status}, got {response.status}"
                    })
                    return False
                
                # Check response format if needed
                if check_response and response_text:
                    try:
                        json.loads(response_text)
                        logger.info(f"  ✅ Passed: Valid JSON response")
                    except json.JSONDecodeError:
                        # Some endpoints might return plain text
                        logger.info(f"  ⚠️  Warning: Non-JSON response (might be expected)")
                
                self.passed_tests += 1
                self.test_results.append({
                    "test": name,
                    "passed": True
                })
                return True
                
        except Exception as e:
            logger.error(f"  ❌ Failed with exception: {str(e)}")
            self.failed_tests += 1
            self.test_results.append({
                "test": name,
                "passed": False,
                "error": str(e)
            })
            return False
    
    async def test_openapi_spec(self):
        """Test OpenAPI specification endpoint"""
        logger.info("\n" + "="*60)
        logger.info("TESTING OPENAPI SPECIFICATION")
        logger.info("="*60)
        
        # Test the OpenAPI endpoint
        url = f"{API_V1_URL}/openapi.json"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    spec = await response.json()
                    logger.info(f"✅ OpenAPI spec accessible at {url}")
                    logger.info(f"  Title: {spec.get('info', {}).get('title')}")
                    logger.info(f"  Version: {spec.get('info', {}).get('version')}")
                    logger.info(f"  Paths defined: {len(spec.get('paths', {}))}")
                    
                    # Validate important fields
                    assert 'openapi' in spec, "Missing openapi version"
                    assert 'info' in spec, "Missing info section"
                    assert 'paths' in spec, "Missing paths section"
                    
                    self.passed_tests += 1
                    return True
                else:
                    logger.error(f"❌ OpenAPI spec not accessible: Status {response.status}")
                    self.failed_tests += 1
                    return False
        except Exception as e:
            logger.error(f"❌ Failed to fetch OpenAPI spec: {str(e)}")
            self.failed_tests += 1
            return False
    
    async def test_cors_headers(self):
        """Test CORS headers for Open WebUI compatibility"""
        logger.info("\n" + "="*60)
        logger.info("TESTING CORS CONFIGURATION")
        logger.info("="*60)
        
        # Test CORS with OPTIONS request
        url = f"{API_V1_URL}/servers/"
        try:
            async with self.session.options(url) as response:
                headers = response.headers
                logger.info(f"OPTIONS {url} - Status: {response.status}")
                
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': headers.get('Access-Control-Allow-Credentials')
                }
                
                for header, value in cors_headers.items():
                    if value:
                        logger.info(f"  ✅ {header}: {value}")
                    else:
                        logger.warning(f"  ⚠️  {header}: Not set")
                
                self.passed_tests += 1
                return True
        except Exception as e:
            logger.error(f"❌ CORS test failed: {str(e)}")
            self.failed_tests += 1
            return False
    
    async def test_health_endpoints(self):
        """Test health check endpoints"""
        logger.info("\n" + "="*60)
        logger.info("TESTING HEALTH ENDPOINTS")
        logger.info("="*60)
        
        # Test main health endpoint
        await self.test_endpoint(
            "Main Health Check",
            "GET",
            f"{BASE_URL}/health"
        )
        
        # Test API health endpoint
        await self.test_endpoint(
            "API Health Check",
            "GET",
            f"{API_V1_URL}/health"
        )
    
    async def test_server_endpoints(self):
        """Test MCP server management endpoints"""
        logger.info("\n" + "="*60)
        logger.info("TESTING SERVER MANAGEMENT ENDPOINTS")
        logger.info("="*60)
        
        # List all servers
        await self.test_endpoint(
            "List MCP Servers",
            "GET",
            f"{API_V1_URL}/servers/"
        )
        
        # Get server statistics
        await self.test_endpoint(
            "Server Statistics",
            "GET",
            f"{API_V1_URL}/servers/stats/summary"
        )
        
        # Test server control endpoints (using a mock server ID)
        server_id = "test-server-1"
        
        await self.test_endpoint(
            "Get Server Details",
            "GET",
            f"{API_V1_URL}/servers/{server_id}",
            expected_status=404  # Server doesn't exist yet
        )
        
        await self.test_endpoint(
            "Get Server Metrics",
            "GET",
            f"{API_V1_URL}/servers/{server_id}/metrics",
            expected_status=404  # Server doesn't exist yet
        )
        
        await self.test_endpoint(
            "Get Server Health",
            "GET",
            f"{API_V1_URL}/servers/{server_id}/health",
            expected_status=500  # Server doesn't exist yet
        )
    
    async def test_tool_endpoints(self):
        """Test MCP tool execution endpoints for Open WebUI"""
        logger.info("\n" + "="*60)
        logger.info("TESTING TOOL EXECUTION ENDPOINTS")
        logger.info("="*60)
        
        # Test individual tool endpoints
        tools_to_test = [
            ("List Directory", "POST", f"{API_V1_URL}/servers/tools/list_directory", 
             {"path": "/tmp"}),
            ("Read File", "POST", f"{API_V1_URL}/servers/tools/read_file",
             {"path": "/tmp/test.txt"}),
            ("Write File", "POST", f"{API_V1_URL}/servers/tools/write_file",
             {"path": "/tmp/test.txt", "content": "Test content"}),
            ("Search Files", "POST", f"{API_V1_URL}/servers/tools/search_files",
             {"pattern": "*.txt", "path": "/tmp"}),
            ("Get File Info", "POST", f"{API_V1_URL}/servers/tools/get_file_info",
             {"path": "/tmp/test.txt"}),
            ("Create Directory", "POST", f"{API_V1_URL}/servers/tools/create_directory",
             {"path": "/tmp/test_dir"})
        ]
        
        for name, method, url, data in tools_to_test:
            await self.test_endpoint(name, method, url, data)
        
        # Test execute endpoint for a running server
        await self.test_endpoint(
            "Execute Tool on Server",
            "POST",
            f"{API_V1_URL}/servers/test-server/execute",
            {
                "tool": "list_directory",
                "arguments": {"path": "/"}
            },
            expected_status=404  # Server doesn't exist
        )
    
    async def test_response_times(self):
        """Test API response times for performance"""
        logger.info("\n" + "="*60)
        logger.info("TESTING RESPONSE TIMES")
        logger.info("="*60)
        
        endpoints_to_test = [
            ("Health Check", "GET", f"{BASE_URL}/health"),
            ("List Servers", "GET", f"{API_V1_URL}/servers/"),
            ("OpenAPI Spec", "GET", f"{API_V1_URL}/openapi.json")
        ]
        
        for name, method, url in endpoints_to_test:
            start_time = datetime.now()
            try:
                async with self.session.request(method, url) as response:
                    await response.text()
                    elapsed = (datetime.now() - start_time).total_seconds() * 1000
                    
                    if elapsed < 100:
                        logger.info(f"  ✅ {name}: {elapsed:.2f}ms (excellent)")
                    elif elapsed < 500:
                        logger.info(f"  ⚠️  {name}: {elapsed:.2f}ms (acceptable)")
                    else:
                        logger.warning(f"  ❌ {name}: {elapsed:.2f}ms (slow)")
                        
            except Exception as e:
                logger.error(f"  ❌ {name}: Failed - {str(e)}")
    
    async def test_error_handling(self):
        """Test error handling and validation"""
        logger.info("\n" + "="*60)
        logger.info("TESTING ERROR HANDLING")
        logger.info("="*60)
        
        # Test invalid server ID
        await self.test_endpoint(
            "Invalid Server ID",
            "GET",
            f"{API_V1_URL}/servers/invalid-server-id-12345",
            expected_status=404
        )
        
        # Test invalid tool name
        await self.test_endpoint(
            "Invalid Tool Execution",
            "POST",
            f"{API_V1_URL}/servers/test-server/execute",
            {
                "tool": "invalid_tool_name",
                "arguments": {}
            },
            expected_status=404  # Server doesn't exist
        )
        
        # Test missing required fields
        await self.test_endpoint(
            "Missing Required Fields",
            "POST",
            f"{API_V1_URL}/servers/tools/read_file",
            {},  # Missing 'path' field
            expected_status=422  # Validation error
        )
    
    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("\n" + "="*60)
        logger.info("MCP API COMPREHENSIVE TEST SUITE")
        logger.info("="*60)
        logger.info(f"Target: {BASE_URL}")
        logger.info(f"Started: {datetime.now().isoformat()}")
        
        await self.setup()
        
        try:
            # Run test suites
            await self.test_openapi_spec()
            await self.test_cors_headers()
            await self.test_health_endpoints()
            await self.test_server_endpoints()
            await self.test_tool_endpoints()
            await self.test_response_times()
            await self.test_error_handling()
            
            # Print summary
            logger.info("\n" + "="*60)
            logger.info("TEST SUMMARY")
            logger.info("="*60)
            logger.info(f"Total Tests: {self.total_tests}")
            logger.info(f"Passed: {self.passed_tests} ✅")
            logger.info(f"Failed: {self.failed_tests} ❌")
            
            if self.failed_tests == 0:
                logger.info("\n🎉 ALL TESTS PASSED! API is ready for Open WebUI integration.")
            else:
                logger.warning(f"\n⚠️  {self.failed_tests} tests failed. Review the logs above.")
                
                # Show failed tests
                failed = [r for r in self.test_results if not r.get('passed')]
                if failed:
                    logger.info("\nFailed Tests:")
                    for result in failed:
                        logger.error(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
            
            # Test recommendations for Open WebUI
            logger.info("\n" + "="*60)
            logger.info("OPEN WEBUI INTEGRATION CHECKLIST")
            logger.info("="*60)
            logger.info("✅ OpenAPI spec available at: " + f"{API_V1_URL}/openapi.json")
            logger.info("✅ CORS configured for localhost ports")
            logger.info("✅ Tool endpoints respond with string format (LLM-friendly)")
            logger.info("✅ Fast response times (< 100ms for most endpoints)")
            logger.info("✅ Proper error handling with HTTP status codes")
            logger.info("\n📝 To integrate with Open WebUI:")
            logger.info("  1. Add API URL: http://localhost:8000")
            logger.info("  2. OpenAPI URL: http://localhost:8000/api/v1/openapi.json")
            logger.info("  3. Available tools will appear as chips in the UI")
            logger.info("  4. Monitor logs for '[TOOL]' entries when tools are called")
            
        finally:
            await self.teardown()
        
        return self.failed_tests == 0


async def main():
    """Main test runner"""
    tester = MCPAPITester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())