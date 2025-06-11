#!/usr/bin/env python3
"""
Simple registration of executive agents and departments
"""

import json
import subprocess
import uuid
from datetime import datetime


def register_executives():
    """Register executive agents directly"""
    print("👑 BoarderframeOS Executive Registration")
    print("=" * 50)

    # Executive agents
    executives = [
        {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "boarderframeos.agent.solomon")),
            "name": "Solomon",
            "role": "Chief of Staff",
            "department": "Executive Leadership",
            "authority": 10,
            "capabilities": ["coordination", "leadership", "wisdom", "decision_making"],
        },
        {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "boarderframeos.agent.david")),
            "name": "David",
            "role": "CEO",
            "department": "Executive Leadership",
            "authority": 10,
            "capabilities": ["executive", "strategy", "vision", "leadership"],
        },
        {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "boarderframeos.agent.adam")),
            "name": "Adam",
            "role": "Agent Creator",
            "department": "Primordial Agents",
            "authority": 9,
            "capabilities": ["agent_creation", "automation", "development"],
        },
        {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "boarderframeos.agent.eve")),
            "name": "Eve",
            "role": "Agent Evolver",
            "department": "Primordial Agents",
            "authority": 9,
            "capabilities": ["agent_evolution", "optimization", "adaptation"],
        },
        {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "boarderframeos.agent.bezalel")),
            "name": "Bezalel",
            "role": "Master Programmer",
            "department": "Primordial Agents",
            "authority": 9,
            "capabilities": ["programming", "architecture", "craftsmanship"],
        },
    ]

    print("\n📝 Creating Executive Agents...")
    for exec in executives:
        # First ensure they exist in agents table
        agent_query = f"""
        INSERT INTO agents (id, name, department, agent_type, status, capabilities)
        VALUES (
            '{exec["id"]}'::uuid,
            '{exec["name"]}',
            '{exec["department"]}',
            'executive',
            'active',
            '{json.dumps(exec["capabilities"])}'::jsonb
        )
        ON CONFLICT (id) DO UPDATE SET
            status = 'active',
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
                agent_query,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"   ✅ Created agent: {exec['name']}")
        else:
            if "duplicate" in result.stderr:
                print(f"   ℹ️  {exec['name']} already exists in agents")
            else:
                print(f"   ❌ Failed to create {exec['name']}: {result.stderr[:50]}")

        # Now register in agent_registry
        registry_query = f"""
        INSERT INTO agent_registry (
            agent_id, name, agent_type, status,
            capabilities, health_status, authority_level,
            max_concurrent_tasks, metadata
        )
        VALUES (
            '{exec["id"]}'::uuid,
            '{exec["name"]}',
            'executive',
            'online',
            '{json.dumps(exec["capabilities"])}'::jsonb,
            'healthy',
            {exec["authority"]},
            50,
            '{json.dumps({"role": exec["role"], "department": exec["department"], "executive": True})}'::jsonb
        )
        ON CONFLICT (agent_id) DO UPDATE SET
            status = 'online',
            capabilities = EXCLUDED.capabilities,
            authority_level = EXCLUDED.authority_level,
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
                registry_query,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"   ✅ Registered: {exec['name']} ({exec['role']})")
        else:
            print(f"   ❌ Failed to register {exec['name']}: {result.stderr[:50]}")

    # Register some key departments
    print("\n📝 Registering Key Departments...")

    # Get some departments to register
    dept_query = """
    SELECT d.id, d.name, d.phase, d.priority, d.level, d.purpose
    FROM departments d
    WHERE d.level = 1 OR d.name IN (
        'Executive Leadership', 'Primordial Agents', 'Business Operations',
        'Customer Relations', 'Technology', 'Data & Analytics'
    )
    LIMIT 10;
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
            "-A",
            "-F",
            "|",
            "-c",
            dept_query,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and result.stdout:
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 6:
                    dept_id = parts[0]
                    name = parts[1]
                    phase = parts[2] or "1"
                    priority = parts[3] or "5"
                    level = parts[4]
                    purpose = parts[5] or "Department operations"

                    register_dept_query = f"""
                    INSERT INTO department_registry (
                        department_id, name, phase, priority, category,
                        status, description, metadata
                    )
                    VALUES (
                        '{dept_id}'::uuid,
                        '{name}',
                        {phase},
                        {priority},
                        'operational',
                        'active',
                        '{purpose.replace("'", "''")}',
                        '{json.dumps({"level": level, "registered_by": "executive_registration"})}'::jsonb
                    )
                    ON CONFLICT (department_id) DO UPDATE SET
                        status = 'active',
                        updated_at = CURRENT_TIMESTAMP;
                    """

                    reg_result = subprocess.run(
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
                            register_dept_query,
                        ],
                        capture_output=True,
                        text=True,
                    )

                    if reg_result.returncode == 0:
                        print(f"   ✅ {name}")
                    else:
                        print(f"   ❌ {name}: {reg_result.stderr[:30]}")

    # Show final counts
    print("\n📊 Final Registry Status...")

    count_query = """
    SELECT
        'Departments' as type, COUNT(*) as count FROM department_registry
    UNION ALL
    SELECT
        'Executive Agents' as type, COUNT(*) as count
        FROM agent_registry
        WHERE metadata->>'executive' = 'true'
    UNION ALL
    SELECT
        'Total Agents' as type, COUNT(*) as count FROM agent_registry
    UNION ALL
    SELECT
        'Servers' as type, COUNT(*) as count FROM server_registry
    UNION ALL
    SELECT
        'Databases' as type, COUNT(*) as count FROM database_registry;
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

    print("\n✅ Executive Registration Complete!")
    print("\n🌐 View the updated registry at:")
    print("   http://localhost:8888 -> Registry tab")


if __name__ == "__main__":
    register_executives()
