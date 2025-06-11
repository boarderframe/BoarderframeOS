#!/usr/bin/env python3
"""
Update leader statuses to reflect reality - all leaders are hired but not built/active
"""

import psycopg2


def update_leader_statuses():
    """Update leader statuses to 'hired' since they're not built yet"""

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5434,
            database="boarderframeos",
            user="boarderframe",
            password="boarderframe_secure_2025",
        )
        cur = conn.cursor()

        print("🔄 Updating leader statuses to reflect reality...")
        print("=" * 60)

        # First, check if we need to add more status options
        cur.execute(
            """
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'department_leaders'
            AND column_name = 'active_status'
        """
        )

        col_info = cur.fetchone()
        print(f"Column 'active_status' type: {col_info[1]} (max length: {col_info[2]})")

        # Update all leaders to 'hired' status
        cur.execute(
            """
            UPDATE department_leaders
            SET active_status = 'hired'
            WHERE active_status = 'active'
            RETURNING name, title
        """
        )

        updated_leaders = cur.fetchall()
        print(f"\n✅ Updated {len(updated_leaders)} leaders to 'hired' status")

        if len(updated_leaders) <= 10:
            for leader in updated_leaders:
                print(f"   - {leader[0]} ({leader[1]})")
        else:
            # Show first 5 and last 5
            for leader in updated_leaders[:5]:
                print(f"   - {leader[0]} ({leader[1]})")
            print(f"   ... and {len(updated_leaders) - 10} more ...")
            for leader in updated_leaders[-5:]:
                print(f"   - {leader[0]} ({leader[1]})")

        # Let's also add a development_status column to track build status
        print("\n🔧 Checking if we need to add development_status column...")
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'department_leaders'
            AND column_name = 'development_status'
        """
        )

        if not cur.fetchone():
            print("📝 Adding development_status column to department_leaders...")
            cur.execute(
                """
                ALTER TABLE department_leaders
                ADD COLUMN development_status VARCHAR(50) DEFAULT 'not_built'
            """
            )
            print("✅ Added development_status column")

        # Update development status for all leaders
        cur.execute(
            """
            UPDATE department_leaders
            SET development_status = 'not_built'
            WHERE development_status IS NULL OR development_status != 'not_built'
        """
        )

        # Show final status summary
        cur.execute(
            """
            SELECT
                active_status,
                development_status,
                COUNT(*) as count
            FROM department_leaders
            GROUP BY active_status, development_status
            ORDER BY count DESC
        """
        )

        print("\n📊 Final Leader Status Summary:")
        print("-" * 40)
        for row in cur.fetchall():
            print(f"Active: {row[0]:<10} Development: {row[1]:<15} Count: {row[2]}")

        conn.commit()
        print("\n✅ All updates committed successfully!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error updating leader statuses: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    update_leader_statuses()
