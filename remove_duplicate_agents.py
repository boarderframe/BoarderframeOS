#!/usr/bin/env python3
"""
Remove duplicate agent entries, keeping only one per implemented agent
"""

import psycopg2

def remove_duplicate_agents():
    """Remove duplicate agent entries"""
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='boarderframeos',
            user='boarderframe',
            password='boarderframe_secure_2025'
        )
        cur = conn.cursor()
        
        print("🔍 Finding and removing duplicate agents...")
        print("=" * 60)
        
        # Find agents with duplicates
        cur.execute("""
            SELECT name, COUNT(*) as count
            FROM agent_registry
            WHERE name IN ('Solomon', 'David', 'Adam', 'Eve', 'Bezalel')
            GROUP BY name
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cur.fetchall()
        
        for agent_name, count in duplicates:
            print(f"\n📋 Found {count} entries for {agent_name}")
            
            # Get all IDs for this agent, ordered by registered_at
            cur.execute("""
                SELECT agent_id, registered_at
                FROM agent_registry
                WHERE name = %s
                ORDER BY registered_at ASC
            """, (agent_name,))
            
            agent_ids = cur.fetchall()
            
            # Keep the first one, delete the rest
            keep_id = agent_ids[0][0]
            delete_ids = [aid[0] for aid in agent_ids[1:]]
            
            print(f"   ✅ Keeping agent_id: {keep_id}")
            print(f"   ❌ Deleting {len(delete_ids)} duplicates")
            
            # Delete duplicates
            for delete_id in delete_ids:
                cur.execute("DELETE FROM agent_registry WHERE agent_id = %s", (delete_id,))
        
        conn.commit()
        
        # Show final counts
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE development_status = 'implemented') as implemented,
                COUNT(*) FILTER (WHERE development_status = 'planned') as planned
            FROM agent_registry
        """)
        
        row = cur.fetchone()
        print("\n✅ Cleanup complete!")
        print("=" * 60)
        print(f"📊 Final Agent Counts:")
        print(f"   Total: {row[0]}")
        print(f"   Implemented: {row[1]}")
        print(f"   Planned: {row[2]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error removing duplicate agents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    remove_duplicate_agents()