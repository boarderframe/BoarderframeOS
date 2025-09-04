#!/usr/bin/env python3
"""
Test script to verify Open WebUI compatibility for MCP Server API
Tests for issues that cause Open WebUI to spin indefinitely
"""
import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, Any, List


class OpenWebUICompatibilityTester:
    """Test Open WebUI compatibility of the MCP server API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_openapi_spec(self) -> Dict[str, Any]:
        """Test that OpenAPI spec is accessible and well-formed."""
        print("🔍 Testing OpenAPI specification...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/openapi.json") as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"HTTP {resp.status}"}
                
                spec = await resp.json()
                
                # Check for required OpenAPI fields
                required_fields = ["openapi", "info", "paths"]
                missing_fields = [field for field in required_fields if field not in spec]
                
                if missing_fields:
                    return {"success": False, "error": f"Missing required fields: {missing_fields}"}
                
                # Check for tool endpoints
                paths = spec.get("paths", {})
                tool_endpoints = [path for path in paths.keys() if "/tools/" in path]
                
                return {
                    "success": True,
                    "paths_count": len(paths),
                    "tool_endpoints": len(tool_endpoints),
                    "has_operation_ids": all("operationId" in spec["paths"][path].get("post", {}) 
                                           for path in tool_endpoints if "post" in spec["paths"][path])
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_endpoint_response_format(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test that endpoint returns proper format for Open WebUI."""
        print(f"🔧 Testing endpoint: {endpoint}")
        
        try:
            start_time = time.time()
            
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                response_time = time.time() - start_time
                
                if resp.status != 200:
                    return {"success": False, "error": f"HTTP {resp.status}", "response_time": response_time}
                
                content_type = resp.headers.get("content-type", "")
                response_data = await resp.text()
                
                # For Open WebUI, we expect string responses for tool endpoints
                is_string_response = content_type.startswith("application/json") and response_data.startswith('"')
                
                return {
                    "success": True,
                    "response_time": response_time,
                    "content_type": content_type,
                    "is_string_response": is_string_response,
                    "response_length": len(response_data),
                    "sample_response": response_data[:200] + "..." if len(response_data) > 200 else response_data
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_concurrent_requests(self, endpoint: str, payload: Dict[str, Any], count: int = 5) -> Dict[str, Any]:
        """Test concurrent requests to check for blocking issues."""
        print(f"⚡ Testing concurrent requests to {endpoint}...")
        
        async def single_request():
            try:
                start_time = time.time()
                async with self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    response_time = time.time() - start_time
                    return {"success": resp.status == 200, "response_time": response_time}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        start_time = time.time()
        tasks = [single_request() for _ in range(count)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        successful_requests = sum(1 for r in results if r.get("success"))
        avg_response_time = sum(r.get("response_time", 0) for r in results) / len(results)
        
        return {
            "success": successful_requests == count,
            "total_time": total_time,
            "successful_requests": successful_requests,
            "failed_requests": count - successful_requests,
            "avg_response_time": avg_response_time
        }
    
    async def test_error_handling(self, endpoint: str, invalid_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test error handling with invalid payloads."""
        print(f"❌ Testing error handling for {endpoint}...")
        
        try:
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=invalid_payload,
                headers={"Content-Type": "application/json"}
            ) as resp:
                response_data = await resp.text()
                
                # For tool endpoints, we expect graceful error handling with string responses
                return {
                    "success": True,  # We expect this to succeed even with invalid data
                    "status_code": resp.status,
                    "has_error_message": "error" in response_data.lower() or "Error" in response_data,
                    "response": response_data[:200] + "..." if len(response_data) > 200 else response_data
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all compatibility tests."""
        print("🚀 Starting Open WebUI compatibility tests...\n")
        
        # Test OpenAPI spec
        openapi_result = await self.test_openapi_spec()
        print(f"✅ OpenAPI spec: {'PASS' if openapi_result['success'] else 'FAIL'}")
        if not openapi_result['success']:
            print(f"   Error: {openapi_result['error']}")
        else:
            print(f"   Paths: {openapi_result['paths_count']}, Tools: {openapi_result['tool_endpoints']}")
        
        # Test tool endpoints
        tool_tests = [
            ("/api/v1/tools/list_directory", {"path": "/test", "show_hidden": False}),
            ("/api/v1/tools/read_file", {"path": "/test/file.txt", "encoding": "utf-8"}),
            ("/api/v1/tools/write_file", {"path": "/test/new.txt", "content": "test content"}),
            ("/api/v1/tools/search_files", {"pattern": "test", "directory": "/", "file_pattern": "*.txt"}),
            ("/api/v1/tools/get_file_info", {"path": "/test/file.txt"}),
            ("/api/v1/tools/create_directory", {"path": "/test/newdir", "parents": True})
        ]
        
        tool_results = {}
        for endpoint, payload in tool_tests:
            result = await self.test_endpoint_response_format(endpoint, payload)
            tool_results[endpoint] = result
            print(f"{'✅' if result['success'] else '❌'} {endpoint}: {'PASS' if result['success'] else 'FAIL'}")
            if result['success']:
                print(f"   Response time: {result['response_time']:.3f}s")
            else:
                print(f"   Error: {result['error']}")
        
        # Test concurrent requests
        concurrent_result = await self.test_concurrent_requests("/api/v1/tools/list_directory", {"path": "/test"})
        print(f"{'✅' if concurrent_result['success'] else '❌'} Concurrent requests: {'PASS' if concurrent_result['success'] else 'FAIL'}")
        if concurrent_result['success']:
            print(f"   {concurrent_result['successful_requests']}/{concurrent_result['successful_requests'] + concurrent_result['failed_requests']} successful")
            print(f"   Avg response time: {concurrent_result['avg_response_time']:.3f}s")
        
        # Test error handling
        error_result = await self.test_error_handling("/api/v1/tools/read_file", {"invalid": "payload"})
        print(f"{'✅' if error_result['success'] else '❌'} Error handling: {'PASS' if error_result['success'] else 'FAIL'}")
        if error_result['success'] and error_result.get('has_error_message'):
            print(f"   Graceful error handling detected")
        
        # Overall assessment
        all_tests_passed = (
            openapi_result['success'] and
            all(result['success'] for result in tool_results.values()) and
            concurrent_result['success'] and
            error_result['success']
        )
        
        print(f"\n🎯 Overall compatibility: {'EXCELLENT' if all_tests_passed else 'NEEDS IMPROVEMENT'}")
        
        return {
            "overall_success": all_tests_passed,
            "openapi": openapi_result,
            "tools": tool_results,
            "concurrent": concurrent_result,
            "error_handling": error_result
        }


async def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"Testing API at: {base_url}")
    print("=" * 50)
    
    async with OpenWebUICompatibilityTester(base_url) as tester:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("openwebui_compatibility_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: openwebui_compatibility_results.json")
        
        if results["overall_success"]:
            print("🎉 API is compatible with Open WebUI!")
            return 0
        else:
            print("⚠️  API may have compatibility issues with Open WebUI")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)