#!/usr/bin/env python3
"""
Stable UI server with error handling and restart capability
"""
import http.server
import signal
import socketserver
import sys
import threading
import time
import webbrowser
from datetime import datetime

PORT = 8888
MAX_RETRIES = 5


class StableHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress access logs to keep output clean
        pass

    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                html = (
                    """<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Dashboard</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: white;
            margin: 0;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #1e40af, #7c3aed);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            margin: 5px;
        }
        .online { background: #059669; }
        .offline { background: #dc2626; }
        .pending { background: #d97706; }
        .card {
            background: #1e293b;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric {
            text-align: center;
            padding: 20px;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .metric-label {
            color: #94a3b8;
            font-size: 14px;
        }
        .solomon-container {
            background: linear-gradient(135deg, #374151, #4b5563);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }
        .solomon-avatar {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2em;
            font-weight: bold;
            margin: 0 auto 20px;
        }
        .chat-area {
            background: #0f172a;
            border-radius: 8px;
            padding: 20px;
            min-height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px 0;
            color: #64748b;
        }
        .setup-step {
            background: #1e293b;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }
        .code-block {
            background: #000;
            color: #00ff00;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            margin: 10px 0;
            overflow-x: auto;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .success-banner {
            background: linear-gradient(135deg, #059669, #10b981);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 BoarderframeOS Dashboard</h1>
        <p>AI Operating System Control Center</p>
        <div>
            <span class="status-badge online">UI Server Online</span>
            <span class="status-badge offline">Backend Offline</span>
            <span class="status-badge pending">Agents Pending</span>
        </div>
    </div>

    <div class="success-banner">
        <h3>✨ Dashboard Successfully Running!</h3>
        <p>Your BoarderframeOS interface is live and stable. Follow the setup steps below to initialize the full AI system.</p>
    </div>

    <div class="grid">
        <div class="card metric">
            <div class="metric-value" style="color: #10b981;">✓</div>
            <div class="metric-label">UI Server Status</div>
        </div>
        <div class="card metric">
            <div class="metric-value" style="color: #f59e0b;">8888</div>
            <div class="metric-label">Server Port</div>
        </div>
        <div class="card metric">
            <div class="metric-value pulse" style="color: #3b82f6;">🤖</div>
            <div class="metric-label">AI System Ready</div>
        </div>
        <div class="card metric">
            <div class="metric-value" style="color: #8b5cf6;">0/5</div>
            <div class="metric-label">Agents Online</div>
        </div>
    </div>

    <div class="card">
        <h2>💬 Solomon Communication Center</h2>
        <div class="solomon-container">
            <div class="solomon-avatar">S</div>
            <div style="text-align: center;">
                <h3>Solomon - Chief of Staff</h3>
                <p style="color: #94a3b8;">Your trusted AI advisor and system interface</p>
                <span class="status-badge offline">Offline - Awaiting Initialization</span>
            </div>
            <div class="chat-area">
                <div style="text-align: center;">
                    <div style="font-size: 3em; margin-bottom: 15px;">🛠️</div>
                    <div>Solomon will come online after you complete the setup process</div>
                    <div style="font-size: 12px; margin-top: 10px;">Real-time chat interface will activate automatically</div>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>🛠️ System Setup Guide</h2>
        <p>Follow these steps to bring your AI operating system online:</p>

        <div class="setup-step">
            <h3>Step 1: Navigate to Project Directory</h3>
            <div class="code-block">cd /Users/cosburn/BoarderframeOS/boarderframeos</div>
        </div>

        <div class="setup-step">
            <h3>Step 2: Run System Setup</h3>
            <div class="code-block">python setup_boarderframeos.py</div>
            <p style="font-size: 14px; color: #94a3b8; margin-top: 10px;">
                This creates the directory structure, installs dependencies, and prepares the environment.
            </p>
        </div>

        <div class="setup-step">
            <h3>Step 3: Start MCP Servers (Background)</h3>
            <div class="code-block">python mcp/database_server.py &<br>python mcp/llm_server.py &<br>python mcp/registry_server.py &</div>
            <p style="font-size: 14px; color: #94a3b8; margin-top: 10px;">
                These provide the backend services for agent communication and data storage.
            </p>
        </div>

        <div class="setup-step">
            <h3>Step 4: Initialize AI Agents</h3>
            <div class="code-block">python startup.py</div>
            <p style="font-size: 14px; color: #94a3b8; margin-top: 10px;">
                This brings Solomon, David, and the Primordial agents online.
            </p>
        </div>
    </div>

    <div class="card">
        <h2>🎯 What Happens Next</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2em; margin-bottom: 10px;">💬</div>
                <h4>Solomon Goes Live</h4>
                <p style="color: #94a3b8; font-size: 14px;">Real-time chat interface with your AI Chief of Staff</p>
            </div>
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2em; margin-bottom: 10px;">🤖</div>
                <h4>Agents Awaken</h4>
                <p style="color: #94a3b8; font-size: 14px;">Adam, Eve, Bezalel, and David come online</p>
            </div>
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2em; margin-bottom: 10px;">🚀</div>
                <h4>System Active</h4>
                <p style="color: #94a3b8; font-size: 14px;">Full AI operating system ready for business</p>
            </div>
        </div>
    </div>

    <div style="text-align: center; margin: 40px 0; color: #64748b;">
        <p>Dashboard auto-refreshes every 30 seconds • Server Time: """
                    + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + """</p>
    </div>

    <script>
        // Keep the connection alive
        setInterval(() => {
            fetch('/health').catch(() => console.log('Server check'));
        }, 10000);

        console.log('BoarderframeOS Dashboard loaded successfully');
    </script>
</body>
</html>"""
                )
                self.wfile.write(html.encode())

            elif self.path == "/health":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = (
                    '{"status":"healthy","timestamp":"'
                    + datetime.now().isoformat()
                    + '"}'
                )
                self.wfile.write(response.encode())

            else:
                self.send_response(404)
                self.end_headers()

        except Exception as e:
            print(f"Request error: {e}")
            self.send_error(500)


def signal_handler(signum, frame):
    print("\n🛑 Shutting down gracefully...")
    sys.exit(0)


def open_browser_delayed():
    time.sleep(2)
    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass


def start_server():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            with socketserver.TCPServer(("", PORT), StableHandler) as httpd:
                # Setup signal handler
                signal.signal(signal.SIGINT, signal_handler)

                print("🚀 BoarderframeOS Stable UI Server")
                print(f"📍 Dashboard: http://localhost:{PORT}")
                print(f"✨ Server running stably on port {PORT}")
                print("🔄 Auto-refresh enabled, connection monitoring active")
                print()
                print("Press Ctrl+C to stop")

                # Open browser in background
                browser_thread = threading.Thread(target=open_browser_delayed)
                browser_thread.daemon = True
                browser_thread.start()

                httpd.serve_forever()

        except OSError as e:
            if "Address already in use" in str(e):
                print(f"❌ Port {PORT} is busy. Waiting 5 seconds...")
                time.sleep(5)
                retries += 1
            else:
                print(f"❌ Server error: {e}")
                break
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            retries += 1
            if retries < MAX_RETRIES:
                print(f"🔄 Retrying in 3 seconds... ({retries}/{MAX_RETRIES})")
                time.sleep(3)

    print("❌ Server failed to start after maximum retries")


if __name__ == "__main__":
    start_server()
