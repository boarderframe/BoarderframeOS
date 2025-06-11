#!/usr/bin/env python3
"""
Database MCP Server Comparison Test
Tests both SQLite and PostgreSQL versions side by side
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict

import aiohttp
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_server_test")


class DatabaseServerTester:
    """Test both database servers for functionality and performance"""

    def __init__(self):
        self.sqlite_url = "http://localhost:8004"
        self.postgres_url = (
            "http://localhost:8005"  # We'll run postgres server on different port
        )
        self.test_results = {}

    async def run_comparison_tests(self):
        """Run comprehensive comparison between SQLite and PostgreSQL servers"""
        logger.info("Starting database server comparison tests...")

        tests = [
            ("Health Check", self.test_health_check),
            ("Basic Queries", self.test_basic_queries),
            ("Insert Operations", self.test_insert_operations),
            ("Update Operations", self.test_update_operations),
            ("Delete Operations", self.test_delete_operations),
            ("Vector Operations", self.test_vector_operations),
            ("Performance", self.test_performance),
            ("Memory Operations", self.test_memory_operations),
        ]

        for test_name, test_func in tests:
            logger.info(f"Running test: {test_name}")

            sqlite_result = await self._run_test_safe(test_func, "sqlite")
            postgres_result = await self._run_test_safe(test_func, "postgres")

            self.test_results[test_name] = {
                "sqlite": sqlite_result,
                "postgres": postgres_result,
            }

            self._compare_results(test_name, sqlite_result, postgres_result)

        return self.test_results

    async def _run_test_safe(self, test_func, server_type: str):
        """Run test safely with error handling"""
        try:
            start_time = time.time()
            result = await test_func(server_type)
            duration = time.time() - start_time

            return {
                "status": "PASSED",
                "duration": round(duration, 3),
                "result": result,
            }
        except Exception as e:
            return {"status": "FAILED", "error": str(e), "duration": 0}

    def _compare_results(
        self, test_name: str, sqlite_result: Dict, postgres_result: Dict
    ):
        """Compare and log test results"""
        sqlite_status = sqlite_result.get("status", "FAILED")
        postgres_status = postgres_result.get("status", "FAILED")

        if sqlite_status == "PASSED" and postgres_status == "PASSED":
            sqlite_time = sqlite_result.get("duration", 0)
            postgres_time = postgres_result.get("duration", 0)

            if postgres_time > 0:
                speedup = sqlite_time / postgres_time
                logger.info(
                    f"✅ {test_name}: Both passed. PostgreSQL {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}"
                )
            else:
                logger.info(f"✅ {test_name}: Both passed")
        elif postgres_status == "PASSED":
            logger.info(
                f"🆕 {test_name}: PostgreSQL passed, SQLite failed (new feature)"
            )
        elif sqlite_status == "PASSED":
            logger.warning(f"⚠️  {test_name}: SQLite passed, PostgreSQL failed")
        else:
            logger.error(f"❌ {test_name}: Both failed")

    async def test_health_check(self, server_type: str):
        """Test health check endpoints"""
        url = self._get_url(server_type)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/health") as response:
                data = await response.json()

                if server_type == "postgres":
                    # Check PostgreSQL-specific fields
                    assert "database" in data
                    assert "redis" in data
                    assert "pool_size" in data
                else:
                    # Check SQLite-specific fields
                    assert "status" in data

                return data

    async def test_basic_queries(self, server_type: str):
        """Test basic query operations"""
        url = self._get_url(server_type)

        if server_type == "postgres":
            query_data = {
                "sql": "SELECT 1 as test_value, NOW() as current_time",
                "fetch_all": False,
            }
        else:
            query_data = {
                "sql": "SELECT 1 as test_value, datetime('now') as current_time",
                "fetch_all": False,
            }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/query", json=query_data) as response:
                data = await response.json()
                assert data["success"] is True
                assert data["data"]["test_value"] == 1
                return data

    async def test_insert_operations(self, server_type: str):
        """Test insert operations"""
        url = self._get_url(server_type)

        # Test table creation first (if needed)
        if server_type == "sqlite":
            create_table_data = {
                "table": "test_agents",
                "schema": {
                    "id": "TEXT PRIMARY KEY",
                    "name": "TEXT NOT NULL",
                    "data": "TEXT",
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{url}/create-table", json=create_table_data
                ) as response:
                    pass  # Ignore if table already exists

        # Test insert
        insert_data = {
            "table": "agents" if server_type == "postgres" else "test_agents",
            "data": {
                "name": f"test_agent_{server_type}",
                "department": "test_department",
                "status": "active",
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/insert", json=insert_data) as response:
                data = await response.json()
                assert data["success"] is True
                return data

    async def test_update_operations(self, server_type: str):
        """Test update operations"""
        url = self._get_url(server_type)

        update_data = {
            "table": "agents" if server_type == "postgres" else "test_agents",
            "data": {"status": "updated"},
            "where": {"name": f"test_agent_{server_type}"},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/update", json=update_data) as response:
                data = await response.json()
                assert data["success"] is True
                return data

    async def test_delete_operations(self, server_type: str):
        """Test delete operations"""
        url = self._get_url(server_type)

        delete_data = {
            "table": "agents" if server_type == "postgres" else "test_agents",
            "where": {"name": f"test_agent_{server_type}"},
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/delete", json=delete_data) as response:
                data = await response.json()
                assert data["success"] is True
                return data

    async def test_vector_operations(self, server_type: str):
        """Test vector operations (PostgreSQL only)"""
        if server_type == "sqlite":
            raise Exception("Vector operations not supported in SQLite version")

        url = self._get_url(server_type)

        # Test vector similarity search
        search_data = {
            "embedding": np.random.random(1536).tolist(),
            "similarity_threshold": 0.5,
            "limit": 5,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url}/vector-search", json=search_data
            ) as response:
                data = await response.json()
                assert data["success"] is True
                return data

    async def test_performance(self, server_type: str):
        """Test performance with multiple operations"""
        url = self._get_url(server_type)
        results = {"queries": 0, "inserts": 0, "total_time": 0}

        start_time = time.time()

        # Run multiple queries
        query_data = {
            "sql": "SELECT 1" if server_type == "postgres" else "SELECT 1",
            "fetch_all": False,
        }

        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(10):
                task = session.post(f"{url}/query", json=query_data)
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            for response in responses:
                data = await response.json()
                if data["success"]:
                    results["queries"] += 1

        results["total_time"] = time.time() - start_time
        return results

    async def test_memory_operations(self, server_type: str):
        """Test memory-specific operations (PostgreSQL only)"""
        if server_type == "sqlite":
            raise Exception("Memory operations not supported in SQLite version")

        url = self._get_url(server_type)

        # Create a test agent first
        agent_insert = {
            "table": "agents",
            "data": {
                "name": "memory_test_agent",
                "department": "test",
                "status": "active",
            },
        }

        async with aiohttp.ClientSession() as session:
            # Insert test agent
            async with session.post(f"{url}/insert", json=agent_insert) as response:
                agent_result = await response.json()
                if not agent_result["success"]:
                    raise Exception("Failed to create test agent")

                agent_id = agent_result["data"]["id"]

            # Insert memory
            memory_data = {
                "agent_id": agent_id,
                "content": "This is a test memory for vector search",
                "memory_type": "test",
                "importance": 0.8,
                "metadata": {"test": True},
            }

            async with session.post(f"{url}/memory", json=memory_data) as response:
                data = await response.json()
                assert data["success"] is True

                # Clean up
                delete_data = {"table": "agents", "where": {"id": agent_id}}
                await session.post(f"{url}/delete", json=delete_data)

                return data

    def _get_url(self, server_type: str) -> str:
        """Get URL for specific server type"""
        return self.postgres_url if server_type == "postgres" else self.sqlite_url


async def main():
    """Main testing function"""
    print("🔄 Database MCP Server Comparison Test")
    print("=" * 60)
    print("SQLite Server: http://localhost:8004")
    print("PostgreSQL Server: http://localhost:8005")
    print("=" * 60)

    tester = DatabaseServerTester()

    try:
        results = await tester.run_comparison_tests()

        # Print summary
        print("\n📊 COMPARISON SUMMARY")
        print("=" * 60)

        postgres_passed = 0
        sqlite_passed = 0
        postgres_only = 0
        both_failed = 0

        for test_name, result in results.items():
            postgres_status = result["postgres"]["status"]
            sqlite_status = result["sqlite"]["status"]

            if postgres_status == "PASSED" and sqlite_status == "PASSED":
                postgres_passed += 1
                sqlite_passed += 1
                status_icon = "✅"
            elif postgres_status == "PASSED" and sqlite_status == "FAILED":
                postgres_passed += 1
                postgres_only += 1
                status_icon = "🆕"
            elif postgres_status == "FAILED" and sqlite_status == "PASSED":
                sqlite_passed += 1
                status_icon = "⚠️ "
            else:
                both_failed += 1
                status_icon = "❌"

            print(
                f"{status_icon} {test_name:<20} | PostgreSQL: {postgres_status:<6} | SQLite: {sqlite_status:<6}"
            )

        print("=" * 60)
        print(
            f"PostgreSQL: {postgres_passed} passed, {postgres_only} exclusive features"
        )
        print(f"SQLite: {sqlite_passed} passed")
        print(f"Both failed: {both_failed}")

        if postgres_passed >= sqlite_passed:
            print("\n🎉 PostgreSQL server is ready for migration!")
        else:
            print("\n⚠️  PostgreSQL server needs fixes before migration")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
