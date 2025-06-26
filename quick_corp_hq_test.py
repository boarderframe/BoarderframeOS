#!/usr/bin/env python3
"""
Quick Corporate HQ Test - Verify Basic Functionality
Run this after starting Corporate HQ to ensure it's working properly
"""

import httpx
import asyncio
import time
from datetime import datetime


async def quick_test():
    """Run quick functionality test"""
    base_url = "http://localhost:8888"
    
    print("🔍 Quick Corporate HQ Functionality Test")
    print("=" * 50)
    print(f"Target: {base_url}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50 + "\n")
    
    tests_passed = 0
    tests_total = 0
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Test 1: Homepage
        tests_total += 1
        try:
            print("1. Testing homepage... ", end="", flush=True)
            start = time.time()
            response = await client.get(base_url)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                print(f"✅ OK ({elapsed:.2f}s)")
                tests_passed += 1
            else:
                print(f"❌ Failed (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 2: Agents API
        tests_total += 1
        try:
            print("2. Testing agents API... ", end="", flush=True)
            start = time.time()
            response = await client.get(f"{base_url}/api/agents")
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ OK ({elapsed:.2f}s) - {len(data)} agents")
                tests_passed += 1
            else:
                print(f"❌ Failed (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 3: Global Refresh
        tests_total += 1
        try:
            print("3. Testing global refresh API... ", end="", flush=True)
            start = time.time()
            response = await client.post(f"{base_url}/api/global/refresh")
            elapsed = time.time() - start
            
            if response.status_code == 200:
                print(f"✅ OK ({elapsed:.2f}s)")
                tests_passed += 1
            else:
                print(f"❌ Failed (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 4: Server Status
        tests_total += 1
        try:
            print("4. Testing server status API... ", end="", flush=True)
            start = time.time()
            response = await client.get(f"{base_url}/api/servers")
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                healthy = sum(1 for s in data.values() if s.get('status') == 'healthy')
                print(f"✅ OK ({elapsed:.2f}s) - {healthy}/{len(data)} healthy")
                tests_passed += 1
            else:
                print(f"❌ Failed (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 5: Health endpoint
        tests_total += 1
        try:
            print("5. Testing health endpoint... ", end="", flush=True)
            start = time.time()
            response = await client.get(f"{base_url}/health")
            elapsed = time.time() - start
            
            if response.status_code == 200:
                print(f"✅ OK ({elapsed:.2f}s)")
                tests_passed += 1
            else:
                print(f"❌ Failed (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Summary
    print(f"\n{'=' * 50}")
    print(f"Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed! Corporate HQ is working properly.")
    elif tests_passed > 0:
        print("⚠️  Some tests failed. Check the errors above.")
    else:
        print("❌ All tests failed. Corporate HQ may not be running.")
    
    print(f"{'=' * 50}")
    
    # Performance notes
    if tests_passed > 0:
        print("\n📊 Performance Notes:")
        print("- Responses under 3s: Good ✅")
        print("- Responses 3-10s: Acceptable ⚠️")
        print("- Responses over 10s: Needs optimization ❌")
        
    return tests_passed == tests_total


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    exit(0 if success else 1)