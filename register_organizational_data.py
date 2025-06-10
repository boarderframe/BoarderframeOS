#!/usr/bin/env python3
"""
Register all organizational data (Agents, Leaders, Departments) in the enhanced registry
"""

import subprocess
import json
import uuid
from datetime import datetime

def register_organizational_data():
    """Register agents, leaders, and departments from existing database"""
    print("🏢 BoarderframeOS Organizational Data Registration")
    print("=" * 50)
    
    # Register Departments
    print("\n📝 Registering Departments from existing data...")
    dept_query = """
    INSERT INTO department_registry (id, name, parent_id, leader_id, status, metadata, registered_at)
    SELECT 
        COALESCE(d.id::text, gen_random_uuid()::text) as id,
        d.name,
        d.parent_id::text,
        dl.leader_id::text,
        'active' as status,
        json_build_object(
            'level', d.level,
            'division_id', d.division_id,
            'purpose', d.purpose,
            'registered_by', 'organizational_sync'
        )::jsonb as metadata,
        CURRENT_TIMESTAMP as registered_at
    FROM departments d
    LEFT JOIN department_leaders dl ON d.id = dl.department_id
    ON CONFLICT (id) DO UPDATE SET
        leader_id = EXCLUDED.leader_id,
        metadata = EXCLUDED.metadata,
        updated_at = CURRENT_TIMESTAMP;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", dept_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Get count of registered departments
        count_result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c",
            "SELECT COUNT(*) FROM department_registry;"
        ], capture_output=True, text=True)
        count = count_result.stdout.strip()
        print(f"   ✅ Registered {count} departments")
    else:
        print(f"   ❌ Failed to register departments: {result.stderr[:100]}")
    
    # Register Leaders/Agents with leadership roles
    print("\n📝 Registering Leaders as Agents...")
    leader_query = """
    INSERT INTO agent_registry (
        id, name, agent_type, status, capabilities, 
        health_status, is_leader, department_id, 
        metadata, registered_at
    )
    SELECT 
        dl.leader_id::text as id,
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
        'leader' as agent_type,
        'active' as status,
        ARRAY['leadership', 'decision_making', 'coordination']::text[] as capabilities,
        'healthy' as health_status,
        true as is_leader,
        dl.department_id::text as department_id,
        json_build_object(
            'role', dl.role,
            'department_name', d.name,
            'registered_by', 'organizational_sync'
        )::jsonb as metadata,
        CURRENT_TIMESTAMP as registered_at
    FROM department_leaders dl
    JOIN departments d ON dl.department_id = d.id
    ON CONFLICT (id) DO UPDATE SET
        department_id = EXCLUDED.department_id,
        metadata = EXCLUDED.metadata,
        updated_at = CURRENT_TIMESTAMP;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", leader_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Get count of leaders
        count_result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c",
            "SELECT COUNT(*) FROM agent_registry WHERE is_leader = true;"
        ], capture_output=True, text=True)
        count = count_result.stdout.strip()
        print(f"   ✅ Registered {count} leaders as agents")
    else:
        print(f"   ❌ Failed to register leaders: {result.stderr[:100]}")
    
    # Register regular agents from agents table
    print("\n📝 Registering Agents from agents table...")
    agent_query = """
    INSERT INTO agent_registry (
        id, name, agent_type, status, capabilities,
        health_status, is_leader, metadata, registered_at
    )
    SELECT 
        a.id::text,
        a.name,
        COALESCE(a.type, 'agent') as agent_type,
        CASE 
            WHEN a.status = 'active' THEN 'online'
            ELSE 'offline'
        END as status,
        COALESCE(
            string_to_array(a.capabilities, ','),
            ARRAY['general']::text[]
        ) as capabilities,
        'healthy' as health_status,
        false as is_leader,
        COALESCE(a.metadata, '{}'::jsonb) || 
        json_build_object('registered_by', 'organizational_sync')::jsonb as metadata,
        CURRENT_TIMESTAMP as registered_at
    FROM agents a
    ON CONFLICT (id) DO UPDATE SET
        status = EXCLUDED.status,
        capabilities = EXCLUDED.capabilities,
        metadata = EXCLUDED.metadata,
        updated_at = CURRENT_TIMESTAMP;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", agent_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ Synchronized agents from agents table")
    else:
        print(f"   ❌ Failed to sync agents: {result.stderr[:100]}")
    
    # Register known executive agents if not already present
    print("\n📝 Ensuring executive agents are registered...")
    executives = [
        {
            "name": "Solomon",
            "role": "Chief of Staff",
            "capabilities": ["coordination", "leadership", "wisdom", "decision_making"]
        },
        {
            "name": "David", 
            "role": "CEO",
            "capabilities": ["executive", "strategy", "vision", "leadership"]
        },
        {
            "name": "Adam",
            "role": "Agent Creator", 
            "capabilities": ["agent_creation", "automation", "development"]
        },
        {
            "name": "Eve",
            "role": "Agent Evolver",
            "capabilities": ["agent_evolution", "optimization", "adaptation"]
        },
        {
            "name": "Bezalel",
            "role": "Master Programmer",
            "capabilities": ["programming", "architecture", "craftsmanship"]
        }
    ]
    
    for exec_agent in executives:
        exec_id = str(uuid.uuid4())
        exec_query = f"""
        INSERT INTO agent_registry (
            id, name, agent_type, status, capabilities,
            health_status, is_leader, metadata, registered_at
        ) VALUES (
            '{exec_id}',
            '{exec_agent["name"]}',
            'executive',
            'active',
            '{{{",".join(f'"{cap}"' for cap in exec_agent["capabilities"])}}}',
            'healthy',
            true,
            '{json.dumps({"role": exec_agent["role"], "registered_by": "executive_registration"})}',
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (name) DO UPDATE SET
            capabilities = EXCLUDED.capabilities,
            metadata = EXCLUDED.metadata,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", exec_query
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ {exec_agent['name']} ({exec_agent['role']})")
        else:
            # Try to extract just the agent name conflict
            if "already exists" in result.stderr:
                print(f"   ℹ️  {exec_agent['name']} already registered")
            else:
                print(f"   ❌ {exec_agent['name']} - {result.stderr[:50]}")
    
    # Log registry event
    event_query = """
    INSERT INTO registry_event_log (
        id, entity_type, entity_id, event_type, 
        event_data, created_at
    ) VALUES (
        gen_random_uuid(),
        'system',
        'organizational_sync',
        'bulk_registration',
        '{"source": "register_organizational_data.py", "description": "Bulk registration of departments, leaders, and agents"}'::jsonb,
        CURRENT_TIMESTAMP
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
        'Leaders' as type, COUNT(*) as count FROM agent_registry WHERE is_leader = true
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
    print("\n💡 The registry now includes all departments, leaders, and agents!")


if __name__ == "__main__":
    register_organizational_data()