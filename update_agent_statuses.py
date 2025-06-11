#!/usr/bin/env python3
"""
Update agent statuses in the database to reflect actual implementation status
"""

from datetime import datetime

import psycopg2


def update_agent_statuses():
    """Update agent statuses to reflect reality"""

    # Agents that have actual Python implementations
    implemented_agents = ['Solomon', 'David', 'Adam', 'Eve', 'Bezalel']

    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='boarderframeos',
            user='boarderframe',
            password='boarderframe_secure_2025'
        )
        cur = conn.cursor()

        print("🔄 Updating agent statuses to reflect reality...")
        print("=" * 60)

        # First, check current status
        cur.execute("""
            SELECT name, status, operational_status, development_status
            FROM agent_registry
            ORDER BY
                CASE
                    WHEN name IN %s THEN 0
                    ELSE 1
                END,
                name
        """, (tuple(implemented_agents),))

        agents = cur.fetchall()
        print(f"\n📊 Current Status: {len(agents)} agents in registry")
        print(f"✅ Implemented: {len(implemented_agents)} agents")
        print(f"📝 Planned/Not Implemented: {len(agents) - len(implemented_agents)} agents")

        # Update implemented agents to "offline" (exists but not running)
        cur.execute("""
            UPDATE agent_registry
            SET
                status = 'offline',
                operational_status = 'idle',
                development_status = 'implemented',
                last_heartbeat = NOW()
            WHERE name IN %s
            RETURNING name
        """, (tuple(implemented_agents),))

        updated_implemented = cur.fetchall()
        print(f"\n✅ Updated {len(updated_implemented)} implemented agents to 'offline/idle/implemented'")
        for agent in updated_implemented:
            print(f"   - {agent[0]}")

        # Update all other agents to "planned" status
        cur.execute("""
            UPDATE agent_registry
            SET
                status = 'offline',
                operational_status = 'not_implemented',
                development_status = 'planned',
                last_heartbeat = NULL
            WHERE name NOT IN %s
            RETURNING name
        """, (tuple(implemented_agents),))

        updated_planned = cur.fetchall()
        print(f"\n📋 Updated {len(updated_planned)} agents to 'offline/not_implemented/planned'")

        # Show summary of new statuses
        cur.execute("""
            SELECT
                development_status,
                operational_status,
                COUNT(*) as count
            FROM agent_registry
            GROUP BY development_status, operational_status
            ORDER BY count DESC
        """)

        print("\n📊 New Status Summary:")
        print("-" * 40)
        for row in cur.fetchall():
            print(f"Development: {row[0]:<15} Operational: {row[1]:<20} Count: {row[2]}")

        # Check if we need to add new operational status values
        cur.execute("""
            SELECT column_name, udt_name
            FROM information_schema.columns
            WHERE table_name = 'agent_registry'
            AND column_name = 'operational_status'
        """)

        col_info = cur.fetchone()
        if col_info:
            print(f"\n📝 Note: operational_status column type is '{col_info[1]}'")

            # If it's an enum, we might need to add 'not_implemented'
            if 'enum' in col_info[1]:
                print("⚠️  May need to add 'not_implemented' to operational_status enum")

                # Let's use a simpler approach - use existing statuses
                cur.execute("""
                    UPDATE agent_registry
                    SET
                        operational_status = 'development'
                    WHERE name NOT IN %s
                """, (tuple(implemented_agents),))

                print("✅ Updated non-implemented agents to 'development' operational status")

        conn.commit()
        print("\n✅ All updates committed successfully!")

        # Show final summary
        cur.execute("""
            SELECT
                CASE
                    WHEN name IN %s THEN 'Implemented'
                    ELSE 'Planned'
                END as implementation_status,
                COUNT(*) as count
            FROM agent_registry
            GROUP BY 1
            ORDER BY 1
        """, (tuple(implemented_agents),))

        print("\n🎯 Final Summary:")
        print("-" * 30)
        for row in cur.fetchall():
            print(f"{row[0]}: {row[1]} agents")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error updating agent statuses: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_agent_statuses()
