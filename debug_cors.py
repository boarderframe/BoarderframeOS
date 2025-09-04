#!/usr/bin/env python3
"""
Debug script to test CORS behavior like a browser would.
This simulates the exact request pattern that browsers use.
"""

import requests
import sys

def test_cors_preflight():
    """Test CORS preflight request"""
    print("=== Testing CORS Preflight Request ===")
    
    headers = {
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    response = requests.options('http://localhost:8080/static/favicon.png', headers=headers)
    
    print(f"Status: {response.status_code}")
    print("Response Headers:")
    for header, value in response.headers.items():
        if 'access-control' in header.lower() or 'origin' in header.lower():
            print(f"  {header}: {value}")
    print()

def test_actual_request():
    """Test actual favicon request with Origin header"""
    print("=== Testing Actual Request with Origin ===")
    
    headers = {
        'Origin': 'http://localhost:5173',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'http://localhost:5173/',
        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
    }
    
    response = requests.get('http://localhost:8080/static/favicon.png', headers=headers)
    
    print(f"Status: {response.status_code}")
    print("Response Headers:")
    for header, value in response.headers.items():
        if 'access-control' in header.lower() or 'origin' in header.lower() or 'content-type' in header.lower():
            print(f"  {header}: {value}")
    print()

def test_api_endpoint():
    """Test API endpoint for comparison"""
    print("=== Testing API Endpoint (/api/config) ===")
    
    headers = {
        'Origin': 'http://localhost:5173',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    response = requests.get('http://localhost:8080/api/config', headers=headers)
    
    print(f"Status: {response.status_code}")
    print("Response Headers:")
    for header, value in response.headers.items():
        if 'access-control' in header.lower() or 'origin' in header.lower() or 'content-type' in header.lower():
            print(f"  {header}: {value}")
    print()

def test_without_origin():
    """Test static file without Origin header"""
    print("=== Testing Static File Without Origin Header ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    response = requests.get('http://localhost:8080/static/favicon.png', headers=headers)
    
    print(f"Status: {response.status_code}")
    print("Response Headers:")
    for header, value in response.headers.items():
        if 'access-control' in header.lower() or 'origin' in header.lower() or 'content-type' in header.lower():
            print(f"  {header}: {value}")
    print()

if __name__ == "__main__":
    print("CORS Debug Test Script")
    print("=" * 50)
    
    try:
        test_cors_preflight()
        test_actual_request()
        test_api_endpoint()
        test_without_origin()
        
        print("=== Analysis ===")
        print("If static files don't have proper CORS headers but API endpoints do,")
        print("then the issue is that static file mounting happens after CORS middleware.")
        print("\nBrowser CORS errors occur when:")
        print("1. The browser sends an Origin header")
        print("2. The server doesn't respond with Access-Control-Allow-Origin")
        print("3. The origins don't match")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Is it running on localhost:8080?")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)