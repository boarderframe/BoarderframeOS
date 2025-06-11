#!/usr/bin/env python3
"""
Simple direct database registration of all BoarderframeOS components
"""

import json
import subprocess
import uuid
from datetime import datetime


def register_all_components():
    """Register all components directly in the database"""
    print("🚀 BoarderframeOS Component Registration")
    print("=" * 50)

    # MCP Servers
    mcp_servers = [
        {
            "name": "Registry Server",
            "server_type": "mcp",
            "port": 8009,
            "url": "http://localhost:8009",
            "capabilities": ["service_discovery", "health_monitoring", "registration"],
        },
        {
            "name": "Filesystem Server",
            "server_type": "mcp",
            "port": 8001,
            "url": "http://localhost:8001",
            "capabilities": ["file_operations", "directory_management", "search"],
        },
        {
            "name": "Database Server",
            "server_type": "mcp",
            "port": 8004,
            "url": "http://localhost:8004",
            "capabilities": ["sqlite_operations", "query_execution"],
        },
        {
            "name": "Analytics Server",
            "server_type": "mcp",
            "port": 8007,
            "url": "http://localhost:8007",
            "capabilities": ["data_analytics", "metrics_collection", "reporting"],
        },
        {
            "name": "Payment Server",
            "server_type": "mcp",
            "port": 8006,
            "url": "http://localhost:8006",
            "capabilities": ["payment_processing", "billing", "revenue_tracking"],
        },
        {
            "name": "Customer Server",
            "server_type": "mcp",
            "port": 8008,
            "url": "http://localhost:8008",
            "capabilities": ["customer_management", "crm", "support_tickets"],
        },
    ]

    # Core Systems
    core_systems = [
        {
            "name": "Corporate Headquarters",
            "server_type": "core_system",
            "port": 8888,
            "url": "http://localhost:8888",
            "capabilities": ["dashboard", "system_monitoring", "agent_management"],
        },
        {
            "name": "Agent Cortex Management",
            "server_type": "core_system",
            "port": 8889,
            "url": "http://localhost:8889",
            "capabilities": [
                "llm_orchestration",
                "model_management",
                "cost_optimization",
            ],
        },
    ]

    # All servers combined
    all_servers = mcp_servers + core_systems

    print("\n📝 Registering Servers...")
    for server in all_servers:
        server_id = str(uuid.uuid4())
        query = f"""
        INSERT INTO server_registry (
            id, name, server_type, status, endpoint_url,
            health_check_url, capabilities, health_status,
            metadata, registered_at, api_version
        ) VALUES (
            '{server_id}',
            '{server["name"]}',
            '{server["server_type"]}',
            'online',
            '{server["url"]}',
            '{server["url"]}/health',
            '{json.dumps(server["capabilities"])}',
            'healthy',
            '{json.dumps({"port": server["port"], "registered_by": "simple_registration"})}',
            '{datetime.utcnow().isoformat()}',
            '1.0'
        )
        ON CONFLICT (name) DO UPDATE SET
            endpoint_url = EXCLUDED.endpoint_url,
            capabilities = EXCLUDED.capabilities,
            metadata = EXCLUDED.metadata,
            updated_at = CURRENT_TIMESTAMP;
        """

        result = subprocess.run(
            [
                "docker",
                "exec",
                "boarderframeos_postgres",
                "psql",
                "-U",
                "boarderframe",
                "-d",
                "boarderframeos",
                "-c",
                query,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"   ✅ {server['name']} (port {server['port']})")
        else:
            print(f"   ❌ {server['name']} - {result.stderr[:50]}")

    # Register Databases
    print("\n📝 Registering Databases...")
    databases = [
        {
            "name": "PostgreSQL Primary",
            "db_type": "postgresql",
            "host": "localhost",
            "port": 5434,
            "database_name": "boarderframeos",
        },
        {
            "name": "Redis Cache",
            "db_type": "redis",
            "host": "localhost",
            "port": 6379,
            "database_name": None,
        },
    ]

    for db in databases:
        db_id = str(uuid.uuid4())
        db_name_value = f"'{db['database_name']}'" if db["database_name"] else "NULL"

        query = f"""
        INSERT INTO database_registry (
            id, name, db_type, status, host, port,
            database_name, health_status, max_connections,
            metadata, registered_at
        ) VALUES (
            '{db_id}',
            '{db["name"]}',
            '{db["db_type"]}',
            'online',
            '{db["host"]}',
            {db["port"]},
            {db_name_value},
            'healthy',
            100,
            '{json.dumps({"registered_by": "simple_registration"})}',
            '{datetime.utcnow().isoformat()}'
        )
        ON CONFLICT (host, port, database_name) DO UPDATE SET
            name = EXCLUDED.name,
            db_type = EXCLUDED.db_type,
            metadata = EXCLUDED.metadata,
            updated_at = CURRENT_TIMESTAMP;
        """

        result = subprocess.run(
            [
                "docker",
                "exec",
                "boarderframeos_postgres",
                "psql",
                "-U",
                "boarderframe",
                "-d",
                "boarderframeos",
                "-c",
                query,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"   ✅ {db['name']} ({db['db_type']} on port {db['port']})")
        else:
            print(f"   ❌ {db['name']} - {result.stderr[:50]}")

    # Show current counts
    print("\n📊 Checking Registration Results...")

    count_query = """
    SELECT
        'Servers' as type, COUNT(*) as count FROM server_registry
    UNION ALL
    SELECT
        'Databases' as type, COUNT(*) as count FROM database_registry
    UNION ALL
    SELECT
        'Agents' as type, COUNT(*) as count FROM agent_registry;
    """

    result = subprocess.run(
        [
            "docker",
            "exec",
            "boarderframeos_postgres",
            "psql",
            "-U",
            "boarderframe",
            "-d",
            "boarderframeos",
            "-t",
            "-c",
            count_query,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("\nRegistry Contents:")
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    type_name = parts[0].strip()
                    count = parts[1].strip()
                    print(f"   {type_name}: {count} registered")

    print("\n✅ Registration Complete!")
    print("\n🌐 View the updated registry at:")
    print("   http://localhost:8888 -> Registry tab")
    print("\n💡 The registry will now show all servers and databases!")


if __name__ == "__main__":
    register_all_components()
