#!/usr/bin/env python3
"""
Test script for the Enhanced Registry System
Demonstrates all major features and capabilities
"""

import asyncio
import logging
import random
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.append('/Users/cosburn/BoarderframeOS')

from core.enhanced_registry_system import (
    EnhancedRegistrySystem, RegistryType, ServiceStatus, HealthStatus,
    EventType, ServerType, LeadershipTier,
    AgentRegistryEntry, LeaderRegistryEntry, DepartmentRegistryEntry,
    DivisionRegistryEntry, DatabaseRegistryEntry, ServerRegistryEntry
)
from core.registry_client import RegistryClient, RegistryConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegistryTestSuite:
    """Comprehensive test suite for Enhanced Registry System"""
    
    def __init__(self):
        self.registry = None
        self.client = None
        self.test_entities = []
        
    async def setup(self):
        """Initialize registry and client"""
        logger.info("Setting up Enhanced Registry System...")
        
        # Start registry server
        self.registry = EnhancedRegistrySystem(
            db_url="postgresql://boarderframe:boarderframe@localhost:5434/boarderframeos",
            redis_url="redis://localhost:6379",
            enable_caching=True,
            enable_websockets=True,
            enable_audit_log=True
        )
        
        # Initialize in background
        await self.registry.initialize()
        
        # Create client
        self.client = RegistryClient(RegistryConfig(
            registry_url="http://localhost:8100",
            websocket_url="ws://localhost:8100/ws"
        ))
        await self.client.connect()
        
        logger.info("Registry system ready!")
        
    async def teardown(self):
        """Clean up resources"""
        logger.info("Cleaning up test entities...")
        
        # Unregister all test entities
        for entity_id in self.test_entities:
            try:
                await self.client.unregister(entity_id)
            except:
                pass
                
        # Disconnect client
        await self.client.disconnect()
        
        # Shutdown registry
        await self.registry.shutdown()
        
        logger.info("Cleanup complete!")
        
    async def test_agent_registration(self):
        """Test agent registration and discovery"""
        logger.info("\n=== Testing Agent Registration ===")
        
        # Register multiple agents
        agents = []
        departments = ["sales", "analytics", "engineering", "support"]
        
        for i in range(10):
            dept = random.choice(departments)
            agent = await self.client.register_agent(
                name=f"TestAgent_{i}",
                capabilities=["analyze", "report", "process"] if i % 2 == 0 else ["support", "communicate"],
                department_id=f"{dept}-dept",
                llm_model="gpt-4" if i % 3 == 0 else "gpt-3.5-turbo",
                metadata={
                    "test": True,
                    "index": i,
                    "created_by": "test_suite"
                }
            )
            agents.append(agent)
            self.test_entities.append(agent.id)
            logger.info(f"Registered agent: {agent.name} (ID: {agent.id})")
            
        # Test discovery
        logger.info("\nDiscovering agents with 'analyze' capability...")
        analytics_agents = await self.client.discover_agents(capability="analyze")
        logger.info(f"Found {len(analytics_agents)} agents with analyze capability")
        
        # Test department filtering
        logger.info("\nDiscovering agents in sales department...")
        sales_agents = await self.client.discover_agents(department_id="sales-dept")
        logger.info(f"Found {len(sales_agents)} agents in sales department")
        
        return agents
        
    async def test_leader_registration(self):
        """Test leader registration"""
        logger.info("\n=== Testing Leader Registration ===")
        
        # Register division leader
        division_leader = await self.client.register_leader(
            name="Solomon_Test",
            leadership_tier=LeadershipTier.DIVISION,
            departments_managed=["sales-dept", "analytics-dept"],
            biblical_archetype="King Solomon",
            authority_level=9,
            metadata={"wisdom": "high", "test": True}
        )
        self.test_entities.append(division_leader.id)
        logger.info(f"Registered division leader: {division_leader.name}")
        
        # Register department leaders
        dept_leaders = []
        for dept in ["sales", "analytics", "engineering"]:
            leader = await self.client.register_leader(
                name=f"{dept.capitalize()}Leader_Test",
                leadership_tier=LeadershipTier.DEPARTMENT,
                departments_managed=[f"{dept}-dept"],
                biblical_archetype="Moses" if dept == "engineering" else "David",
                authority_level=7
            )
            dept_leaders.append(leader)
            self.test_entities.append(leader.id)
            logger.info(f"Registered department leader: {leader.name}")
            
        return division_leader, dept_leaders
        
    async def test_department_registration(self):
        """Test department registration"""
        logger.info("\n=== Testing Department Registration ===")
        
        # Create division first
        division = DivisionRegistryEntry(
            id="test-division",
            name="Test Division",
            division_purpose="Testing the enhanced registry",
            metadata={"test": True}
        )
        await self.registry.register(division)
        self.test_entities.append(division.id)
        
        # Register departments
        departments = []
        for dept_name in ["Sales", "Analytics", "Engineering", "Support"]:
            dept = await self.client.register_department(
                name=f"{dept_name} Department",
                division_id=division.id,
                capabilities=[f"{dept_name.lower()}_analysis", f"{dept_name.lower()}_reporting"],
                operational_status="operational",
                agent_capacity=20,
                metadata={"test": True}
            )
            departments.append(dept)
            self.test_entities.append(dept.id)
            logger.info(f"Registered department: {dept.name}")
            
        return division, departments
        
    async def test_server_registration(self):
        """Test server registration"""
        logger.info("\n=== Testing Server Registration ===")
        
        # Register MCP servers
        mcp_servers = []
        mcp_ports = [8001, 8002, 8003, 8004, 8005]
        mcp_names = ["filesystem", "database", "analytics", "payment", "registry"]
        
        for port, name in zip(mcp_ports, mcp_names):
            server = await self.client.register_server(
                name=f"{name}_server_test",
                server_type=ServerType.MCP_SERVER,
                host="localhost",
                port=port,
                endpoints=[
                    {"path": "/health", "method": "GET"},
                    {"path": f"/{name}", "method": "POST"}
                ],
                capabilities=[name, "mcp_protocol"],
                metadata={"test": True}
            )
            mcp_servers.append(server)
            self.test_entities.append(server.id)
            logger.info(f"Registered MCP server: {server.name} on port {port}")
            
        # Register business service
        api_server = await self.client.register_server(
            name="test_api_server",
            server_type=ServerType.BUSINESS_SERVICE,
            host="localhost",
            port=9000,
            protocol="https",
            ssl_enabled=True,
            endpoints=[
                {"path": "/api/v1/users", "method": "GET"},
                {"path": "/api/v1/analytics", "method": "POST"}
            ],
            metadata={"test": True, "version": "1.0.0"}
        )
        self.test_entities.append(api_server.id)
        logger.info(f"Registered business service: {api_server.name}")
        
        return mcp_servers, api_server
        
    async def test_database_registration(self):
        """Test database registration"""
        logger.info("\n=== Testing Database Registration ===")
        
        # Register PostgreSQL
        postgres = await self.client.register_database(
            name="test_postgres",
            db_type="postgresql",
            host="localhost",
            port=5434,
            database_name="boarderframeos_test",
            max_connections=100,
            metadata={"test": True, "primary": True}
        )
        self.test_entities.append(postgres.id)
        logger.info(f"Registered PostgreSQL: {postgres.name}")
        
        # Register Redis
        redis = await self.client.register_database(
            name="test_redis",
            db_type="redis",
            host="localhost",
            port=6379,
            max_connections=50,
            metadata={"test": True, "cache": True}
        )
        self.test_entities.append(redis.id)
        logger.info(f"Registered Redis: {redis.name}")
        
        return postgres, redis
        
    async def test_heartbeat_and_health(self):
        """Test heartbeat and health monitoring"""
        logger.info("\n=== Testing Heartbeat and Health ===")
        
        # Register a test agent
        agent = await self.client.register_agent(
            name="HeartbeatTestAgent",
            capabilities=["test"],
            metadata={"test": True}
        )
        self.test_entities.append(agent.id)
        
        # Send manual heartbeats
        for i in range(5):
            await self.client.send_heartbeat(agent.id)
            logger.info(f"Sent heartbeat {i+1} for agent {agent.id}")
            await asyncio.sleep(2)
            
        # Check health
        updated_agent = await self.client.get_entity(agent.id)
        logger.info(f"Agent health score: {updated_agent.health_score}")
        logger.info(f"Last heartbeat: {updated_agent.last_heartbeat}")
        
    async def test_event_subscriptions(self):
        """Test event subscription system"""
        logger.info("\n=== Testing Event Subscriptions ===")
        
        events_received = []
        
        # Define event handler
        async def on_event(event):
            events_received.append(event)
            logger.info(f"Received event: {event.event_type} for {event.entity_type} {event.entity_id}")
            
        # Subscribe to events
        self.client.on_event(EventType.REGISTERED, on_event)
        self.client.on_event(EventType.STATUS_CHANGED, on_event)
        
        await self.client.subscribe_to_events(
            event_types=[EventType.REGISTERED, EventType.STATUS_CHANGED],
            entity_types=[RegistryType.AGENT]
        )
        
        # Give WebSocket time to connect
        await asyncio.sleep(2)
        
        # Trigger events by registering new agent
        test_agent = await self.client.register_agent(
            name="EventTestAgent",
            capabilities=["trigger_events"],
            metadata={"test": True}
        )
        self.test_entities.append(test_agent.id)
        
        # Change status to trigger event
        await asyncio.sleep(1)
        await self.client.update_status(test_agent.id, ServiceStatus.MAINTENANCE)
        
        # Wait for events
        await asyncio.sleep(3)
        
        logger.info(f"Total events received: {len(events_received)}")
        
    async def test_organizational_hierarchy(self):
        """Test organizational hierarchy retrieval"""
        logger.info("\n=== Testing Organizational Hierarchy ===")
        
        hierarchy = await self.client.get_organizational_hierarchy()
        
        logger.info(f"Total divisions: {len(hierarchy['divisions'])}")
        logger.info(f"Total departments: {hierarchy['total_departments']}")
        logger.info(f"Total agents: {hierarchy['total_agents']}")
        logger.info(f"Total leaders: {hierarchy['total_leaders']}")
        
        # Print division details
        for division in hierarchy['divisions']:
            logger.info(f"\nDivision: {division['name']}")
            logger.info(f"  Departments: {len(division['departments'])}")
            logger.info(f"  Total agents: {division['metrics']['total_agents']}")
            
    async def test_statistics(self):
        """Test statistics endpoint"""
        logger.info("\n=== Testing Statistics ===")
        
        stats = await self.client.get_statistics()
        
        logger.info(f"\nRegistry Statistics:")
        logger.info(f"Total entries: {stats['total_entries']}")
        logger.info(f"By type: {stats['by_type']}")
        logger.info(f"By status: {stats['by_status']}")
        logger.info(f"Health distribution: {stats['by_health']}")
        logger.info(f"Average health score: {stats['performance']['average_health_score']:.2f}")
        logger.info(f"Online percentage: {stats['performance']['online_percentage']:.2f}%")
        
    async def test_performance(self):
        """Test registry performance"""
        logger.info("\n=== Testing Performance ===")
        
        # Measure registration time
        start = datetime.utcnow()
        agents = []
        
        for i in range(50):
            agent = await self.client.register_agent(
                name=f"PerfTestAgent_{i}",
                capabilities=["performance_test"],
                metadata={"test": True, "batch": "performance"}
            )
            agents.append(agent.id)
            self.test_entities.append(agent.id)
            
        registration_time = (datetime.utcnow() - start).total_seconds()
        logger.info(f"Registered 50 agents in {registration_time:.2f} seconds")
        logger.info(f"Average registration time: {(registration_time/50)*1000:.2f} ms")
        
        # Measure discovery time
        start = datetime.utcnow()
        discovered = await self.client.discover_agents(capability="performance_test")
        discovery_time = (datetime.utcnow() - start).total_seconds()
        logger.info(f"Discovered {len(discovered)} agents in {discovery_time*1000:.2f} ms")
        
        # Measure batch update time
        start = datetime.utcnow()
        for agent_id in agents[:10]:
            await self.client.update_entity(agent_id, {
                "status": ServiceStatus.ONLINE,
                "current_load": random.uniform(0, 100)
            })
        update_time = (datetime.utcnow() - start).total_seconds()
        logger.info(f"Updated 10 agents in {update_time:.2f} seconds")
        
    async def run_all_tests(self):
        """Run all test scenarios"""
        try:
            await self.setup()
            
            # Run tests
            await self.test_agent_registration()
            await self.test_leader_registration()
            await self.test_department_registration()
            await self.test_server_registration()
            await self.test_database_registration()
            await self.test_heartbeat_and_health()
            await self.test_event_subscriptions()
            await self.test_organizational_hierarchy()
            await self.test_statistics()
            await self.test_performance()
            
            logger.info("\n=== All Tests Completed Successfully! ===")
            
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
        finally:
            await self.teardown()


async def main():
    """Main test runner"""
    # Print header
    print("=" * 60)
    print("BoarderframeOS Enhanced Registry System Test Suite")
    print("=" * 60)
    
    # Run tests
    test_suite = RegistryTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())