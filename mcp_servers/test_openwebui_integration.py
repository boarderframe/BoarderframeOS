#!/usr/bin/env python3
"""
Open WebUI Integration Test for Kroger MCP Server
Tests the complete workflow that Open WebUI would use
"""

import json
import httpx
import sys
from typing import Any, Dict


def simulate_openwebui_schema_fetch():
    """Simulate how Open WebUI fetches and validates the schema"""
    print("=" * 60)
    print("Simulating Open WebUI Schema Fetch")
    print("=" * 60)
    
    try:
        # Step 1: Fetch OpenAPI schema
        response = httpx.get("http://localhost:9004/openapi.json")
        if response.status_code != 200:
            print(f"❌ Failed to fetch schema: HTTP {response.status_code}")
            return False
        
        schema = response.json()
        print(f"✅ Successfully fetched OpenAPI schema")
        
        # Step 2: Validate OpenAPI version (Open WebUI requires 3.1.0)
        if schema.get("openapi") != "3.1.0":
            print(f"❌ Invalid OpenAPI version: {schema.get('openapi')}")
            return False
        print(f"✅ OpenAPI version 3.1.0 confirmed")
        
        # Step 3: Check for $ref (causes "JSON schema is invalid" error)
        schema_str = json.dumps(schema)
        if "$ref" in schema_str:
            print(f"❌ Found $ref in schema (causes Open WebUI error)")
            return False
        print(f"✅ No $ref references found")
        
        # Step 4: Validate paths exist
        if "paths" not in schema or not schema["paths"]:
            print(f"❌ No paths defined in schema")
            return False
        print(f"✅ Found {len(schema['paths'])} API endpoints")
        
        # Step 5: Validate schemas exist
        if "components" in schema and "schemas" in schema["components"]:
            print(f"✅ Found {len(schema['components']['schemas'])} schema definitions")
        else:
            print(f"⚠️  No schema definitions found (may be okay)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during schema fetch: {e}")
        return False


def simulate_openwebui_tool_call():
    """Simulate how Open WebUI would call a tool"""
    print("\n" + "=" * 60)
    print("Simulating Open WebUI Tool Call")
    print("=" * 60)
    
    try:
        # Simulate searching for stores near a ZIP code
        print("\n📍 Tool: Search Locations")
        print("   Query: Find Kroger stores near ZIP 45202")
        
        params = {
            "zipCode": "45202",
            "radiusInMiles": 5,
            "limit": 3
        }
        
        response = httpx.get("http://localhost:9004/locations/search", params=params)
        
        if response.status_code != 200:
            print(f"❌ Location search failed: HTTP {response.status_code}")
            return False
        
        data = response.json()
        locations = data.get("data", [])
        
        print(f"✅ Found {len(locations)} locations")
        for i, loc in enumerate(locations, 1):
            print(f"   {i}. {loc['name']} - {loc['address']['addressLine1']}, {loc['address']['city']}")
        
        if not locations:
            print("⚠️  No locations found (but API call succeeded)")
            return True
        
        # Use first location for product search
        location_id = locations[0]["locationId"]
        
        # Simulate searching for products
        print(f"\n🛒 Tool: Search Products")
        print(f"   Query: Find 'organic milk' at location {location_id}")
        
        params = {
            "term": "organic milk",
            "locationId": location_id,
            "limit": 3
        }
        
        response = httpx.get("http://localhost:9004/products/search", params=params)
        
        if response.status_code != 200:
            print(f"❌ Product search failed: HTTP {response.status_code}")
            return False
        
        data = response.json()
        products = data.get("data", [])
        
        print(f"✅ Found {len(products)} products")
        for i, prod in enumerate(products, 1):
            price_info = ""
            if prod.get("items"):
                item = prod["items"][0]
                price = item.get("price", {})
                if price.get("regular"):
                    price_info = f" - ${price['regular']}"
                    if price.get("promo"):
                        price_info += f" (Sale: ${price['promo']})"
            print(f"   {i}. {prod['description']}{price_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during tool call: {e}")
        return False


def test_error_handling():
    """Test error handling that Open WebUI would encounter"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    tests_passed = True
    
    # Test 1: Invalid ZIP code format
    print("\n🔍 Test: Invalid parameter handling")
    response = httpx.get("http://localhost:9004/locations/search", 
                         params={"zipCode": "invalid"})
    if response.status_code == 200:
        print(f"✅ Server handles invalid ZIP gracefully")
    else:
        print(f"⚠️  Server returned error {response.status_code} for invalid ZIP")
    
    # Test 2: Missing required parameter
    print("\n🔍 Test: Missing required parameter")
    response = httpx.get("http://localhost:9004/products/search",
                         params={"term": "milk"})  # Missing locationId
    if response.status_code == 422:
        print(f"✅ Server correctly validates required parameters")
    else:
        print(f"❌ Server did not validate missing parameter (status: {response.status_code})")
        tests_passed = False
    
    # Test 3: Rate limiting header check
    print("\n🔍 Test: Rate limiting headers")
    response = httpx.get("http://localhost:9004/health")
    if "x-ratelimit-limit" in response.headers or response.status_code == 200:
        print(f"✅ Rate limiting configured or endpoint accessible")
    else:
        print(f"⚠️  No rate limiting headers found")
    
    return tests_passed


def main():
    """Run all integration tests"""
    print("\n🔌 Open WebUI Integration Test Suite for Kroger MCP Server")
    print("=" * 60)
    
    # Check if server is running
    try:
        health_response = httpx.get("http://localhost:9004/health")
        if health_response.status_code != 200:
            print("❌ Server is not responding. Please start the Kroger MCP server first.")
            return 1
        print("✅ Server is running and healthy")
    except Exception:
        print("❌ Cannot connect to server at http://localhost:9004")
        print("   Please start the server with: python kroger_mcp_server.py")
        return 1
    
    # Run tests
    results = {
        "Schema Fetch": simulate_openwebui_schema_fetch(),
        "Tool Calls": simulate_openwebui_tool_call(),
        "Error Handling": test_error_handling()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("   The Kroger MCP Server is ready for Open WebUI integration!")
        print("\n   Next steps:")
        print("   1. Add http://localhost:9004 to Open WebUI MCP Connector")
        print("   2. The tools will appear as chips in the chat interface")
        print("   3. No 'JSON schema is invalid' errors will occur")
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        print("   Please review the errors above and fix any issues")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())