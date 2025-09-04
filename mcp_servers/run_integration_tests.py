#!/usr/bin/env python3
"""
Simplified Integration Test Runner for MCP-UI System
Runs comprehensive tests without browser dependencies
"""

import asyncio
import json
import time
import httpx
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedIntegrationTester:
    """Simplified integration tester without browser dependencies"""
    
    def __init__(self):
        self.base_urls = {
            "main_api": "http://localhost:8000",
            "filesystem_server": "http://localhost:9001", 
            "kroger_server": "http://localhost:9003",
            "playwright_server": "http://localhost:9004",
            "kroger_enhanced": "http://localhost:9005",
            "kroger_v2": "http://localhost:9010"
        }
        self.test_results = {}
        self.performance_metrics = {}
        self.security_findings = []
        
    async def run_all_tests(self):
        """Run all available tests"""
        logger.info("🚀 Starting Simplified MCP-UI Integration Testing")
        
        try:
            # 1. Service Health Tests
            await self.test_service_health()
            
            # 2. MCP-UI Protocol Tests  
            await self.test_mcp_ui_protocol()
            
            # 3. Kroger Integration Tests
            await self.test_kroger_integration()
            
            # 4. Performance Tests
            await self.test_performance()
            
            # 5. Security Tests
            await self.test_security()
            
            # Generate report
            report = self.generate_report()
            
            # Save to file
            with open("integration_test_report.json", "w") as f:
                json.dump(report, f, indent=2)
            
            logger.info("✅ All tests completed successfully")
            return report
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {str(e)}")
            raise

    async def test_service_health(self):
        """Test all service health endpoints"""
        logger.info("🏥 Testing Service Health")
        
        health_results = {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for service_name, base_url in self.base_urls.items():
                try:
                    start_time = time.time()
                    response = await client.get(f"{base_url}/health")
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    
                    if response.status_code == 200:
                        try:
                            health_data = response.json()
                        except:
                            health_data = {"status": "ok"}
                        
                        health_results[service_name] = {
                            "status": "healthy",
                            "response_time_ms": response_time,
                            "health_data": health_data
                        }
                        logger.info(f"✅ {service_name}: Healthy ({response_time:.1f}ms)")
                    else:
                        health_results[service_name] = {
                            "status": "unhealthy",
                            "status_code": response.status_code,
                            "response_time_ms": response_time
                        }
                        logger.warning(f"⚠️  {service_name}: Unhealthy (Status: {response.status_code})")
                        
                except Exception as e:
                    health_results[service_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    logger.error(f"❌ {service_name}: Error - {str(e)}")
        
        self.test_results["service_health"] = health_results

    async def test_mcp_ui_protocol(self):
        """Test MCP-UI Protocol compliance"""
        logger.info("🔌 Testing MCP-UI Protocol")
        
        protocol_results = {}
        ui_servers = ["kroger_enhanced", "kroger_v2"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for server_name in ui_servers:
                if server_name not in self.base_urls:
                    continue
                    
                base_url = self.base_urls[server_name]
                server_results = {}
                
                try:
                    # Test UI registry
                    registry_response = await client.get(f"{base_url}/ui/registry")
                    if registry_response.status_code == 200:
                        registry_data = registry_response.json()
                        server_results["ui_registry"] = {
                            "available": True,
                            "components_count": len(registry_data.get("components", [])),
                            "data": registry_data
                        }
                        logger.info(f"✅ {server_name}: UI Registry available ({len(registry_data.get('components', []))} components)")
                    else:
                        server_results["ui_registry"] = {
                            "available": False,
                            "status_code": registry_response.status_code
                        }
                    
                    # Test UI endpoints
                    ui_endpoints = [
                        "/ui/product-search?query=test&theme=light",
                        "/ui/shopping-list?theme=light",
                        "/ui/product-comparison?theme=light"
                    ]
                    
                    for endpoint in ui_endpoints:
                        try:
                            ui_response = await client.get(f"{base_url}{endpoint}")
                            endpoint_key = endpoint.split('?')[0].replace('/', '_').replace('-', '_')
                            
                            server_results[f"endpoint{endpoint_key}"] = {
                                "status_code": ui_response.status_code,
                                "content_type": ui_response.headers.get("content-type", ""),
                                "response_size": len(ui_response.content),
                                "available": ui_response.status_code == 200
                            }
                            
                            if ui_response.status_code == 200:
                                logger.info(f"✅ {server_name}: {endpoint} - Working")
                            else:
                                logger.warning(f"⚠️  {server_name}: {endpoint} - Status {ui_response.status_code}")
                                
                        except Exception as e:
                            endpoint_key = endpoint.split('?')[0].replace('/', '_').replace('-', '_')
                            server_results[f"endpoint{endpoint_key}"] = {
                                "error": str(e),
                                "available": False
                            }
                    
                except Exception as e:
                    server_results["error"] = str(e)
                    logger.error(f"❌ {server_name}: Protocol test failed - {str(e)}")
                
                protocol_results[server_name] = server_results
        
        self.test_results["mcp_ui_protocol"] = protocol_results

    async def test_kroger_integration(self):
        """Test Kroger API integration"""
        logger.info("🛒 Testing Kroger Integration")
        
        kroger_results = {}
        kroger_servers = ["kroger_server", "kroger_enhanced", "kroger_v2"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for server_name in kroger_servers:
                if server_name not in self.base_urls:
                    continue
                    
                base_url = self.base_urls[server_name]
                server_results = {}
                
                try:
                    # Test product search
                    search_terms = ["milk", "bread", "eggs"]
                    search_results = {}
                    
                    for term in search_terms:
                        try:
                            search_response = await client.get(f"{base_url}/products/search?term={term}")
                            
                            if search_response.status_code == 200:
                                search_data = search_response.json()
                                products_count = len(search_data.get("products", []))
                                
                                search_results[term] = {
                                    "status": "success",
                                    "products_count": products_count,
                                    "has_valid_structure": "products" in search_data
                                }
                                logger.info(f"✅ {server_name}: Search '{term}' - {products_count} products")
                            else:
                                search_results[term] = {
                                    "status": "error",
                                    "status_code": search_response.status_code
                                }
                                logger.warning(f"⚠️  {server_name}: Search '{term}' failed - {search_response.status_code}")
                                
                        except Exception as e:
                            search_results[term] = {
                                "status": "error",
                                "error": str(e)
                            }
                    
                    server_results["product_search"] = search_results
                    
                    # Test authentication status (if available)
                    try:
                        auth_response = await client.get(f"{base_url}/auth/status")
                        if auth_response.status_code == 200:
                            auth_data = auth_response.json()
                            server_results["authentication"] = {
                                "status": "available",
                                "authenticated": auth_data.get("authenticated", False),
                                "data": auth_data
                            }
                        else:
                            server_results["authentication"] = {
                                "status": "unavailable",
                                "status_code": auth_response.status_code
                            }
                    except:
                        server_results["authentication"] = {"status": "not_implemented"}
                    
                    # Test API documentation
                    try:
                        docs_response = await client.get(f"{base_url}/openapi.json")
                        if docs_response.status_code == 200:
                            docs_data = docs_response.json()
                            endpoints_count = len(docs_data.get("paths", {}))
                            server_results["api_documentation"] = {
                                "available": True,
                                "endpoints_count": endpoints_count
                            }
                            logger.info(f"✅ {server_name}: API docs available ({endpoints_count} endpoints)")
                        else:
                            server_results["api_documentation"] = {"available": False}
                    except:
                        server_results["api_documentation"] = {"available": False}
                        
                except Exception as e:
                    server_results["error"] = str(e)
                    logger.error(f"❌ {server_name}: Kroger integration test failed - {str(e)}")
                
                kroger_results[server_name] = server_results
        
        self.test_results["kroger_integration"] = kroger_results

    async def test_performance(self):
        """Test performance metrics"""
        logger.info("⚡ Testing Performance")
        
        performance_results = {}
        
        # Test response times
        async with httpx.AsyncClient(timeout=30.0) as client:
            for service_name, base_url in self.base_urls.items():
                try:
                    # Test multiple requests for average
                    response_times = []
                    
                    for i in range(5):
                        start_time = time.time()
                        response = await client.get(f"{base_url}/health")
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            response_times.append((end_time - start_time) * 1000)
                    
                    if response_times:
                        avg_time = sum(response_times) / len(response_times)
                        min_time = min(response_times)
                        max_time = max(response_times)
                        
                        performance_results[service_name] = {
                            "avg_response_time_ms": avg_time,
                            "min_response_time_ms": min_time,
                            "max_response_time_ms": max_time,
                            "samples": len(response_times)
                        }
                        
                        logger.info(f"📊 {service_name}: Avg {avg_time:.1f}ms (min: {min_time:.1f}ms, max: {max_time:.1f}ms)")
                    
                except Exception as e:
                    performance_results[service_name] = {"error": str(e)}
        
        # Test concurrent load
        logger.info("🔥 Testing Concurrent Load")
        load_results = await self.test_concurrent_load()
        performance_results["load_testing"] = load_results
        
        self.performance_metrics = performance_results
        self.test_results["performance"] = performance_results

    async def test_concurrent_load(self):
        """Test concurrent load handling"""
        target_url = f"{self.base_urls['kroger_enhanced']}/products/search?term=milk"
        concurrent_requests = 10
        
        async def make_request():
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    start_time = time.time()
                    response = await client.get(target_url)
                    end_time = time.time()
                    
                    return {
                        "success": response.status_code == 200,
                        "status_code": response.status_code,
                        "response_time_ms": (end_time - start_time) * 1000
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "response_time_ms": None
                    }
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]
        
        if successful:
            response_times = [r["response_time_ms"] for r in successful if r["response_time_ms"]]
            avg_response = sum(response_times) / len(response_times) if response_times else 0
        else:
            avg_response = 0
        
        load_results = {
            "total_requests": concurrent_requests,
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate_percent": (len(successful) / concurrent_requests) * 100,
            "total_time_seconds": total_time,
            "requests_per_second": concurrent_requests / total_time,
            "avg_response_time_ms": avg_response
        }
        
        logger.info(f"🔥 Load Test: {load_results['success_rate_percent']:.1f}% success rate, {load_results['requests_per_second']:.1f} req/s")
        
        return load_results

    async def test_security(self):
        """Test basic security measures"""
        logger.info("🔒 Testing Security")
        
        security_findings = []
        
        # Test for exposed config endpoints
        async with httpx.AsyncClient(timeout=30.0) as client:
            for service_name, base_url in self.base_urls.items():
                try:
                    # Check for common security issues
                    config_response = await client.get(f"{base_url}/config")
                    if config_response.status_code == 200:
                        security_findings.append({
                            "service": service_name,
                            "severity": "MEDIUM",
                            "issue": "Config endpoint exposed",
                            "description": f"Config endpoint accessible at {base_url}/config"
                        })
                except:
                    pass  # Expected for most services
                
                try:
                    # Test CORS headers
                    options_response = await client.options(f"{base_url}/health", 
                                                           headers={"Origin": "https://malicious-site.com"})
                    
                    cors_header = options_response.headers.get("Access-Control-Allow-Origin")
                    if cors_header == "*":
                        security_findings.append({
                            "service": service_name,
                            "severity": "LOW",
                            "issue": "Permissive CORS policy",
                            "description": "CORS allows requests from any origin"
                        })
                except:
                    pass
        
        # Test input validation
        malicious_inputs = ["<script>alert('xss')</script>", "'; DROP TABLE users; --"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for malicious_input in malicious_inputs:
                try:
                    response = await client.get(f"{self.base_urls['kroger_enhanced']}/products/search?term={malicious_input}")
                    if response.status_code == 200 and malicious_input in response.text:
                        security_findings.append({
                            "service": "kroger_enhanced",
                            "severity": "HIGH",
                            "issue": "Potential XSS vulnerability",
                            "description": f"Malicious input reflected in response: {malicious_input}"
                        })
                except:
                    pass
        
        self.security_findings = security_findings
        self.test_results["security"] = security_findings
        
        if security_findings:
            logger.warning(f"⚠️  Found {len(security_findings)} security findings")
            for finding in security_findings:
                logger.warning(f"   {finding['severity']}: {finding['issue']} in {finding['service']}")
        else:
            logger.info("✅ No critical security issues found")

    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating Test Report")
        
        # Calculate metrics
        total_services = len(self.base_urls)
        healthy_services = sum(1 for result in self.test_results.get("service_health", {}).values() 
                             if result.get("status") == "healthy")
        
        health_score = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        # Security summary
        security_summary = {}
        if self.security_findings:
            by_severity = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for finding in self.security_findings:
                severity = finding.get("severity", "LOW")
                by_severity[severity] += 1
            security_summary = {
                "total_findings": len(self.security_findings),
                "by_severity": by_severity
            }
        else:
            security_summary = {"total_findings": 0, "by_severity": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}
        
        # Performance summary
        performance_summary = {}
        if self.performance_metrics:
            all_times = []
            for service_data in self.performance_metrics.values():
                if isinstance(service_data, dict) and "avg_response_time_ms" in service_data:
                    all_times.append(service_data["avg_response_time_ms"])
            
            if all_times:
                performance_summary = {
                    "avg_response_time_ms": sum(all_times) / len(all_times),
                    "slowest_service_ms": max(all_times),
                    "fastest_service_ms": min(all_times)
                }
        
        # Generate recommendations
        recommendations = []
        
        if healthy_services < total_services:
            recommendations.append({
                "priority": "HIGH",
                "category": "Service Health",
                "title": "Fix Unhealthy Services",
                "description": f"{total_services - healthy_services} services are unhealthy"
            })
        
        if security_summary["by_severity"]["HIGH"] > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Security",
                "title": "Address Critical Security Issues",
                "description": f"Found {security_summary['by_severity']['HIGH']} high-severity security issues"
            })
        
        if performance_summary.get("avg_response_time_ms", 0) > 1000:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Performance",
                "title": "Optimize Response Times",
                "description": f"Average response time is {performance_summary.get('avg_response_time_ms', 0):.1f}ms"
            })
        
        # Production readiness assessment
        if health_score >= 90 and security_summary["by_severity"]["HIGH"] == 0:
            readiness = "READY"
        elif health_score >= 70 and security_summary["by_severity"]["HIGH"] <= 1:
            readiness = "NEEDS_MINOR_FIXES"
        else:
            readiness = "NOT_READY"
        
        report = {
            "test_execution_summary": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "health_score": health_score,
                "total_services": total_services,
                "healthy_services": healthy_services,
                "production_readiness": readiness
            },
            "service_health_summary": {
                "total_services": total_services,
                "healthy_services": healthy_services,
                "unhealthy_services": total_services - healthy_services,
                "health_percentage": health_score
            },
            "security_summary": security_summary,
            "performance_summary": performance_summary,
            "recommendations": recommendations,
            "detailed_results": self.test_results,
            "production_readiness_assessment": {
                "status": readiness,
                "health_score": health_score,
                "critical_blockers": security_summary["by_severity"]["HIGH"],
                "estimated_fix_time": "1-2 weeks" if readiness == "NEEDS_MINOR_FIXES" else "Ready" if readiness == "READY" else "2-4 weeks"
            }
        }
        
        return report

    def print_summary(self, report):
        """Print test summary to console"""
        print("\n" + "="*80)
        print("🎯 MCP-UI SYSTEM INTEGRATION TEST RESULTS")
        print("="*80)
        print(f"Health Score: {report['test_execution_summary']['health_score']:.1f}/100")
        print(f"Services Tested: {report['service_health_summary']['total_services']}")
        print(f"Healthy Services: {report['service_health_summary']['healthy_services']}")
        print(f"Production Readiness: {report['production_readiness_assessment']['status']}")
        
        if report['security_summary']['total_findings'] > 0:
            print(f"\n🔒 Security Findings: {report['security_summary']['total_findings']}")
            for severity, count in report['security_summary']['by_severity'].items():
                if count > 0:
                    print(f"   {severity}: {count}")
        
        if report['performance_summary']:
            print(f"\n⚡ Performance:")
            print(f"   Average Response Time: {report['performance_summary'].get('avg_response_time_ms', 0):.1f}ms")
        
        if report['recommendations']:
            print(f"\n🔥 TOP RECOMMENDATIONS:")
            for rec in report['recommendations'][:3]:
                print(f"   • [{rec['priority']}] {rec['title']}")
        
        print(f"\n📊 Full report saved to: integration_test_report.json")
        print("="*80)


async def main():
    """Run the simplified integration test suite"""
    tester = SimplifiedIntegrationTester()
    
    try:
        report = await tester.run_all_tests()
        tester.print_summary(report)
        return report
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())