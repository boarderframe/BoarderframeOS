#!/usr/bin/env python3
"""
Simplest possible Agent Cortex Panel
Just to get something running
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class CortexHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Cortex Panel</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #0a0e27;
            color: #e0e6ed;
            padding: 20px;
            margin: 0;
        }
        h1 { color: #64ffda; }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: #1a1f2e;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        a { color: #64ffda; }
        .status { color: #50fa7b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Agent Cortex Management Panel</h1>
        <div class="card">
            <h2 class="status">✅ Panel is Running!</h2>
            <p>The Agent Cortex Panel is now accessible on port 9999</p>
        </div>
        
        <div class="card">
            <h3>Configured Agents</h3>
            <ul>
                <li>David (CEO) - claude-opus-4-20250514</li>
                <li>Solomon (Chief of Staff) - claude-opus-4-20250514</li>
                <li>Adam (Agent Creator) - claude-4-sonnet-20250514</li>
                <li>Eve (Agent Evolver) - claude-4-sonnet-20250514</li>
                <li>Bezalel (Master Programmer) - claude-4-sonnet-20250514</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>LLM Providers</h3>
            <ul>
                <li>Anthropic (Claude models)</li>
                <li>OpenAI (GPT models)</li>
                <li>Ollama (Local models)</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>SDK Features</h3>
            <p>The LLM Provider SDK and Agent Development Kit are integrated and ready to use.</p>
            <ul>
                <li>40+ models from 8+ providers</li>
                <li>Agent templates for quick creation</li>
                <li>Swarm orchestration patterns</li>
                <li>Cost optimization and routing</li>
            </ul>
        </div>
        
        <div class="card">
            <h3>API Endpoints</h3>
            <ul>
                <li><a href="/api/status">/api/status</a> - System status</li>
                <li><a href="/api/agents">/api/agents</a> - List agents</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
            self.wfile.write(html.encode())
            
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                "status": "operational",
                "agents": 5,
                "providers": 3,
                "port": 9999
            }
            self.wfile.write(json.dumps(status).encode())
            
        elif self.path == '/api/agents':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            agents = [
                {"name": "David", "model": "claude-opus-4-20250514"},
                {"name": "Solomon", "model": "claude-opus-4-20250514"},
                {"name": "Adam", "model": "claude-4-sonnet-20250514"},
                {"name": "Eve", "model": "claude-4-sonnet-20250514"},
                {"name": "Bezalel", "model": "claude-4-sonnet-20250514"}
            ]
            self.wfile.write(json.dumps(agents).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress request logging
        pass

def main():
    print("\n🚀 Starting Simple Agent Cortex Panel...")
    print("=" * 60)
    print("🌐 Server running at: http://localhost:9999")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 60)
    
    server = HTTPServer(('localhost', 9999), CortexHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        server.server_close()

if __name__ == '__main__':
    main()