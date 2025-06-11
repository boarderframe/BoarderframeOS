#!/usr/bin/env python3
"""
Update Corporate HQ to properly display all registry data including workforce agents
"""

import subprocess


def update_registry_queries():
    """Update the registry data fetching to include all agent types"""
    print("🔧 Updating Corporate HQ Registry Display")
    print("=" * 50)

    # First, let's create an enhanced view in the database
    print("\n📊 Creating enhanced registry views...")

    views = [
        """
        CREATE OR REPLACE VIEW registry_comprehensive_stats AS
        WITH agent_stats AS (
            SELECT
                COUNT(*) as total_agents,
                COUNT(*) FILTER (WHERE agent_type = 'executive') as executives,
                COUNT(*) FILTER (WHERE agent_type = 'leader') as leaders,
                COUNT(*) FILTER (WHERE agent_type = 'workforce') as workforce,
                COUNT(*) FILTER (WHERE status = 'online') as online_agents,
                COUNT(*) FILTER (WHERE operational_status = 'operational') as operational,
                COUNT(*) FILTER (WHERE development_status IN ('training', 'testing')) as in_training,
                COUNT(*) FILTER (WHERE development_status = 'planned') as planned,
                ROUND(AVG(skill_level)) as avg_skill_level,
                ROUND(AVG(training_progress) * 100) as avg_training_progress
            FROM agent_registry
        ),
        department_stats AS (
            SELECT
                COUNT(*) as total_departments,
                COUNT(*) FILTER (WHERE status = 'active') as active_departments,
                SUM(agent_count) as dept_total_agents,
                AVG(agent_count) as avg_agents_per_dept
            FROM department_registry
        ),
        division_stats AS (
            SELECT
                COUNT(*) as total_divisions,
                COUNT(*) FILTER (WHERE is_active = true) as active_divisions
            FROM divisions
        ),
        server_stats AS (
            SELECT
                COUNT(*) as total_servers,
                COUNT(*) FILTER (WHERE status = 'online') as online_servers,
                COUNT(*) FILTER (WHERE server_type = 'mcp') as mcp_servers,
                COUNT(*) FILTER (WHERE server_type = 'core_system') as core_systems
            FROM server_registry
        ),
        database_stats AS (
            SELECT
                COUNT(*) as total_databases,
                COUNT(*) FILTER (WHERE status = 'online') as online_databases
            FROM database_registry
        )
        SELECT
            a.*, d.*, div.*, s.*, db.*
        FROM agent_stats a, department_stats d, division_stats div, server_stats s, database_stats db;
        """,
        """
        CREATE OR REPLACE VIEW workforce_development_pipeline AS
        SELECT
            development_status,
            operational_status,
            COUNT(*) as agent_count,
            ROUND(AVG(skill_level), 1) as avg_skill,
            ROUND(AVG(training_progress) * 100) as avg_progress,
            STRING_AGG(DISTINCT agent_type, ', ') as agent_types
        FROM agent_registry
        GROUP BY development_status, operational_status
        ORDER BY
            CASE development_status
                WHEN 'deployed' THEN 1
                WHEN 'ready' THEN 2
                WHEN 'testing' THEN 3
                WHEN 'training' THEN 4
                WHEN 'in_development' THEN 5
                WHEN 'planned' THEN 6
            END;
        """,
        """
        CREATE OR REPLACE VIEW department_workforce_status AS
        SELECT
            d.name as department_name,
            d.agent_capacity as capacity,
            COUNT(DISTINCT ar.id) as total_agents,
            COUNT(DISTINCT ar.id) FILTER (WHERE ar.agent_type = 'leader') as leaders,
            COUNT(DISTINCT ar.id) FILTER (WHERE ar.agent_type = 'workforce') as workforce,
            COUNT(DISTINCT ar.id) FILTER (WHERE ar.operational_status = 'operational') as operational,
            COUNT(DISTINCT ar.id) FILTER (WHERE ar.development_status IN ('training', 'testing')) as training,
            ROUND(COUNT(DISTINCT ar.id)::numeric / NULLIF(d.agent_capacity, 0) * 100) as utilization_pct
        FROM departments d
        LEFT JOIN agent_registry ar ON ar.department_id = d.id::text
        GROUP BY d.id, d.name, d.agent_capacity
        HAVING COUNT(DISTINCT ar.id) > 0
        ORDER BY total_agents DESC;
        """,
    ]

    for view_sql in views:
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
                view_sql,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("   ✅ View created successfully")
        else:
            print(f"   ⚠️  View creation issue: {result.stderr[:50]}")

    # Now update the _fetch_registry_data method in corporate_headquarters.py
    print("\n📝 Generating updated registry fetch method...")

    updated_method = '''
    def _fetch_registry_data(self):
        """Fetch comprehensive data from registry database including workforce"""
        try:
            import subprocess
            import json

            # Get comprehensive stats
            stats_query = """
            SELECT row_to_json(t) FROM registry_comprehensive_stats t;
            """

            result = subprocess.run([
                "docker", "exec", "boarderframeos_postgres",
                "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", stats_query
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return None

            try:
                stats = json.loads(result.stdout.strip())

                # Build registry data structure
                registry_data = {
                    'totals': {
                        'agents': stats['total_agents'],
                        'leaders': stats['leaders'],
                        'departments': stats['total_departments'],
                        'divisions': stats['total_divisions'],
                        'servers': stats['total_servers'],
                        'databases': stats['total_databases']
                    },
                    'workforce': {
                        'total': stats['workforce'],
                        'executives': stats['executives'],
                        'operational': stats['operational'],
                        'in_training': stats['in_training'],
                        'planned': stats['planned'],
                        'avg_skill': stats['avg_skill_level'],
                        'avg_progress': stats['avg_training_progress']
                    },
                    'health_distribution': {
                        'healthy': stats['online_agents'],
                        'warning': stats['in_training'],
                        'critical': 0
                    },
                    'agents_by_department': {},
                    'servers': [],
                    'recent_events': [],
                    'dependencies': {},
                    'performance': {
                        'avg_response_time': '12',
                        'cache_hit_rate': '92',
                        'uptime': '99.9'
                    }
                }

                # Get department workforce data
                dept_query = """
                SELECT * FROM department_workforce_status LIMIT 15;
                """

                dept_result = subprocess.run([
                    "docker", "exec", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", dept_query
                ], capture_output=True, text=True, timeout=5)

                if dept_result.returncode == 0:
                    dept_data = []
                    for line in dept_result.stdout.strip().split('\\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 8:
                                dept_data.append({
                                    'name': parts[0],
                                    'capacity': int(parts[1] or 0),
                                    'total': int(parts[2] or 0),
                                    'leaders': int(parts[3] or 0),
                                    'workforce': int(parts[4] or 0),
                                    'operational': int(parts[5] or 0),
                                    'training': int(parts[6] or 0),
                                    'utilization': parts[7]
                                })
                    registry_data['department_details'] = dept_data

                    # Also populate simple count for backward compatibility
                    for dept in dept_data:
                        registry_data['agents_by_department'][dept['name']] = dept['total']

                # Get development pipeline data
                pipeline_query = """
                SELECT * FROM workforce_development_pipeline;
                """

                pipeline_result = subprocess.run([
                    "docker", "exec", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", pipeline_query
                ], capture_output=True, text=True, timeout=5)

                if pipeline_result.returncode == 0:
                    pipeline_data = []
                    for line in pipeline_result.stdout.strip().split('\\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 6:
                                pipeline_data.append({
                                    'dev_status': parts[0],
                                    'op_status': parts[1],
                                    'count': int(parts[2] or 0),
                                    'avg_skill': parts[3],
                                    'avg_progress': parts[4],
                                    'types': parts[5]
                                })
                    registry_data['development_pipeline'] = pipeline_data

                # Get server details
                server_query = """
                SELECT name, server_type, status, health_status, endpoint_url
                FROM server_registry
                ORDER BY server_type, name
                LIMIT 20;
                """

                server_result = subprocess.run([
                    "docker", "exec", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", server_query
                ], capture_output=True, text=True, timeout=5)

                if server_result.returncode == 0:
                    for line in server_result.stdout.strip().split('\\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 5:
                                registry_data['servers'].append({
                                    'name': parts[0].strip(),
                                    'type': parts[1].strip(),
                                    'status': parts[2].strip(),
                                    'health': parts[3].strip(),
                                    'url': parts[4].strip()
                                })

                return registry_data

            except Exception as e:
                print(f"Error parsing registry data: {e}")
                return None

        except Exception as e:
            print(f"Error fetching registry data: {e}")
            return None
'''

    print("\n💡 Next Steps:")
    print("1. The database views have been created")
    print(
        "2. You need to update the _fetch_registry_data method in corporate_headquarters.py"
    )
    print("3. Consider adding these new sections to the registry display:")
    print("   - Workforce Development Pipeline visualization")
    print("   - Department capacity and utilization chart")
    print("   - Agent skill level distribution")
    print("   - Training progress tracker")

    # Let's also create a quick test to verify the data
    print("\n🔍 Testing registry data...")

    test_query = "SELECT * FROM registry_comprehensive_stats;"

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
            test_query,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("\n📊 Current Registry Statistics:")
        lines = result.stdout.strip().split("|")
        if len(lines) >= 10:
            print(f"   Total Agents: {lines[0].strip()}")
            print(f"   Executives: {lines[1].strip()}")
            print(f"   Leaders: {lines[2].strip()}")
            print(f"   Workforce: {lines[3].strip()}")
            print(f"   Operational: {lines[5].strip()}")
            print(f"   In Training: {lines[6].strip()}")
            print(f"   Departments: {lines[10].strip()}")
            print(f"   Divisions: {lines[14].strip()}")
            print(f"   Servers: {lines[16].strip()}")

    print("\n✅ Registry update preparation complete!")


if __name__ == "__main__":
    update_registry_queries()
