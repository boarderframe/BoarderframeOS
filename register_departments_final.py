#!/usr/bin/env python3
"""
Final department registration script
"""

import subprocess
import json

def register_departments():
    """Register all departments in the registry"""
    print("🏢 Registering All Departments")
    print("=" * 50)
    
    # Get all departments
    get_depts_query = """
    SELECT 
        d.id,
        d.name,
        d.phase,
        d.priority,
        d.category,
        d.description,
        d.department_purpose,
        COUNT(dl.id) as leader_count
    FROM departments d
    LEFT JOIN department_leaders dl ON d.id = dl.department_id
    GROUP BY d.id, d.name, d.phase, d.priority, d.category, d.description, d.department_purpose
    ORDER BY d.phase, d.priority;
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-A", "-F", "|", "-c", get_depts_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout:
        departments = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 8:
                    departments.append({
                        "id": parts[0],
                        "name": parts[1],
                        "phase": parts[2] or "1",
                        "priority": parts[3] or "5",
                        "category": parts[4] or "operational",
                        "description": parts[5] or parts[6] or "Department operations",
                        "leader_count": parts[7]
                    })
        
        print(f"\n📝 Found {len(departments)} departments to register...")
        
        success_count = 0
        for dept in departments:
            # Prepare description, escaping single quotes
            description = dept["description"].replace("'", "''")
            
            register_query = f"""
            INSERT INTO department_registry (
                department_id, name, phase, priority, category,
                status, description, agent_count, metadata
            )
            VALUES (
                '{dept["id"]}'::uuid,
                '{dept["name"].replace("'", "''")}',
                {dept["phase"]},
                {dept["priority"]},
                '{dept["category"]}',
                'active',
                '{description}',
                {dept["leader_count"]},
                '{json.dumps({"leaders": int(dept["leader_count"]), "registered_by": "bulk_department_registration"})}'::jsonb
            )
            ON CONFLICT (department_id) DO UPDATE SET
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                agent_count = EXCLUDED.agent_count,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP;
            """
            
            reg_result = subprocess.run([
                "docker", "exec", "boarderframeos_postgres",
                "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", register_query
            ], capture_output=True, text=True)
            
            if reg_result.returncode == 0:
                success_count += 1
                print(f"   ✅ {dept['name']} (Phase {dept['phase']}, Priority {dept['priority']})")
            else:
                print(f"   ❌ {dept['name']}: {reg_result.stderr[:50]}")
        
        print(f"\n✅ Successfully registered {success_count}/{len(departments)} departments")
    
    # Update department leaders in registry
    print("\n📝 Updating department leaders...")
    
    leaders_query = """
    UPDATE department_registry dr
    SET leaders = (
        SELECT json_agg(json_build_object(
            'id', dl.id,
            'name', dl.name,
            'title', dl.title,
            'is_primary', dl.is_primary
        ))
        FROM department_leaders dl
        WHERE dl.department_id = dr.department_id
    )
    WHERE EXISTS (
        SELECT 1 FROM department_leaders dl2 
        WHERE dl2.department_id = dr.department_id
    );
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-c", leaders_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ Updated department leaders information")
    
    # Show summary
    print("\n📊 Department Registration Summary...")
    
    summary_query = """
    SELECT 
        'Total Departments' as metric, COUNT(*) as value 
    FROM department_registry
    UNION ALL
    SELECT 
        'Departments with Leaders' as metric, 
        COUNT(*) as value 
    FROM department_registry 
    WHERE leaders IS NOT NULL AND jsonb_array_length(leaders) > 0
    UNION ALL
    SELECT 
        'Phase 1 Departments' as metric, 
        COUNT(*) as value 
    FROM department_registry 
    WHERE phase = 1
    UNION ALL
    SELECT 
        'Active Departments' as metric, 
        COUNT(*) as value 
    FROM department_registry 
    WHERE status = 'active';
    """
    
    result = subprocess.run([
        "docker", "exec", "boarderframeos_postgres",
        "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", summary_query
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\nDepartment Metrics:")
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    metric = parts[0].strip()
                    value = parts[1].strip()
                    print(f"   {metric}: {value}")
    
    print("\n✅ Department Registration Complete!")


if __name__ == "__main__":
    register_departments()