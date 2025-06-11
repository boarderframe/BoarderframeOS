#!/usr/bin/env python3
"""
Quick test to verify registry visualization is working
"""

import json
import subprocess


def test_registry_tables():
    """Test if registry tables exist and have data"""
    print("Testing Registry Tables...")

    # Test query
    query = """
    SELECT
        'agent_registry' as table_name, COUNT(*) as count
    FROM agent_registry
    UNION ALL
    SELECT
        'server_registry' as table_name, COUNT(*) as count
    FROM server_registry
    UNION ALL
    SELECT
        'database_registry' as table_name, COUNT(*) as count
    FROM database_registry
    UNION ALL
    SELECT
        'department_registry' as table_name, COUNT(*) as count
    FROM department_registry
    UNION ALL
    SELECT
        'divisions' as table_name, COUNT(*) as count
    FROM divisions;
    """

    try:
        result = subprocess.run([
            "docker", "exec", "boarderframeos_postgres",
            "psql", "-U", "boarderframe", "-d", "boarderframeos", "-t", "-c", query
        ], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print("✅ Registry tables accessible")
            print("\nTable counts:")
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        table = parts[0].strip()
                        count = parts[1].strip()
                        print(f"  {table}: {count} records")
        else:
            print("❌ Failed to query registry tables")
            print("Error:", result.stderr)
            print("\nYou may need to run the migration:")
            print("psql -U boarderframe -h localhost -p 5434 -d boarderframeos -f migrations/006_enhanced_registry_tables.sql")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure Docker is running and PostgreSQL container is up")

if __name__ == "__main__":
    test_registry_tables()
