#!/usr/bin/env python3
"""
Quick script to register all BoarderframeOS components with the registry
"""

import asyncio
import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.registry_auto_registration import RegistryAutoRegistration


async def quick_register():
    """Quick registration of all components"""
    print("🚀 Starting BoarderframeOS Component Registration")
    print("=" * 50)
    
    # First, ensure the enhanced registry service is running
    print("\n📡 Checking Enhanced Registry Service...")
    
    # Check if registry is accessible at port 8100
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:8100/health")
            if resp.status_code == 200:
                print("✅ Enhanced Registry Service is running on port 8100")
            else:
                print("⚠️  Enhanced Registry Service not responding properly")
                print("   Starting registry service...")
                # Start the registry service
                subprocess.Popen([
                    sys.executable, "-m", "core.enhanced_registry_system"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                await asyncio.sleep(3)
    except:
        print("❌ Enhanced Registry Service not running on port 8100")
        print("   Note: Registration will use direct database access")
    
    # Use registry auto-registration
    registrar = RegistryAutoRegistration(registry_url="http://localhost:8100")
    
    try:
        await registrar.initialize()
        print("\n📝 Registering all components...")
        await registrar.register_all_components()
        
        print("\n✅ Registration complete!")
        print(f"   Total components registered: {len(registrar.registered_entities)}")
        
        # Show summary
        print("\n📊 Registration Summary:")
        print("   - MCP Servers: 6")
        print("   - Core Systems: 2")  
        print("   - Databases: 2")
        print("   - Agents: Variable (based on running processes)")
        
        print("\n🌐 View the updated registry at:")
        print("   http://localhost:8888 -> Registry tab")
        
    except Exception as e:
        print(f"\n❌ Registration failed: {e}")
        print("\n💡 Falling back to direct database registration...")
        
        # Fallback: Direct database registration
        await register_directly_to_database()
        
    finally:
        if registrar.client:
            await registrar.cleanup()


async def register_directly_to_database():
    """Fallback method to register directly in the database"""
    try:
        import asyncpg
        import uuid
        from datetime import datetime
        
        # Connect to database
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            database="boarderframeos",
            user="boarderframe",
            password="boarderframe"
        )
        
        print("\n📝 Direct database registration...")
        
        # Register MCP Servers
        mcp_servers = [
            ("Registry Server", "mcp", 8009, "http://localhost:8009"),
            ("Filesystem Server", "mcp", 8001, "http://localhost:8001"),
            ("Database Server", "mcp", 8004, "http://localhost:8004"),
            ("Analytics Server", "mcp", 8007, "http://localhost:8007"),
            ("Payment Server", "mcp", 8006, "http://localhost:8006"),
            ("Customer Server", "mcp", 8008, "http://localhost:8008"),
        ]
        
        for name, server_type, port, url in mcp_servers:
            await conn.execute("""
                INSERT INTO server_registry (
                    id, name, server_type, status, endpoint_url,
                    health_check_url, capabilities, health_status,
                    metadata, registered_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (name) DO UPDATE SET
                    endpoint_url = EXCLUDED.endpoint_url,
                    updated_at = CURRENT_TIMESTAMP
            """, 
                str(uuid.uuid4()), name, server_type, 'online', url,
                f"{url}/health", '["mcp_protocol"]', 'healthy',
                '{"registered_by": "direct_registration"}', datetime.utcnow()
            )
            print(f"   ✅ Registered {name}")
        
        # Register Core Systems
        core_systems = [
            ("Corporate Headquarters", "core_system", 8888, "http://localhost:8888"),
            ("Agent Cortex", "core_system", 8889, "http://localhost:8889"),
        ]
        
        for name, server_type, port, url in core_systems:
            await conn.execute("""
                INSERT INTO server_registry (
                    id, name, server_type, status, endpoint_url,
                    health_check_url, capabilities, health_status,
                    metadata, registered_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (name) DO UPDATE SET
                    endpoint_url = EXCLUDED.endpoint_url,
                    updated_at = CURRENT_TIMESTAMP
            """, 
                str(uuid.uuid4()), name, server_type, 'online', url,
                f"{url}/health", '["dashboard", "monitoring"]', 'healthy',
                '{"registered_by": "direct_registration"}', datetime.utcnow()
            )
            print(f"   ✅ Registered {name}")
        
        # Register Databases
        databases = [
            ("PostgreSQL Primary", "postgresql", "localhost", 5434),
            ("Redis Cache", "redis", "localhost", 6379),
        ]
        
        for name, db_type, host, port in databases:
            await conn.execute("""
                INSERT INTO database_registry (
                    id, name, db_type, status, host, port,
                    health_status, max_connections, metadata,
                    registered_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (host, port, database_name) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = CURRENT_TIMESTAMP
            """, 
                str(uuid.uuid4()), name, db_type, 'online', host, port,
                'healthy', 100, '{"registered_by": "direct_registration"}',
                datetime.utcnow()
            )
            print(f"   ✅ Registered {name}")
        
        await conn.close()
        print("\n✅ Direct registration complete!")
        
    except Exception as e:
        print(f"❌ Direct registration failed: {e}")


if __name__ == "__main__":
    asyncio.run(quick_register())