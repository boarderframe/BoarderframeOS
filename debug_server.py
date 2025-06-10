#!/usr/bin/env python3
"""Debug server binding issue"""

import socket
import sys
import os

# Test 1: Can we bind to a socket?
print("Test 1: Socket binding test")
for port in [8890, 8891, 8892, 9999]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', port))
        s.listen(1)
        print(f"  ✅ Successfully bound to port {port}")
        s.close()
    except Exception as e:
        print(f"  ❌ Failed to bind to port {port}: {e}")

# Test 2: Simple Flask without any imports
print("\nTest 2: Minimal Flask app")
try:
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return 'Hello from Flask!'
    
    # Use werkzeug directly
    from werkzeug.serving import run_simple
    print("  ✅ Starting Flask on port 5555...")
    run_simple('127.0.0.1', 5555, app, use_reloader=False, use_debugger=False)
    
except Exception as e:
    print(f"  ❌ Flask error: {e}")
    import traceback
    traceback.print_exc()