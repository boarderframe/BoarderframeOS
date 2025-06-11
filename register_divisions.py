#!/usr/bin/env python3
"""
Register divisions in the registry system
"""

import json
import subprocess
from datetime import datetime


def register_divisions():
    """Ensure divisions table exists in registry and populate it"""
    print("🏛️ BoarderframeOS Division Registration")
    print("=" * 50)

    # First, create division_registry table if it doesn't exist
    print("\n📊 Creating division_registry table...")

    create_table_query = """
    CREATE TABLE IF NOT EXISTS division_registry (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        division_id UUID NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        division_key VARCHAR(100) NOT NULL,
        priority INTEGER NOT NULL DEFAULT 5,
        status VARCHAR(50) DEFAULT 'active',
        departments JSONB DEFAULT '[]'::jsonb,
        leaders JSONB DEFAULT '[]'::jsonb,
        total_agents INTEGER DEFAULT 0,
        operational_agents INTEGER DEFAULT 0,
        total_capacity INTEGER DEFAULT 0,
        description TEXT,
        objectives JSONB DEFAULT '[]'::jsonb,
        metadata JSONB DEFAULT '{}'::jsonb,
        registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (division_id) REFERENCES divisions(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_division_registry_status ON division_registry(status);
    CREATE INDEX IF NOT EXISTS idx_division_registry_priority ON division_registry(priority);
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", create_table_query
    ], capture_output=True, text=True)

    if result.returncode == 0 or "already exists" in result.stderr:
        print("   ✅ Division registry table ready")
    else:
        print(f"   ❌ Failed to create table: {result.stderr[:100]}")

    # Get all divisions with their statistics
    print("\n📊 Gathering division data...")

    division_query = """
    SELECT
        d.id,
        d.division_name,
        d.division_key,
        d.priority,
        d.is_active,
        COUNT(DISTINCT dept.id) as dept_count,
        COUNT(DISTINCT dl.id) as leader_count,
        COUNT(DISTINCT a.id) as agent_count,
        COUNT(DISTINCT CASE WHEN a.operational_status = 'operational' THEN a.id END) as operational_count,
        SUM(DISTINCT dept.agent_capacity) as total_capacity,
        STRING_AGG(DISTINCT dept.name, '|' ORDER BY dept.name) as dept_names
    FROM divisions d
    LEFT JOIN departments dept ON dept.division_id = d.id
    LEFT JOIN department_leaders dl ON dl.department_id = dept.id
    LEFT JOIN agents a ON a.department = dept.name
    GROUP BY d.id, d.division_name, d.division_key, d.priority, d.is_active
    ORDER BY d.priority;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", division_query
    ], capture_output=True, text=True)

    divisions = []
    if result.returncode == 0 and result.stdout:
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 11:
                    divisions.append({
                        "id": parts[0],
                        "name": parts[1],
                        "key": parts[2],
                        "priority": parts[3],
                        "is_active": parts[4] == "t",
                        "dept_count": int(parts[5] or 0),
                        "leader_count": int(parts[6] or 0),
                        "agent_count": int(parts[7] or 0),
                        "operational_count": int(parts[8] or 0),
                        "total_capacity": int(parts[9] or 0),
                        "dept_names": parts[10].split('|') if parts[10] else []
                    })

    print(f"   Found {len(divisions)} divisions to register")

    # Register each division
    print("\n📝 Registering divisions...")

    for div in divisions:
        # Prepare department and leader lists
        departments = []
        leaders = []

        if div["dept_names"]:
            # Get department details
            dept_detail_query = f"""
            SELECT
                dept.id,
                dept.name,
                dept.operational_status,
                COUNT(DISTINCT a.id) as agents
            FROM departments dept
            LEFT JOIN agents a ON a.department = dept.name
            WHERE dept.division_id = '{div["id"]}'::uuid
            GROUP BY dept.id, dept.name, dept.operational_status;
            """

            dept_result = subprocess.run([
                "docker", "exec", "boarderframeos_postgres",
                "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", dept_detail_query
            ], capture_output=True, text=True)

            if dept_result.returncode == 0 and dept_result.stdout:
                for line in dept_result.stdout.strip().split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 4:
                            departments.append({
                                "id": parts[0],
                                "name": parts[1],
                                "status": parts[2],
                                "agents": int(parts[3] or 0)
                            })

        # Define division objectives based on key
        objectives_map = {
            "executive": ["Strategic leadership", "Organizational governance", "Vision setting"],
            "programming_development": ["Agent creation", "System architecture", "Code excellence"],
            "information_technology": ["Infrastructure management", "Security", "System reliability"],
            "product_operations": ["Product delivery", "Quality assurance", "Customer satisfaction"],
            "revenue_generation": ["Revenue growth", "Sales excellence", "Market expansion"],
            "business_operations": ["Operational efficiency", "Process optimization", "Resource management"],
            "customer_experience": ["Customer satisfaction", "Support excellence", "Retention"],
            "content_generation": ["Content creation", "Brand messaging", "Media production"],
            "continuous_improvement": ["Innovation", "Learning", "Process improvement"]
        }

        objectives = objectives_map.get(div["key"], ["Divisional excellence", "Team collaboration"])

        # Register the division
        register_query = f"""
        INSERT INTO division_registry (
            division_id, name, division_key, priority, status,
            departments, total_agents, operational_agents,
            total_capacity, description, objectives, metadata
        ) VALUES (
            '{div["id"]}'::uuid,
            '{div["name"].replace("'", "''")}',
            '{div["key"]}',
            {div["priority"]},
            '{"active" if div["is_active"] else "inactive"}',
            '{json.dumps(departments)}'::jsonb,
            {div["agent_count"]},
            {div["operational_count"]},
            {div["total_capacity"]},
            'Strategic division overseeing {div["dept_count"]} departments',
            '{json.dumps(objectives)}'::jsonb,
            '{json.dumps({
                "department_count": div["dept_count"],
                "leader_count": div["leader_count"],
                "registered_by": "division_registration"
            })}'::jsonb
        )
        ON CONFLICT (division_id) DO UPDATE SET
            name = EXCLUDED.name,
            status = EXCLUDED.status,
            departments = EXCLUDED.departments,
            total_agents = EXCLUDED.total_agents,
            operational_agents = EXCLUDED.operational_agents,
            total_capacity = EXCLUDED.total_capacity,
            metadata = EXCLUDED.metadata,
            updated_at = CURRENT_TIMESTAMP;
        """

        result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", register_query
        ], capture_output=True, text=True)

        if result.returncode == 0:
            status_icon = "🟢" if div["is_active"] else "🟡"
            print(f"   {status_icon} {div['name']} - {div['dept_count']} depts, {div['agent_count']} agents")
        else:
            print(f"   ❌ Failed to register {div['name']}: {result.stderr[:50]}")

    # Show summary
    print("\n📊 Division Registry Summary...")

    summary_query = """
    SELECT
        'Total Divisions' as metric, COUNT(*) as value
    FROM division_registry
    UNION ALL
    SELECT
        'Active Divisions', COUNT(*)
    FROM division_registry
    WHERE status = 'active'
    UNION ALL
    SELECT
        'Total Departments', SUM(jsonb_array_length(departments))
    FROM division_registry
    UNION ALL
    SELECT
        'Total Division Capacity', SUM(total_capacity)
    FROM division_registry
    UNION ALL
    SELECT
        'Total Agents in Divisions', SUM(total_agents)
    FROM division_registry
    UNION ALL
    SELECT
        'Operational Agents', SUM(operational_agents)
    FROM division_registry;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", summary_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("\nRegistry Metrics:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    metric = parts[0].strip()
                    value = parts[1].strip() or "0"
                    print(f"   {metric}: {value}")

    # Update registry counts in corporate HQ
    print("\n📊 Final Registry Counts...")

    final_query = """
    SELECT
        'Divisions' as type, COUNT(*) FROM division_registry
    UNION ALL
    SELECT 'Departments', COUNT(*) FROM department_registry
    UNION ALL
    SELECT 'Agents', COUNT(*) FROM agent_registry
    UNION ALL
    SELECT 'Leaders', COUNT(*) FROM agent_registry WHERE metadata->>'is_leader' = 'true'
    UNION ALL
    SELECT 'Servers', COUNT(*) FROM server_registry
    UNION ALL
    SELECT 'Databases', COUNT(*) FROM database_registry
    ORDER BY type;
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", final_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("\nComplete Registry:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    type_name = parts[0].strip()
                    count = parts[1].strip()
                    print(f"   {type_name}: {count}")

    print("\n✅ Division registration complete!")
    print("\n🌐 Complete organizational structure now registered:")
    print("   - Divisions → Departments → Leaders → Agents")
    print("   - View at: http://localhost:8888 -> Registry tab")


if __name__ == "__main__":
    register_divisions()
