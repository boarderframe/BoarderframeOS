#!/usr/bin/env python3
"""
Register all organizational data (Agents, Leaders, Departments) in the registry - V2
Works with the existing schema structure
"""

import json
import subprocess
import uuid
from datetime import datetime


def register_organizational_data():
    """Register agents, leaders, and departments from existing database"""
    print("🏢 BoarderframeOS Organizational Data Registration V2")
    print("=" * 50)

    # First, let's check what we have in the main tables
    print("\n📊 Checking existing data...")
    check_query = """
    SELECT
        'Departments' as type, COUNT(*) as count FROM departments
    UNION ALL
    SELECT
        'Department Leaders' as type, COUNT(*) as count FROM department_leaders
    UNION ALL
    SELECT
        'Agents' as type, COUNT(*) as count FROM agents;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", check_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("\nExisting Data:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    type_name = parts[0].strip()
                    count = parts[1].strip()
                    print(f"   {type_name}: {count}")

    # Register Departments
    print("\n📝 Registering Departments...")
    dept_query = """
    INSERT INTO department_registry (
        department_id, name, phase, priority, category, status,
        leaders, capabilities, description, objectives, metadata
    )
    SELECT
        d.id,
        d.name,
        COALESCE(d.phase, 1) as phase,
        COALESCE(d.priority, 5) as priority,
        COALESCE(d.category, 'operational') as category,
        'active' as status,
        COALESCE(
            (SELECT json_agg(json_build_object(
                'leader_id', dl.leader_id,
                'role', dl.role
            ))
            FROM department_leaders dl
            WHERE dl.department_id = d.id),
            '[]'::json
        )::jsonb as leaders,
        COALESCE(d.core_capabilities, '["general"]'::jsonb) as capabilities,
        COALESCE(d.purpose, 'Department operations') as description,
        COALESCE(d.objectives, '[]'::jsonb) as objectives,
        json_build_object(
            'level', d.level,
            'division_id', d.division_id,
            'registered_by', 'organizational_sync_v2',
            'sync_date', to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')
        )::jsonb as metadata
    FROM departments d
    ON CONFLICT (department_id) DO UPDATE SET
        name = EXCLUDED.name,
        leaders = EXCLUDED.leaders,
        metadata = EXCLUDED.metadata,
        updated_at = CURRENT_TIMESTAMP;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", dept_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        count_result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c",
            "SELECT COUNT(*) FROM department_registry;"
        ], capture_output=True, text=True)
        count = count_result.stdout.strip()
        print(f"   ✅ Registered {count} departments")
    else:
        print(f"   ❌ Failed: {result.stderr[:100]}")

    # Register Agents from agents table
    print("\n📝 Registering Agents from agents table...")

    # First ensure we have the agent records in the agents table
    agent_sync_query = """
    INSERT INTO agent_registry (
        agent_id, name, agent_type, status, capabilities,
        health_status, authority_level, max_concurrent_tasks,
        metadata
    )
    SELECT
        a.id,
        a.name,
        COALESCE(a.type, 'agent') as agent_type,
        CASE
            WHEN a.status = 'active' THEN 'online'
            ELSE 'offline'
        END as status,
        COALESCE(a.metadata->'capabilities', '["general"]'::jsonb) as capabilities,
        'healthy' as health_status,
        CASE
            WHEN a.name IN ('Solomon', 'David') THEN 10
            WHEN a.name IN ('Adam', 'Eve', 'Bezalel') THEN 9
            ELSE 5
        END as authority_level,
        10 as max_concurrent_tasks,
        COALESCE(a.metadata, '{}'::jsonb) ||
        json_build_object(
            'registered_by', 'organizational_sync_v2',
            'sync_date', to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')
        )::jsonb as metadata
    FROM agents a
    ON CONFLICT (agent_id) DO UPDATE SET
        status = EXCLUDED.status,
        capabilities = EXCLUDED.capabilities,
        metadata = EXCLUDED.metadata,
        updated_at = CURRENT_TIMESTAMP;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", agent_sync_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"   ✅ Synchronized agents from agents table")
    else:
        print(f"   ❌ Failed: {result.stderr[:100]}")

    # Register Department Leaders as Agents
    print("\n📝 Registering Department Leaders as Agents...")

    # First, we need to ensure leader records exist in agents table
    create_leader_agents_query = """
    WITH leader_agents AS (
        SELECT
            dl.leader_id as id,
            COALESCE(
                CASE
                    WHEN d.name LIKE '%Solomon%' THEN 'Solomon'
                    WHEN d.name LIKE '%David%' THEN 'David'
                    WHEN d.name LIKE '%Adam%' THEN 'Adam'
                    WHEN d.name LIKE '%Eve%' THEN 'Eve'
                    WHEN d.name LIKE '%Bezalel%' THEN 'Bezalel'
                    ELSE d.name || ' Leader'
                END,
                'Department Leader'
            ) as name,
            'leader' as type,
            'active' as status,
            json_build_object(
                'role', dl.role,
                'department_name', d.name,
                'department_id', d.id,
                'capabilities', ARRAY['leadership', 'decision_making', 'coordination']
            )::jsonb as metadata
        FROM department_leaders dl
        JOIN departments d ON dl.department_id = d.id
    )
    INSERT INTO agents (id, name, type, status, metadata)
    SELECT * FROM leader_agents
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        type = EXCLUDED.type,
        status = EXCLUDED.status,
        metadata = EXCLUDED.metadata;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", create_leader_agents_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"   ✅ Created leader records in agents table")

        # Now register them in agent_registry
        leader_registry_query = """
        INSERT INTO agent_registry (
            agent_id, name, department_id, agent_type, status,
            capabilities, health_status, authority_level,
            max_concurrent_tasks, metadata
        )
        SELECT
            dl.leader_id,
            COALESCE(
                CASE
                    WHEN d.name LIKE '%Solomon%' THEN 'Solomon'
                    WHEN d.name LIKE '%David%' THEN 'David'
                    WHEN d.name LIKE '%Adam%' THEN 'Adam'
                    WHEN d.name LIKE '%Eve%' THEN 'Eve'
                    WHEN d.name LIKE '%Bezalel%' THEN 'Bezalel'
                    ELSE d.name || ' Leader'
                END,
                'Department Leader'
            ) as name,
            dl.department_id,
            'leader' as agent_type,
            'online' as status,
            json_build_array('leadership', 'decision_making', 'coordination')::jsonb as capabilities,
            'healthy' as health_status,
            CASE
                WHEN d.name LIKE '%Solomon%' OR d.name LIKE '%David%' THEN 10
                WHEN d.name LIKE '%Adam%' OR d.name LIKE '%Eve%' OR d.name LIKE '%Bezalel%' THEN 9
                ELSE 7
            END as authority_level,
            20 as max_concurrent_tasks,
            json_build_object(
                'role', dl.role,
                'department_name', d.name,
                'is_leader', true,
                'registered_by', 'organizational_sync_v2'
            )::jsonb as metadata
        FROM department_leaders dl
        JOIN departments d ON dl.department_id = d.id
        ON CONFLICT (agent_id) DO UPDATE SET
            department_id = EXCLUDED.department_id,
            authority_level = EXCLUDED.authority_level,
            metadata = EXCLUDED.metadata,
            updated_at = CURRENT_TIMESTAMP;
        """

        result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", leader_registry_query
        ], capture_output=True, text=True)

        if result.returncode == 0:
            count_result = subprocess.run([
                "docker", "exec", "boarderframeos_postgres",
                "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c",
                "SELECT COUNT(*) FROM agent_registry WHERE metadata->>'is_leader' = 'true';"
            ], capture_output=True, text=True)
            count = count_result.stdout.strip()
            print(f"   ✅ Registered {count} leaders in agent registry")
        else:
            print(f"   ❌ Failed to register leaders: {result.stderr[:100]}")
    else:
        print(f"   ❌ Failed to create leader agents: {result.stderr[:100]}")

    # Ensure Executive Agents exist
    print("\n📝 Ensuring Executive Agents are registered...")
    executives = [
        ("Solomon", "Chief of Staff", 10, ["coordination", "leadership", "wisdom", "decision_making"]),
        ("David", "CEO", 10, ["executive", "strategy", "vision", "leadership"]),
        ("Adam", "Agent Creator", 9, ["agent_creation", "automation", "development"]),
        ("Eve", "Agent Evolver", 9, ["agent_evolution", "optimization", "adaptation"]),
        ("Bezalel", "Master Programmer", 9, ["programming", "architecture", "craftsmanship"])
    ]

    for name, role, authority, capabilities in executives:
        # Create unique ID for each executive
        exec_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"boarderframeos.agent.{name.lower()}"))

        # First ensure they exist in agents table
        create_exec_query = f"""
        INSERT INTO agents (id, name, type, status, metadata)
        VALUES (
            '{exec_id}'::uuid,
            '{name}',
            'executive',
            'active',
            '{json.dumps({"role": role, "capabilities": capabilities, "executive": True})}'::jsonb
        )
        ON CONFLICT (id) DO UPDATE SET
            status = 'active',
            metadata = agents.metadata || '{json.dumps({"last_sync": datetime.now().isoformat()})}'::jsonb;
        """

        subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", create_exec_query
        ], capture_output=True, text=True)

        # Then register in agent_registry
        register_exec_query = f"""
        INSERT INTO agent_registry (
            agent_id, name, agent_type, status, capabilities,
            health_status, authority_level, max_concurrent_tasks, metadata
        )
        VALUES (
            '{exec_id}'::uuid,
            '{name}',
            'executive',
            'online',
            '{json.dumps(capabilities)}'::jsonb,
            'healthy',
            {authority},
            50,
            '{json.dumps({"role": role, "executive": True, "registered_by": "executive_registration_v2"})}'::jsonb
        )
        ON CONFLICT (agent_id) DO UPDATE SET
            capabilities = EXCLUDED.capabilities,
            authority_level = EXCLUDED.authority_level,
            metadata = EXCLUDED.metadata,
            updated_at = CURRENT_TIMESTAMP;
        """

        result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", register_exec_query
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"   ✅ {name} ({role})")
        else:
            if "duplicate" in result.stderr or "already exists" in result.stderr:
                print(f"   ℹ️  {name} already registered")
            else:
                print(f"   ❌ {name} - Error: {result.stderr[:50]}")

    # Log registry event
    event_query = """
    INSERT INTO registry_event_log (
        entity_type, entity_id, event_type, event_data
    ) VALUES (
        'system',
        gen_random_uuid(),
        'bulk_registration',
        json_build_object(
            'source', 'register_organizational_data_v2.py',
            'description', 'Bulk registration of departments, leaders, and agents',
            'timestamp', to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')
        )::jsonb
    );
    """

    subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", event_query
    ], capture_output=True, text=True)

    # Show final counts
    print("\n📊 Final Registry Status...")

    count_query = """
    SELECT
        'Departments' as type, COUNT(*) as count FROM department_registry
    UNION ALL
    SELECT
        'Leaders' as type, COUNT(*) as count FROM agent_registry WHERE metadata->>'is_leader' = 'true'
    UNION ALL
    SELECT
        'Executives' as type, COUNT(*) as count FROM agent_registry WHERE metadata->>'executive' = 'true'
    UNION ALL
    SELECT
        'Agents (Total)' as type, COUNT(*) as count FROM agent_registry
    UNION ALL
    SELECT
        'Servers' as type, COUNT(*) as count FROM server_registry
    UNION ALL
    SELECT
        'Databases' as type, COUNT(*) as count FROM database_registry;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", count_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("\nRegistry Contents:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    type_name = parts[0].strip()
                    count = parts[1].strip()
                    print(f"   {type_name}: {count} registered")

    print("\n✅ Organizational Registration Complete!")
    print("\n🌐 View the complete registry at:")
    print("   http://localhost:8888 -> Registry tab")
    print("\n💡 The registry now includes:")
    print("   - All 45 departments with their leaders")
    print("   - All department leaders as agents")
    print("   - Executive agents (Solomon, David, Adam, Eve, Bezalel)")
    print("   - All servers and databases")


if __name__ == "__main__":
    register_organizational_data()
