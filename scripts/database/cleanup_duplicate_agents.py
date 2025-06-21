#!/usr/bin/env python3
"""
Cleanup Duplicate Agent Records
Removes duplicate agent entries keeping the most recent one
"""

from datetime import datetime

import psycopg2


def cleanup_duplicates():
    """Remove duplicate agents, keeping the most recent record"""

    db_config = {
        "host": "localhost",
        "port": 5434,
        "database": "boarderframeos",
        "user": "boarderframe",
        "password": "boarderframe_secure_2025",
    }

    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    print("🧹 Cleaning up duplicate agent records...")

    # Find duplicates
    cur.execute(
        """
        SELECT name, COUNT(*) as count
        FROM agents
        GROUP BY name
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """
    )

    duplicates = cur.fetchall()
    print(f"Found {len(duplicates)} agents with duplicates:")

    total_removed = 0

    for agent_name, count in duplicates:
        print(f"  {agent_name}: {count} copies")

        # Keep only the most recent record (by updated_at, then created_at)
        cur.execute(
            """
            DELETE FROM agents
            WHERE name = %s
            AND id NOT IN (
                SELECT id FROM agents
                WHERE name = %s
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 1
            )
        """,
            (agent_name, agent_name),
        )

        removed = cur.rowcount
        total_removed += removed
        print(f"    Removed {removed} duplicate(s)")

    conn.commit()

    # Verify cleanup
    cur.execute("SELECT COUNT(*) FROM agents")
    total_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT development_status, operational_status, COUNT(*)
        FROM agents
        GROUP BY development_status, operational_status
        ORDER BY COUNT(*) DESC
    """
    )

    print(f"\n✅ Cleanup complete!")
    print(f"  - Removed {total_removed} duplicate records")
    print(f"  - Total agents now: {total_count}")
    print(f"\nFinal status distribution:")

    for row in cur.fetchall():
        print(f"  {row[0]}/{row[1]}: {row[2]} agents")

    cur.close()
    conn.close()


if __name__ == "__main__":
    cleanup_duplicates()
