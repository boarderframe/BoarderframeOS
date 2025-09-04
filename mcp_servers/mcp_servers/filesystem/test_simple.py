#!/usr/bin/env python3
"""
Simple test MCP server that stays alive and responds to basic requests
"""
import sys
import json
import time

def main():
    print("Simple MCP server starting...", file=sys.stderr)
    
    # Send an initial message to indicate we're ready
    response = {
        "jsonrpc": "2.0",
        "id": None,
        "method": "initialized",
        "params": {}
    }
    print(json.dumps(response), flush=True)
    
    # Keep the server alive
    try:
        while True:
            # Wait for input
            line = sys.stdin.readline()
            if not line:
                break
                
            # Simple echo response
            try:
                data = json.loads(line.strip())
                response = {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "status": "ok",
                        "server": "filesystem",
                        "timestamp": time.time()
                    }
                }
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                # Just acknowledge non-JSON input
                response = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": "acknowledged"
                }
                print(json.dumps(response), flush=True)
                
    except KeyboardInterrupt:
        print("Server shutting down...", file=sys.stderr)
    except EOFError:
        print("Input closed, shutting down...", file=sys.stderr)

if __name__ == "__main__":
    main()