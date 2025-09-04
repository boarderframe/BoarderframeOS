"""
Comprehensive performance testing suite with load testing and benchmarks.
Tests API performance, database performance, and system scalability.
"""
import pytest
import asyncio
import time
import psutil
import statistics
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock
import httpx
from fastapi import status
import pytest_benchmark
from concurrent.futures import ThreadPoolExecutor, as_completed

from tests.utils.test_helpers import APITestHelper, DataFactory, PerformanceTestHelper


@pytest.mark.performance
@pytest.mark.asyncio
class TestAPIPerformance:
    """Test API endpoint performance and scalability."""
    
    @pytest.fixture(autouse=True)
    def setup_performance_monitoring(self, performance_monitor):
        """Set up performance monitoring for all tests."""
        pass
    
    async def test_health_endpoint_performance(self, async_client, benchmark):
        """Benchmark health endpoint performance."""
        
        async def health_check():
            response = await async_client.get("/api/v1/health")
            assert response.status_code == status.HTTP_200_OK
            return response
        
        # Benchmark single request
        result = benchmark(asyncio.run, health_check())
        
        # Performance assertions
        assert result.status_code == status.HTTP_200_OK
        
        # Response time should be under 100ms
        PerformanceTestHelper.assert_response_time(benchmark.stats.mean, 0.1)
    
    async def test_server_list_performance(self, async_client, benchmark):
        """Benchmark server list endpoint with various data sizes."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create test servers
        server_count = 100
        for i in range(server_count):
            server_data = DataFactory.create_mcp_server_data(
                name=f"perf-server-{i}",
                port=8000 + i
            )
            await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=headers
            )
        
        async def list_servers():
            response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
            return response
        
        # Benchmark list operation
        result = benchmark(asyncio.run, list_servers())
        
        if result.status_code == status.HTTP_200_OK:
            servers = result.json()
            assert len(servers) >= server_count
            
            # List operation should be fast even with many servers
            PerformanceTestHelper.assert_response_time(benchmark.stats.mean, 1.0)
    
    async def test_concurrent_requests_performance(self, async_client):
        """Test performance under concurrent load."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Test concurrent health checks
        concurrent_requests = 50
        start_time = time.time()
        
        async def make_request():
            return await async_client.get("/api/v1/health", headers=headers)
        
        # Execute concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_responses = [
            r for r in responses 
            if isinstance(r, httpx.Response) and r.status_code == 200
        ]
        
        success_rate = len(successful_responses) / concurrent_requests
        requests_per_second = concurrent_requests / total_time
        
        # Performance assertions
        assert success_rate >= 0.95  # 95% success rate
        assert requests_per_second >= 25  # At least 25 RPS
        assert total_time < 5.0  # Complete within 5 seconds
    
    async def test_database_query_performance(self, async_client, benchmark):
        """Benchmark database query performance."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create multiple servers for query testing
        for i in range(50):
            server_data = DataFactory.create_mcp_server_data(
                name=f"query-test-{i}",
                port=8000 + i
            )
            await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=headers
            )
        
        async def complex_query():
            # Simulate complex query with filters
            response = await async_client.get(
                "/api/v1/mcp-servers/?search=query-test&status=active&limit=20",
                headers=headers
            )
            return response
        
        # Benchmark query
        result = benchmark(asyncio.run, complex_query())
        
        # Query should be fast even with filters
        if result.status_code == status.HTTP_200_OK:
            PerformanceTestHelper.assert_response_time(benchmark.stats.mean, 0.5)
    
    async def test_memory_usage_under_load(self, async_client):
        """Test memory usage under sustained load."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate sustained load
        request_count = 200
        batch_size = 10
        
        for batch in range(0, request_count, batch_size):
            tasks = []
            for i in range(min(batch_size, request_count - batch)):
                task = async_client.get("/api/v1/health", headers=headers)
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Brief pause between batches
            await asyncio.sleep(0.1)
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"
    
    async def test_response_time_consistency(self, async_client):
        """Test response time consistency over multiple requests."""
        headers = {"Authorization": "Bearer test-token"}
        
        response_times = []
        request_count = 100
        
        for i in range(request_count):
            start_time = time.time()
            response = await async_client.get("/api/v1/health", headers=headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            assert response.status_code == status.HTTP_200_OK
        
        # Analyze response time statistics
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        stdev_time = statistics.stdev(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        p99_time = sorted(response_times)[int(0.99 * len(response_times))]
        
        # Performance assertions
        assert mean_time < 0.1  # Average under 100ms
        assert median_time < 0.05  # Median under 50ms
        assert p95_time < 0.2  # 95th percentile under 200ms
        assert p99_time < 0.5  # 99th percentile under 500ms
        assert stdev_time < 0.05  # Low variance (consistent performance)


@pytest.mark.performance
@pytest.mark.asyncio
class TestDatabasePerformance:
    """Test database performance and optimization."""
    
    async def test_bulk_insert_performance(self, test_session, benchmark):
        """Benchmark bulk insert operations."""
        from app.models.mcp_server import MCPServer
        
        def bulk_insert():
            servers = []
            for i in range(1000):
                server = MCPServer(
                    name=f"bulk-server-{i}",
                    host="localhost",
                    port=8000 + i,
                    protocol="stdio",
                    command="/usr/bin/python",
                    args=["-m", "test_server"],
                    env={"TEST": "true"},
                    config={"timeout": 30}
                )
                servers.append(server)
            
            test_session.bulk_save_objects(servers)
            test_session.commit()
            return len(servers)
        
        # Benchmark bulk insert
        result = benchmark(bulk_insert)
        
        assert result == 1000
        # Bulk insert should be fast
        PerformanceTestHelper.assert_response_time(benchmark.stats.mean, 2.0)
    
    async def test_query_optimization(self, test_session, benchmark):
        """Test query performance with various optimization techniques."""
        from app.models.mcp_server import MCPServer
        from sqlalchemy import and_, or_
        
        # Create test data
        for i in range(500):
            server = MCPServer(
                name=f"query-opt-{i}",
                host="localhost",
                port=8000 + i,
                protocol="stdio" if i % 2 == 0 else "http",
                command="/usr/bin/python",
                status="running" if i % 3 == 0 else "stopped"
            )
            test_session.add(server)
        test_session.commit()
        
        def optimized_query():
            # Query with proper indexing and filtering
            return test_session.query(MCPServer).filter(
                and_(
                    MCPServer.protocol == "stdio",
                    MCPServer.status == "running",
                    MCPServer.port.between(8000, 8100)
                )
            ).limit(20).all()
        
        # Benchmark optimized query
        result = benchmark(optimized_query)
        
        assert len(result) <= 20
        # Query should be fast with proper indexing
        PerformanceTestHelper.assert_response_time(benchmark.stats.mean, 0.1)
    
    async def test_connection_pool_performance(self, test_session, benchmark):
        """Test database connection pool performance."""
        from app.models.mcp_server import MCPServer
        
        def connection_intensive_operations():
            results = []
            for i in range(50):
                # Simulate multiple operations per connection
                server = test_session.query(MCPServer).first()
                if server:
                    server.name = f"updated-{i}"
                    test_session.commit()
                results.append(i)
            return len(results)
        
        # Benchmark connection usage
        result = benchmark(connection_intensive_operations)
        
        assert result == 50
        # Connection pool should handle operations efficiently
        PerformanceTestHelper.assert_response_time(benchmark.stats.mean, 1.0)


@pytest.mark.performance
class TestSystemPerformance:
    """Test overall system performance and resource usage."""
    
    def test_cpu_usage_under_load(self, benchmark):
        """Test CPU usage under computational load."""
        import json
        
        def cpu_intensive_task():
            # Simulate JSON processing (common in API servers)
            data = {"servers": []}
            for i in range(1000):
                server_data = {
                    "id": i,
                    "name": f"server-{i}",
                    "config": {
                        "port": 8000 + i,
                        "timeout": 30,
                        "retries": 3,
                        "metadata": {
                            "created": "2025-01-15T10:30:00Z",
                            "updated": "2025-01-15T10:30:00Z"
                        }
                    }
                }
                data["servers"].append(server_data)
            
            # Serialize and deserialize
            json_str = json.dumps(data)
            parsed_data = json.loads(json_str)
            
            return len(parsed_data["servers"])
        
        # Monitor CPU usage
        cpu_before = psutil.cpu_percent(interval=0.1)
        
        result = benchmark(cpu_intensive_task)
        
        cpu_after = psutil.cpu_percent(interval=0.1)
        
        assert result == 1000
        
        # CPU usage should be reasonable
        cpu_increase = cpu_after - cpu_before
        assert cpu_increase < 80  # Should not max out CPU
    
    def test_memory_efficiency(self, benchmark):
        """Test memory efficiency of data structures."""
        import sys
        
        def memory_efficient_operations():
            # Test memory-efficient data handling
            servers = []
            
            for i in range(10000):
                # Use slots for memory efficiency
                server_data = {
                    "id": i,
                    "name": f"server-{i}",
                    "port": 8000 + i
                }
                servers.append(server_data)
            
            # Process data efficiently
            active_servers = [s for s in servers if s["port"] % 2 == 0]
            
            return len(active_servers)
        
        # Monitor memory usage
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        result = benchmark(memory_efficient_operations)
        
        memory_after = process.memory_info().rss
        memory_used = (memory_after - memory_before) / 1024 / 1024  # MB
        
        assert result == 5000  # Half the servers (even ports)
        
        # Memory usage should be reasonable for 10k objects
        assert memory_used < 50  # Less than 50MB for 10k simple objects
    
    def test_file_io_performance(self, benchmark, temp_dir):
        """Test file I/O performance for configuration management."""
        import json
        import os
        
        def file_operations():
            config_files = []
            
            # Write multiple config files
            for i in range(100):
                config_data = {
                    "server_id": i,
                    "name": f"config-{i}",
                    "settings": {
                        "port": 8000 + i,
                        "timeout": 30,
                        "retries": 3,
                        "environment": {f"VAR_{j}": f"value_{j}" for j in range(10)}
                    }
                }
                
                file_path = os.path.join(temp_dir, f"config-{i}.json")
                with open(file_path, 'w') as f:
                    json.dump(config_data, f)
                config_files.append(file_path)
            
            # Read and parse all config files
            parsed_configs = []
            for file_path in config_files:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                parsed_configs.append(config)
            
            return len(parsed_configs)
        
        result = benchmark(file_operations)
        
        assert result == 100
        # File operations should be reasonably fast
        PerformanceTestHelper.assert_response_time(benchmark.stats.mean, 1.0)


@pytest.mark.performance
@pytest.mark.asyncio
class TestScalabilityTesting:
    """Test system scalability under various load conditions."""
    
    async def test_user_scaling(self, async_client):
        """Test performance scaling with multiple concurrent users."""
        user_counts = [1, 5, 10, 25, 50]
        results = {}
        
        for user_count in user_counts:
            # Create unique auth headers for each user
            auth_headers = [
                {"Authorization": f"Bearer user-{i}-token"}
                for i in range(user_count)
            ]
            
            async def user_session(headers):
                """Simulate a user session with multiple requests."""
                requests_per_user = 10
                user_results = []
                
                for _ in range(requests_per_user):
                    start_time = time.time()
                    response = await async_client.get("/api/v1/health", headers=headers)
                    end_time = time.time()
                    
                    user_results.append({
                        "status_code": response.status_code,
                        "response_time": end_time - start_time
                    })
                    
                    # Brief pause between requests
                    await asyncio.sleep(0.01)
                
                return user_results
            
            # Execute concurrent user sessions
            start_time = time.time()
            tasks = [user_session(headers) for headers in auth_headers]
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            total_requests = user_count * 10
            successful_requests = 0
            response_times = []
            
            for user_result in user_results:
                if isinstance(user_result, list):
                    for request_result in user_result:
                        if request_result["status_code"] == 200:
                            successful_requests += 1
                        response_times.append(request_result["response_time"])
            
            success_rate = successful_requests / total_requests
            avg_response_time = statistics.mean(response_times) if response_times else 0
            total_time = end_time - start_time
            throughput = total_requests / total_time
            
            results[user_count] = {
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "throughput": throughput,
                "total_time": total_time
            }
        
        # Analyze scaling characteristics
        for user_count, metrics in results.items():
            print(f"\n{user_count} users:")
            print(f"  Success rate: {metrics['success_rate']:.2%}")
            print(f"  Avg response time: {metrics['avg_response_time']:.3f}s")
            print(f"  Throughput: {metrics['throughput']:.1f} req/s")
            
            # Performance should remain reasonable as users scale
            assert metrics["success_rate"] >= 0.95
            assert metrics["avg_response_time"] < 1.0
    
    async def test_data_scaling(self, async_client):
        """Test performance scaling with increasing data sizes."""
        headers = {"Authorization": "Bearer test-token"}
        data_sizes = [10, 50, 100, 500, 1000]
        results = {}
        
        for size in data_sizes:
            # Create servers for this size test
            for i in range(size):
                server_data = DataFactory.create_mcp_server_data(
                    name=f"scale-test-{size}-{i}",
                    port=8000 + i
                )
                await async_client.post(
                    "/api/v1/mcp-servers/",
                    json=server_data,
                    headers=headers
                )
            
            # Test query performance with this data size
            start_time = time.time()
            response = await async_client.get("/api/v1/mcp-servers/", headers=headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == status.HTTP_200_OK:
                servers = response.json()
                actual_count = len([s for s in servers if f"scale-test-{size}" in s.get("name", "")])
                
                results[size] = {
                    "response_time": response_time,
                    "actual_count": actual_count,
                    "expected_count": size
                }
            
            # Clean up for next iteration
            # (In a real test, you might want to use different databases)
        
        # Analyze data scaling
        for size, metrics in results.items():
            print(f"\n{size} servers:")
            print(f"  Response time: {metrics['response_time']:.3f}s")
            print(f"  Data integrity: {metrics['actual_count']}/{metrics['expected_count']}")
            
            # Performance should scale reasonably
            assert metrics["response_time"] < size * 0.01  # Linear scaling tolerance
            assert metrics["actual_count"] >= metrics["expected_count"]


@pytest.mark.performance
class TestBenchmarkSuite:
    """Comprehensive benchmark suite for key operations."""
    
    def test_json_serialization_performance(self, benchmark):
        """Benchmark JSON serialization/deserialization."""
        import json
        
        # Create complex data structure
        test_data = {
            "servers": [
                DataFactory.create_mcp_server_data(name=f"bench-server-{i}")
                for i in range(100)
            ],
            "metadata": {
                "total_count": 100,
                "generated_at": "2025-01-15T10:30:00Z",
                "version": "1.0.0"
            }
        }
        
        def json_operations():
            # Serialize
            json_str = json.dumps(test_data)
            
            # Deserialize
            parsed_data = json.loads(json_str)
            
            return len(parsed_data["servers"])
        
        result = benchmark(json_operations)
        assert result == 100
    
    def test_validation_performance(self, benchmark):
        """Benchmark data validation performance."""
        from pydantic import BaseModel, ValidationError
        from typing import Optional, Dict, Any, List
        
        class ServerConfig(BaseModel):
            name: str
            host: str
            port: int
            protocol: str
            command: Optional[str] = None
            args: Optional[List[str]] = None
            env: Optional[Dict[str, str]] = None
            config: Optional[Dict[str, Any]] = None
        
        def validation_operations():
            valid_count = 0
            test_data = [
                DataFactory.create_mcp_server_data(name=f"valid-{i}")
                for i in range(100)
            ]
            
            for data in test_data:
                try:
                    ServerConfig(**data)
                    valid_count += 1
                except ValidationError:
                    pass
            
            return valid_count
        
        result = benchmark(validation_operations)
        assert result == 100  # All should be valid
    
    def test_crypto_performance(self, benchmark):
        """Benchmark cryptographic operations."""
        import hashlib
        import hmac
        import secrets
        
        def crypto_operations():
            results = []
            
            for i in range(100):
                # Generate random data
                data = f"test-data-{i}".encode()
                salt = secrets.token_bytes(32)
                
                # Hash operations
                sha256_hash = hashlib.sha256(data + salt).hexdigest()
                
                # HMAC operations
                key = secrets.token_bytes(32)
                hmac_result = hmac.new(key, data, hashlib.sha256).hexdigest()
                
                results.append((sha256_hash, hmac_result))
            
            return len(results)
        
        result = benchmark(crypto_operations)
        assert result == 100