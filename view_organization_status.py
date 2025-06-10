#!/usr/bin/env python3
"""
View complete organizational structure and workforce status
"""

import subprocess
import json

def view_organization():
    """Display comprehensive organizational status"""
    print("🏢 BoarderframeOS Organizational Status Report")
    print("=" * 70)
    print(f"Generated: {subprocess.check_output(['date']).decode().strip()}")
    print("=" * 70)
    
    # Executive Summary
    print("\n📊 EXECUTIVE SUMMARY")
    print("-" * 70)
    
    summary_query = """
    SELECT 
        'Total Divisions' as metric, COUNT(DISTINCT d.id) as value 
    FROM divisions d
    UNION ALL
    SELECT 
        'Total Departments', COUNT(DISTINCT dept.id) 
    FROM departments dept
    UNION ALL
    SELECT 
        'Total Agents', COUNT(DISTINCT a.id) 
    FROM agents a
    UNION ALL
    SELECT 
        'Operational Agents', COUNT(DISTINCT a.id) 
    FROM agents a 
    WHERE a.operational_status = 'operational'
    UNION ALL
    SELECT 
        'Agents in Training', COUNT(DISTINCT a.id) 
    FROM agents a 
    WHERE a.development_status IN ('training', 'testing')
    UNION ALL
    SELECT 
        'Leaders', COUNT(DISTINCT a.id) 
    FROM agents a 
    WHERE a.agent_type = 'leader'
    UNION ALL
    SELECT 
        'Executive Agents', COUNT(DISTINCT a.id) 
    FROM agents a 
    WHERE a.agent_type = 'executive'
    UNION ALL
    SELECT 
        'Total Capacity', SUM(dept.agent_capacity) 
    FROM departments dept
    UNION ALL
    SELECT 
        'Capacity Utilization %', 
        ROUND((COUNT(DISTINCT a.id)::numeric / NULLIF(SUM(DISTINCT dept.agent_capacity), 0)) * 100)
    FROM agents a
    JOIN departments dept ON a.department = dept.name;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", summary_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    metric = parts[0].strip()
                    value = parts[1].strip() or "0"
                    print(f"   {metric:<30} {value:>10}")
    
    # Division Breakdown
    print("\n\n🏛️ DIVISION BREAKDOWN")
    print("-" * 70)
    
    division_query = """
    SELECT 
        d.division_name,
        COUNT(DISTINCT dept.id) as departments,
        COUNT(DISTINCT dl.id) as leaders,
        COUNT(DISTINCT a.id) as agents,
        COUNT(DISTINCT CASE WHEN a.operational_status = 'operational' THEN a.id END) as operational,
        SUM(DISTINCT dept.agent_capacity) as capacity
    FROM divisions d
    LEFT JOIN departments dept ON dept.division_id = d.id
    LEFT JOIN department_leaders dl ON dl.department_id = dept.id
    LEFT JOIN agents a ON a.department = dept.name
    GROUP BY d.id, d.division_name, d.priority
    ORDER BY d.priority;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", division_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{'Division':<35} {'Depts':>6} {'Leaders':>8} {'Agents':>8} {'Active':>8} {'Capacity':>10}")
        print("-" * 85)
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 6:
                    print(f"{parts[0]:<35} {parts[1]:>6} {parts[2]:>8} {parts[3]:>8} {parts[4]:>8} {parts[5]:>10}")
    
    # Department Status by Phase
    print("\n\n📈 DEPARTMENT STATUS BY PHASE")
    print("-" * 70)
    
    phase_query = """
    SELECT 
        d.phase,
        COUNT(DISTINCT d.id) as departments,
        COUNT(DISTINCT a.id) as agents,
        COUNT(DISTINCT CASE WHEN a.operational_status = 'operational' THEN a.id END) as operational,
        COUNT(DISTINCT CASE WHEN a.development_status IN ('training', 'testing') THEN a.id END) as training,
        COUNT(DISTINCT CASE WHEN a.development_status = 'planned' THEN a.id END) as planned
    FROM departments d
    LEFT JOIN agents a ON a.department = d.name
    GROUP BY d.phase
    ORDER BY d.phase;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", phase_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{'Phase':>7} {'Departments':>12} {'Total Agents':>13} {'Operational':>12} {'Training':>10} {'Planned':>9}")
        print("-" * 70)
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 6:
                    print(f"{parts[0]:>7} {parts[1]:>12} {parts[2]:>13} {parts[3]:>12} {parts[4]:>10} {parts[5]:>9}")
    
    # Top Departments by Agent Count
    print("\n\n🏆 TOP DEPARTMENTS BY WORKFORCE")
    print("-" * 70)
    
    top_dept_query = """
    SELECT 
        d.name,
        COUNT(DISTINCT a.id) as total_agents,
        COUNT(DISTINCT CASE WHEN a.agent_type = 'leader' THEN a.id END) as leaders,
        COUNT(DISTINCT CASE WHEN a.agent_type = 'workforce' THEN a.id END) as workforce,
        COUNT(DISTINCT CASE WHEN a.operational_status = 'operational' THEN a.id END) as operational,
        d.agent_capacity as capacity,
        ROUND((COUNT(DISTINCT a.id)::numeric / NULLIF(d.agent_capacity, 0)) * 100) as utilization_pct
    FROM departments d
    LEFT JOIN agents a ON a.department = d.name
    GROUP BY d.id, d.name, d.agent_capacity
    HAVING COUNT(DISTINCT a.id) > 0
    ORDER BY total_agents DESC
    LIMIT 15;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", top_dept_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{'Department':<35} {'Total':>6} {'Leaders':>8} {'Workers':>8} {'Active':>7} {'Cap':>5} {'Util%':>6}")
        print("-" * 85)
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 7:
                    dept_name = parts[0][:34]  # Truncate long names
                    print(f"{dept_name:<35} {parts[1]:>6} {parts[2]:>8} {parts[3]:>8} {parts[4]:>7} {parts[5]:>5} {parts[6]:>6}%")
    
    # Agent Development Pipeline
    print("\n\n🔄 AGENT DEVELOPMENT PIPELINE")
    print("-" * 70)
    
    pipeline_query = """
    SELECT 
        a.development_status,
        a.operational_status,
        COUNT(*) as count,
        STRING_AGG(DISTINCT a.agent_type, ', ') as types
    FROM agents a
    GROUP BY a.development_status, a.operational_status
    ORDER BY 
        CASE a.development_status
            WHEN 'deployed' THEN 1
            WHEN 'ready' THEN 2
            WHEN 'testing' THEN 3
            WHEN 'training' THEN 4
            WHEN 'in_development' THEN 5
            WHEN 'planned' THEN 6
        END;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", pipeline_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{'Development Status':<20} {'Operational Status':<20} {'Count':>8} {'Agent Types':<30}")
        print("-" * 80)
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    print(f"{parts[0]:<20} {parts[1]:<20} {parts[2]:>8} {parts[3]:<30}")
    
    # Registry Synchronization Status
    print("\n\n🔄 REGISTRY SYNCHRONIZATION STATUS")
    print("-" * 70)
    
    sync_query = """
    SELECT 
        'Agents in Main Table' as location, COUNT(*) as count
    FROM agents
    UNION ALL
    SELECT 
        'Agents in Registry', COUNT(*)
    FROM agent_registry
    UNION ALL
    SELECT 
        'Departments in Main Table', COUNT(*)
    FROM departments
    UNION ALL
    SELECT 
        'Departments in Registry', COUNT(*)
    FROM department_registry
    UNION ALL
    SELECT 
        'Agents Missing from Registry', COUNT(*)
    FROM agents a
    WHERE NOT EXISTS (SELECT 1 FROM agent_registry ar WHERE ar.agent_id = a.id)
    UNION ALL
    SELECT 
        'Departments Missing from Registry', COUNT(*)
    FROM departments d
    WHERE NOT EXISTS (SELECT 1 FROM department_registry dr WHERE dr.department_id = d.id);
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", sync_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    location = parts[0].strip()
                    count = parts[1].strip()
                    status = "⚠️ " if "Missing" in location and int(count) > 0 else "✅ "
                    print(f"   {status}{location:<40} {count:>10}")
    
    print("\n" + "=" * 70)
    print("📍 View live dashboard at: http://localhost:8888")
    print("💡 Use register_organizational_data_v2.py to sync any missing registries")
    print("=" * 70)


if __name__ == "__main__":
    view_organization()