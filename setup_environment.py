#!/usr/bin/env python3
"""
BoarderframeOS Environment Setup
Ensures proper environment configuration before startup
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil

def setup_environment():
    """Setup the environment for BoarderframeOS"""
    print("🔧 Setting up BoarderframeOS environment...")
    
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    # Create .env file if it doesn't exist
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        shutil.copy(env_example, env_file)
        print("✅ .env file created")
        print("💡 Edit .env file to configure your API keys and settings")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No .env.example found, creating basic .env file...")
        with open(env_file, 'w') as f:
            f.write("""# BoarderframeOS Environment Configuration
POSTGRES_PASSWORD=boarderframe_secure_2025
POSTGRES_PORT=5434
DATABASE_URL=postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
""")
        print("✅ Basic .env file created")
    
    # Check Docker
    print("🐳 Checking Docker availability...")
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is available")
        else:
            print("❌ Docker not found")
            return False
    except FileNotFoundError:
        print("❌ Docker not installed")
        return False
    
    # Check docker-compose
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose is available")
        else:
            print("❌ Docker Compose not found")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose not installed")
        return False
    
    print("✅ Environment setup complete!")
    return True

def ensure_database_setup():
    """Ensure database containers are running and initialized"""
    print("🗄️  Setting up database infrastructure...")
    
    project_root = Path(__file__).parent
    
    # Start PostgreSQL and Redis containers
    print("🚀 Starting PostgreSQL and Redis containers...")
    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d", "postgresql", "redis"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Database containers started")
        else:
            print(f"❌ Failed to start containers: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error starting containers: {e}")
        return False
    
    # Wait for PostgreSQL to be ready
    print("⏳ Waiting for PostgreSQL to be ready...")
    import time
    for i in range(30):
        try:
            result = subprocess.run(
                ["docker", "exec", "boarderframeos_postgres", "pg_isready", "-U", "boarderframe", "-d", "boarderframeos"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ PostgreSQL is ready")
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        print("⚠️  PostgreSQL readiness check timeout")
    
    # Create a simple test to verify database works
    print("🧪 Testing database connectivity...")
    try:
        result = subprocess.run(
            ["docker", "exec", "boarderframeos_postgres", "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", "SELECT 1;"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Database connectivity confirmed")
            return True
        else:
            print(f"❌ Database test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

if __name__ == "__main__":
    if not setup_environment():
        sys.exit(1)
        
    if not ensure_database_setup():
        print("⚠️  Database setup had issues, but continuing...")
        
    print("\n🎉 Environment setup complete!")
    print("💡 You can now run: python startup.py")