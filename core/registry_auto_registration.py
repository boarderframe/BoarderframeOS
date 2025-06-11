#!/usr/bin/env python3
"""
BoarderframeOS Automatic Registry Registration
==============================================

Automatically registers all system components with the enhanced registry:
- MCP Servers
- Databases (PostgreSQL, Redis)
- Core Systems (Corporate HQ, Agent Cortex)
- Agents
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .enhanced_registry_system import ServiceStatus
from .registry_client import RegistryClient, RegistryConfig, ServerType

logger = logging.getLogger(__name__)


class RegistryAutoRegistration:
    """Handles automatic registration of all BoarderframeOS components"""

    def __init__(self, registry_url: str = "http://localhost:8100"):
        self.registry_config = RegistryConfig(registry_url=registry_url)
        self.client = None
        self.registered_entities = set()

    async def initialize(self):
        """Initialize registry client"""
        self.client = RegistryClient(self.registry_config)
        await self.client.connect()
        logger.info("Registry auto-registration initialized")

    async def cleanup(self):
        """Cleanup registry client"""
        if self.client:
            await self.client.disconnect()

    async def register_all_components(self):
        """Register all BoarderframeOS components"""
        try:
            logger.info("Starting comprehensive component registration...")

            # Register MCP Servers
            await self.register_mcp_servers()

            # Register Core Systems
            await self.register_core_systems()

            # Register Databases
            await self.register_databases()

            # Register Agents (if running)
            await self.register_running_agents()

            logger.info(f"Registration complete! Registered {len(self.registered_entities)} components")

        except Exception as e:
            logger.error(f"Failed to register components: {e}")
            raise

    async def register_mcp_servers(self):
        """Register all MCP servers"""
        mcp_servers = [
            {
                "name": "Registry Server",
                "port": 8009,
                "capabilities": ["service_discovery", "health_monitoring", "registration"],
                "description": "Central service registry and discovery"
            },
            {
                "name": "Filesystem Server",
                "port": 8001,
                "capabilities": ["file_operations", "directory_management", "search", "monitoring"],
                "description": "File system operations and management"
            },
            {
                "name": "Database Server",
                "port": 8004,
                "capabilities": ["sqlite_operations", "query_execution", "data_management"],
                "description": "SQLite database operations"
            },
            {
                "name": "Analytics Server",
                "port": 8007,
                "capabilities": ["data_analytics", "metrics_collection", "reporting", "visualization"],
                "description": "Analytics and business intelligence"
            },
            {
                "name": "Payment Server",
                "port": 8006,
                "capabilities": ["payment_processing", "billing", "invoicing", "revenue_tracking"],
                "description": "Payment and revenue management"
            },
            {
                "name": "Customer Server",
                "port": 8008,
                "capabilities": ["customer_management", "crm", "support_tickets", "user_tracking"],
                "description": "Customer relationship management"
            }
        ]

        for server_info in mcp_servers:
            try:
                # Check if server is running
                import httpx
                async with httpx.AsyncClient(timeout=2.0) as client:
                    try:
                        resp = await client.get(f"http://localhost:{server_info['port']}/health")
                        is_online = resp.status_code == 200
                    except:
                        is_online = False

                # Register the server
                server = await self.client.register_server(
                    name=server_info["name"],
                    server_type=ServerType.MCP_SERVER,
                    host="localhost",
                    port=server_info["port"],
                    capabilities=server_info["capabilities"],
                    metadata={
                        "description": server_info["description"],
                        "mcp_version": "1.0",
                        "registered_by": "auto_registration"
                    }
                )

                # Update status if online
                if is_online:
                    await self.client.update_status(server.id, ServiceStatus.ONLINE)

                self.registered_entities.add(server.id)
                logger.info(f"✅ Registered MCP Server: {server_info['name']} (port {server_info['port']})")

            except Exception as e:
                logger.error(f"Failed to register {server_info['name']}: {e}")

    async def register_core_systems(self):
        """Register core system servers"""
        core_systems = [
            {
                "name": "Corporate Headquarters",
                "port": 8888,
                "server_type": ServerType.CORE_SYSTEM,
                "capabilities": ["dashboard", "system_monitoring", "agent_management", "chat_interface"],
                "description": "Main system dashboard and control center"
            },
            {
                "name": "Agent Cortex",
                "port": 8889,
                "server_type": ServerType.CORE_SYSTEM,
                "capabilities": ["llm_orchestration", "model_management", "cost_optimization", "intelligent_routing"],
                "description": "Intelligent LLM orchestration system"
            }
        ]

        for system in core_systems:
            try:
                # Check if system is running
                import httpx
                async with httpx.AsyncClient(timeout=2.0) as client:
                    try:
                        resp = await client.get(f"http://localhost:{system['port']}/")
                        is_online = resp.status_code == 200
                    except:
                        is_online = False

                # Register the system
                server = await self.client.register_server(
                    name=system["name"],
                    server_type=system["server_type"],
                    host="localhost",
                    port=system["port"],
                    capabilities=system["capabilities"],
                    metadata={
                        "description": system["description"],
                        "version": "2.0",
                        "registered_by": "auto_registration"
                    }
                )

                # Update status if online
                if is_online:
                    await self.client.update_status(server.id, ServiceStatus.ONLINE)

                self.registered_entities.add(server.id)
                logger.info(f"✅ Registered Core System: {system['name']} (port {system['port']})")

            except Exception as e:
                logger.error(f"Failed to register {system['name']}: {e}")

    async def register_databases(self):
        """Register database systems"""
        databases = [
            {
                "name": "PostgreSQL Primary",
                "db_type": "postgresql",
                "host": "localhost",
                "port": 5434,
                "database_name": "boarderframeos",
                "max_connections": 100,
                "capabilities": ["relational_storage", "json_support", "vector_search", "full_text_search"],
                "description": "Primary PostgreSQL database with pgvector"
            },
            {
                "name": "Redis Cache",
                "db_type": "redis",
                "host": "localhost",
                "port": 6379,
                "max_connections": 50,
                "capabilities": ["caching", "pub_sub", "streams", "real_time_messaging"],
                "description": "Redis for caching and real-time events"
            }
        ]

        for db_info in databases:
            try:
                # Check if database is accessible
                is_online = False
                if db_info["db_type"] == "postgresql":
                    try:
                        import asyncpg
                        conn = await asyncpg.connect(
                            host=db_info["host"],
                            port=db_info["port"],
                            database=db_info.get("database_name", "postgres"),
                            user="boarderframe",
                            password="boarderframe",
                            timeout=2
                        )
                        await conn.close()
                        is_online = True
                    except:
                        pass
                elif db_info["db_type"] == "redis":
                    try:
                        import aioredis
                        redis = await aioredis.create_redis_pool(
                            f"redis://{db_info['host']}:{db_info['port']}",
                            timeout=2
                        )
                        await redis.ping()
                        redis.close()
                        await redis.wait_closed()
                        is_online = True
                    except:
                        pass

                # Register the database
                database = await self.client.register_database(
                    name=db_info["name"],
                    db_type=db_info["db_type"],
                    host=db_info["host"],
                    port=db_info["port"],
                    database_name=db_info.get("database_name"),
                    max_connections=db_info.get("max_connections", 100),
                    capabilities=db_info.get("capabilities", []),
                    metadata={
                        "description": db_info["description"],
                        "registered_by": "auto_registration"
                    }
                )

                # Update status if online
                if is_online:
                    await self.client.update_status(database.id, ServiceStatus.ONLINE)

                self.registered_entities.add(database.id)
                logger.info(f"✅ Registered Database: {db_info['name']} ({db_info['db_type']} on port {db_info['port']})")

            except Exception as e:
                logger.error(f"Failed to register {db_info['name']}: {e}")

    async def register_running_agents(self):
        """Register currently running agents"""
        try:
            # Get running agents from the system
            import re

            import psutil

            agent_patterns = [
                (r'agents/solomon/solomon\.py', 'Solomon', 'Chief of Staff', ['coordination', 'leadership', 'decision_making']),
                (r'agents/david/david\.py', 'David', 'CEO', ['executive', 'strategy', 'vision']),
                (r'agents/primordials/adam\.py', 'Adam', 'Agent Creator', ['agent_creation', 'automation', 'development']),
                (r'agents/primordials/eve\.py', 'Eve', 'Agent Evolver', ['agent_evolution', 'optimization', 'adaptation']),
                (r'agents/primordials/bezalel\.py', 'Bezalel', 'Master Programmer', ['programming', 'architecture', 'craftsmanship'])
            ]

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])

                    for pattern, agent_name, role, capabilities in agent_patterns:
                        if re.search(pattern, cmdline):
                            # Register the agent
                            agent = await self.client.register_agent(
                                name=agent_name,
                                capabilities=capabilities,
                                metadata={
                                    "role": role,
                                    "pid": proc.info['pid'],
                                    "registered_by": "auto_registration",
                                    "process_detection": True
                                }
                            )

                            # Mark as online
                            await self.client.update_status(agent.id, ServiceStatus.ONLINE)

                            self.registered_entities.add(agent.id)
                            logger.info(f"✅ Registered Agent: {agent_name} ({role}) - PID {proc.info['pid']}")
                            break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.error(f"Failed to register running agents: {e}")

    async def start_heartbeat_loop(self):
        """Start heartbeat loop for all registered entities"""
        while True:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

                for entity_id in self.registered_entities:
                    try:
                        await self.client.send_heartbeat(entity_id)
                    except Exception as e:
                        logger.error(f"Failed to send heartbeat for {entity_id}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")


async def run_auto_registration():
    """Run the auto-registration process"""
    registrar = RegistryAutoRegistration()

    try:
        await registrar.initialize()
        await registrar.register_all_components()

        # Start heartbeat loop
        heartbeat_task = asyncio.create_task(registrar.start_heartbeat_loop())

        # Keep running
        await asyncio.sleep(3600)  # Run for 1 hour

        heartbeat_task.cancel()
        await heartbeat_task

    finally:
        await registrar.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run auto-registration
    asyncio.run(run_auto_registration())
