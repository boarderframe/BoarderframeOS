#!/usr/bin/env python3
"""
Patch Corporate HQ to fix registry display
"""

import os


def patch_corporate_hq():
    """Apply patches to corporate_headquarters.py"""
    print("🔧 Patching Corporate HQ Registry Display")
    print("=" * 50)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()

    # Backup original
    backup_path = file_path + '.backup'
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"✅ Created backup at {backup_path}")

    # Fix 1: Update the agent count query to include all types
    old_agent_query = "FROM agent_registry WHERE agent_type = 'agent'"
    new_agent_query = "FROM agent_registry"

    # Fix 2: Update leaders query to use metadata field
    old_leader_query = "FROM agent_registry WHERE agent_type = 'leader'"
    new_leader_query = "FROM agent_registry WHERE metadata->>'is_leader' = 'true'"

    # Apply fixes
    content = content.replace(old_agent_query, new_agent_query)
    content = content.replace(old_leader_query, new_leader_query)

    # Fix 3: Update the department query to handle UUID conversion
    old_dept_join = "LEFT JOIN agent_registry ar ON ar.department_id = d.id::text"
    new_dept_join = "LEFT JOIN agent_registry ar ON ar.department_id::uuid = d.id"

    content = content.replace(old_dept_join, new_dept_join)

    # Write updated content
    with open(file_path, 'w') as f:
        f.write(content)

    print("\n✅ Applied patches:")
    print("   1. Fixed agent count to include all types (not just 'agent')")
    print("   2. Fixed leader count to use metadata field")
    print("   3. Fixed department join to handle UUID conversion")

    # Now let's also add a new section after the existing registry stats
    # to show workforce development stats

    workforce_section = '''
                # Add workforce development stats
                workforce_query = """
                SELECT
                    COUNT(*) FILTER (WHERE agent_type = 'workforce') as workforce_total,
                    COUNT(*) FILTER (WHERE agent_type = 'workforce' AND operational_status = 'operational') as operational,
                    COUNT(*) FILTER (WHERE agent_type = 'workforce' AND development_status IN ('training', 'testing')) as training,
                    COUNT(*) FILTER (WHERE agent_type = 'workforce' AND development_status = 'planned') as planned,
                    COUNT(*) FILTER (WHERE agent_type = 'executive') as executives,
                    ROUND(AVG(CASE WHEN agent_type = 'workforce' THEN skill_level END)) as avg_skill,
                    ROUND(AVG(CASE WHEN agent_type = 'workforce' THEN training_progress END) * 100) as avg_progress
                FROM agent_registry;
                """

                workforce_result = subprocess.run([
                    "docker", "exec", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", workforce_query
                ], capture_output=True, text=True, timeout=5)

                if workforce_result.returncode == 0:
                    parts = workforce_result.stdout.strip().split('|')
                    if len(parts) >= 7:
                        registry_data['workforce_stats'] = {
                            'total': int(parts[0].strip() or 0),
                            'operational': int(parts[1].strip() or 0),
                            'training': int(parts[2].strip() or 0),
                            'planned': int(parts[3].strip() or 0),
                            'executives': int(parts[4].strip() or 0),
                            'avg_skill': parts[5].strip() or '0',
                            'avg_progress': parts[6].strip() or '0'
                        }
'''

    # Find where to insert the workforce section
    insert_marker = "# Get agents by department"
    if insert_marker in content:
        parts = content.split(insert_marker)
        content = parts[0] + workforce_section + "\n                " + insert_marker + parts[1]

        with open(file_path, 'w') as f:
            f.write(content)

        print("   4. Added workforce development statistics section")

    print("\n🎯 Next steps:")
    print("1. Restart Corporate HQ to apply changes")
    print("2. Visit http://localhost:8888 -> Registry tab")
    print("3. You should now see:")
    print("   - Total Agents: 195 (not 40)")
    print("   - Leaders: 33")
    print("   - Workforce breakdown with operational/training stats")

    # Test the query to verify it works
    print("\n🔍 Testing updated queries...")
    import subprocess

    test_query = """
    SELECT
        'Total Agents' as metric, COUNT(*) as value FROM agent_registry
    UNION ALL
    SELECT 'Leaders', COUNT(*) FROM agent_registry WHERE metadata->>'is_leader' = 'true'
    UNION ALL
    SELECT 'Workforce', COUNT(*) FROM agent_registry WHERE agent_type = 'workforce'
    UNION ALL
    SELECT 'Executives', COUNT(*) FROM agent_registry WHERE agent_type = 'executive'
    UNION ALL
    SELECT 'Operational', COUNT(*) FROM agent_registry WHERE operational_status = 'operational';
    """

    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", test_query
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("\nQuery Test Results:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    print(f"   {parts[0].strip()}: {parts[1].strip()}")

    print("\n✅ Patching complete!")


if __name__ == "__main__":
    patch_corporate_hq()
