#!/usr/bin/env python3
"""
Debug why active agents shows 2 instead of 80
"""

import psycopg2

def debug_metrics():
    """Check what's in the database vs what's displayed"""
    print("🔍 Debugging Active Agent Count")
    print("=" * 50)
    
    # Check database directly
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5434,
            database='boarderframeos',
            user='boarderframe',
            password='boarderframe_secure_2025'
        )
        cur = conn.cursor()
        
        # Check centralized metrics view
        cur.execute("SELECT * FROM hq_centralized_metrics")
        result = cur.fetchone()
        if result:
            print("\n📊 Database Centralized Metrics:")
            print(f"   Total Agents: {result[0]}")
            print(f"   Active Agents: {result[1]}")
            print(f"   Operational Agents: {result[2]}")
        
        # Check agents table directly
        cur.execute("SELECT COUNT(*) FROM agents WHERE status = 'online'")
        online_count = cur.fetchone()[0]
        print(f"\n📊 Agents with status='online': {online_count}")
        
        # Check what statuses exist
        cur.execute("SELECT status, COUNT(*) FROM agents GROUP BY status")
        status_counts = cur.fetchall()
        print("\n📊 Agent Status Distribution:")
        for status, count in status_counts:
            print(f"   {status}: {count}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("\n💡 The issue:")
    print("   - Database shows 80 agents with status='online'")
    print("   - But the page shows 2 (from running processes)")
    print("   - Need to ensure _get_centralized_metrics() is called")
    print("   - And that the override logic is working")


if __name__ == "__main__":
    debug_metrics()