#!/usr/bin/env python3
import http.server
import socketserver

PORT = 8888

class TestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request: {self.path}")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>BoarderframeOS Test Server</h1><p>Server is working!</p>")

try:
    print(f"Starting test server on port {PORT}...")
    with socketserver.TCPServer(("", PORT), TestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print("Server will run for 30 seconds...")
        httpd.timeout = 30
        httpd.serve_forever()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()