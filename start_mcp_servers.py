#!/usr/bin/env python3
"""
Start all MCP servers with proper process management
"""
import subprocess
import time
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def start_server(name, script, port):
    """Start a single MCP server"""
    print(f"Starting {name} on port {port}...", end=" ", flush=True)
    
    # Path to the MCP server script
    script_path = Path(__file__).parent / "mcp" / script
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return None
    
    # Use the same Python interpreter
    cmd = [sys.executable, str(script_path)]
    
    # Special handling for PostgreSQL server
    if name == "database_postgres":
        cmd.extend(["--port", str(port)])
    
    try:
        # Start the server
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent),
            env=os.environ.copy()
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's still running
        if process.poll() is None:
            print("✅ Started")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed")
            if stderr:
                print(f"  Error: {stderr.decode()[:100]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Start all MCP servers"""
    print("🔌 Starting MCP Servers...")
    print("=" * 50)
    
    servers = [
        ("registry", "registry_server.py", 8000),
        ("filesystem", "filesystem_server.py", 8001),
        ("database_postgres", "database_server_postgres.py", 8010),
        ("database_sqlite", "database_server.py", 8004),
        ("agent_cortex_api", "agent_cortex_server.py", 8005),
        ("payment", "payment_server.py", 8006),
        ("analytics", "analytics_server.py", 8007),
        ("customer", "customer_server.py", 8008),
        ("screenshot", "screenshot_server.py", 8011),
        ("agent_cortex_ui", "agent_cortex_ui_server.py", 8889),
    ]
    
    processes = {}
    
    for name, script, port in servers:
        process = start_server(name, script, port)
        if process:
            processes[name] = process
    
    print("=" * 50)
    print(f"✅ Started {len(processes)}/{len(servers)} servers")
    
    if processes:
        print("\nServers are running. Press Ctrl+C to stop all servers.")
        try:
            # Keep the script running
            while True:
                time.sleep(1)
                # Check if any processes have died
                for name, proc in list(processes.items()):
                    if proc.poll() is not None:
                        print(f"\n⚠️ {name} server died!")
                        del processes[name]
                
                if not processes:
                    print("\n❌ All servers have stopped!")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping all servers...")
            for name, proc in processes.items():
                print(f"  Stopping {name}...", end=" ")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    print("✅")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print("⚠️ (force killed)")
            print("✅ All servers stopped")

if __name__ == "__main__":
    main()