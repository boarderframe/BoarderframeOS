#!/usr/bin/env python3
"""
Establish workforce agents for all departments with proper status tracking
"""

import subprocess
import json
import uuid
from datetime import datetime

def establish_workforce():
    """Create and register workforce agents for all departments"""
    print("🏭 BoarderframeOS Workforce Establishment")
    print("=" * 50)
    
    # First, let's add a development_status column to agents table if it doesn't exist
    print("\n📊 Updating database schema for workforce tracking...")
    
    schema_updates = [
        """
        ALTER TABLE agents 
        ADD COLUMN IF NOT EXISTS development_status VARCHAR(50) DEFAULT 'planned',
        ADD COLUMN IF NOT EXISTS operational_status VARCHAR(50) DEFAULT 'not_started',
        ADD COLUMN IF NOT EXISTS skill_level INTEGER DEFAULT 1,
        ADD COLUMN IF NOT EXISTS training_progress REAL DEFAULT 0.0,
        ADD COLUMN IF NOT EXISTS deployment_date TIMESTAMP,
        ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        """,
        """
        ALTER TABLE agents
        ADD CONSTRAINT IF NOT EXISTS agents_development_status_check 
        CHECK (development_status IN ('planned', 'in_development', 'training', 'testing', 'ready', 'deployed', 'retired'));
        """,
        """
        ALTER TABLE agents
        ADD CONSTRAINT IF NOT EXISTS agents_operational_status_check 
        CHECK (operational_status IN ('not_started', 'initializing', 'learning', 'operational', 'maintenance', 'offline', 'deprecated'));
        """,
        """
        ALTER TABLE agent_registry
        ADD COLUMN IF NOT EXISTS development_status VARCHAR(50) DEFAULT 'planned',
        ADD COLUMN IF NOT EXISTS operational_status VARCHAR(50) DEFAULT 'not_started',
        ADD COLUMN IF NOT EXISTS skill_level INTEGER DEFAULT 1,
        ADD COLUMN IF NOT EXISTS training_progress REAL DEFAULT 0.0;
        """
    ]
    
    for query in schema_updates:
        result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", query
        ], capture_output=True, text=True)
        
        if result.returncode == 0 or "already exists" in result.stderr:
            print("   ✅ Schema update applied")
        else:
            print(f"   ⚠️  Schema update issue: {result.stderr[:50]}")
    
    # Get all departments with their capacity and current agent count
    print("\n📊 Analyzing department workforce needs...")
    
    dept_query = """
    SELECT 
        d.id,
        d.name,
        d.agent_capacity,
        d.operational_status,
        dl.name as leader_name,
        dl.id as leader_id,
        COUNT(DISTINCT a.id) as current_agents
    FROM departments d
    LEFT JOIN department_leaders dl ON d.id = dl.department_id AND dl.is_primary = true
    LEFT JOIN agents a ON a.department = d.name AND a.agent_type != 'leader'
    GROUP BY d.id, d.name, d.agent_capacity, d.operational_status, dl.name, dl.id
    ORDER BY d.priority, d.name;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", dept_query
    ], capture_output=True, text=True)
    
    departments = []
    if result.returncode == 0 and result.stdout:
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 7:
                    departments.append({
                        "id": parts[0],
                        "name": parts[1],
                        "capacity": int(parts[2] or 10),
                        "operational_status": parts[3],
                        "leader_name": parts[4],
                        "leader_id": parts[5],
                        "current_agents": int(parts[6])
                    })
    
    print(f"\nFound {len(departments)} departments to staff")
    
    # Define agent roles and their development phases
    agent_roles = {
        "operational": [
            ("Senior Agent", "ready", "operational", 5, 1.0),
            ("Agent", "deployed", "operational", 3, 0.9),
            ("Junior Agent", "testing", "learning", 2, 0.7)
        ],
        "planned": [
            ("Agent Trainee", "training", "initializing", 1, 0.5),
            ("Agent Candidate", "in_development", "not_started", 1, 0.3),
            ("Future Agent", "planned", "not_started", 1, 0.0)
        ]
    }
    
    total_created = 0
    
    # Create workforce agents for each department
    print("\n🤖 Creating workforce agents...")
    
    for dept in departments:
        # Determine how many agents to create based on operational status
        if dept["operational_status"] in ["active", "operational"]:
            # For operational departments, create 3-5 agents in various stages
            agents_to_create = min(5, dept["capacity"] - dept["current_agents"])
            role_pool = agent_roles["operational"]
        else:
            # For planning/development departments, create 1-3 planned agents
            agents_to_create = min(3, dept["capacity"] - dept["current_agents"])
            role_pool = agent_roles["planned"]
        
        if agents_to_create <= 0:
            continue
            
        print(f"\n📁 {dept['name']} (Capacity: {dept['capacity']}, Current: {dept['current_agents']})")
        
        for i in range(agents_to_create):
            role_info = role_pool[i % len(role_pool)]
            role_name, dev_status, op_status, skill_level, training = role_info
            
            # Generate agent name based on department and role
            agent_number = dept["current_agents"] + i + 1
            agent_name = f"{dept['name'].split()[0]}-{role_name.replace(' ', '')}-{agent_number}"
            agent_id = str(uuid.uuid4())
            
            # Create agent in agents table
            create_agent_query = f"""
            INSERT INTO agents (
                id, name, department, agent_type, status,
                development_status, operational_status, skill_level,
                training_progress, capabilities, generation
            ) VALUES (
                '{agent_id}'::uuid,
                '{agent_name}',
                '{dept["name"].replace("'", "''")}',
                'workforce',
                'active',
                '{dev_status}',
                '{op_status}',
                {skill_level},
                {training},
                '{json.dumps([
                    "task_execution",
                    "collaboration",
                    "reporting",
                    dept["name"].lower().replace(" ", "_")
                ])}'::jsonb,
                1
            );
            """
            
            result = subprocess.run([
                "docker", "exec", "boarderframeos_postgres",
                "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", create_agent_query
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Register in agent_registry
                registry_status = "online" if op_status == "operational" else "offline"
                
                register_query = f"""
                INSERT INTO agent_registry (
                    agent_id, name, department_id, agent_type, status,
                    development_status, operational_status, skill_level,
                    training_progress, capabilities, health_status,
                    authority_level, max_concurrent_tasks, metadata
                ) VALUES (
                    '{agent_id}'::uuid,
                    '{agent_name}',
                    '{dept["id"]}'::uuid,
                    'workforce',
                    '{registry_status}',
                    '{dev_status}',
                    '{op_status}',
                    {skill_level},
                    {training},
                    '{json.dumps([
                        "task_execution",
                        "collaboration", 
                        "reporting"
                    ])}'::jsonb,
                    'healthy',
                    {skill_level},
                    {skill_level * 2},
                    '{json.dumps({
                        "role": role_name,
                        "department": dept["name"],
                        "leader": dept["leader_name"],
                        "created_by": "workforce_establishment"
                    })}'::jsonb
                );
                """
                
                reg_result = subprocess.run([
                    "docker", "exec", "boarderframeos_postgres",
                    "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", register_query
                ], capture_output=True, text=True)
                
                if reg_result.returncode == 0:
                    total_created += 1
                    status_icon = "🟢" if registry_status == "online" else "🟡"
                    print(f"   {status_icon} {agent_name} - {role_name} ({dev_status})")
    
    # Update department performance metrics
    print("\n📊 Updating department performance metrics...")
    
    update_metrics_query = """
    UPDATE department_performance dp
    SET 
        assigned_agents_count = (
            SELECT COUNT(*) 
            FROM agents a 
            WHERE a.department = (SELECT name FROM departments WHERE id = dp.department_id)
        ),
        active_agents_count = (
            SELECT COUNT(*) 
            FROM agents a 
            WHERE a.department = (SELECT name FROM departments WHERE id = dp.department_id)
            AND a.operational_status IN ('operational', 'learning')
        ),
        health_score = CASE 
            WHEN assigned_agents_count > 0 THEN 75.0
            ELSE 25.0
        END,
        updated_at = CURRENT_TIMESTAMP;
    """
    
    subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", update_metrics_query
    ], capture_output=True, text=True)
    
    # Show summary statistics
    print("\n📊 Workforce Establishment Summary...")
    
    summary_query = """
    SELECT 
        'Total Agents' as metric, COUNT(*) as value 
    FROM agents
    UNION ALL
    SELECT 
        'Workforce Agents', COUNT(*) 
    FROM agents 
    WHERE agent_type = 'workforce'
    UNION ALL
    SELECT 
        'Operational Agents', COUNT(*) 
    FROM agents 
    WHERE operational_status = 'operational'
    UNION ALL
    SELECT 
        'In Training', COUNT(*) 
    FROM agents 
    WHERE development_status IN ('training', 'testing')
    UNION ALL
    SELECT 
        'Planned Agents', COUNT(*) 
    FROM agents 
    WHERE development_status = 'planned'
    UNION ALL
    SELECT 
        'Departments Staffed', COUNT(DISTINCT department) 
    FROM agents 
    WHERE agent_type = 'workforce';
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", summary_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\nWorkforce Metrics:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    metric = parts[0].strip()
                    value = parts[1].strip()
                    print(f"   {metric}: {value}")
    
    # Show development pipeline
    print("\n🔄 Development Pipeline Status...")
    
    pipeline_query = """
    SELECT 
        development_status,
        operational_status,
        COUNT(*) as agents,
        ROUND(AVG(training_progress) * 100) as avg_progress
    FROM agents
    WHERE agent_type = 'workforce'
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
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", pipeline_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\nDevelopment Status:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    dev_status = parts[0].strip()
                    op_status = parts[1].strip()
                    count = parts[2].strip()
                    progress = parts[3].strip() or "0"
                    print(f"   {dev_status} / {op_status}: {count} agents ({progress}% progress)")
    
    print(f"\n✅ Workforce establishment complete!")
    print(f"   Created {total_created} new workforce agents")
    print("\n🌐 View the updated workforce at:")
    print("   http://localhost:8888 -> Registry tab")
    print("\n💡 Next steps:")
    print("   - Monitor agent training progress")
    print("   - Deploy ready agents to production")
    print("   - Scale departments based on workload")


if __name__ == "__main__":
    establish_workforce()