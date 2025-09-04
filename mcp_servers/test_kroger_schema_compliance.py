#!/usr/bin/env python3
"""Test script to validate that the Kroger MCP server's OpenAPI schema is JSON Schema 2020-12 compliant."""

import json
import sys
import requests
from typing import Any, Dict, List, Set


def find_refs(obj: Any, path: str = "") -> List[str]:
    """Recursively find all $ref occurrences in a JSON object."""
    refs = []
    if isinstance(obj, dict):
        if "$ref" in obj:
            refs.append(f"{path}.$ref = {obj['$ref']}")
        for key, value in obj.items():
            refs.extend(find_refs(value, f"{path}.{key}" if path else key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            refs.extend(find_refs(item, f"{path}[{i}]"))
    return refs


def find_problematic_fields(obj: Any, path: str = "") -> List[str]:
    """Find fields that may cause JSON Schema 2020-12 compatibility issues."""
    problematic = []
    problematic_keys = {
        "title", "examples", "x-examples", "$schema", "definitions",
        "$id", "$comment", "$defs", "const", "contentEncoding", 
        "contentMediaType", "if", "then", "else", "dependentSchemas",
        "dependentRequired", "unevaluatedProperties", "unevaluatedItems",
        "$vocabulary", "$dynamicRef", "$dynamicAnchor", "prefixItems"
    }
    
    if isinstance(obj, dict):
        for key in obj.keys():
            if key in problematic_keys:
                problematic.append(f"{path}.{key}" if path else key)
        for key, value in obj.items():
            problematic.extend(find_problematic_fields(value, f"{path}.{key}" if path else key))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            problematic.extend(find_problematic_fields(item, f"{path}[{i}]"))
    
    return problematic


def validate_schema_compliance(schema: Dict) -> tuple[bool, List[str]]:
    """Validate that an OpenAPI schema is JSON Schema 2020-12 compliant."""
    errors = []
    
    # Check for $ref references
    refs = find_refs(schema)
    if refs:
        errors.append(f"Found {len(refs)} $ref references:")
        errors.extend(refs[:5])  # Show first 5
        if len(refs) > 5:
            errors.append(f"... and {len(refs) - 5} more")
    
    # Check for problematic fields (but be lenient on some)
    problematic = find_problematic_fields(schema)
    # Filter out some that might be okay in certain contexts
    critical_problematic = [p for p in problematic if not any(
        okay in p for okay in ["openapi.info.title", "servers", "tags"]
    )]
    
    if critical_problematic:
        errors.append(f"Found {len(critical_problematic)} potentially problematic fields:")
        errors.extend(critical_problematic[:5])
        if len(critical_problematic) > 5:
            errors.append(f"... and {len(critical_problematic) - 5} more")
    
    # Check OpenAPI version
    if schema.get("openapi") != "3.1.0":
        errors.append(f"OpenAPI version should be 3.1.0, got: {schema.get('openapi')}")
    
    return len(errors) == 0, errors


def main():
    """Main test function."""
    print("Testing Kroger MCP Server OpenAPI Schema Compliance...")
    print("=" * 60)
    
    try:
        # Fetch the OpenAPI schema
        response = requests.get("http://localhost:9004/openapi.json", timeout=5)
        response.raise_for_status()
        schema = response.json()
        
        print(f"✓ Successfully fetched OpenAPI schema")
        print(f"  OpenAPI version: {schema.get('openapi')}")
        print(f"  Title: {schema.get('info', {}).get('title')}")
        print()
        
        # Validate compliance
        is_compliant, errors = validate_schema_compliance(schema)
        
        if is_compliant:
            print("✅ Schema is JSON Schema 2020-12 compliant!")
            print("   - No $ref references found")
            print("   - No problematic fields found")
            print("   - OpenAPI 3.1.0 version correctly set")
        else:
            print("❌ Schema has compliance issues:")
            for error in errors:
                print(f"   {error}")
            return 1
        
        # Test specific endpoints
        print("\n" + "=" * 60)
        print("Testing specific endpoints...")
        
        test_endpoints = [
            "/locations/search",
            "/products/search",
            "/cart"
        ]
        
        for endpoint in test_endpoints:
            if endpoint in schema.get("paths", {}):
                endpoint_schema = schema["paths"][endpoint]
                refs = find_refs(endpoint_schema)
                if refs:
                    print(f"❌ {endpoint}: Found {len(refs)} $ref references")
                else:
                    print(f"✅ {endpoint}: No $ref references")
            else:
                print(f"⚠️  {endpoint}: Not found in schema")
        
        # Check for validation error responses
        print("\n" + "=" * 60)
        print("Checking validation error responses...")
        
        validation_errors_found = False
        for path, methods in schema.get("paths", {}).items():
            for method, operation in methods.items():
                if isinstance(operation, dict) and "responses" in operation:
                    if "422" in operation["responses"]:
                        response_422 = operation["responses"]["422"]
                        if "content" in response_422:
                            for content_type, content in response_422["content"].items():
                                if "schema" in content:
                                    refs = find_refs(content["schema"])
                                    if refs:
                                        print(f"❌ {method.upper()} {path}: 422 response has $ref")
                                        validation_errors_found = True
        
        if not validation_errors_found:
            print("✅ All 422 validation error responses are properly inlined")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Schema is Claude Opus 4.1 compatible.")
        return 0
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server at http://localhost:9004")
        print("   Make sure the Kroger MCP server is running")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())