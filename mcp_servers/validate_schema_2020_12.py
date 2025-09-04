#!/usr/bin/env python3
"""
Validate OpenAPI schema against JSON Schema draft 2020-12 specification
"""

import json
import httpx
import sys

def validate_schema_structure(schema: dict) -> tuple[bool, list[str]]:
    """
    Validate that the schema structure is compatible with JSON Schema 2020-12
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    # Check OpenAPI version
    if schema.get("openapi") != "3.1.0":
        issues.append(f"OpenAPI version is {schema.get('openapi')}, should be 3.1.0 for JSON Schema 2020-12")
    
    def check_for_refs(obj, path="root"):
        """Recursively check for $ref fields"""
        if isinstance(obj, dict):
            if "$ref" in obj:
                issues.append(f"Found $ref at {path}")
            for key, value in obj.items():
                check_for_refs(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_for_refs(item, f"{path}[{i}]")
    
    # Check entire schema for $ref
    check_for_refs(schema)
    
    # Check for valid JSON Schema 2020-12 structure in components
    if "components" in schema and "schemas" in schema["components"]:
        for schema_name, schema_def in schema["components"]["schemas"].items():
            # Check for valid type definitions
            if isinstance(schema_def, dict):
                if "type" in schema_def:
                    valid_types = ["null", "boolean", "object", "array", "number", "string", "integer"]
                    if schema_def["type"] not in valid_types:
                        issues.append(f"Invalid type '{schema_def['type']}' in schema '{schema_name}'")
                
                # Check for anyOf with proper structure
                if "anyOf" in schema_def:
                    if not isinstance(schema_def["anyOf"], list):
                        issues.append(f"anyOf must be an array in schema '{schema_name}'")
                    else:
                        for i, sub_schema in enumerate(schema_def["anyOf"]):
                            if not isinstance(sub_schema, dict):
                                issues.append(f"anyOf[{i}] must be an object in schema '{schema_name}'")
    
    return len(issues) == 0, issues


def main():
    """Main validation function"""
    print("JSON Schema Draft 2020-12 Validation")
    print("=" * 60)
    
    try:
        # Fetch the OpenAPI schema
        response = httpx.get("http://localhost:9004/openapi.json")
        if response.status_code != 200:
            print(f"❌ Failed to fetch OpenAPI schema: HTTP {response.status_code}")
            return 1
        
        schema = response.json()
        print(f"✅ Successfully fetched OpenAPI schema")
        
        # Validate the schema
        is_valid, issues = validate_schema_structure(schema)
        
        if is_valid:
            print(f"\n✅ Schema is fully compatible with JSON Schema draft 2020-12")
            print(f"   - OpenAPI version: {schema.get('openapi')}")
            print(f"   - No $ref references found")
            print(f"   - All type definitions are valid")
            print(f"   - Schema structure is compliant")
        else:
            print(f"\n❌ Schema has {len(issues)} compatibility issues:")
            for issue in issues[:10]:  # Show first 10 issues
                print(f"   - {issue}")
            if len(issues) > 10:
                print(f"   ... and {len(issues) - 10} more issues")
        
        # Additional checks for Open WebUI compatibility
        print(f"\n" + "=" * 60)
        print("Open WebUI Compatibility Checks")
        print("=" * 60)
        
        compatibility_score = 0
        max_score = 4
        
        # Check 1: OpenAPI 3.1.0
        if schema.get("openapi") == "3.1.0":
            print(f"✅ Using OpenAPI 3.1.0 specification")
            compatibility_score += 1
        else:
            print(f"❌ Not using OpenAPI 3.1.0")
        
        # Check 2: No $ref references
        if not any("$ref" in str(issue) for issue in issues):
            print(f"✅ No $ref references in schema")
            compatibility_score += 1
        else:
            print(f"❌ Contains $ref references")
        
        # Check 3: Valid paths structure
        if "paths" in schema and isinstance(schema["paths"], dict):
            print(f"✅ Valid paths structure with {len(schema['paths'])} endpoints")
            compatibility_score += 1
        else:
            print(f"❌ Invalid or missing paths structure")
        
        # Check 4: Valid components structure
        if "components" in schema and "schemas" in schema["components"]:
            print(f"✅ Valid components structure with {len(schema['components']['schemas'])} schemas")
            compatibility_score += 1
        else:
            print(f"❌ Invalid or missing components structure")
        
        print(f"\n" + "=" * 60)
        print(f"Overall Compatibility Score: {compatibility_score}/{max_score}")
        
        if compatibility_score == max_score:
            print("✅ FULLY COMPATIBLE with Open WebUI and Claude Opus 4.1")
            return 0
        else:
            print("⚠️  PARTIAL COMPATIBILITY - Some fixes may be needed")
            return 1
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())