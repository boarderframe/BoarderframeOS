#!/usr/bin/env python3
"""
Start all BoarderframeOS services in the correct order
"""
import subprocess
import time
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def start_docker_containers():
    """Start PostgreSQL and Redis containers"""
    print("🐳 Starting Docker containers...")
    try:
        subprocess.run(['docker-compose', 'up', '-d', 'postgresql', 'redis'], 
                      check=True, capture_output=True)
        print("  ✅ Docker containers started")
        time.sleep(5)  # Give containers time to initialize
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to start containers: {e}")
        return False

def start_mcp_server(name, script, port):
    """Start a single MCP server"""
    print(f"  Starting {name} on port {port}...", end=" ", flush=True)
    
    script_path = Path(__file__).parent / "mcp" / script
    if not script_path.exists():
        print(f"❌ Script not found")
        return None
    
    cmd = [sys.executable, str(script_path)]
    if name == "database_postgres":
        cmd.extend(["--port", str(port)])
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent),
            env=os.environ.copy()
        )
        
        time.sleep(2)
        
        if process.poll() is None:
            print("✅")
            return process
        else:
            print("❌ Failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def start_service(name, script):
    """Start a regular service"""
    print(f"  Starting {name}...", end=" ", flush=True)
    
    script_path = Path(__file__).parent / script
    if not script_path.exists():
        print(f"❌ Script not found")
        return None
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).parent),
            env=os.environ.copy()
        )
        
        time.sleep(3)
        
        if process.poll() is None:
            print("✅")
            return process
        else:
            print("❌ Failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Start all BoarderframeOS services"""
    print("🚀 Starting BoarderframeOS Services")
    print("=" * 60)
    
    processes = {}
    
    # 1. Check Docker
    print("\n📦 Checking Docker...")
    if not check_docker():
        print("  ❌ Docker is not running! Please start Docker Desktop first.")
        return
    print("  ✅ Docker is running")
    
    # 2. Start Docker containers
    if not start_docker_containers():
        print("  ⚠️  Failed to start Docker containers")
        return
    
    # 3. Start MCP Servers
    print("\n🔌 Starting MCP Servers...")
    mcp_servers = [
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
    
    for name, script, port in mcp_servers:
        process = start_mcp_server(name, script, port)
        if process:
            processes[f"mcp_{name}"] = process
    
    # 4. Start Core Services
    print("\n🎛️ Starting Core Services...")
    
    # Agent Communication Center
    acc_process = start_service("Agent Communication Center", "agent_communication_center_enhanced.py")
    if acc_process:
        processes["acc"] = acc_process
    
    # Corporate Headquarters
    hq_process = start_service("Corporate Headquarters", "corporate_headquarters.py")
    if hq_process:
        processes["corporate_hq"] = hq_process
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Started {len(processes)} services successfully")
    print("\n🌐 Access Points:")
    print("  📍 Corporate HQ: http://localhost:8888")
    print("  📍 Agent Cortex UI: http://localhost:8889")
    print("  📍 Agent Comm Center: http://localhost:8890")
    
    if processes:
        print("\n💡 Press Ctrl+C to stop all services")
        try:
            while True:
                time.sleep(1)
                # Check if any processes have died
                for name, proc in list(processes.items()):
                    if proc.poll() is not None:
                        print(f"\n⚠️ {name} has stopped!")
                        del processes[name]
                
                if not processes:
                    print("\n❌ All services have stopped!")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping all services...")
            for name, proc in processes.items():
                print(f"  Stopping {name}...", end=" ")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    print("✅")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print("⚠️ (force killed)")
            
            print("\n🐳 Stopping Docker containers...")
            subprocess.run(['docker-compose', 'down'], capture_output=True)
            print("  ✅ Docker containers stopped")
            
            print("\n✅ All services stopped")

if __name__ == "__main__":
    main()