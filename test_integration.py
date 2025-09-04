#!/usr/bin/env python3
"""
Comprehensive Integration Test for LangGraph Multi-Agent System with Open WebUI
Tests the complete flow: Open WebUI → Pipeline → LangGraph backend
"""

import requests
import json
import time
import sys
from typing import Dict, Any


class IntegrationTester:
    def __init__(self):
        self.pipeline_url = "http://localhost:9099"
        self.langgraph_url = "http://localhost:9000"
        self.openwebui_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:5173"
        self.pipeline_api_key = "0p3n-w3bu!"
        
    def test_service_health(self, name: str, url: str, endpoint: str = "") -> bool:
        """Test if a service is responding"""
        try:
            response = requests.get(f"{url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} is healthy (HTTP {response.status_code})")
                return True
            else:
                print(f"⚠️  {name} responded with HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ {name} is not responding: {e}")
            return False

    def test_pipeline_models(self) -> bool:
        """Test pipeline server models endpoint"""
        try:
            headers = {"Authorization": f"Bearer {self.pipeline_api_key}"}
            response = requests.get(f"{self.pipeline_url}/models", headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                
                # Check for our multi-agent model
                multi_agent_found = False
                for model in models:
                    if model.get("id") == "langgraph.multi-agent":
                        multi_agent_found = True
                        print(f"✅ Multi-Agent model found: {model.get('name')}")
                        break
                
                if multi_agent_found:
                    print(f"✅ Pipeline server has {len(models)} model(s) available")
                    return True
                else:
                    print("❌ Multi-Agent model not found in pipeline")
                    return False
            else:
                print(f"❌ Pipeline models endpoint failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Pipeline models test failed: {e}")
            return False

    def test_langgraph_direct(self) -> bool:
        """Test direct connection to LangGraph backend"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.langgraph_url}/test", timeout=5)
            if response.status_code == 200:
                print(f"✅ LangGraph backend is responding: {response.json()}")
                return True
            else:
                print(f"❌ LangGraph backend test failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ LangGraph direct test failed: {e}")
            return False

    def test_pipeline_to_langgraph_flow(self) -> bool:
        """Test the complete flow through pipeline to LangGraph"""
        try:
            headers = {
                "Authorization": f"Bearer {self.pipeline_api_key}",
                "Content-Type": "application/json"
            }
            
            # Simulate a chat completion request through the pipeline
            data = {
                "model": "langgraph.multi-agent",
                "messages": [
                    {"role": "user", "content": "Hello! This is a test message. Please respond briefly."}
                ],
                "stream": True
            }
            
            response = requests.post(
                f"{self.pipeline_url}/v1/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=15
            )
            
            if response.status_code == 200:
                print("✅ Pipeline → LangGraph flow initiated successfully")
                
                # Read first few chunks of streaming response
                chunk_count = 0
                for line in response.iter_lines():
                    if line:
                        chunk_count += 1
                        if chunk_count <= 3:  # Just read first few chunks
                            try:
                                line_str = line.decode('utf-8')
                                if line_str.startswith('data: '):
                                    data_part = line_str[6:]  # Remove 'data: ' prefix
                                    if data_part.strip() != '[DONE]':
                                        chunk_data = json.loads(data_part)
                                        if 'choices' in chunk_data:
                                            print(f"✅ Received streaming chunk {chunk_count}")
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                continue
                        else:
                            break
                
                print(f"✅ Successfully received {chunk_count} streaming chunks")
                return True
            else:
                print(f"❌ Pipeline flow failed: HTTP {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Pipeline to LangGraph flow test failed: {e}")
            return False

    def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ Frontend is accessible")
                return True
            else:
                print(f"❌ Frontend not accessible: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Frontend accessibility test failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🔬 Starting LangGraph Multi-Agent System Integration Tests")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Service Health Checks
        print("\n📋 1. Service Health Checks")
        results["pipeline_health"] = self.test_service_health("Pipeline Server", self.pipeline_url)
        results["langgraph_health"] = self.test_service_health("LangGraph Backend", self.langgraph_url, "/test")
        results["openwebui_health"] = self.test_service_health("Open WebUI Backend", self.openwebui_url)
        results["frontend_health"] = self.test_service_health("Frontend", self.frontend_url)
        
        # Test 2: Pipeline Models
        print("\n📋 2. Pipeline Models Test")
        results["pipeline_models"] = self.test_pipeline_models()
        
        # Test 3: LangGraph Direct
        print("\n📋 3. LangGraph Direct Connection Test")  
        results["langgraph_direct"] = self.test_langgraph_direct()
        
        # Test 4: Complete Flow
        print("\n📋 4. Complete Integration Flow Test")
        results["complete_flow"] = self.test_pipeline_to_langgraph_flow()
        
        # Test 5: Frontend Accessibility
        print("\n📋 5. Frontend Accessibility Test")
        results["frontend_access"] = self.test_frontend_accessibility()
        
        return results

    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! System is ready for user interaction.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
            return False


def main():
    """Main function to run integration tests"""
    tester = IntegrationTester()
    results = tester.run_all_tests()
    success = tester.print_summary(results)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()