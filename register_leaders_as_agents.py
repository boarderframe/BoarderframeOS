#!/usr/bin/env python3
"""
Register department leaders as agents in the agent registry
"""

import json
import subprocess
import uuid


def register_leaders():
    """Register all department leaders as agents"""
    print("👔 Registering Department Leaders as Agents")
    print("=" * 50)

    # Get all department leaders
    leaders_query = """
    SELECT
        dl.id,
        dl.name,
        dl.title,
        dl.department_id,
        d.name as department_name,
        dl.authority_level,
        dl.biblical_archetype,
        dl.specialization,
        dl.is_primary
    FROM department_leaders dl
    JOIN departments d ON dl.department_id = d.id
    WHERE dl.active_status = 'active'
    ORDER BY dl.authority_level DESC, dl.name;
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
            leaders_query,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0 and result.stdout:
        leaders = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 9:
                    leaders.append(
                        {
                            "id": parts[0],
                            "name": parts[1],
                            "title": parts[2],
                            "department_id": parts[3],
                            "department_name": parts[4],
                            "authority_level": parts[5] or "5",
                            "biblical_archetype": parts[6],
                            "specialization": parts[7],
                            "is_primary": parts[8] == "t",
                        }
                    )

        print(f"\n📝 Found {len(leaders)} leaders to register as agents...")

        success_count = 0
        for leader in leaders:
            # Generate a unique UUID for the leader as an agent
            leader_agent_id = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"boarderframeos.leader.{leader['id']}")
            )

            # First create in agents table
            create_agent_query = f"""
            INSERT INTO agents (id, name, department, agent_type, status, capabilities)
            VALUES (
                '{leader_agent_id}'::uuid,
                '{leader["name"].replace("'", "''")}',
                '{leader["department_name"].replace("'", "''")}',
                'leader',
                'active',
                '["leadership", "decision_making", "coordination"]'::jsonb
            )
            ON CONFLICT (id) DO UPDATE SET
                department = EXCLUDED.department,
                status = 'active',
                updated_at = CURRENT_TIMESTAMP;
            """

            agent_result = subprocess.run(
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
                    create_agent_query,
                ],
                capture_output=True,
                text=True,
            )

            if agent_result.returncode == 0 or "duplicate" in agent_result.stderr:
                # Now register in agent_registry
                capabilities = ["leadership", "decision_making", "coordination"]
                if leader["specialization"]:
                    capabilities.append(
                        leader["specialization"].lower().replace(" ", "_")
                    )

                register_query = f"""
                INSERT INTO agent_registry (
                    agent_id, name, department_id, agent_type, status,
                    capabilities, health_status, authority_level,
                    max_concurrent_tasks, metadata
                )
                VALUES (
                    '{leader_agent_id}'::uuid,
                    '{leader["name"].replace("'", "''")}',
                    '{leader["department_id"]}'::uuid,
                    'leader',
                    'online',
                    '{json.dumps(capabilities)}'::jsonb,
                    'healthy',
                    {leader["authority_level"]},
                    20,
                    '{json.dumps({
                        "title": leader["title"],
                        "department_name": leader["department_name"],
                        "is_primary": leader["is_primary"],
                        "biblical_archetype": leader["biblical_archetype"],
                        "leader_table_id": int(leader["id"]),
                        "is_leader": True,
                        "registered_by": "leader_registration"
                    })}'::jsonb
                )
                ON CONFLICT (agent_id) DO UPDATE SET
                    department_id = EXCLUDED.department_id,
                    authority_level = EXCLUDED.authority_level,
                    metadata = EXCLUDED.metadata,
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
                        register_query,
                    ],
                    capture_output=True,
                    text=True,
                )

                if reg_result.returncode == 0:
                    success_count += 1
                    primary_tag = " (Primary)" if leader["is_primary"] else ""
                    print(f"   ✅ {leader['name']} - {leader['title']}{primary_tag}")
                else:
                    print(
                        f"   ❌ Failed to register {leader['name']}: {reg_result.stderr[:50]}"
                    )

        print(
            f"\n✅ Successfully registered {success_count}/{len(leaders)} leaders as agents"
        )

    # Show summary
    print("\n📊 Leader Registration Summary...")

    summary_query = """
    SELECT
        'Total Leaders' as metric,
        COUNT(*) as value
    FROM agent_registry
    WHERE metadata->>'is_leader' = 'true'
    UNION ALL
    SELECT
        'Primary Leaders' as metric,
        COUNT(*) as value
    FROM agent_registry
    WHERE metadata->>'is_leader' = 'true'
        AND metadata->>'is_primary' = 'true'
    UNION ALL
    SELECT
        'Leaders by Authority' || ' (Level ' || authority_level || ')' as metric,
        COUNT(*) as value
    FROM agent_registry
    WHERE metadata->>'is_leader' = 'true'
    GROUP BY authority_level
    ORDER BY metric;
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
            summary_query,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("\nLeader Metrics:")
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    metric = parts[0].strip()
                    value = parts[1].strip()
                    print(f"   {metric}: {value}")

    # Final registry status
    print("\n📊 Final Registry Status...")

    final_query = """
    SELECT
        'Total Agents' as type, COUNT(*) FROM agent_registry
    UNION ALL
    SELECT
        'Leaders' as type, COUNT(*)
        FROM agent_registry
        WHERE metadata->>'is_leader' = 'true'
    UNION ALL
    SELECT
        'Executives' as type, COUNT(*)
        FROM agent_registry
        WHERE metadata->>'executive' = 'true'
    UNION ALL
    SELECT
        'Departments' as type, COUNT(*) FROM department_registry
    UNION ALL
    SELECT
        'Servers' as type, COUNT(*) FROM server_registry
    UNION ALL
    SELECT
        'Databases' as type, COUNT(*) FROM database_registry;
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
            final_query,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("\nComplete Registry:")
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    type_name = parts[0].strip()
                    count = parts[1].strip()
                    print(f"   {type_name}: {count}")

    print("\n✅ Leader Registration Complete!")
    print("\n🌐 View the complete registry at:")
    print("   http://localhost:8888 -> Registry tab")


if __name__ == "__main__":
    register_leaders()
