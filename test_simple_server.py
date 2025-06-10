#!/usr/bin/env python3
"""Test simple HTTP server on different port"""

import http.server
import socketserver
import threading

PORT = 9999

Handler = http.server.SimpleHTTPRequestHandler

print(f"Testing simple HTTP server on port {PORT}...")

with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"✅ Server started at http://localhost:{PORT}")
    print("Try accessing this URL in your browser")
    print("Press Ctrl+C to stop")
    
    # Serve in a thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.shutdown()