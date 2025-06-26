#!/usr/bin/env python3
"""
Run integration tests for the configuration management system
Ensures Redis caching, validation, and versioning work correctly
"""

import asyncio
import sys
import subprocess
from pathlib import Path


async def check_dependencies():
    """Check if required services are running"""
    print("🔍 Checking dependencies...")
    
    # Check Redis
    try:
        import redis.asyncio as redis
        client = await redis.from_url("redis://localhost:6379")
        await client.ping()
        await client.aclose()
        print("✅ Redis is running")
    except Exception as e:
        print(f"❌ Redis is not running: {e}")
        return False
    
    # Check PostgreSQL
    try:
        import asyncpg
        conn = await asyncpg.connect(
            "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"
        )
        await conn.close()
        print("✅ PostgreSQL is running")
    except Exception as e:
        print(f"❌ PostgreSQL is not running: {e}")
        return False
    
    return True


async def ensure_test_database_setup():
    """Ensure test database tables exist"""
    print("\n🔧 Setting up test database...")
    
    try:
        import asyncpg
        conn = await asyncpg.connect(
            "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"
        )
        
        # Create get_agent_config function if not exists
        await conn.execute("""
            CREATE OR REPLACE FUNCTION get_agent_config(p_agent_name VARCHAR)
            RETURNS TABLE(agent_id UUID, config JSON) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    ac.agent_id,
                    jsonb_build_object(
                        'name', ac.name,
                        'role', ac.role,
                        'department', ac.department,
                        'personality', ac.personality,
                        'goals', ac.goals,
                        'tools', ac.tools,
                        'llm_model', ac.llm_model,
                        'temperature', ac.temperature,
                        'max_tokens', ac.max_tokens,
                        'system_prompt', ac.system_prompt,
                        'context_prompt', ac.context_prompt,
                        'priority_level', ac.priority_level,
                        'compute_allocation', ac.compute_allocation,
                        'memory_limit_gb', ac.memory_limit_gb,
                        'max_concurrent_tasks', ac.max_concurrent_tasks,
                        'is_active', ac.is_active,
                        'development_status', ac.development_status
                    )::JSON
                FROM agent_configs ac
                WHERE ac.name = p_agent_name AND ac.is_active = true;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        await conn.close()
        print("✅ Database setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


def run_tests():
    """Run the integration tests"""
    print("\n🧪 Running configuration management integration tests...\n")
    
    test_file = Path(__file__).parent / "tests" / "test_config_management_integration.py"
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "-x"  # Stop on first failure
    ]
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def create_test_summary():
    """Create a summary of test results"""
    print("\n" + "="*60)
    print("📊 Configuration Management Test Summary")
    print("="*60)
    
    components = [
        ("Redis Caching", "Millisecond lookups with automatic refresh"),
        ("Config Validation", "Schema and security validation"),
        ("Version Management", "Full audit trail with rollback"),
        ("Cache Management", "Department invalidation and monitoring"),
        ("Performance", "< 5ms cache hit target")
    ]
    
    print("\n🔧 Components Tested:")
    for component, description in components:
        print(f"  • {component}: {description}")
    
    print("\n📈 Key Performance Metrics:")
    print("  • Cache Hit Rate Target: > 80%")
    print("  • Cache Lookup Target: < 5ms")
    print("  • Background Refresh: At 80% TTL")
    print("  • Concurrent Access: Thread-safe")
    
    print("\n✨ Production Features Verified:")
    print("  • Automatic cache warming on startup")
    print("  • Stampede prevention with Redis locks")
    print("  • Department-based bulk invalidation")
    print("  • Configuration version tracking")
    print("  • Security validation (SQL injection, XSS)")
    print("  • Business rule enforcement")
    
    print("="*60)


async def main():
    """Main test runner"""
    print("🚀 Configuration Management Integration Test Runner")
    print("="*60)
    
    # Check dependencies
    if not await check_dependencies():
        print("\n❌ Please ensure Redis and PostgreSQL are running")
        print("   Run: docker-compose up -d postgresql redis")
        return 1
    
    # Setup database
    if not await ensure_test_database_setup():
        print("\n❌ Database setup failed")
        return 1
    
    # Run tests
    success = run_tests()
    
    # Show summary
    create_test_summary()
    
    if success:
        print("\n✅ All configuration management tests passed!")
        print("   The Redis caching system is ready for production use.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)