#!/usr/bin/env python3
import http.server
import socketserver
import threading
import time
import webbrowser

PORT = 8888

html = """<!DOCTYPE html>
<html><head><title>BoarderframeOS Dashboard</title>
<style>body{font-family:Arial;background:#111;color:white;padding:20px}
.header{background:#333;padding:20px;border-radius:8px;margin-bottom:20px}
.card{background:#222;padding:20px;border-radius:8px;margin-bottom:20px}
.green{color:#0f0}.red{color:#f00}.yellow{color:#ff0}</style></head>
<body><div class="header"><h1>🚀 BoarderframeOS Dashboard</h1>
<p>Status: <span class="green">UI Server Online</span></p></div>
<div class="card"><h2>System Status</h2>
<div>UI Server: <span class="green">✓ Running on port 8888</span></div>
<div>Backend: <span class="red">✗ Offline (run setup)</span></div></div>
<div class="card"><h2>💬 Solomon Interface</h2>
<p>Solomon is offline. Complete setup to activate AI agents.</p></div>
<div class="card"><h2>🛠️ Setup Instructions</h2>
<p>1. cd /Users/cosburn/BoarderframeOS/boarderframeos</p>
<p>2. python setup_boarderframeos.py</p>
<p>3. python startup.py</p></div></body></html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

def open_browser():
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

print(f"🚀 Simple UI Server starting on port {PORT}")
print(f"📍 Dashboard: http://localhost:{PORT}")

threading.Thread(target=open_browser, daemon=True).start()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
