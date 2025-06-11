#!/usr/bin/env python3
"""Test server binding issues"""

import socket

from flask import Flask


# Test if port is available
def test_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except:
        return False

print(f"Testing port 8890...")
if test_port(8890):
    print("✅ Port 8890 is available")
else:
    print("❌ Port 8890 is in use or blocked")

# Try different ports
for port in [8891, 8892, 8893]:
    if test_port(port):
        print(f"✅ Port {port} is available")
        break

# Try a simple server
app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Test Server Running!</h1>'

print("\nStarting test server on http://localhost:8891")
try:
    app.run(host='127.0.0.1', port=8891, debug=False)
except Exception as e:
    print(f"❌ Error: {e}")
