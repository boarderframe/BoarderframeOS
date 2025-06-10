#!/usr/bin/env python3
"""Manually test server health and see what's happening"""

import requests
import json

servers = [
    ("corporate_headquarters", 8888),
    ("registry", 8000),
    ("filesystem", 8001), 
    ("database", 8004),
    ("payment", 8006),
    ("analytics", 8007),
    ("customer", 8008)
]

print("🔍 Checking server health endpoints directly...")
print("=" * 60)

for name, port in servers:
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name:20} (port {port}): {data.get('status', 'OK')}")
        else:
            print(f"⚠️  {name:20} (port {port}): Status {response.status_code}")
    except Exception as e:
        print(f"❌ {name:20} (port {port}): {type(e).__name__}")

print("\n📊 Summary:")
print("All servers above showing ✅ should display as 'Online' in the UI")
print("The UI should update within 15-30 seconds via background refresh")
print("\nIf servers still show offline in UI after 30 seconds:")
print("1. Try refreshing the browser page")
print("2. Check the 'Refresh' button on the Servers page")
print("3. The background update thread may need investigation")