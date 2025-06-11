#!/usr/bin/env python3
"""
Minimal working server for BoarderframeOS UI
"""
import http.server
import json
import os
import socketserver
from urllib.parse import parse_qs, urlparse

PORT = 8080


class BoarderframeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoarderframeOS Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <nav class="bg-gray-800 border-b border-gray-700">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-bold text-blue-400">BoarderframeOS Dashboard</h1>
                </div>
                <div class="flex items-center">
                    <div class="flex items-center space-x-2">
                        <div class="bg-green-500 w-3 h-3 rounded-full"></div>
                        <span class="text-sm">UI Server Online</span>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto p-6" x-data="dashboard">
        <!-- System Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 class="text-lg font-semibold mb-2">System Status</h3>
                <div class="text-2xl font-bold text-green-400">Online</div>
                <div class="text-sm text-gray-400">UI Server Running</div>
            </div>
            <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 class="text-lg font-semibold mb-2">Core Agents</h3>
                <div class="text-2xl font-bold text-yellow-400">Pending</div>
                <div class="text-sm text-gray-400">Run setup to initialize</div>
            </div>
            <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 class="text-lg font-semibold mb-2">Backend</h3>
                <div class="text-2xl font-bold text-red-400">Offline</div>
                <div class="text-sm text-gray-400">MCP servers needed</div>
            </div>
            <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <h3 class="text-lg font-semibold mb-2">Port Status</h3>
                <div class="text-2xl font-bold text-blue-400">8080</div>
                <div class="text-sm text-gray-400">Server active</div>
            </div>
        </div>

        <!-- Solomon Chat Interface -->
        <div class="mb-8">
            <div class="bg-gray-800 rounded-lg border border-gray-700 p-6">
                <div class="flex items-center space-x-4 mb-4">
                    <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                        <span class="text-xl font-bold">S</span>
                    </div>
                    <div>
                        <h2 class="text-xl font-bold">Solomon Communication</h2>
                        <p class="text-gray-400">Chief of Staff Interface</p>
                    </div>
                    <div class="ml-auto">
                        <div class="flex items-center space-x-2">
                            <div class="bg-red-500 w-3 h-3 rounded-full"></div>
                            <span class="text-sm">Offline</span>
                        </div>
                    </div>
                </div>

                <div class="bg-gray-900 rounded-lg p-4 mb-4 h-48 overflow-y-auto">
                    <div class="text-gray-400 text-center pt-16">
                        Solomon is offline. Run the setup script to initialize the AI operating system.
                    </div>
                </div>

                <div class="flex space-x-3">
                    <input type="text" placeholder="Message Solomon..."
                           class="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
                           disabled>
                    <button class="bg-gray-600 px-6 py-2 rounded-lg cursor-not-allowed" disabled>
                        Send
                    </button>
                </div>
            </div>
        </div>

        <!-- Setup Instructions -->
        <div class="bg-gray-800 rounded-lg border border-gray-700 p-6">
            <h2 class="text-xl font-bold mb-4">🚀 Next Steps to Start BoarderframeOS</h2>
            <div class="space-y-4">
                <div class="bg-gray-900 p-4 rounded-lg">
                    <h3 class="font-semibold text-green-400 mb-2">1. Run System Setup</h3>
                    <code class="text-sm bg-black p-2 rounded block">cd /Users/cosburn/BoarderframeOS/boarderframeos && python setup_boarderframeos.py</code>
                </div>

                <div class="bg-gray-900 p-4 rounded-lg">
                    <h3 class="font-semibold text-blue-400 mb-2">2. Start MCP Servers</h3>
                    <code class="text-sm bg-black p-2 rounded block">python mcp/filesystem_server.py &</code>
                    <code class="text-sm bg-black p-2 rounded block">python mcp/database_server.py &</code>
                    <code class="text-sm bg-black p-2 rounded block">python mcp/llm_server.py &</code>
                </div>

                <div class="bg-gray-900 p-4 rounded-lg">
                    <h3 class="font-semibold text-purple-400 mb-2">3. Initialize Agents</h3>
                    <code class="text-sm bg-black p-2 rounded block">python startup.py</code>
                </div>
            </div>

            <div class="mt-6 p-4 bg-blue-900 rounded-lg">
                <p class="text-sm">
                    <strong>✨ This is your BoarderframeOS UI!</strong> The interface is ready and waiting.
                    Once you run the setup, Solomon will come online for real-time chat, agents will start evolving,
                    and you'll have full control over the AI operating system.
                </p>
            </div>
        </div>
    </div>

    <script>
        function dashboard() {
            return {
                init() {
                    console.log('BoarderframeOS Dashboard initialized');
                    this.checkBackend();
                },

                async checkBackend() {
                    // Simulate backend check
                    setTimeout(() => {
                        console.log('Backend check complete - setup required');
                    }, 1000);
                }
            }
        }
    </script>
</body>
</html>"""
            self.wfile.write(html.encode())

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = json.dumps(
                {"status": "healthy", "service": "boarderframe_ui", "port": PORT}
            )
            self.wfile.write(response.encode())

        else:
            super().do_GET()


def main():
    try:
        with socketserver.TCPServer(("", PORT), BoarderframeHandler) as httpd:
            print("🚀 BoarderframeOS UI Server Starting...")
            print(f"📍 Dashboard: http://localhost:{PORT}")
            print(f"🔧 Health Check: http://localhost:{PORT}/health")
            print("✨ UI is ready! Run the setup script to initialize the full system.")
            print()
            print("Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == "__main__":
    main()
