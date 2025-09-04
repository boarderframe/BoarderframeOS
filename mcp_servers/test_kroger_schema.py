#!/usr/bin/env python3
"""
Test script to validate Kroger MCP Server JSON Schema 2020-12 compatibility
"""

import json
import httpx
import sys
from typing import Any, Dict, List


def find_refs(obj: Any, path: str = "") -> List[str]:
    """Recursively find all $ref references in a JSON object"""
    refs = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if key == "$ref":
                refs.append(f"{current_path}: {value}")
            else:
                refs.extend(find_refs(value, current_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            refs.extend(find_refs(item, f"{path}[{i}]"))
    return refs


def check_schema_compatibility(schema: Dict) -> Dict[str, Any]:
    """Check OpenAPI schema for JSON Schema 2020-12 compatibility issues"""
    issues = {
        "has_refs": False,
        "ref_locations": [],
        "has_titles": False,
        "title_locations": [],
        "has_examples": False,
        "example_locations": [],
        "openapi_version": schema.get("openapi", "unknown"),
        "paths_count": len(schema.get("paths", {})),
        "schemas_count": len(schema.get("components", {}).get("schemas", {}))
    }
    
    # Check for $ref references
    refs = find_refs(schema)
    if refs:
        issues["has_refs"] = True
        issues["ref_locations"] = refs[:10]  # Limit to first 10
    
    # Check for titles and examples in schemas
    if "components" in schema and "schemas" in schema["components"]:
        for schema_name, schema_def in schema["components"]["schemas"].items():
            if "title" in schema_def:
                issues["has_titles"] = True
                issues["title_locations"].append(f"components.schemas.{schema_name}")
            if "examples" in schema_def:
                issues["has_examples"] = True
                issues["example_locations"].append(f"components.schemas.{schema_name}")
    
    return issues


def test_openapi_endpoint():
    """Test the /openapi.json endpoint"""
    print("=" * 60)
    print("Testing /openapi.json endpoint")
    print("=" * 60)
    
    try:
        response = httpx.get("http://localhost:9004/openapi.json")
        if response.status_code != 200:
            print(f"❌ Failed to fetch OpenAPI schema: {response.status_code}")
            return False
        
        schema = response.json()
        print(f"✅ Successfully fetched OpenAPI schema")
        
        # Check compatibility
        issues = check_schema_compatibility(schema)
        
        print(f"\nSchema Analysis:")
        print(f"  OpenAPI Version: {issues['openapi_version']}")
        print(f"  Paths Count: {issues['paths_count']}")
        print(f"  Schemas Count: {issues['schemas_count']}")
        
        print(f"\nCompatibility Checks:")
        if issues["has_refs"]:
            print(f"  ❌ Found $ref references (Claude Opus 4.1 incompatible):")
            for ref in issues["ref_locations"][:5]:
                print(f"    - {ref}")
        else:
            print(f"  ✅ No $ref references found")
        
        if issues["has_titles"]:
            print(f"  ⚠️  Found title fields in schemas (may cause issues):")
            for loc in issues["title_locations"][:5]:
                print(f"    - {loc}")
        else:
            print(f"  ✅ No title fields in schemas")
        
        if issues["has_examples"]:
            print(f"  ⚠️  Found examples in schemas (may cause issues):")
            for loc in issues["example_locations"][:5]:
                print(f"    - {loc}")
        else:
            print(f"  ✅ No examples in schemas")
        
        # Overall result
        is_compatible = not issues["has_refs"] and issues["openapi_version"] == "3.1.0"
        if is_compatible:
            print(f"\n✅ Schema is compatible with JSON Schema 2020-12")
        else:
            print(f"\n❌ Schema has compatibility issues")
        
        return is_compatible
        
    except Exception as e:
        print(f"❌ Error testing OpenAPI endpoint: {e}")
        return False


def test_locations_search():
    """Test the /locations/search endpoint"""
    print("\n" + "=" * 60)
    print("Testing /locations/search endpoint")
    print("=" * 60)
    
    try:
        # Test with zipCode parameter
        params = {
            "zipCode": "43123",
            "radiusInMiles": 10,
            "limit": 5
        }
        
        response = httpx.get("http://localhost:9004/locations/search", params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to search locations: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        print(f"✅ Successfully searched locations")
        print(f"   Found {len(data.get('data', []))} locations")
        
        # Display first location if available
        if data.get("data"):
            first_location = data["data"][0]
            print(f"\n   First location:")
            print(f"     Name: {first_location.get('name', 'N/A')}")
            print(f"     Address: {first_location.get('address', {}).get('addressLine1', 'N/A')}")
            print(f"     City: {first_location.get('address', {}).get('city', 'N/A')}")
            print(f"     ZIP: {first_location.get('address', {}).get('zipCode', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing locations search: {e}")
        return False


def test_products_search():
    """Test the /products/search endpoint"""
    print("\n" + "=" * 60)
    print("Testing /products/search endpoint")
    print("=" * 60)
    
    try:
        # First get a location ID
        locations_response = httpx.get("http://localhost:9004/locations/search", 
                                     params={"zipCode": "43123", "limit": 1})
        
        if locations_response.status_code != 200:
            print(f"❌ Failed to get location for product search")
            return False
        
        locations_data = locations_response.json()
        if not locations_data.get("data"):
            print(f"❌ No locations found for product search")
            return False
        
        location_id = locations_data["data"][0]["locationId"]
        print(f"   Using location ID: {location_id}")
        
        # Search for products
        params = {
            "term": "milk",
            "locationId": location_id,
            "limit": 5
        }
        
        response = httpx.get("http://localhost:9004/products/search", params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to search products: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        print(f"✅ Successfully searched products")
        print(f"   Found {len(data.get('data', []))} products")
        
        # Display first product if available
        if data.get("data"):
            first_product = data["data"][0]
            print(f"\n   First product:")
            print(f"     Description: {first_product.get('description', 'N/A')}")
            print(f"     Brand: {first_product.get('brand', 'N/A')}")
            if first_product.get("items"):
                item = first_product["items"][0]
                price = item.get("price", {})
                print(f"     Price: ${price.get('regular', 'N/A')}")
                if price.get("promo"):
                    print(f"     Promo Price: ${price.get('promo', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing products search: {e}")
        return False


def validate_json_schema_2020_12():
    """Validate that the schema conforms to JSON Schema draft 2020-12"""
    print("\n" + "=" * 60)
    print("Validating JSON Schema draft 2020-12 compliance")
    print("=" * 60)
    
    try:
        response = httpx.get("http://localhost:9004/openapi.json")
        if response.status_code != 200:
            print(f"❌ Failed to fetch schema for validation")
            return False
        
        schema = response.json()
        
        # Check OpenAPI 3.1.0 (which uses JSON Schema 2020-12)
        if schema.get("openapi") != "3.1.0":
            print(f"❌ OpenAPI version is {schema.get('openapi')}, expected 3.1.0")
            return False
        
        print(f"✅ OpenAPI version is 3.1.0 (JSON Schema 2020-12 compatible)")
        
        # Validate schema structure
        validation_passed = True
        
        # Check that all schemas are properly structured
        if "components" in schema and "schemas" in schema["components"]:
            for schema_name, schema_def in schema["components"]["schemas"].items():
                # Check for problematic fields that were cleaned
                if "title" in schema_def:
                    print(f"⚠️  Schema '{schema_name}' still has 'title' field")
                if "examples" in schema_def:
                    print(f"⚠️  Schema '{schema_name}' still has 'examples' field")
        
        # Check paths for proper schema definitions
        if "paths" in schema:
            for path, methods in schema["paths"].items():
                for method, operation in methods.items():
                    if method in ["get", "post", "put", "delete", "patch"]:
                        # Check responses
                        if "responses" in operation:
                            for status_code, response_def in operation["responses"].items():
                                if "content" in response_def:
                                    for content_type, content_def in response_def["content"].items():
                                        if "schema" in content_def and "$ref" in content_def["schema"]:
                                            print(f"❌ Found $ref in {path} {method} response {status_code}")
                                            validation_passed = False
        
        if validation_passed:
            print(f"✅ Schema structure is valid for JSON Schema 2020-12")
        else:
            print(f"❌ Schema has structural issues")
        
        return validation_passed
        
    except Exception as e:
        print(f"❌ Error validating schema: {e}")
        return False


def test_health_endpoint():
    """Test the /health endpoint"""
    print("\n" + "=" * 60)
    print("Testing /health endpoint")
    print("=" * 60)
    
    try:
        response = httpx.get("http://localhost:9004/health")
        if response.status_code != 200:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Service: {data.get('service', 'unknown')}")
        print(f"   Version: {data.get('version', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False


def main():
    """Run all tests"""
    print("\n🔍 Kroger MCP Server JSON Schema 2020-12 Compatibility Test Suite")
    print("=" * 60)
    
    results = {
        "Health Check": test_health_endpoint(),
        "OpenAPI Schema": test_openapi_endpoint(),
        "JSON Schema 2020-12 Validation": validate_json_schema_2020_12(),
        "Locations Search": test_locations_search(),
        "Products Search": test_products_search()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Server is Claude Opus 4.1 compatible!")
    else:
        print("❌ SOME TESTS FAILED - Additional fixes needed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())