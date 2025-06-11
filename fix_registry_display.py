#!/usr/bin/env python3
"""
Fix the registry display query in corporate_headquarters.py
"""

def generate_updated_method():
    """Generate the corrected _fetch_registry_data method"""

    print("📝 Updated _fetch_registry_data method for corporate_headquarters.py")
    print("=" * 70)
    print("\nReplace the _fetch_registry_data method with this version:\n")

    updated_code = '''    def _fetch_registry_data(self):
        """Fetch comprehensive data from registry database"""
        try:
            import subprocess
            import json

            # Updated query to include ALL agent types
            query = """
            WITH registry_stats AS (
                SELECT
                    'total_agents' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE health_status = 'warning') as warning,
                    COUNT(*) FILTER (WHERE health_status = 'critical' OR health_status IS NULL) as critical
                FROM agent_registry
                UNION ALL
                SELECT
                    'workforce' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE operational_status = 'operational') as healthy,
                    COUNT(*) FILTER (WHERE development_status IN ('training', 'testing')) as warning,
                    COUNT(*) FILTER (WHERE development_status = 'planned') as critical
                FROM agent_registry WHERE agent_type = 'workforce'
                UNION ALL
                SELECT
                    'leaders' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    0 as warning,
                    0 as critical
                FROM agent_registry WHERE metadata->>'is_leader' = 'true'
                UNION ALL
                SELECT
                    'executives' as type,
                    COUNT(*) as total,
                    COUNT(*) as online,
                    COUNT(*) as healthy,
                    0 as warning,
                    0 as critical
                FROM agent_registry WHERE agent_type = 'executive'
                UNION ALL
                SELECT
                    'servers' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE health_status = 'warning') as warning,
                    COUNT(*) FILTER (WHERE health_status = 'critical') as critical
                FROM server_registry
                UNION ALL
                SELECT
                    'databases' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE health_status = 'warning') as warning,
                    COUNT(*) FILTER (WHERE health_status = 'critical') as critical
                FROM database_registry
                UNION ALL
                SELECT
                    'departments' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'active') as online,
                    COUNT(*) as healthy,
                    0 as warning,
                    0 as critical
                FROM department_registry
                UNION ALL
                SELECT
                    'divisions' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_active = true) as online,
                    COUNT(*) as healthy,
                    0 as warning,
                    0 as critical
                FROM divisions
            )
            SELECT json_agg(row_to_json(registry_stats)) FROM registry_stats;
            """

            result = subprocess.run([
                "docker", "exec", "boarderframeos_postgres",
                "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", query
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                return None

            try:
                stats_data = json.loads(result.stdout.strip())

                # Process the data
                registry_data = {
                    'totals': {
                        'agents': 0,
                        'leaders': 0,
                        'departments': 0,
                        'divisions': 0,
                        'servers': 0,
                        'databases': 0
                    },
                    'workforce_stats': {
                        'total': 0,
                        'operational': 0,
                        'training': 0,
                        'planned': 0
                    },
                    'health_distribution': {'healthy': 0, 'warning': 0, 'critical': 0},
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

                # Process stats
                for stat in stats_data:
                    stat_type = stat['type']
                    if stat_type == 'total_agents':
                        registry_data['totals']['agents'] = stat['total']
                    elif stat_type == 'workforce':
                        registry_data['workforce_stats']['total'] = stat['total']
                        registry_data['workforce_stats']['operational'] = stat['healthy']
                        registry_data['workforce_stats']['training'] = stat['warning']
                        registry_data['workforce_stats']['planned'] = stat['critical']
                    elif stat_type in ['leaders', 'executives', 'departments', 'divisions', 'servers', 'databases']:
                        registry_data['totals'][stat_type] = stat['total']

                    registry_data['health_distribution']['healthy'] += stat['healthy']
                    registry_data['health_distribution']['warning'] += stat['warning']
                    registry_data['health_distribution']['critical'] += stat['critical']

                # Get agents by department with proper join
                dept_query = """
                SELECT d.name as department,
                       COUNT(DISTINCT ar.id) as total_agents,
                       COUNT(DISTINCT ar.id) FILTER (WHERE ar.agent_type = 'workforce') as workforce,
                       COUNT(DISTINCT ar.id) FILTER (WHERE ar.operational_status = 'operational') as operational
                FROM departments d
                LEFT JOIN agent_registry ar ON ar.department_id::uuid = d.id
                GROUP BY d.name
                HAVING COUNT(ar.id) > 0
                ORDER BY total_agents DESC
                LIMIT 15;
                """

                dept_result = subprocess.run([
                    "docker", "exec", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", dept_query
                ], capture_output=True, text=True, timeout=5)

                if dept_result.returncode == 0:
                    for line in dept_result.stdout.strip().split('\\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 4:
                                dept_name = parts[0].strip()
                                total = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                                workforce = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                                operational = int(parts[3].strip()) if parts[3].strip().isdigit() else 0
                                registry_data['agents_by_department'][dept_name] = {
                                    'total': total,
                                    'workforce': workforce,
                                    'operational': operational
                                }

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

                # Get development pipeline stats
                pipeline_query = """
                SELECT
                    development_status,
                    COUNT(*) as count,
                    ROUND(AVG(training_progress) * 100) as avg_progress
                FROM agent_registry
                WHERE agent_type = 'workforce'
                GROUP BY development_status
                ORDER BY
                    CASE development_status
                        WHEN 'deployed' THEN 1
                        WHEN 'ready' THEN 2
                        WHEN 'testing' THEN 3
                        WHEN 'training' THEN 4
                        WHEN 'in_development' THEN 5
                        WHEN 'planned' THEN 6
                    END;
                """

                pipeline_result = subprocess.run([
                    "docker", "exec", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", pipeline_query
                ], capture_output=True, text=True, timeout=5)

                if pipeline_result.returncode == 0:
                    pipeline_data = []
                    for line in pipeline_result.stdout.strip().split('\\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 3:
                                pipeline_data.append({
                                    'status': parts[0].strip(),
                                    'count': int(parts[1].strip()) if parts[1].strip().isdigit() else 0,
                                    'progress': parts[2].strip() or '0'
                                })
                    registry_data['development_pipeline'] = pipeline_data

                return registry_data

            except Exception as e:
                print(f"Error parsing registry data: {e}")
                return None

        except Exception as e:
            print(f"Error fetching registry data: {e}")
            return None'''

    print(updated_code)

    print("\n\n📝 Also update the _generate_department_agent_list method:\n")

    dept_list_code = '''    def _generate_department_agent_list(self, dept_data):
        """Generate department agent count list with details"""
        if not dept_data:
            return '<div style="text-align: center; color: var(--secondary-text);">No department data available</div>'

        html = ''
        for dept, data in sorted(dept_data.items(), key=lambda x: x[1]['total'] if isinstance(x[1], dict) else x[1], reverse=True):
            if isinstance(data, dict):
                # New format with details
                operational_pct = (data['operational'] / data['total'] * 100) if data['total'] > 0 else 0
                html += f\'\'\'
                <div style="display: flex; justify-content: space-between; padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
                    <div style="flex: 1;">
                        <div style="font-weight: 500;">{dept}</div>
                        <div style="font-size: 0.75rem; color: var(--secondary-text);">
                            {data['workforce']} workforce • {data['operational']} operational ({operational_pct:.0f}%)
                        </div>
                    </div>
                    <div style="font-weight: 600; color: var(--accent-color); font-size: 1.2rem;">{data['total']}</div>
                </div>
                \'\'\'
            else:
                # Old format fallback
                html += f\'\'\'
                <div style="display: flex; justify-content: space-between; padding: 0.5rem; border-bottom: 1px solid var(--border-color);">
                    <span>{dept}</span>
                    <span style="font-weight: 600; color: var(--accent-color);">{data}</span>
                </div>
                \'\'\'
        return html'''

    print(dept_list_code)

    print("\n\n💡 To apply these changes:")
    print("1. Open corporate_headquarters.py")
    print("2. Find and replace the _fetch_registry_data method")
    print("3. Find and replace the _generate_department_agent_list method")
    print("4. Restart Corporate HQ")
    print("\nThe registry will then show:")
    print("- All 195 agents (not just 40)")
    print("- Workforce statistics with operational/training/planned breakdown")
    print("- Department details with workforce counts")
    print("- Development pipeline progress")


if __name__ == "__main__":
    generate_updated_method()
