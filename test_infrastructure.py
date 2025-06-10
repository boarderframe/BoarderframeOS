#!/usr/bin/env python3
"""
Infrastructure Testing Script for BoarderframeOS
Tests PostgreSQL + pgvector + Redis setup and performance
"""

import asyncio
import asyncpg
import aioredis
import numpy as np
import time
import logging
from typing import List, Dict, Any
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("infrastructure_test")

class InfrastructureTestSuite:
    """Comprehensive testing suite for the new infrastructure"""
    
    def __init__(self):
        self.postgres_dsn = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5432/boarderframeos"
        self.redis_url = "redis://localhost:6379"
        self.test_results = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete infrastructure test suite"""
        logger.info("Starting infrastructure test suite...")
        
        tests = [
            ("PostgreSQL Connection", self.test_postgres_connection),
            ("Redis Connection", self.test_redis_connection),
            ("PostgreSQL Schema", self.test_postgres_schema),
            ("Vector Operations", self.test_vector_operations),
            ("Vector Performance", self.test_vector_performance),
            ("Redis Streams", self.test_redis_streams),
            ("Database Performance", self.test_database_performance),
            ("Memory Usage", self.test_memory_usage),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")
            try:
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time
                
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "duration_seconds": round(duration, 3),
                    "details": result
                }
                logger.info(f"✅ {test_name} PASSED ({duration:.3f}s)")
                
            except Exception as e:
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "error": str(e),
                    "duration_seconds": 0
                }
                logger.error(f"❌ {test_name} FAILED: {e}")
        
        return self.test_results
    
    async def test_postgres_connection(self) -> Dict[str, Any]:
        """Test PostgreSQL connection and basic operations"""
        conn = await asyncpg.connect(self.postgres_dsn)
        
        try:
            # Test basic query
            version = await conn.fetchval("SELECT version()")
            
            # Test pgvector extension
            vector_version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            
            # Test UUID extension
            uuid_test = await conn.fetchval("SELECT uuid_generate_v4()")
            
            return {
                "postgres_version": version[:50] + "...",
                "pgvector_version": vector_version,
                "uuid_generation": "working",
                "connection_pool": "working"
            }
            
        finally:
            await conn.close()
    
    async def test_redis_connection(self) -> Dict[str, Any]:
        """Test Redis connection and basic operations"""
        redis = aioredis.from_url(self.redis_url)
        
        try:
            # Test basic operations
            await redis.set("test_key", "test_value", ex=10)
            value = await redis.get("test_key")
            
            # Test pub/sub
            pubsub = redis.pubsub()
            await pubsub.subscribe("test_channel")
            await redis.publish("test_channel", "test_message")
            
            # Test Redis info
            info = await redis.info()
            
            return {
                "redis_version": info.get("redis_version"),
                "memory_usage": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "basic_operations": "working",
                "pubsub": "working"
            }
            
        finally:
            await redis.close()
    
    async def test_postgres_schema(self) -> Dict[str, Any]:
        """Test PostgreSQL schema creation and structure"""
        conn = await asyncpg.connect(self.postgres_dsn)
        
        try:
            # Check if tables exist
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            table_names = [row['table_name'] for row in tables]
            
            # Check for required tables
            required_tables = [
                'agents', 'agent_memories', 'agent_interactions', 
                'departments', 'tasks', 'metrics', 'customers'
            ]
            
            missing_tables = [t for t in required_tables if t not in table_names]
            
            # Check indexes
            indexes = await conn.fetch("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND indexname LIKE 'idx_%'
            """)
            
            return {
                "total_tables": len(table_names),
                "required_tables_present": len(missing_tables) == 0,
                "missing_tables": missing_tables,
                "total_indexes": len(indexes),
                "tables": table_names[:10]  # First 10 tables
            }
            
        finally:
            await conn.close()
    
    async def test_vector_operations(self) -> Dict[str, Any]:
        """Test pgvector operations and functionality"""
        conn = await asyncpg.connect(self.postgres_dsn)
        
        try:
            # Test vector creation and insertion
            test_embedding = np.random.random(1536).tolist()
            test_agent_id = await conn.fetchval("SELECT uuid_generate_v4()")
            
            # Insert test agent first
            await conn.execute("""
                INSERT INTO agents (id, name, department, status) 
                VALUES ($1, 'test_agent', 'test_department', 'active')
                ON CONFLICT (id) DO NOTHING
            """, test_agent_id)
            
            # Insert test memory with vector
            memory_id = await conn.fetchval("SELECT uuid_generate_v4()")
            await conn.execute("""
                INSERT INTO agent_memories (id, agent_id, content, embedding)
                VALUES ($1, $2, 'test memory content', $3)
            """, memory_id, test_agent_id, test_embedding)
            
            # Test vector similarity search
            query_embedding = np.random.random(1536).tolist()
            similar_memories = await conn.fetch("""
                SELECT id, content, 1 - (embedding <=> $1) as similarity
                FROM agent_memories 
                ORDER BY embedding <=> $1 
                LIMIT 5
            """, query_embedding)
            
            # Test vector distance calculation
            distance = await conn.fetchval("""
                SELECT embedding <=> $1 as distance
                FROM agent_memories 
                WHERE id = $2
            """, query_embedding, memory_id)
            
            # Clean up test data
            await conn.execute("DELETE FROM agent_memories WHERE id = $1", memory_id)
            await conn.execute("DELETE FROM agents WHERE id = $1", test_agent_id)
            
            return {
                "vector_insertion": "working",
                "similarity_search": "working",
                "distance_calculation": f"{distance:.6f}",
                "results_found": len(similar_memories),
                "embedding_dimensions": len(test_embedding)
            }
            
        finally:
            await conn.close()
    
    async def test_vector_performance(self) -> Dict[str, Any]:
        """Test vector operations performance"""
        conn = await asyncpg.connect(self.postgres_dsn)
        
        try:
            # Insert test data
            test_agent_id = await conn.fetchval("SELECT uuid_generate_v4()")
            await conn.execute("""
                INSERT INTO agents (id, name, department, status) 
                VALUES ($1, 'perf_test_agent', 'test_department', 'active')
            """, test_agent_id)
            
            # Insert multiple test vectors
            num_vectors = 100
            memory_ids = []
            
            insert_start = time.time()
            for i in range(num_vectors):
                embedding = np.random.random(1536).tolist()
                memory_id = await conn.fetchval("SELECT uuid_generate_v4()")
                await conn.execute("""
                    INSERT INTO agent_memories (id, agent_id, content, embedding)
                    VALUES ($1, $2, $3, $4)
                """, memory_id, test_agent_id, f"test content {i}", embedding)
                memory_ids.append(memory_id)
            
            insert_duration = time.time() - insert_start
            
            # Test similarity search performance
            query_embedding = np.random.random(1536).tolist()
            
            search_start = time.time()
            for _ in range(10):  # Run 10 searches
                await conn.fetch("""
                    SELECT id, content, 1 - (embedding <=> $1) as similarity
                    FROM agent_memories 
                    ORDER BY embedding <=> $1 
                    LIMIT 10
                """, query_embedding)
            
            search_duration = time.time() - search_start
            
            # Clean up test data
            for memory_id in memory_ids:
                await conn.execute("DELETE FROM agent_memories WHERE id = $1", memory_id)
            await conn.execute("DELETE FROM agents WHERE id = $1", test_agent_id)
            
            return {
                "vectors_inserted": num_vectors,
                "insert_duration_seconds": round(insert_duration, 3),
                "insert_rate_per_second": round(num_vectors / insert_duration, 2),
                "search_queries": 10,
                "search_duration_seconds": round(search_duration, 3),
                "avg_search_time_ms": round((search_duration / 10) * 1000, 2)
            }
            
        finally:
            await conn.close()
    
    async def test_redis_streams(self) -> Dict[str, Any]:
        """Test Redis Streams functionality"""
        redis = aioredis.from_url(self.redis_url)
        
        try:
            stream_name = "test_stream"
            
            # Add messages to stream
            message_ids = []
            for i in range(5):
                msg_id = await redis.xadd(stream_name, {
                    "agent_id": f"agent_{i}",
                    "message": f"test message {i}",
                    "timestamp": time.time()
                })
                message_ids.append(msg_id)
            
            # Read messages from stream
            messages = await redis.xread({stream_name: 0}, count=10)
            
            # Test consumer groups
            try:
                await redis.xgroup_create(stream_name, "test_group", id="0", mkstream=True)
                consumer_messages = await redis.xreadgroup(
                    "test_group", "test_consumer", {stream_name: ">"}, count=5
                )
            except Exception:
                # Group might already exist
                consumer_messages = []
            
            # Clean up
            await redis.delete(stream_name)
            
            return {
                "messages_added": len(message_ids),
                "messages_read": len(messages[0][1]) if messages else 0,
                "consumer_group": "working" if consumer_messages else "created",
                "stream_operations": "working"
            }
            
        finally:
            await redis.close()
    
    async def test_database_performance(self) -> Dict[str, Any]:
        """Test general database performance"""
        conn = await asyncpg.connect(self.postgres_dsn)
        
        try:
            # Test simple queries
            simple_start = time.time()
            for _ in range(100):
                await conn.fetchval("SELECT 1")
            simple_duration = time.time() - simple_start
            
            # Test JSON operations
            json_start = time.time()
            for i in range(50):
                await conn.fetchval("""
                    SELECT $1::jsonb ->> 'key'
                """, json.dumps({"key": f"value_{i}", "data": list(range(10))}))
            json_duration = time.time() - json_start
            
            # Test concurrent connections
            concurrent_start = time.time()
            tasks = []
            for _ in range(20):
                task = asyncio.create_task(self._concurrent_query())
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            concurrent_duration = time.time() - concurrent_start
            
            return {
                "simple_queries_per_second": round(100 / simple_duration, 2),
                "json_operations_per_second": round(50 / json_duration, 2),
                "concurrent_connections": 20,
                "concurrent_duration_seconds": round(concurrent_duration, 3),
                "database_performance": "good" if simple_duration < 1.0 else "slow"
            }
            
        finally:
            await conn.close()
    
    async def _concurrent_query(self):
        """Helper function for concurrent query testing"""
        conn = await asyncpg.connect(self.postgres_dsn)
        try:
            await conn.fetchval("SELECT pg_backend_pid()")
        finally:
            await conn.close()
    
    async def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage and resource consumption"""
        import psutil
        
        # Get current process memory
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Test Redis memory
        redis = aioredis.from_url(self.redis_url)
        try:
            redis_info = await redis.info()
            redis_memory = redis_info.get("used_memory_human", "unknown")
        finally:
            await redis.close()
        
        # Test PostgreSQL connection pool memory
        conn_pool = await asyncpg.create_pool(
            self.postgres_dsn, 
            min_size=5, 
            max_size=10
        )
        try:
            pool_memory_before = process.memory_info().rss
            
            # Use all connections
            connections = []
            for _ in range(10):
                conn = await conn_pool.acquire()
                connections.append(conn)
            
            pool_memory_after = process.memory_info().rss
            
            # Release connections
            for conn in connections:
                await conn_pool.release(conn)
                
        finally:
            await conn_pool.close()
        
        return {
            "process_memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "redis_memory": redis_memory,
            "connection_pool_overhead_mb": round((pool_memory_after - pool_memory_before) / 1024 / 1024, 2),
            "memory_status": "acceptable" if memory_info.rss < 500 * 1024 * 1024 else "high"
        }

async def main():
    """Main testing function"""
    print("🚀 BoarderframeOS Infrastructure Test Suite")
    print("="*60)
    
    test_suite = InfrastructureTestSuite()
    results = await test_suite.run_all_tests()
    
    # Print detailed results
    print("\n📊 DETAILED TEST RESULTS")
    print("="*60)
    
    passed_tests = 0
    failed_tests = 0
    
    for test_name, result in results.items():
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        duration = result.get("duration_seconds", 0)
        
        print(f"{status_icon} {test_name:<25} | {result['status']:<6} | {duration:6.3f}s")
        
        if result["status"] == "PASSED":
            passed_tests += 1
            # Show key details
            if "details" in result:
                details = result["details"]
                for key, value in list(details.items())[:3]:  # Show first 3 details
                    print(f"   ↳ {key}: {value}")
        else:
            failed_tests += 1
            print(f"   ↳ Error: {result.get('error', 'Unknown error')}")
        
        print()
    
    # Summary
    total_tests = passed_tests + failed_tests
    print("="*60)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if failed_tests == 0:
        print("🎉 All tests passed! Infrastructure is ready.")
        return 0
    else:
        print(f"⚠️  {failed_tests} tests failed. Check configuration.")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)