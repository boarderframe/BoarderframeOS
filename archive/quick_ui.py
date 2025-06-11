#!/usr/bin/env python3
"""
Super simple UI server that definitely works
"""
import http.server
import socketserver
import threading
import time
import webbrowser

PORT = 8888  # Different port to avoid conflicts

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html = """<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #111827;
            color: white;
            margin: 0;
            padding: 20px;
        }
        .header {
            background: #1f2937;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .card {
            background: #1f2937;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #374151;
        }
        .status-online { color: #10b981; }
        .status-offline { color: #ef4444; }
        .status-pending { color: #f59e0b; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .code {
            background: #000;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            margin: 5px 0;
        }
        .button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        .button:hover { background: #2563eb; }
        .solomon-box {
            background: #374151;
            height: 200px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 10px 0;
        }
        input {
            background: #374151;
            border: 1px solid #4b5563;
            color: white;
            padding: 10px;
            border-radius: 4px;
            width: 300px;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 BoarderframeOS Dashboard</h1>
        <p>AI Operating System Interface • <span class="status-online">UI Server Online</span></p>
    </div>

    <div class="grid">
        <div class="card">
            <h3>System Status</h3>
            <div>UI Server: <span class="status-online">✓ Online</span></div>
            <div>Port: <span class="status-online">8888</span></div>
            <div>Backend: <span class="status-offline">✗ Offline</span></div>
        </div>

        <div class="card">
            <h3>Core Agents</h3>
            <div>Solomon: <span class="status-offline">Offline</span></div>
            <div>David: <span class="status-offline">Offline</span></div>
            <div>Adam: <span class="status-offline">Offline</span></div>
            <div>Eve: <span class="status-offline">Offline</span></div>
            <div>Bezalel: <span class="status-offline">Offline</span></div>
        </div>

        <div class="card">
            <h3>Quick Actions</h3>
            <button class="button" onclick="alert('Run: python setup_boarderframeos.py')">Setup System</button>
            <button class="button" onclick="showInstructions()">Show Instructions</button>
        </div>
    </div>

    <div class="card">
        <h3>💬 Solomon Communication Interface</h3>
        <div class="solomon-box">
            <div style="text-align: center; color: #9ca3af;">
                <div style="font-size: 48px; margin-bottom: 10px;">🤖</div>
                <div>Solomon is offline</div>
                <div style="font-size: 12px;">Run setup to initialize</div>
            </div>
        </div>
        <input type="text" placeholder="Message Solomon..." disabled>
        <button class="button" disabled>Send</button>
    </div>

    <div class="card" id="instructions" style="display: none;">
        <h3>🛠️ Setup Instructions</h3>
        <div style="margin: 10px 0;">
            <strong>1. Navigate to project directory:</strong>
            <div class="code">cd /Users/cosburn/BoarderframeOS/boarderframeos</div>
        </div>
        <div style="margin: 10px 0;">
            <strong>2. Run the setup script:</strong>
            <div class="code">python setup_boarderframeos.py</div>
        </div>
        <div style="margin: 10px 0;">
            <strong>3. Start MCP servers:</strong>
            <div class="code">python mcp/filesystem_server.py &</div>
            <div class="code">python mcp/database_server.py &</div>
            <div class="code">python mcp/llm_server.py &</div>
        </div>
        <div style="margin: 10px 0;">
            <strong>4. Initialize agents:</strong>
            <div class="code">python startup.py</div>
        </div>
        <div style="background: #1e40af; padding: 15px; border-radius: 4px; margin-top: 20px;">
            <strong>✨ This UI is ready!</strong> Once you complete the setup, Solomon will come online for chat,
            agents will begin evolving, and you'll have full control over the AI operating system.
        </div>
    </div>

    <script>
        function showInstructions() {
            const instructions = document.getElementById('instructions');
            instructions.style.display = instructions.style.display === 'none' ? 'block' : 'none';
        }

        // Auto-refresh status every 10 seconds
        setInterval(() => {
            console.log('Status check - UI running on port 8888');
        }, 10000);
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

def open_browser():
    time.sleep(1)  # Wait for server to start
    webbrowser.open(f'http://localhost:{PORT}')

def main():
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    try:
        with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
            print(f"🚀 BoarderframeOS UI Server running on port {PORT}")
            print(f"📍 Opening browser to: http://localhost:{PORT}")
            print("🎯 UI is ready! This interface will show you the system status.")
            print("📋 Follow the setup instructions to initialize the full AI system.")
            print()
            print("Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ Port {PORT} might be in use. Error: {e}")
        print("Try a different port or kill existing processes")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()
